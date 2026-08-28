from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.database.monitoring_repository import (
    InMemoryMonitoringRepository,
    get_monitoring_repository,
)
from app.main import app


def test_in_memory_repository_links_sensor_weather_and_assessment() -> None:
    repository = InMemoryMonitoringRepository()
    sensor = repository.save_reading(
        {
            "device_id": "ESP32_SERIAL_01",
            "soil_moisture": 18.0,
            "water_level": 4.0,
            "risk_level": "critical",
            "alert_sent": False,
        }
    )
    weather = repository.save_weather_data(
        {
            "monitoring_id": sensor["id"],
            "observed_at": "2026-08-28T08:00:00Z",
            "forecast_precipitation_7d_mm": 2.0,
        }
    )
    assessment = repository.save_drought_assessment(
        {
            "monitoring_id": sensor["id"],
            "weather_id": weather["id"],
            "risk_level": "critical",
            "risk_score": 82.0,
        }
    )

    context = repository.get_drought_chat_context(assessment["id"])

    assert context is not None
    assert context["sensor"]["soil_moisture"] == 18.0
    assert context["weather"]["forecast_precipitation_7d_mm"] == 2.0
    assert context["assessment"]["risk_score"] == 82.0


def test_default_api_accepts_serial_data_without_supabase(monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_BACKEND", "memory")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
    get_settings.cache_clear()
    get_monitoring_repository.cache_clear()

    try:
        with TestClient(app) as client:
            saved = client.post(
                "/api/readings/serial",
                json={
                    "type": "data_ideal",
                    "water_level": 1200,
                    "soil_moisture": 2000,
                    "led_color": "GREEN",
                    "timestamp_ms": 1234,
                },
            )
            dashboard = client.get("/api/dashboard/readings?limit=5")
            health = client.get("/health")
    finally:
        get_monitoring_repository.cache_clear()
        get_settings.cache_clear()

    assert saved.status_code == 201
    assert dashboard.status_code == 200
    assert dashboard.json()[0]["sensor_transport"] == "usb_serial"
    assert health.json()["storage"] == "memory"
