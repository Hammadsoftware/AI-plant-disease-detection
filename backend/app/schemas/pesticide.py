from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.research import ResearchSource


class PesticideSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PesticideRecommendation(PesticideSchema):
    product_name: str = Field(min_length=1)
    active_ingredient: str = Field(min_length=1)
    pesticide_type: Literal[
        "fungicide", "insecticide", "bactericide", "acaricide", "other"
    ]
    target_disease_or_pest: str = Field(min_length=1)
    registration_status: Literal["verified", "unverified"] = "unverified"
    country: str = "Pakistan"
    application_information: str = Field(min_length=1)
    source: ResearchSource
