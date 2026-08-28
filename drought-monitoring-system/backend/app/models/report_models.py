from typing import Literal

from pydantic import BaseModel, Field

from app.models.sensor_models import RiskLevel, SensorReadingCreate
from app.models.weather_models import WeatherSnapshot


class DroughtAnalysisRequest(SensorReadingCreate):
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class GeminiDroughtAnalysis(BaseModel):
    summary: str = Field(min_length=1, max_length=1200)
    drivers: list[str] = Field(min_length=1, max_length=6)
    recommendations: list[str] = Field(min_length=1, max_length=6)
    confidence: Literal["low", "medium", "high"]
    requires_immediate_action: bool


class DroughtRiskResult(BaseModel):
    score: float = Field(ge=0, le=100)
    level: RiskLevel
    factors: dict[str, float]


class DroughtAnalysisResponse(BaseModel):
    sensor_reading_id: int
    weather_id: int
    assessment_id: int
    data_sources: dict[str, str]
    sensor: SensorReadingCreate
    weather: WeatherSnapshot
    risk: DroughtRiskResult
    gemini: GeminiDroughtAnalysis
