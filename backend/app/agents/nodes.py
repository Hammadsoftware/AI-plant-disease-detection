import re
from collections.abc import Iterable

from app.agents.state import PlantDiagnosisState
from app.schemas.diagnosis import DiseaseExplanation, ExplanationDiagnosis
from app.schemas.pesticide import PesticideRecommendation
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
)


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

    async def extract_crop_and_disease(self, state: PlantDiagnosisState) -> PlantDiagnosisState:
        raw_class = state["raw_class_name"]
        crop_raw = raw_class.split("___", 1)[0] if "___" in raw_class else raw_class
        crop = " ".join(crop_raw.replace("_", " ").replace(",", " ").split()).strip()
        crop = crop or "Unknown plant"
        return {"crop": crop, "plant": crop}

    async def disease_research(self, state: PlantDiagnosisState) -> PlantDiagnosisState:
        if not state.get("include_web_research", True):
            return {"disease_research": _empty_bundle("disease")}
        crop, disease = state["crop"], state["predicted_disease"]
        queries = [
            f'"{crop}" "{disease}" symptoms pathogen disease cycle environmental conditions extension',
            f'"{crop}" "{disease}" management prevention government agriculture FAO',
        ]
        return await self._research("disease", queries, "disease_research")

    async def treatment_research(self, state: PlantDiagnosisState) -> PlantDiagnosisState:
        if not state.get("include_web_research", True):
            return {"treatment_research": _empty_bundle("treatment")}
        crop, disease = state["crop"], state["predicted_disease"]
        queries = [
            f'"{crop}" "{disease}" integrated pest management cultural biological physical chemical control',
            f'"{crop}" "{disease}" treatment management university extension agriculture',
        ]
        return await self._research("treatment", queries, "treatment_research")

    async def pesticide_research(self, state: PlantDiagnosisState) -> PlantDiagnosisState:
        if not state.get("include_web_research", True) or not state.get("include_pesticides", True):
            return {"pesticide_research": _empty_bundle("pesticide")}
        crop, disease = state["crop"], state["predicted_disease"]
        country = self.research_country
        queries = [
            f'"{crop}" "{disease}" {country} registered pesticide Department of Plant Protection',
            f'"{crop}" "{disease}" pesticide label active ingredient site:gov.pk',
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
        official_pk = any(
            source.source_type == "government"
            and (source.source.endswith(".pk") or ".gov.pk" in source.source)
            for source in pesticide_bundle.sources
        )
        if pesticide_bundle.status != "disabled" and not official_pk:
            warnings.append(
                "Pakistan pesticide registration could not be verified from an authoritative government source."
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

    async def generate_explanation(self, state: PlantDiagnosisState) -> PlantDiagnosisState:
        evidence = state["evidence"]
        if evidence.status in {"disabled", "unavailable"}:
            return {
                "explanation": None,
                "groq_status": "disabled",
                "errors": ["Groq synthesis was skipped because validated web evidence is unavailable."],
            }
        if not await self.groq_service.check_available():
            return {
                "explanation": None,
                "groq_status": "unavailable",
                "errors": ["The configured Groq model is unavailable."],
            }

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
                "registration_requires_authoritative_government_evidence": True,
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

    async def validate_final_response(self, state: PlantDiagnosisState) -> PlantDiagnosisState:
        explanation = state.get("explanation")
        if explanation is None:
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
            explanation.symptoms, disease_sources, "symptom", validation_warnings
        )
        possible_causes = _filter_supported(
            explanation.possible_causes, disease_sources, "cause", validation_warnings
        )
        cultural = _filter_supported(
            explanation.management.cultural, treatment_sources, "cultural management", validation_warnings
        )
        biological = _filter_supported(
            explanation.management.biological, treatment_sources, "biological management", validation_warnings
        )
        physical = _filter_supported(
            explanation.management.physical, treatment_sources, "physical management", validation_warnings
        )
        chemical = _filter_supported(
            explanation.management.chemical,
            treatment_sources + pesticide_sources,
            "chemical management",
            validation_warnings,
            reject_unsupported_dose=True,
        )
        prevention = _filter_supported(
            explanation.prevention, disease_sources + treatment_sources, "prevention", validation_warnings
        )
        recommendations = _filter_supported(
            explanation.recommendations,
            disease_sources + treatment_sources,
            "recommendation",
            validation_warnings,
        )
        pesticides = _validate_pesticides(
            explanation.pesticides,
            pesticide_sources,
            state["predicted_disease"],
            validation_warnings,
        )

        if state["uncertain_prediction"]:
            confidence_note = (
                "This is an uncertain image-based prediction below the configured confidence "
                "threshold. Provide a clearer image, multiple leaf images, and seek qualified "
                "agricultural verification before treatment."
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
            explanation.warnings
            + evidence.warnings
            + evidence.disagreements
            + validation_warnings
        )
        if pesticides:
            warnings = _unique(
                warnings
                + [
                    "Follow the current product label and applicable local requirements.",
                    "Use label-required personal protective equipment and safe handling practices.",
                ]
            )

        cleaned = explanation.model_copy(
            update={
                "summary": (
                    f"The vision model predicts {state['predicted_disease']} with "
                    f"{state['confidence']:.1%} confidence. The remaining fields summarize "
                    "the retrieved evidence and do not replace field diagnosis."
                ),
                "diagnosis": ExplanationDiagnosis(
                    disease=state["predicted_disease"],
                    confidence=state["confidence"],
                    confidence_note=confidence_note,
                ),
                "symptoms": symptoms,
                "possible_causes": possible_causes,
                "management": explanation.management.model_copy(
                    update={
                        "cultural": cultural,
                        "biological": biological,
                        "physical": physical,
                        "chemical": chemical,
                    }
                ),
                "pesticides": pesticides,
                "prevention": prevention,
                "recommendations": _unique(recommendations),
                "warnings": warnings,
                "sources": evidence.sources,
            }
        )
        return {"explanation": DiseaseExplanation.model_validate(cleaned)}


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


def _validate_pesticides(
    candidates: list[PesticideRecommendation],
    sources: list[ResearchSource],
    predicted_disease: str,
    warnings: list[str],
) -> list[PesticideRecommendation]:
    source_by_url = {source.url: source for source in sources}
    validated: list[PesticideRecommendation] = []
    for candidate in candidates:
        source = source_by_url.get(candidate.source.url)
        if source is None:
            warnings.append("A pesticide entry with an unknown source was omitted.")
            continue
        evidence_text = _normalize(f"{source.title} {source.snippet}")
        product_supported = _normalize(candidate.product_name) in evidence_text
        ingredient_supported = _normalize(candidate.active_ingredient) in evidence_text
        if not product_supported or not ingredient_supported:
            warnings.append("A pesticide entry not explicitly supported by its cited source was omitted.")
            continue

        official_pakistan_source = (
            source.source_type == "government"
            and (source.source.endswith(".pk") or ".gov.pk" in source.source)
            and any(term in evidence_text for term in ("registered", "registration"))
        )
        registration_status = "verified" if (
            candidate.registration_status == "verified" and official_pakistan_source
        ) else "unverified"

        application = " ".join(candidate.application_information.split()).strip()
        if _normalize(application) not in evidence_text:
            application = (
                "No source-verifiable application rate was retrieved. Follow the current "
                "product label and applicable local requirements."
            )
        validated.append(
            candidate.model_copy(
                update={
                    "target_disease_or_pest": predicted_disease,
                    "registration_status": registration_status,
                    "country": "Pakistan",
                    "application_information": application,
                    "source": source,
                }
            )
        )
    return validated


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
