import httpx
import pandas as pd

from services.backend_client import (
    BackendClient,
    _build_live_alerts,
    _merge_weather_into_history,
    _normalize_assessment,
)


def test_normalizes_saved_gemini_assessment() -> None:
    report = _normalize_assessment(
        {
            "id": 3,
            "created_at": "2026-08-27T10:00:00Z",
            "risk_level": "high",
            "risk_score": 62.5,
            "confidence": "high",
            "summary": "Dry conditions are likely to continue.",
            "drivers": ["Low forecast rainfall"],
            "recommendations": ["Inspect irrigation"],
            "risk_factors": {"rainfall_deficit": 90},
            "analysis_source": "gemini-2.5-flash-lite",
        }
    )

    assert report["risk_score"] == 62.5
    assert report["confidence"] == "high"
    assert report["drivers"] == ["Low forecast rainfall"]
    assert report["analysis_source"] == "gemini-2.5-flash-lite"


def test_merges_live_weather_and_builds_device_alert() -> None:
    history = pd.DataFrame(
        {
            "id": [1],
            "created_at": pd.to_datetime(["2026-08-27T10:00:00Z"]),
            "soil_moisture": [10.0],
            "water_level": [5.0],
            "temperature": [float("nan")],
            "humidity": [float("nan")],
            "risk_level": ["critical"],
            "message_type": ["alert_critical_dry_no_water"],
            "alert_sent": [False],
        }
    )
    weather = pd.DataFrame(
        {
            "observed_at": pd.to_datetime(["2026-08-27T10:05:00Z"]),
            "temperature_c": [35.0],
            "humidity_percent": [38.0],
        }
    )

    enriched = _merge_weather_into_history(history, weather)
    alerts = _build_live_alerts(enriched)

    assert enriched.iloc[0]["temperature"] == 35
    assert enriched.iloc[0]["humidity"] == 38
    assert alerts.iloc[0]["risk_level"] == "critical"
    assert alerts.iloc[0]["status"] == "Not sent"


def test_ngrok_client_sends_chat_with_selected_assessment() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["ngrok-skip-browser-warning"] == "true"
        assert request.url.path == "/api/drought/chat"
        payload = __import__("json").loads(request.content)
        assert payload["assessment_id"] == 33
        assert payload["question"] == "Explain the forecast"
        return httpx.Response(
            200,
            json={
                "answer": "Low rainfall and dry soil drive the saved risk.",
                "assessment_id": 33,
            },
        )

    client = BackendClient(
        base_url="https://test.ngrok-free.app",
        transport=httpx.MockTransport(handler),
    )
    response = client.ask_forecast(
        question="Explain the forecast",
        assessment_id=33,
        history=[],
    )

    assert response["assessment_id"] == 33
    assert "Low rainfall" in response["answer"]
