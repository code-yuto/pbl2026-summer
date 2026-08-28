from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class WeatherSnapshot(BaseModel):
    """Current and forecast weather returned by Open-Meteo."""

    source: Literal["open-meteo"] = "open-meteo"
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    observed_at: datetime
    temperature_c: float
    humidity_percent: float = Field(ge=0, le=100)
    precipitation_mm: float = Field(ge=0)
    recent_precipitation_7d_mm: float = Field(ge=0)
    forecast_precipitation_3d_mm: float = Field(ge=0)
    forecast_precipitation_7d_mm: float = Field(ge=0)
    evapotranspiration_mm: float = Field(ge=0)
    forecast_evapotranspiration_7d_mm: float = Field(ge=0)
    forecast_temperature_max_3d_c: float
