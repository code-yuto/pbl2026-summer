from datetime import datetime, timezone
from typing import Any

from fastapi.testclient import TestClient

from app.database.monitoring_repository import get_monitoring_repository
from app.main import app


class FakeMonitoringRepository:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def save_reading(self, reading: dict[str, Any]) -> dict[str, Any]:
        record = {
            "id": len(self.records) + 1,
            **reading,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.records.append(record)
        return record

    def get_latest_reading(self) -> dict[str, Any] | None:
        return self.records[-1] if self.records else None

    def get_reading_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return list(reversed(self.records[-limit:]))


def test_create_critical_reading() -> None:
    repository = FakeMonitoringRepository()
    app.dependency_overrides[get_monitoring_repository] = lambda: repository

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/readings",
                json={
                    "device_id": "SIMULATED_01",
                    "soil_moisture": 18,
                    "water_level": 4,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["risk_level"] == "critical"
    assert response.json()["saved"] is True


def test_rejects_invalid_soil_moisture() -> None:
    repository = FakeMonitoringRepository()
    app.dependency_overrides[get_monitoring_repository] = lambda: repository

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/readings",
                json={
                    "device_id": "SIMULATED_01",
                    "soil_moisture": 150,
                    "water_level": 4,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_accepts_exact_esp32_serial_payload() -> None:
    repository = FakeMonitoringRepository()
    app.dependency_overrides[get_monitoring_repository] = lambda: repository

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/readings/serial",
                json={
                    "type": "data",
                    "water_level": 512,
                    "soil_moisture": 1800,
                    "timestamp_ms": 123456,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["message_type"] == "data"
    assert body["water_level_raw"] == 512
    assert body["soil_moisture_raw"] == 1800
    assert body["device_timestamp_ms"] == 123456
    assert body["water_level"] == 34.13
    assert body["soil_moisture"] == 76.92
    assert body["device_alert"] is False
    assert body["raw_payload"]["type"] == "data"


def test_preserves_esp32_alert_type() -> None:
    repository = FakeMonitoringRepository()
    app.dependency_overrides[get_monitoring_repository] = lambda: repository

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/readings/serial",
                json={
                    "type": "alert",
                    "water_level": 3999,
                    "soil_moisture": 1800,
                    "timestamp_ms": 999999,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["device_alert"] is True
    assert repository.records[0]["message_type"] == "alert"


def test_accepts_detailed_serial_status_and_led_colour() -> None:
    repository = FakeMonitoringRepository()
    app.dependency_overrides[get_monitoring_repository] = lambda: repository

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/readings/serial?device_id=ESP32_FIELD_01",
                json={
                    "type": "alert_critical_dry_no_water",
                    "water_level": 120,
                    "soil_moisture": 3100,
                    "led_color": "PURPLE",
                    "timestamp_ms": 999999,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["device_id"] == "ESP32_FIELD_01"
    assert body["message_type"] == "alert_critical_dry_no_water"
    assert body["led_color"] == "PURPLE"
    assert body["device_alert"] is True
