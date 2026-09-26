import operator
from typing import Annotated, Any, Literal, TypedDict

from app.schemas.diagnosis import DiseaseExplanation
from app.schemas.research import EvidenceReport, ResearchBundle, ResearchStatus


class PlantDiagnosisState(TypedDict, total=False):
    """Strongly typed state shared by the modular diagnosis research graph."""

    image_id: str | None
    predicted_disease: str
    raw_class_name: str
    confidence: float
    top_predictions: list[dict[str, Any]]
    uncertain_prediction: bool
    crop: str
    plant: str
    include_web_research: bool
    include_pesticides: bool
    disease_research: ResearchBundle
    treatment_research: ResearchBundle
    pesticide_research: ResearchBundle
    evidence: EvidenceReport
    explanation: DiseaseExplanation | None
    research_status: ResearchStatus
    groq_status: Literal["available", "unavailable", "disabled"]
    errors: Annotated[list[str], operator.add]
    warnings: Annotated[list[str], operator.add]
