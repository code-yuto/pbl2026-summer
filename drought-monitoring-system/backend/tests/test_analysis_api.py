from datetime import datetime, timezone
from typing import Any

from fastapi.testclient import TestClient

from app.database.monitoring_repository import get_monitoring_repository
from app.main import app
from app.models.report_models import GeminiDroughtAnalysis
from app.models.weather_models import WeatherSnapshot
from app.services.gemini_service import get_gemini_service
from app.services.weather_service import get_weather_service


class FakeRepository:
    def save_reading(self, reading: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": 11,
            **reading,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def save_weather_data(self, weather: dict[str, Any]) -> dict[str, Any]:
        return {"id": 22, **weather}

    def save_drought_assessment(
        self,
        assessment: dict[str, Any],
    ) -> dict[str, Any]:
        return {"id": 33, **assessment}


class FakeWeatherService:
    async def fetch_snapshot(
        self,
        latitude: float,
        longitude: float,
    ) -> WeatherSnapshot:
        return WeatherSnapshot(
            latitude=latitude,
            longitude=longitude,
            observed_at="2026-08-27T10:00:00+07:00",
            temperature_c=35,
            humidity_percent=40,
            precipitation_mm=0,
            recent_precipitation_7d_mm=3,
            forecast_precipitation_3d_mm=1,
            forecast_precipitation_7d_mm=2,
            evapotranspiration_mm=5,
            forecast_evapotranspiration_7d_mm=35,
            forecast_temperature_max_3d_c=37,
        )


class FakeGeminiService:
    model = "gemini-2.5-flash-lite"

    async def analyze(self, sensor, weather, risk) -> GeminiDroughtAnalysis:
        return GeminiDroughtAnalysis(
            summary="Critical drought risk detected.",
            drivers=["Dry soil", "Little forecast rain"],
            recommendations=["Inspect irrigation"],
            confidence="high",
            requires_immediate_action=True,
        )


def test_complete_drought_analysis_pipeline() -> None:
    app.dependency_overrides[get_monitoring_repository] = FakeRepository
    app.dependency_overrides[get_weather_service] = FakeWeatherService
    app.dependency_overrides[get_gemini_service] = FakeGeminiService

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/drought/analyze",
                json={
                    "device_id": "SIMULATED_01",
                    "soil_moisture": 18,
                    "water_level": 4,
                    "latitude": 21.0278,
                    "longitude": 105.8342,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["sensor_reading_id"] == 11
    assert body["weather_id"] == 22
    assert body["assessment_id"] == 33
    assert body["risk"]["level"] == "critical"
    assert body["data_sources"]["soil_moisture"] == "physical sensor"
    assert body["data_sources"]["temperature"] == "Open-Meteo API"
