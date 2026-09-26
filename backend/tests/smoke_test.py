"""Run with: PYTHONPATH=. UPLOAD_DIR=/tmp/plant-api-test python tests/smoke_test.py."""

import asyncio
import io
import os

from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.agents.graph import DiseaseResearchAgent
from app.agents.nodes import DiseaseAgentNodes
from app.schemas.diagnosis import (
    Diagnosis,
    DiseaseExplanationDraft,
    ExplanationDiagnosis,
    ManagementRecommendations,
    PredictionItem,
)
from app.schemas.pesticide import PesticideDraft, SourceRef
from app.schemas.research import ResearchBundle, ResearchSource


DISEASE_SOURCE = ResearchSource(
    title="University Extension Rust Guide",
    url="https://extension.example.edu/corn-rust",
    source="extension.example.edu",
    source_type="university_extension",
    snippet=(
        "Common rust of corn causes small cinnamon-brown pustules. The fungus develops during "
        "cool humid weather and wind carries spores between plants."
    ),
    query="corn common rust symptoms",
    authoritative=True,
)
TREATMENT_SOURCE = ResearchSource(
    title="University Extension IPM Guide",
    url="https://extension.example.edu/corn-rust-ipm",
    source="extension.example.edu",
    source_type="university_extension",
    snippet=(
        "Integrated management includes resistant hybrids, scouting, removing volunteer corn, "
        "and using a labeled fungicide only when disease risk and crop stage justify treatment."
    ),
    query="corn common rust integrated management",
    authoritative=True,
)
PESTICIDE_SOURCE = ResearchSource(
    title="Pakistan Department of Plant Protection registration record",
    url="https://dpp.gov.pk/registered-products/ruststop",
    source="dpp.gov.pk",
    source_type="government",
    snippet=(
        "Registered product RustStop 50 WP contains active ingredient Mancozeb for corn common "
        "rust. Apply 2 g/L to corn foliage according to the current product label."
    ),
    query="Pakistan corn rust registered pesticide",
    authoritative=True,
)


class FakeSearchService:
    async def search(self, queries, *, topic: str) -> ResearchBundle:
        source = {
            "disease": DISEASE_SOURCE,
            "treatment": TREATMENT_SOURCE,
            "pesticide": PESTICIDE_SOURCE,
        }[topic]
        return ResearchBundle(topic=topic, status="available", queries=list(queries), sources=[source])


class FakeGroqService:
    async def check_available(self) -> bool:
        return True

    async def generate_explanation(self, evidence_payload: dict) -> DiseaseExplanationDraft:
        assert evidence_payload["model_prediction"]["predicted_disease"] == "Corn (Maize) Common Rust"
        return DiseaseExplanationDraft(
            summary="An intentionally replaceable model summary.",
            diagnosis=ExplanationDiagnosis(
                disease="A different disease",
                confidence=0.99,
                confidence_note="Overconfident output",
            ),
            symptoms=["Small cinnamon-brown pustules"],
            possible_causes=["Fungus favored by cool humid weather"],
            management=ManagementRecommendations(
                cultural=["Use resistant hybrids and remove volunteer corn"],
                biological=[],
                physical=["Scout corn plants"],
                chemical=["Use a labeled fungicide only when disease risk justifies treatment"],
            ),
            pesticides=[
                PesticideDraft(
                    product_name="RustStop 50 WP",
                    active_ingredient="Mancozeb",
                    type="fungicide",
                    registration_status="verified",
                    application_information="Apply 2 g/L to corn foliage according to the current product label.",
                    source=SourceRef(title=PESTICIDE_SOURCE.title, url=PESTICIDE_SOURCE.url),
                )
            ],
            prevention=["Use resistant hybrids"],
            recommendations=["Scout corn plants before deciding on treatment"],
            warnings=[],
        )


def make_diagnosis(class_name: str, disease: str, confidence: float) -> Diagnosis:
    return Diagnosis(
        class_name=class_name,
        disease=disease,
        confidence=confidence,
        is_uncertain=confidence < 0.70,
        top_predictions=[
            PredictionItem(class_name=class_name, disease=disease, confidence=confidence)
        ],
        class_probabilities={class_name: confidence},
    )


async def test_graph() -> None:
    diagnosis = make_diagnosis("Corn_(maize)___Common_rust_", "Corn (Maize) Common Rust", 0.42)
    nodes = DiseaseAgentNodes(FakeSearchService(), FakeGroqService(), 0.70, "Pakistan")
    agent = DiseaseResearchAgent(nodes)
    outcome = await agent.explain(
        "a" * 32,
        diagnosis,
        include_web_research=True,
        include_pesticides=True,
    )
    assert outcome.research_status == "available"
    assert outcome.groq_status == "available"
    assert outcome.explanation is not None
    # The LLM tried to replace the model prediction; the validator restored it.
    assert outcome.explanation.diagnosis.disease == diagnosis.disease
    assert outcome.explanation.diagnosis.confidence == diagnosis.confidence
    assert "uncertain" in outcome.explanation.diagnosis.confidence_note.lower()
    pesticide = outcome.explanation.pesticides[0]
    assert pesticide.registration_status == "verified"
    assert pesticide.type == "fungicide"
    assert pesticide.country == "Pakistan"
    assert pesticide.source.url == PESTICIDE_SOURCE.url
    assert len(outcome.explanation.sources) == 3


async def test_unregistered_pesticide_is_downgraded() -> None:
    """A product on a non-government source can never be presented as registered."""

    class ExtensionGroqService(FakeGroqService):
        async def generate_explanation(self, evidence_payload: dict) -> DiseaseExplanationDraft:
            draft = await super().generate_explanation(evidence_payload)
            return draft.model_copy(
                update={
                    "pesticides": [
                        draft.pesticides[0].model_copy(
                            update={
                                "source": SourceRef(
                                    title=TREATMENT_SOURCE.title, url=TREATMENT_SOURCE.url
                                )
                            }
                        )
                    ]
                }
            )

    nodes = DiseaseAgentNodes(FakeSearchService(), ExtensionGroqService(), 0.70, "Pakistan")
    agent = DiseaseResearchAgent(nodes)
    outcome = await agent.explain(
        "a" * 32,
        make_diagnosis("Corn_(maize)___Common_rust_", "Corn (Maize) Common Rust", 0.91),
        include_web_research=True,
        include_pesticides=True,
    )
    assert outcome.explanation is not None
    # The extension source does not contain the product name, so it is dropped.
    assert outcome.explanation.pesticides == []
    assert any("pesticide" in warning.lower() for warning in outcome.explanation.warnings)


async def test_healthy_class_skips_research() -> None:
    """A healthy class must not trigger symptom or pesticide searches."""

    class ExplodingSearchService:
        async def search(self, queries, *, topic: str) -> ResearchBundle:
            raise AssertionError(f"research must not run for a healthy class, got {topic}")

    diagnosis = make_diagnosis("Tomato___healthy", "Tomato Healthy", 0.95)
    nodes = DiseaseAgentNodes(ExplodingSearchService(), FakeGroqService(), 0.70, "Pakistan")
    agent = DiseaseResearchAgent(nodes)
    outcome = await agent.explain(
        "a" * 32, diagnosis, include_web_research=True, include_pesticides=True
    )
    assert outcome.research_status == "disabled"
    assert outcome.groq_status == "disabled"
    # A deterministic, evidence-free explanation is returned instead of an error.
    assert outcome.explanation is not None
    assert outcome.explanation.diagnosis.disease == "Tomato Healthy"
    assert outcome.explanation.symptoms == []
    assert outcome.explanation.pesticides == []
    assert outcome.explanation.sources == []
    assert outcome.explanation.warnings
    assert not outcome.errors
    assert any("healthy" in warning.lower() for warning in outcome.warnings)


async def test_search_unavailable_keeps_agent_running() -> None:
    """A missing Tavily key degrades evidence, it does not break the workflow."""
    from app.core.config import Settings
    from app.services.web_search_service import WebSearchService

    settings = Settings(search_provider="tavily", tavily_api_key="")
    search = WebSearchService(settings)
    assert search.configured is False

    class UnreachableGroqService:
        async def check_available(self) -> bool:
            return True

        async def generate_explanation(self, evidence_payload: dict):
            raise AssertionError("Groq must not run without validated evidence")

    nodes = DiseaseAgentNodes(search, UnreachableGroqService(), 0.70, "Pakistan")
    agent = DiseaseResearchAgent(nodes)
    outcome = await agent.explain(
        "a" * 32,
        make_diagnosis("Corn_(maize)___Common_rust_", "Corn (Maize) Common Rust", 0.88),
        include_web_research=True,
        include_pesticides=True,
    )
    assert outcome.research_status == "unavailable"
    assert outcome.groq_status == "disabled"
    assert outcome.explanation is None
    assert outcome.research.disease.status == "unavailable"
    assert outcome.errors
    await search.close()


def test_reasoning_effort_is_model_aware() -> None:
    from app.core.config import Settings

    llama = Settings(groq_model="llama-3.3-70b-versatile", groq_reasoning_effort="auto")
    assert llama.resolved_reasoning_effort == ""
    reasoning = Settings(groq_model="openai/gpt-oss-120b", groq_reasoning_effort="auto")
    assert reasoning.resolved_reasoning_effort == "low"
    forced = Settings(groq_model="llama-3.3-70b-versatile", groq_reasoning_effort="high")
    assert forced.resolved_reasoning_effort == ""
    off = Settings(groq_model="openai/gpt-oss-20b", groq_reasoning_effort="none")
    assert off.resolved_reasoning_effort == ""


def test_pesticide_schema_matches_contract() -> None:
    """The API pesticide payload must expose the documented field names."""
    from app.schemas.pesticide import PesticideRecommendation

    record = PesticideRecommendation(
        product_name="RustStop 50 WP",
        active_ingredient="Mancozeb",
        type="fungicide",
        target_disease_or_pest="corn common rust",
        registration_status="unverified",
        country="Pakistan",
        application_information="Follow the current product label.",
        source=PESTICIDE_SOURCE,
    )
    payload = record.model_dump(mode="json")
    assert set(payload) >= {
        "product_name",
        "active_ingredient",
        "type",
        "registration_status",
        "application_information",
        "source",
    }
    assert payload["source"]["title"] and payload["source"]["url"]


def sample_image_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (256, 256), color=(50, 130, 45)).save(buffer, format="JPEG")
    return buffer.getvalue()


async def test_api() -> None:
    os.environ.setdefault("UPLOAD_DIR", "/tmp/plant-api-route-test")
    os.environ["TAVILY_API_KEY"] = ""
    os.environ["GROQ_API_KEY"] = ""
    from app.main import app, lifespan

    sample_bytes = sample_image_bytes()
    print("starting FastAPI lifespan", flush=True)
    async with lifespan(app):
        print("FastAPI lifespan started", flush=True)
        transport = ASGITransport(app=app, raise_app_exceptions=True)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            health = await client.get("/api/v1/health")
            assert health.status_code == 200, health.text
            health_body = health.json()
            assert health_body["model_loaded"] is True, health_body
            assert health_body["groq_available"] is False, health_body
            assert health_body["web_search_available"] is False, health_body

            missing = await client.post("/api/v1/diagnose")
            assert missing.status_code == 422, missing.text

            invalid = await client.post(
                "/api/v1/diagnose",
                files={"image": ("leaf.jpg", b"not-an-image", "image/jpeg")},
            )
            assert invalid.status_code == 400, invalid.text

            unsupported = await client.post(
                "/api/v1/diagnose",
                files={"image": ("leaf.txt", sample_bytes, "text/plain")},
            )
            assert unsupported.status_code == 400, unsupported.text

            response = await client.post(
                "/api/v1/diagnose",
                files={"image": ("leaf.jpg", sample_bytes, "image/jpeg")},
                data={
                    "include_explanation": "true",
                    "include_web_research": "true",
                    "include_pesticides": "true",
                },
            )
            assert response.status_code == 200, response.text
            body = response.json()
            assert body["success"] is True
            assert len(body["diagnosis"]["top_predictions"]) == 3
            assert len(body["diagnosis"]["class_probabilities"]) == 38
            # The ML diagnosis always survives, even with no Groq key and no search key.
            assert body["diagnosis"]["disease"]
            assert 0.0 <= body["diagnosis"]["confidence"] <= 1.0
            assert body["research"] is not None
            assert body["research"]["evidence"]["sources"] == []
            # A healthy class short-circuits research entirely; anything else reports
            # that live search was unavailable.
            assert body["research_status"] in {"disabled", "unavailable"}
            if body["diagnosis"]["disease"].casefold().endswith("healthy"):
                assert body["research_status"] == "disabled"
                assert body["explanation_error"] is None
                # A deterministic healthy explanation is served instead of an error.
                assert body["explanation"] is not None
                assert body["explanation"]["symptoms"] == []
                assert body["explanation"]["pesticides"] == []
                assert any("healthy" in w.lower() for w in body["warnings"])
            else:
                assert body["research_status"] == "unavailable"
                # No evidence and no Groq key: the explanation is absent, with a reason.
                assert body["explanation"] is None
                assert body["explanation_error"]

            # The model prediction is unchanged when the explanation layer is skipped.
            explain_off = await client.post(
                "/api/v1/diagnose",
                files={"image": ("leaf.jpg", sample_bytes, "image/jpeg")},
                data={"include_explanation": "false"},
            )
            assert explain_off.status_code == 200
            assert explain_off.json()["explanation"] is None

            # Opting out of research is a client choice, not a failure.
            research_off = await client.post(
                "/api/v1/diagnose",
                files={"image": ("leaf.jpg", sample_bytes, "image/jpeg")},
                data={"include_web_research": "false", "include_pesticides": "false"},
            )
            assert research_off.status_code == 200
            off_body = research_off.json()
            assert off_body["diagnosis"]["disease"] == body["diagnosis"]["disease"]
            assert off_body["research_status"] == "disabled"
            assert off_body["explanation_error"] is None
            assert off_body["research"]["disease"]["sources"] == []
            assert explain_off.json()["research"] is None

            image_response = await client.get(body["image"]["url"])
            assert image_response.status_code == 200
            assert image_response.headers["content-type"] == "image/jpeg"
            print(
                "real model/API diagnosis:",
                body["diagnosis"]["disease"],
                body["diagnosis"]["confidence"],
                flush=True,
            )


if __name__ == "__main__":
    asyncio.run(test_graph())
    print("parallel LangGraph evidence workflow: OK", flush=True)
    asyncio.run(test_unregistered_pesticide_is_downgraded())
    print("unverified pesticide downgrade: OK", flush=True)
    asyncio.run(test_healthy_class_skips_research())
    print("healthy class short-circuit: OK", flush=True)
    asyncio.run(test_search_unavailable_keeps_agent_running())
    print("unconfigured search degradation: OK", flush=True)
    test_reasoning_effort_is_model_aware()
    print("model-aware reasoning effort: OK", flush=True)
    test_pesticide_schema_matches_contract()
    print("pesticide response contract: OK", flush=True)
    asyncio.run(test_api())
    print("FastAPI real-checkpoint routes and graceful degradation: OK", flush=True)
