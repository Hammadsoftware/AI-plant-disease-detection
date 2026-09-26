import asyncio

from fastapi import APIRouter, Request

from app.schemas.diagnosis import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Service health")
async def health(request: Request) -> HealthResponse:
    groq_available, web_search_available = await asyncio.gather(
        request.app.state.groq_service.check_available(),
        request.app.state.web_search_service.check_available(),
    )
    return HealthResponse(
        status="ok",
        model_loaded=request.app.state.plant_model.loaded,
        groq_available=groq_available,
        web_search_available=web_search_available,
        groq_model=request.app.state.groq_service.model,
        search_provider=request.app.state.web_search_service.provider,
    )
