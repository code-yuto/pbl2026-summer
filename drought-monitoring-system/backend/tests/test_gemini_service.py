import asyncio
import json

import httpx
import pytest

from app.models.sensor_models import SensorReadingCreate
from app.models.report_models import ForecastChatTurn
from app.models.weather_models import WeatherSnapshot
from app.services.gemini_service import (
    GeminiConfigurationError,
    GeminiService,
)
from app.services.risk_service import DroughtRiskAssessment


def make_weather() -> WeatherSnapshot:
    return WeatherSnapshot(
        latitude=21.0278,
        longitude=105.8342,
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


def test_gemini_returns_structured_analysis() -> None:
    async def run_test() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads((await request.aread()).decode())
            prompt = body["contents"][0]["parts"][0]["text"]
            assert "critical" in prompt
            assert body["generationConfig"]["responseMimeType"] == (
                "application/json"
            )
            return httpx.Response(
                200,
                json={
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "text": json.dumps(
                                            {
                                                "summary": "Critical risk.",
                                                "drivers": ["Dry soil"],
                                                "recommendations": [
                                                    "Inspect irrigation"
                                                ],
                                                "confidence": "high",
                                                "requires_immediate_action": True,
                                            }
                                        )
                                    }
                                ]
                            }
                        }
                    ]
                },
            )

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            service = GeminiService(
                api_key="test-key",
                model="gemini-2.5-flash-lite",
                base_url="https://gemini.test/v1beta",
                client=client,
            )
            result = await service.analyze(
                SensorReadingCreate(
                    device_id="TEST_01",
                    soil_moisture=18,
                    water_level=4,
                ),
                make_weather(),
                DroughtRiskAssessment(
                    score=82,
                    level="critical",
                    factors={"soil_dryness": 100},
                ),
            )

        assert result.confidence == "high"
        assert result.requires_immediate_action is True

    asyncio.run(run_test())


def test_gemini_requires_an_api_key() -> None:
    service = GeminiService(
        api_key="",
        model="gemini-2.5-flash-lite",
        base_url="https://gemini.test/v1beta",
    )

    with pytest.raises(GeminiConfigurationError):
        asyncio.run(
            service.analyze(
                SensorReadingCreate(
                    device_id="TEST_01",
                    soil_moisture=18,
                    water_level=4,
                ),
                make_weather(),
                DroughtRiskAssessment(
                    score=82,
                    level="critical",
                    factors={},
                ),
            )
        )


def test_gemini_chat_uses_live_forecast_context() -> None:
    async def run_test() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads((await request.aread()).decode())
            prompt = body["contents"][0]["parts"][0]["text"]
            assert "LIVE_CONTEXT" in prompt
            assert '"soil_moisture": 18.0' in prompt
            assert '"forecast_precipitation_7d_mm": 2.0' in prompt
            assert "Why is the drought risk critical?" in prompt
            return httpx.Response(
                200,
                json={
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "text": (
                                            "The saved risk is critical because "
                                            "the soil is dry and little rain is forecast."
                                        )
                                    }
                                ]
                            }
                        }
                    ]
                },
            )

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            service = GeminiService(
                api_key="test-key",
                model="gemini-2.5-flash-lite",
                base_url="https://gemini.test/v1beta",
                client=client,
            )
            answer = await service.answer_forecast_question(
                question="Why is the drought risk critical?",
                context={
                    "sensor": {"soil_moisture": 18.0},
                    "weather": {"forecast_precipitation_7d_mm": 2.0},
                    "assessment": {"risk_level": "critical"},
                },
                history=[
                    ForecastChatTurn(
                        role="user",
                        content="Explain the rain forecast.",
                    )
                ],
            )

        assert "saved risk is critical" in answer

    asyncio.run(run_test())
