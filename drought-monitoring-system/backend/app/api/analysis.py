from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.database.monitoring_repository import (
    MonitoringRepository,
    get_monitoring_repository,
)
from app.models.report_models import (
    DroughtAnalysisRequest,
    DroughtAnalysisResponse,
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
    except GeminiConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except (WeatherServiceError, GeminiServiceError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    except MonitoringPersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
