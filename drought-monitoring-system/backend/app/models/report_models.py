from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.sensor_models import RiskLevel, SensorReadingCreate
from app.models.weather_models import WeatherSnapshot


class DroughtAnalysisRequest(SensorReadingCreate):
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class ForecastChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ForecastChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=600)
    assessment_id: int | None = Field(default=None, ge=1)
    history: list[ForecastChatTurn] = Field(default_factory=list, max_length=8)

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("question cannot be empty")
        return cleaned


class ForecastChatResponse(BaseModel):
    answer: str = Field(min_length=1, max_length=5000)
    assessment_id: int
    model: str
    context_created_at: datetime | None = None
    data_sources: list[str]


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
