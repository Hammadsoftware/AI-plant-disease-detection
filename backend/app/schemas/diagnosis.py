from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pesticide import PesticideRecommendation
from app.schemas.research import DiagnosisResearch, ResearchSource, ResearchStatus


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PredictionItem(StrictSchema):
    class_name: str
    disease: str
    confidence: float = Field(ge=0.0, le=1.0)


class Diagnosis(StrictSchema):
    class_name: str
    disease: str
    confidence: float = Field(ge=0.0, le=1.0)
    is_uncertain: bool
    top_predictions: list[PredictionItem]
    class_probabilities: dict[str, float]


class ExplanationDiagnosis(StrictSchema):
    disease: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_note: str = Field(min_length=1)


class ManagementRecommendations(StrictSchema):
    cultural: list[str] = Field(default_factory=list)
    biological: list[str] = Field(default_factory=list)
    physical: list[str] = Field(default_factory=list)
    chemical: list[str] = Field(default_factory=list)


class DiseaseExplanation(StrictSchema):
    summary: str = Field(min_length=1)
    diagnosis: ExplanationDiagnosis
    symptoms: list[str] = Field(default_factory=list)
    possible_causes: list[str] = Field(default_factory=list)
    management: ManagementRecommendations = Field(default_factory=ManagementRecommendations)
    pesticides: list[PesticideRecommendation] = Field(default_factory=list)
    prevention: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    sources: list[ResearchSource] = Field(default_factory=list)


class ImageReference(StrictSchema):
    image_id: str
    url: str
    media_type: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    kind: str = "processed"


class DiagnosisResponse(StrictSchema):
    success: bool = True
    image: ImageReference | None = None
    diagnosis: Diagnosis
    explanation: DiseaseExplanation | None = None
    explanation_error: str | None = None
    research_status: ResearchStatus = "disabled"
    groq_status: Literal["available", "unavailable", "disabled"] = "disabled"
    research: DiagnosisResearch | None = None
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(StrictSchema):
    status: str
    model_loaded: bool
    groq_available: bool
    web_search_available: bool
    groq_model: str
    search_provider: str
