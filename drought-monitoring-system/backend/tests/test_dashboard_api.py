from typing import Any

from fastapi.testclient import TestClient

from app.database.monitoring_repository import get_monitoring_repository
from app.main import app


class FakeDashboardRepository:
    def get_reading_history(self, limit: int) -> list[dict[str, Any]]:
        return [{"id": 1, "soil_moisture_raw": 1800}]

    def get_weather_history(self, limit: int) -> list[dict[str, Any]]:
        return [{"id": 2, "forecast_precipitation_7d_mm": 4.5}]

    def get_drought_assessment_history(
        self,
        limit: int,
    ) -> list[dict[str, Any]]:
        return [{"id": 3, "summary": "High drought risk."}]


def test_dashboard_supabase_feeds() -> None:
    app.dependency_overrides[get_monitoring_repository] = (
        FakeDashboardRepository
    )

    try:
        with TestClient(app) as client:
            readings = client.get("/api/dashboard/readings?limit=10")
            weather = client.get("/api/dashboard/weather?limit=10")
            reports = client.get("/api/dashboard/assessments?limit=10")
    finally:
        app.dependency_overrides.clear()

    assert readings.status_code == 200
    assert readings.json()[0]["soil_moisture_raw"] == 1800
    assert weather.status_code == 200
    assert weather.json()[0]["forecast_precipitation_7d_mm"] == 4.5
    assert reports.status_code == 200
    assert reports.json()[0]["summary"] == "High drought risk."
