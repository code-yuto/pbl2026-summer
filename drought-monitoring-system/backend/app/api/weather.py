from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.config import Settings, get_settings
from app.models.weather_models import WeatherSnapshot
from app.services.weather_service import (
    WeatherService,
    WeatherServiceError,
    get_weather_service,
)


router = APIRouter(tags=["Weather"])


@router.get("/weather", response_model=WeatherSnapshot)
async def get_weather(
    latitude: float | None = Query(default=None, ge=-90, le=90),
    longitude: float | None = Query(default=None, ge=-180, le=180),
    weather_service: WeatherService = Depends(get_weather_service),
    settings: Settings = Depends(get_settings),
) -> WeatherSnapshot:
    selected_latitude = (
        latitude if latitude is not None else settings.farm_latitude
    )
    selected_longitude = (
        longitude if longitude is not None else settings.farm_longitude
    )

    try:
        return await weather_service.fetch_snapshot(
            selected_latitude,
            selected_longitude,
        )
    except WeatherServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
