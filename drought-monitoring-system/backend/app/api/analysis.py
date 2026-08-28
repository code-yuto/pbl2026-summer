from fastapi import APIRouter, Depends, HTTPException, status
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings, get_settings
from app.database.monitoring_repository import (
    MonitoringRepository,
    get_monitoring_repository,
)
from app.models.report_models import (
    DroughtAnalysisRequest,
    DroughtAnalysisResponse,
    ForecastChatRequest,
    ForecastChatResponse,
)
from app.services.gemini_service import (
    GeminiConfigurationError,
    GeminiService,
    GeminiServiceError,
    get_gemini_service,
)
from app.services.monitoring_service import (
    MonitoringPersistenceError,
    MonitoringService,
)
from app.services.weather_service import (
    WeatherService,
    WeatherServiceError,
    get_weather_service,
)


router = APIRouter(tags=["Drought analysis"])


def _raise_service_error(error: Exception) -> None:
    if isinstance(error, GeminiConfigurationError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    if isinstance(error, (WeatherServiceError, GeminiServiceError)):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    if isinstance(error, MonitoringPersistenceError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    raise error


@router.post(
    "/drought/analyze",
    response_model=DroughtAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_drought(
    request: DroughtAnalysisRequest,
    repository: MonitoringRepository = Depends(get_monitoring_repository),
    weather_service: WeatherService = Depends(get_weather_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
    settings: Settings = Depends(get_settings),
) -> DroughtAnalysisResponse:
    service = MonitoringService(
        repository=repository,
        weather_service=weather_service,
        gemini_service=gemini_service,
        settings=settings,
    )

    try:
        return await service.analyze_and_store(request)
    except (
        GeminiConfigurationError,
        WeatherServiceError,
        GeminiServiceError,
        MonitoringPersistenceError,
    ) as error:
        _raise_service_error(error)


@router.post(
    "/drought/analyze/latest",
    response_model=DroughtAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_latest_sensor_reading(
    repository: MonitoringRepository = Depends(get_monitoring_repository),
    weather_service: WeatherService = Depends(get_weather_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
    settings: Settings = Depends(get_settings),
) -> DroughtAnalysisResponse:
    service = MonitoringService(
        repository=repository,
        weather_service=weather_service,
        gemini_service=gemini_service,
        settings=settings,
    )

    try:
        result = await service.analyze_latest_reading()
    except (
        GeminiConfigurationError,
        WeatherServiceError,
        GeminiServiceError,
        MonitoringPersistenceError,
    ) as error:
        _raise_service_error(error)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No live sensor readings have been received",
        )
    return result


@router.post(
    "/drought/chat",
    response_model=ForecastChatResponse,
)
async def chat_about_saved_forecast(
    request: ForecastChatRequest,
    repository: MonitoringRepository = Depends(get_monitoring_repository),
    gemini_service: GeminiService = Depends(get_gemini_service),
) -> ForecastChatResponse:
    try:
        context = await run_in_threadpool(
            repository.get_drought_chat_context,
            request.assessment_id,
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to load the current forecast context",
        ) from error

    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested saved drought assessment was not found",
        )

    try:
        answer = await gemini_service.answer_forecast_question(
            request.question,
            context,
            request.history,
        )
    except (GeminiConfigurationError, GeminiServiceError) as error:
        _raise_service_error(error)

    assessment = context["assessment"]
    return ForecastChatResponse(
        answer=answer,
        assessment_id=int(assessment["id"]),
        model=gemini_service.model,
        context_created_at=assessment.get("created_at"),
        data_sources=[
            "ESP32 USB Serial sensor reading",
            "Open-Meteo weather API",
            "Deterministic risk calculation",
        ],
    )
