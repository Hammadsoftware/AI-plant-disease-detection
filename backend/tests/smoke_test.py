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
    DiseaseExplanation,
    ExplanationDiagnosis,
    ManagementRecommendations,
    PredictionItem,
)
from app.schemas.pesticide import PesticideRecommendation
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

    async def generate_explanation(self, evidence_payload: dict) -> DiseaseExplanation:
        assert evidence_payload["model_prediction"]["predicted_disease"] == "Corn (Maize) Common Rust"
        return DiseaseExplanation(
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
                PesticideRecommendation(
                    product_name="RustStop 50 WP",
                    active_ingredient="Mancozeb",
                    pesticide_type="fungicide",
                    target_disease_or_pest="corn common rust",
                    registration_status="verified",
                    country="Pakistan",
                    application_information="Apply 2 g/L to corn foliage according to the current product label.",
                    source=PESTICIDE_SOURCE,
                )
            ],
            prevention=["Use resistant hybrids"],
            recommendations=["Scout corn plants before deciding on treatment"],
            warnings=[],
            sources=[DISEASE_SOURCE],
        )


async def test_graph() -> None:
    diagnosis = Diagnosis(
        class_name="Corn_(maize)___Common_rust_",
        disease="Corn (Maize) Common Rust",
        confidence=0.42,
        is_uncertain=True,
        top_predictions=[
            PredictionItem(
                class_name="Corn_(maize)___Common_rust_",
                disease="Corn (Maize) Common Rust",
                confidence=0.42,
            )
        ],
        class_probabilities={"Corn_(maize)___Common_rust_": 0.42},
    )
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
    assert outcome.explanation.diagnosis.disease == diagnosis.disease
    assert outcome.explanation.diagnosis.confidence == diagnosis.confidence
    assert "uncertain" in outcome.explanation.diagnosis.confidence_note.lower()
    assert outcome.explanation.pesticides[0].registration_status == "verified"
    assert len(outcome.explanation.sources) == 3


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
            assert body["explanation"] is None
            assert body["research_status"] == "unavailable"
            assert body["research"] is not None
            assert body["research"]["evidence"]["sources"] == []
            assert body["explanation_error"]

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
    asyncio.run(test_api())
    print("FastAPI real-checkpoint routes and graceful degradation: OK", flush=True)
