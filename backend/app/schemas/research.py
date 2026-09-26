from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator


ResearchStatus = Literal["available", "partial", "unavailable", "disabled"]
SourceType = Literal[
    "government",
    "university_extension",
    "international_organization",
    "peer_reviewed",
    "research_institution",
    "other",
]


class ResearchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResearchSource(ResearchSchema):
    title: str = Field(min_length=1)
    url: str = Field(min_length=1)
    source: str = Field(min_length=1, description="Publisher or hostname")
    source_type: SourceType
    snippet: str = Field(min_length=1)
    query: str = Field(min_length=1)
    authoritative: bool = False

    @field_validator("url")
    @classmethod
    def validate_http_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("source URL must be an absolute HTTP(S) URL")
        return value


class ResearchBundle(ResearchSchema):
    topic: Literal["disease", "treatment", "pesticide"]
    status: ResearchStatus
    queries: list[str] = Field(default_factory=list)
    sources: list[ResearchSource] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class EvidenceClaim(ResearchSchema):
    category: Literal["disease", "treatment", "pesticide"]
    claim: str = Field(min_length=1)
    source_urls: list[str] = Field(min_length=1)
    authoritative: bool


class EvidenceReport(ResearchSchema):
    status: ResearchStatus
    claims: list[EvidenceClaim] = Field(default_factory=list)
    sources: list[ResearchSource] = Field(default_factory=list)
    disagreements: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DiagnosisResearch(ResearchSchema):
    disease: ResearchBundle
    treatment: ResearchBundle
    pesticide: ResearchBundle
    evidence: EvidenceReport
