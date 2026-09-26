import logging
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response

from app.schemas.diagnosis import DiagnosisResponse
from app.services.plant_disease_model import InferenceError, ModelNotReadyError
from app.utils.image import ImageValidationError, resolve_stored_image, validate_image


logger = logging.getLogger(__name__)
router = APIRouter(tags=["diagnosis"])


@router.post(
    "/diagnose",
    response_model=DiagnosisResponse,
    summary="Diagnose a plant leaf image and retrieve treatment evidence",
    responses={
        400: {"description": "Invalid or unsupported image"},
        413: {"description": "Upload or image dimensions are too large"},
        503: {"description": "Model is unavailable"},
    },
)
async def diagnose(
    request: Request,
    image: Annotated[UploadFile, File(description="A plant leaf image")],
    include_web_research: Annotated[
        bool, Form(description="Retrieve live disease and treatment evidence")
    ] = True,
    include_pesticides: Annotated[
        bool, Form(description="Research source-backed pesticide information")
    ] = True,
    include_explanation: Annotated[
        bool, Form(description="Run the LangGraph research and Groq explanation workflow")
    ] = True,
) -> DiagnosisResponse:
    settings = request.app.state.settings
    declared_content_type = image.content_type
    try:
        upload = await image.read(settings.max_upload_size_bytes + 1)
    finally:
        await image.close()

    try:
        validated_image = validate_image(
            upload,
            declared_content_type,
            max_size_bytes=settings.max_upload_size_bytes,
            min_dimension=settings.min_image_dimension,
            max_dimension=settings.max_image_dimension,
            max_pixels=settings.max_image_pixels,
        )
        return await request.app.state.diagnosis_service.diagnose(
            validated_image,
            include_explanation=include_explanation,
            include_web_research=include_web_research,
            include_pesticides=include_pesticides,
        )
    except ImageValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except ModelNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Plant disease model is unavailable.",
        ) from exc
    except InferenceError as exc:
        logger.exception("Model inference failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Plant disease inference failed.",
        ) from exc


@router.get(
    "/images/{image_id}",
    response_class=Response,
    summary="Retrieve a processed diagnosis image",
    responses={404: {"description": "Image not found"}},
)
async def get_processed_image(request: Request, image_id: str) -> Response:
    path = resolve_stored_image(request.app.state.settings.resolved_upload_dir, image_id)
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    try:
        image_content = path.read_bytes()
    except OSError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.") from exc
    return Response(
        content=image_content,
        media_type="image/jpeg",
        headers={"Cache-Control": "private, max-age=86400"},
    )
