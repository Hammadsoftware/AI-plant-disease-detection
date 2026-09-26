from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.research import ResearchSource


PesticideType = Literal[
    "fungicide",
    "insecticide",
    "bactericide",
    "acaricide",
    "herbicide",
    "other",
]
RegistrationStatus = Literal["verified", "unverified"]


class PesticideSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceRef(PesticideSchema):
    """Minimal citation the model is allowed to produce: title plus URL."""

    title: str = Field(min_length=1)
    url: str = Field(min_length=1)


class PesticideDraft(PesticideSchema):
    """The only pesticide shape the LLM may emit. It is never returned to clients.

    The model may only restate a product that a retrieved pesticide source already
    contains. ``registration_status`` defaults to ``unverified`` and is downgraded
    again by the final validator unless an official registration source backs it.
    """

    product_name: str = Field(min_length=1)
    active_ingredient: str = Field(min_length=1)
    type: PesticideType
    registration_status: RegistrationStatus = "unverified"
    application_information: str = Field(min_length=1)
    source: SourceRef


class PesticideRecommendation(PesticideDraft):
    """Validated pesticide record: a draft whose source is a retrieved, real source."""

    target_disease_or_pest: str = Field(min_length=1)
    country: str = Field(min_length=1)
    source: ResearchSource
