from typing import Any

from fastapi.testclient import TestClient

from app.database.monitoring_repository import get_monitoring_repository
from app.main import app
from app.services.gemini_service import get_gemini_service


class FakeChatRepository:
    def get_drought_chat_context(
        self,
        assessment_id: int | None,
    ) -> dict[str, Any] | None:
        if assessment_id == 999:
            return None
        return {
            "sensor": {
                "id": 11,
                "soil_moisture": 18,
                "water_level": 4,
            },
            "weather": {
                "id": 22,
                "forecast_precipitation_7d_mm": 2,
                "forecast_temperature_max_3d_c": 37,
            },
            "assessment": {
                "id": 33,
                "risk_level": "critical",
                "risk_score": 82,
                "created_at": "2026-08-27T10:00:00Z",
            },
        }


class FakeChatGeminiService:
    model = "gemini-2.5-flash-lite"

    async def answer_forecast_question(
        self,
        question,
        context,
        history,
    ) -> str:
        assert context["sensor"]["soil_moisture"] == 18
        assert context["assessment"]["risk_level"] == "critical"
        assert question == "Why is the risk critical?"
        return "The stored soil moisture is low and little rain is forecast."


def test_chat_explains_linked_live_forecast() -> None:
    app.dependency_overrides[get_monitoring_repository] = FakeChatRepository
    app.dependency_overrides[get_gemini_service] = FakeChatGeminiService

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/drought/chat",
                json={
                    "question": "Why is the risk critical?",
                    "assessment_id": 33,
                    "history": [],
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["assessment_id"] == 33
    assert body["model"] == "gemini-2.5-flash-lite"
    assert "soil moisture is low" in body["answer"]
    assert "ESP32 USB Serial sensor reading" in body["data_sources"]


def test_chat_rejects_missing_assessment() -> None:
    app.dependency_overrides[get_monitoring_repository] = FakeChatRepository
    app.dependency_overrides[get_gemini_service] = FakeChatGeminiService

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/drought/chat",
                json={
                    "question": "Explain this forecast.",
                    "assessment_id": 999,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
