import asyncio
import logging

from app.agents.graph import DiseaseResearchAgent
from app.core.config import Settings
from app.schemas.diagnosis import DiagnosisResponse, ImageReference
from app.services.plant_disease_model import PlantDiseaseModel
from app.utils.image import ValidatedImage, save_processed_image


logger = logging.getLogger(__name__)


class DiagnosisService:
    def __init__(
        self,
        model: PlantDiseaseModel,
        disease_agent: DiseaseResearchAgent,
        settings: Settings,
    ) -> None:
        self.model = model
        self.disease_agent = disease_agent
        self.settings = settings
        self._inference_slots = asyncio.Semaphore(settings.max_concurrent_inferences)

    async def diagnose(
        self,
        validated_image: ValidatedImage,
        *,
        include_explanation: bool,
        include_web_research: bool,
        include_pesticides: bool,
    ) -> DiagnosisResponse:
        async with self._inference_slots:
            diagnosis = await self.model.predict_async(validated_image.image)

        warnings: list[str] = []
        if diagnosis.is_uncertain:
            warnings.append(
                "Low-confidence prediction: provide a clearer image, multiple leaf images, "
                "and seek qualified agricultural verification before treatment."
            )

        image_reference = await self._store_image(validated_image, warnings)
        explanation = None
        explanation_error = None
        research_status = "disabled"
        groq_status = "disabled"
        research = None
        if include_explanation:
            try:
                outcome = await self.disease_agent.explain(
                    image_reference.image_id if image_reference else None,
                    diagnosis,
                    include_web_research=include_web_research,
                    include_pesticides=include_pesticides,
                )
                explanation = outcome.explanation
                research_status = outcome.research_status
                groq_status = outcome.groq_status
                research = outcome.research
                warnings.extend(outcome.warnings)
                if outcome.errors:
                    explanation_error = " ".join(outcome.errors)
            except Exception:
                logger.exception("Disease research graph failed")
                explanation_error = "Disease research and explanation workflow failed."
                research_status = "unavailable" if include_web_research else "disabled"
                groq_status = "unavailable"

        return DiagnosisResponse(
            image=image_reference,
            diagnosis=diagnosis,
            explanation=explanation,
            explanation_error=explanation_error,
            research_status=research_status,
            groq_status=groq_status,
            research=research,
            warnings=list(dict.fromkeys(warnings)),
        )

    async def _store_image(
        self, validated_image: ValidatedImage, warnings: list[str]
    ) -> ImageReference | None:
        if not self.settings.store_uploads:
            return None
        try:
            image_id = save_processed_image(
                validated_image.image,
                self.settings.resolved_upload_dir,
                jpeg_quality=self.settings.image_jpeg_quality,
            )
            return ImageReference(
                image_id=image_id,
                url=f"{self.settings.api_prefix}/images/{image_id}",
                media_type="image/jpeg",
                width=validated_image.width,
                height=validated_image.height,
            )
        except Exception:
            logger.exception("Unable to store processed upload")
            warnings.append("The diagnosis succeeded, but the processed image could not be stored.")
            return None
