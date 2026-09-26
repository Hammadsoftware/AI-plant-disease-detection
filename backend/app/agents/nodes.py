import logging
import re
from collections.abc import Iterable

from app.agents.state import PlantDiagnosisState
from app.schemas.diagnosis import (
    DiseaseExplanation,
    ExplanationDiagnosis,
    ManagementRecommendations,
)
from app.schemas.pesticide import PesticideDraft, PesticideRecommendation
from app.schemas.research import EvidenceClaim, EvidenceReport, ResearchBundle, ResearchSource
from app.services.groq_service import (
    GroqInvalidResponseError,
    GroqNotConfiguredError,
    GroqService,
    GroqTimeoutError,
    GroqUnavailableError,
)
from app.services.web_search_service import (
    WebSearchError,
    WebSearchNotConfiguredError,
    WebSearchService,
    is_official_registration_source,
)


logger = logging.getLogger(__name__)


class AgentValidationError(RuntimeError):
    pass


_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is",
    "it", "of", "on", "or", "that", "the", "their", "this", "to", "with", "your",
}
_DOSE_PATTERN = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:g|kg|mg|ml|l|litre|liter|oz|lb|%|ppm)(?:\s*/\s*\w+)?\b",
    re.IGNORECASE,
)
# The 38 training classes label disease-free plants as "<crop>___healthy".
_HEALTHY_PATTERN = re.compile(r"___healthy$|healthy$", re.IGNORECASE)


def _empty_bundle(topic: str, status: str = "disabled", error: str | None = None) -> ResearchBundle:
    return ResearchBundle(
        topic=topic,
        status=status,
        errors=[error] if error else [],
    )


class DiseaseAgentNodes:
    def __init__(
        self,
        search_service: WebSearchService,
        groq_service: GroqService,
        low_confidence_threshold: float,
        research_country: str,
    ) -> None:
        self.search_service = search_service
        self.groq_service = groq_service
        self.low_confidence_threshold = low_confidence_threshold
        self.research_country = research_country

    async def validate_prediction(self, state: PlantDiagnosisState) -> PlantDiagnosisState:
        disease = state.get("predicted_disease")
        confidence = state.get("confidence")
        predictions = state.get("top_predictions")
        if not isinstance(disease, str) or not disease.strip():
            raise AgentValidationError("The graph received no predicted disease.")
        if not isinstance(confidence, (int, float)) or not 0.0 <= confidence <= 1.0:
            raise AgentValidationError("The graph received invalid prediction confidence.")
        if not isinstance(predictions, list) or not predictions:
            raise AgentValidationError("The graph received no ranked predictions.")
        return {"uncertain_prediction": confidence < self.low_confidence_threshold}

    async def extract_disease_context(self, state: PlantDiagnosisState) -> PlantDiagnosisState:
        """Derive the crop, the plant name, and whether the class is a healthy class."""
        raw_class = state["raw_class_name"]
        crop_raw = raw_class.split("___", 1)[0] if "___" in raw_class else raw_class
        crop = " ".join(crop_raw.replace("_", " ").replace(",", " ").split()).strip()
        crop = crop or "Unknown plant"
        return {
            "crop": crop,
            "plant": crop,
            "is_healthy_class": bool(_HEALTHY_PATTERN.search(raw_class.strip())),
        }

    async def parallel_research(self, state: PlantDiagnosisState) -> PlantDiagnosisState:
        """Fan-out point. Research is only dispatched when it can produce evidence.

        A `healthy` class is not a disease, so disease, treatment, and pesticide
        queries are skipped rather than searching for symptoms of a non-existent
        condition.
        """
        if not state.get("include_web_research", True):
            return {}
        if state.get("is_healthy_class", False):
            return {
                "disease_research": _empty_bundle("disease"),
                "treatment_research": _empty_bundle("treatment"),
                "pesticide_research": _empty_bundle("pesticide"),
                "warnings": [
                    "The model classified this plant as healthy, so no disease, treatment, "
                    "or pesticide research was performed."
                ],
            }
        return {}

    def _research_enabled(self, state: PlantDiagnosisState) -> bool:
        """Research only runs for real disease classes with web search switched on."""
        if not state.get("include_web_research", True):
            return False
        return not state.get("is_healthy_class", False)

    async def disease_research(self, state: PlantDiagnosisState) -> PlantDiagnosisState:
        if not self._research_enabled(state):
            return {"disease_research": _empty_bundle("disease")}
        crop, disease = state["crop"], state["predicted_disease"]
        queries = [
            f'"{crop}" "{disease}" symptoms pathogen disease cycle environmental conditions extension',
            f'"{crop}" "{disease}" causal organism diagnosis government agriculture FAO',
        ]
        return await self._research("disease", queries, "disease_research")

    async def treatment_research(self, state: PlantDiagnosisState) -> PlantDiagnosisState:
        if not self._research_enabled(state):
            return {"treatment_research": _empty_bundle("treatment")}
        crop, disease = state["crop"], state["predicted_disease"]
        queries = [
            f'"{crop}" "{disease}" integrated pest management cultural biological physical control',
            f'"{crop}" "{disease}" treatment management prevention university extension agriculture',
        ]
        return await self._research("treatment", queries, "treatment_research")

    async def pesticide_research(self, state: PlantDiagnosisState) -> PlantDiagnosisState:
        if not self._research_enabled(state) or not state.get("include_pesticides", True):
            return {"pesticide_research": _empty_bundle("pesticide")}
        crop, disease = state["crop"], state["predicted_disease"]
        country = self.research_country
        queries = [
            f'"{crop}" "{disease}" {country} registered pesticide Department of Plant Protection',
            f'"{crop}" "{disease}" fungicide active ingredient label {country} agriculture department',
        ]
        return await self._research("pesticide", queries, "pesticide_research")

    async def _research(
        self, topic: str, queries: list[str], state_key: str
    ) -> PlantDiagnosisState:
        try:
            bundle = await self.search_service.search(queries, topic=topic)
            result: PlantDiagnosisState = {state_key: bundle}  # type: ignore[typeddict-item]
            if bundle.errors:
                result["errors"] = bundle.errors
            return result
        except WebSearchNotConfiguredError:
            message = "Live web search is not configured."
        except WebSearchError:
            message = f"Live {topic} evidence retrieval failed."
        except Exception:
            message = f"Live {topic} evidence retrieval failed."
        return {
            state_key: _empty_bundle(topic, "unavailable", message),  # type: ignore[typeddict-item]
            "errors": [message],
        }

    async def evidence_validation(self, state: PlantDiagnosisState) -> PlantDiagnosisState:
        bundles = [
            state.get("disease_research", _empty_bundle("disease", "unavailable")),
            state.get("treatment_research", _empty_bundle("treatment", "unavailable")),
            state.get("pesticide_research", _empty_bundle("pesticide", "unavailable")),
        ]
        unique_sources: dict[str, ResearchSource] = {}
        claims: list[EvidenceClaim] = []
        warnings: list[str] = []
        for bundle in bundles:
            category_sources = bundle.sources[:6]
            for source in category_sources:
                unique_sources.setdefault(source.url, source)
                claims.append(
                    EvidenceClaim(
                        category=bundle.topic,
                        claim=source.snippet,
                        source_urls=[source.url],
                        authoritative=source.authoritative,
                    )
                )
            if bundle.status not in {"disabled"} and category_sources and not any(
                source.authoritative for source in category_sources
            ):
                warnings.append(
                    f"No authoritative {bundle.topic} source was retrieved; treat that evidence as uncertain."
                )

        pesticide_bundle = bundles[2]
        official_registration_source = any(
            is_official_registration_source(source) for source in pesticide_bundle.sources
        )
        if pesticide_bundle.status != "disabled" and not official_registration_source:
            warnings.append(
                f"{self.research_country} pesticide registration could not be verified from an "
                "official government source; any product listed will be marked unverified."
            )

        active = [bundle for bundle in bundles if bundle.status != "disabled"]
        if not active:
            status = "disabled"
        elif not unique_sources:
            status = "unavailable"
        elif any(bundle.status != "available" for bundle in active):
            status = "partial"
        else:
            status = "available"

        disagreements = _detect_explicit_disagreement(unique_sources.values())
        report = EvidenceReport(
            status=status,
            claims=claims,
            sources=list(unique_sources.values()),
            disagreements=disagreements,
            warnings=warnings,
        )
        return {
            "evidence": report,
            "research_status": status,
            "warnings": warnings + disagreements,
        }

    async def groq_explanation(self, state: PlantDiagnosisState) -> PlantDiagnosisState:
        evidence = state["evidence"]
        if state.get("is_healthy_class", False):
            # Not an error: there is no disease to explain. `validate_structured_output`
            # returns a deterministic, evidence-free explanation instead.
            return {
                "explanation": None,
                "groq_status": "disabled",
            }
        if not state.get("include_web_research", True):
            # The client opted out. This is not a failure, so no error is recorded.
            return {"explanation": None, "groq_status": "disabled"}
        if evidence.status in {"disabled", "unavailable"}:
            return {
                "explanation": None,
                "groq_status": "disabled",
                "errors": ["Groq synthesis was skipped because validated web evidence is unavailable."],
            }
        if not await self.groq_service.check_available():
            # The availability probe can fail on a slow network rather than an invalid
            # credential. Validated evidence is already in hand, so attempt generation
            # and let the real call decide. A genuinely bad key fails fast with 401.
            logger.warning(
                "Groq availability probe failed; attempting synthesis with %s anyway",
                self.groq_service.model,
            )

        payload = {
            "model_prediction": {
                "image_id": state.get("image_id"),
                "predicted_disease": state["predicted_disease"],
                "raw_class_name": state["raw_class_name"],
                "crop": state["crop"],
                "confidence": state["confidence"],
                "uncertain_prediction": state["uncertain_prediction"],
                "top_predictions": state["top_predictions"],
            },
            "validated_evidence": evidence.model_dump(mode="json"),
            "pesticide_policy": {
                "country": self.research_country,
                "registration_requires_official_government_evidence": True,
                "omit_unsupported_products_and_rates": True,
                "preserve_source_units_exactly": True,
            },
        }
        try:
            explanation = await self.groq_service.generate_explanation(payload)
            return {"explanation": explanation, "groq_status": "available"}
        except GroqNotConfiguredError:
            message = "The Groq explanation service is not configured."
        except GroqTimeoutError:
            message = "Groq explanation generation timed out."
        except GroqInvalidResponseError:
            message = "Groq returned invalid structured output."
        except GroqUnavailableError:
            message = "Groq explanation generation is unavailable."
        return {
            "explanation": None,
            "groq_status": "unavailable",
            "errors": [message],
        }

    async def validate_structured_output(self, state: PlantDiagnosisState) -> PlantDiagnosisState:
        """Last policy gate before anything reaches the client.

        It restores the vision model's disease and confidence verbatim, drops
        claims the retrieved evidence does not support, and rebuilds each
        pesticide against a real retrieved source.
        """
        if state.get("is_healthy_class", False):
            return {"final_explanation": self._healthy_explanation(state)}
        draft = state.get("explanation")
        if draft is None:
            return {}
        evidence = state["evidence"]
        disease_sources = [
            source for source in evidence.sources if any(
                claim.category == "disease" and source.url in claim.source_urls
                for claim in evidence.claims
            )
        ]
        treatment_sources = [
            source for source in evidence.sources if any(
                claim.category == "treatment" and source.url in claim.source_urls
                for claim in evidence.claims
            )
        ]
        pesticide_sources = [
            source for source in evidence.sources if any(
                claim.category == "pesticide" and source.url in claim.source_urls
                for claim in evidence.claims
            )
        ]
        validation_warnings: list[str] = []

        symptoms = _filter_supported(
            draft.symptoms, disease_sources, "symptom", validation_warnings
        )
        possible_causes = _filter_supported(
            draft.possible_causes, disease_sources, "cause", validation_warnings
        )
        cultural = _filter_supported(
            draft.management.cultural, treatment_sources, "cultural management", validation_warnings
        )
        biological = _filter_supported(
            draft.management.biological, treatment_sources, "biological management", validation_warnings
        )
        physical = _filter_supported(
            draft.management.physical, treatment_sources, "physical management", validation_warnings
        )
        chemical = _filter_supported(
            draft.management.chemical,
            treatment_sources + pesticide_sources,
            "chemical management",
            validation_warnings,
            reject_unsupported_dose=True,
        )
        prevention = _filter_supported(
            draft.prevention, disease_sources + treatment_sources, "prevention", validation_warnings
        )
        recommendations = _filter_supported(
            draft.recommendations,
            disease_sources + treatment_sources,
            "recommendation",
            validation_warnings,
        )
        pesticides = self._validate_pesticides(
            draft.pesticides,
            pesticide_sources,
            state["predicted_disease"],
            validation_warnings,
        )

        if state["uncertain_prediction"]:
            confidence_note = (
                "This is an uncertain image-based prediction below the configured confidence "
                "threshold. The image-based diagnosis is uncertain: provide a clearer image, "
                "multiple leaf images, and qualified agricultural verification before treatment."
            )
            recommendations.extend(
                item for item in (
                    "Capture a clearer, well-lit image of the affected leaf.",
                    "Submit multiple images showing both affected and unaffected plant parts.",
                    "Ask a qualified local agricultural expert to verify the diagnosis.",
                ) if item not in recommendations
            )
        else:
            confidence_note = (
                "The model confidence is not the same as a confirmed field diagnosis; compare "
                "the plant with the cited evidence and seek local verification when needed."
            )

        warnings = _unique(
            draft.warnings
            + evidence.warnings
            + evidence.disagreements
            + validation_warnings
        )
        if pesticides:
            warnings = _unique(
                warnings
                + [
                    "Follow the current product label and applicable local agricultural requirements.",
                    "Use label-required personal protective equipment and safe handling practices.",
                ]
            )

        final = DiseaseExplanation(
            summary=(
                f"The vision model predicts {state['predicted_disease']} with "
                f"{state['confidence']:.1%} confidence. The remaining fields summarize "
                "the retrieved evidence and do not replace field diagnosis."
            ),
            diagnosis=ExplanationDiagnosis(
                disease=state["predicted_disease"],
                confidence=state["confidence"],
                confidence_note=confidence_note,
            ),
            symptoms=symptoms,
            possible_causes=possible_causes,
            management=draft.management.model_copy(
                update={
                    "cultural": cultural,
                    "biological": biological,
                    "physical": physical,
                    "chemical": chemical,
                }
            ),
            pesticides=pesticides,
            prevention=prevention,
            recommendations=_unique(recommendations),
            warnings=warnings,
            sources=evidence.sources,
        )
        return {"final_explanation": final}

    def _healthy_explanation(self, state: PlantDiagnosisState) -> DiseaseExplanation:
        """Deterministic response for a healthy class.

        No research is run for a healthy classification, so this deliberately
        contains no symptoms, causes, management, pesticides, or sources. It only
        restates what the model produced and how to interpret it.
        """
        if state["uncertain_prediction"]:
            confidence_note = (
                "This is an uncertain image-based prediction below the configured confidence "
                "threshold. A healthy classification is not a confirmed field diagnosis: "
                "provide a clearer image and qualified agricultural verification if symptoms "
                "are present."
            )
            recommendations = [
                "Capture a clearer, well-lit image of the affected leaf.",
                "Submit multiple images showing both affected and unaffected plant parts.",
                "Ask a qualified local agricultural expert to review the plant if symptoms are present.",
            ]
        else:
            confidence_note = (
                "The model found no disease class for this plant. A healthy classification is "
                "not a confirmed field diagnosis; re-check the plant if symptoms develop."
            )
            recommendations = [
                "Continue to monitor the plant and re-submit images if symptoms develop.",
                "Compare the plant with the model's alternative predictions if you see symptoms.",
            ]
        return DiseaseExplanation(
            summary=(
                f"The vision model classifies this plant as {state['predicted_disease']} with "
                f"{state['confidence']:.1%} confidence. No disease class was detected, so no "
                "disease, treatment, or pesticide evidence was retrieved."
            ),
            diagnosis=ExplanationDiagnosis(
                disease=state["predicted_disease"],
                confidence=state["confidence"],
                confidence_note=confidence_note,
            ),
            management=ManagementRecommendations(),
            pesticides=[],
            recommendations=recommendations,
            warnings=[
                "No web research was performed because the model classified the plant as healthy."
            ],
            sources=[],
        )

    def _validate_pesticides(
        self,
        candidates: list[PesticideDraft],
        sources: list[ResearchSource],
        predicted_disease: str,
        warnings: list[str],
    ) -> list[PesticideRecommendation]:
        """Rebuild every proposed pesticide from retrieved evidence.

        Nothing survives unless the cited pesticide source literally contains the
        product name and the active ingredient. ``verified`` registration survives
        only with explicit registration wording from an official government
        source; everything else is downgraded to ``unverified``, and an
        application rate is kept only when the source states it verbatim.
        """
        source_by_url = {source.url: source for source in sources}
        source_by_title: dict[str, ResearchSource] = {}
        for source in sources:
            source_by_title.setdefault(_normalize(source.title), source)

        validated: list[PesticideRecommendation] = []
        for candidate in candidates:
            source = source_by_url.get(candidate.source.url) or source_by_title.get(
                _normalize(candidate.source.title)
            )
            if source is None:
                warnings.append("A pesticide entry with an unknown source was omitted.")
                continue
            evidence_text = _normalize(f"{source.title} {source.snippet}")
            product_supported = _normalize(candidate.product_name) in evidence_text
            ingredient_supported = _normalize(candidate.active_ingredient) in evidence_text
            if not product_supported or not ingredient_supported:
                warnings.append("A pesticide entry not explicitly supported by its cited source was omitted.")
                continue

            registration_verified = (
                is_official_registration_source(source)
                and any(term in evidence_text for term in ("registered", "registration"))
            )
            registration_status = (
                "verified"
                if candidate.registration_status == "verified" and registration_verified
                else "unverified"
            )

            application = " ".join(candidate.application_information.split()).strip()
            if _normalize(application) not in evidence_text:
                application = (
                    "No source-verifiable application rate was retrieved. Follow the current "
                    "product label and applicable local agricultural requirements."
                )
            validated.append(
                PesticideRecommendation(
                    product_name=candidate.product_name,
                    active_ingredient=candidate.active_ingredient,
                    type=candidate.type,
                    target_disease_or_pest=predicted_disease,
                    registration_status=registration_status,
                    country=self.research_country,
                    application_information=application,
                    source=source,
                )
            )
        return validated


def _detect_explicit_disagreement(sources: Iterable[ResearchSource]) -> list[str]:
    snippets = [source.snippet.casefold() for source in sources]
    positive = any("recommended" in snippet for snippet in snippets)
    negative = any(
        phrase in snippet
        for snippet in snippets
        for phrase in ("not recommended", "no longer recommended", "should not be used")
    )
    if positive and negative:
        return [
            "Retrieved sources contain conflicting recommendation language; inspect the cited sources and current local guidance."
        ]
    return []


def _filter_supported(
    items: list[str],
    sources: list[ResearchSource],
    label: str,
    warnings: list[str],
    *,
    reject_unsupported_dose: bool = False,
) -> list[str]:
    kept: list[str] = []
    for item in items:
        text = " ".join(item.split()).strip()
        if not text:
            continue
        exact_support = any(_normalize(text) in _normalize(source.snippet) for source in sources)
        if reject_unsupported_dose and _DOSE_PATTERN.search(text) and not exact_support:
            warnings.append(f"An unsupported dosage was removed from {label} guidance.")
            continue
        if exact_support or any(_claim_overlap(text, source.snippet) for source in sources):
            kept.append(text)
        else:
            warnings.append(f"An unsupported {label} claim was omitted.")
    return _unique(kept)


def _claim_overlap(claim: str, evidence: str) -> bool:
    claim_tokens = _tokens(claim)
    evidence_tokens = _tokens(evidence)
    if not claim_tokens:
        return False
    overlap = len(claim_tokens & evidence_tokens)
    required = 1 if len(claim_tokens) <= 3 else min(3, max(2, len(claim_tokens) // 3))
    return overlap >= required


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.casefold())
        if len(token) > 2 and token not in _STOP_WORDS
    }


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9.%/]+", value.casefold()))


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))
