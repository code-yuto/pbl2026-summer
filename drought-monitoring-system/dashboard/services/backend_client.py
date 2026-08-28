import os
from dataclasses import dataclass
from typing import Any

import httpx
import pandas as pd
import streamlit as st


NGROK_HEADERS = {"ngrok-skip-browser-warning": "true"}


@dataclass
class DashboardSnapshot:
    history: pd.DataFrame
    weather: pd.DataFrame
    alerts: pd.DataFrame
    reports: list[dict[str, object]]
    source: str
    source_details: str
    backend_online: bool
    history_live: bool
    weather_live: bool
    reports_live: bool


class BackendClient:
    def __init__(
        self,
        base_url: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("BACKEND_URL", "http://localhost:8000")
        ).rstrip("/")
        self.transport = transport

    def _client(self, timeout: float) -> httpx.Client:
        return httpx.Client(
            timeout=timeout,
            trust_env=False,
            transport=self.transport,
            headers=NGROK_HEADERS,
        )

    def is_online(self) -> bool:
        with self._client(timeout=2.5) as client:
            response = client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json().get("status") == "healthy"

    def _get_records(
        self,
        path: str,
        limit: int,
        timeout: float = 8,
    ) -> list[dict[str, Any]]:
        with self._client(timeout=timeout) as client:
            response = client.get(
                f"{self.base_url}{path}",
                params={"limit": limit},
            )
            response.raise_for_status()
            records = response.json()

        if not isinstance(records, list):
            raise ValueError(f"{path} did not return a list")
        return records

    def get_history(self, limit: int = 720) -> pd.DataFrame:
        records = self._get_records("/api/dashboard/readings", limit)
        if not records:
            raise ValueError("No live sensor readings have been received")

        frame = pd.DataFrame(records)
        frame["created_at"] = pd.to_datetime(frame["created_at"], utc=True)
        frame = frame.sort_values("created_at").reset_index(drop=True)
        return _add_missing_sensor_columns(frame)

    def get_weather(self, limit: int = 100) -> pd.DataFrame:
        records = self._get_records("/api/dashboard/weather", limit)
        if not records:
            raise ValueError("No session weather snapshots are available")

        frame = pd.DataFrame(records)
        frame["observed_at"] = pd.to_datetime(frame["observed_at"], utc=True)
        if "fetched_at" in frame:
            frame["fetched_at"] = pd.to_datetime(frame["fetched_at"], utc=True)
        return frame.sort_values("observed_at").reset_index(drop=True)

    def get_current_weather(self) -> pd.DataFrame:
        with self._client(timeout=20) as client:
            response = client.get(f"{self.base_url}/api/weather")
            response.raise_for_status()
            record = response.json()
        if not isinstance(record, dict) or not record.get("observed_at"):
            raise ValueError("Open-Meteo returned invalid weather data")
        frame = pd.DataFrame([record])
        frame["observed_at"] = pd.to_datetime(frame["observed_at"], utc=True)
        return frame

    def get_assessments(self, limit: int = 100) -> list[dict[str, object]]:
        records = self._get_records("/api/dashboard/assessments", limit)
        if not records:
            raise ValueError("No Gemini assessments exist in this session")
        return [_normalize_assessment(record) for record in records]

    def analyze_latest(self) -> dict[str, Any]:
        with self._client(timeout=45) as client:
            response = client.post(
                f"{self.base_url}/api/drought/analyze/latest"
            )
            response.raise_for_status()
            result = response.json()
        if not isinstance(result, dict):
            raise ValueError("Latest forecast endpoint returned invalid data")
        return result

    def ask_forecast(
        self,
        question: str,
        assessment_id: int,
        history: list[dict[str, str]],
    ) -> dict[str, Any]:
        with self._client(timeout=45) as client:
            response = client.post(
                f"{self.base_url}/api/drought/chat",
                json={
                    "question": question,
                    "assessment_id": assessment_id,
                    "history": history[-8:],
                },
            )
            response.raise_for_status()
            result = response.json()
        if not isinstance(result, dict) or not result.get("answer"):
            raise ValueError("Forecast chat endpoint returned invalid data")
        return result


def _add_missing_sensor_columns(frame: pd.DataFrame) -> pd.DataFrame:
    enriched = frame.copy()
    defaults: dict[str, object] = {
        "temperature": float("nan"),
        "humidity": float("nan"),
        "rain_probability": float("nan"),
        "risk_level": "normal",
        "alert_sent": False,
        "device_id": "UNKNOWN_DEVICE",
        "message_type": "data",
        "sensor_transport": "http",
        "soil_moisture_raw": pd.NA,
        "water_level_raw": pd.NA,
        "device_timestamp_ms": pd.NA,
        "led_color": pd.NA,
    }

    for column, value in defaults.items():
        if column not in enriched:
            enriched[column] = value
        elif column in {"risk_level", "device_id", "message_type"}:
            enriched[column] = enriched[column].fillna(value)

    return enriched


def _merge_weather_into_history(
    history: pd.DataFrame,
    weather: pd.DataFrame,
) -> pd.DataFrame:
    if history.empty or weather.empty or "observed_at" not in weather:
        return history

    weather_columns = weather[
        ["observed_at", "temperature_c", "humidity_percent"]
    ].sort_values("observed_at")
    merged = pd.merge_asof(
        history.sort_values("created_at"),
        weather_columns,
        left_on="created_at",
        right_on="observed_at",
        direction="nearest",
        tolerance=pd.Timedelta(hours=6),
    )
    merged["temperature"] = merged["temperature"].fillna(
        merged["temperature_c"]
    )
    merged["humidity"] = merged["humidity"].fillna(
        merged["humidity_percent"]
    )
    return merged.drop(
        columns=["observed_at", "temperature_c", "humidity_percent"],
        errors="ignore",
    )


def _normalize_assessment(record: dict[str, Any]) -> dict[str, object]:
    confidence = str(record.get("confidence", "low")).lower()
    confidence_percent = {"low": 55, "medium": 75, "high": 90}.get(
        confidence,
        55,
    )
    risk_level = str(record.get("risk_level", "normal")).lower()
    return {
        "id": record.get("id"),
        "created_at": record.get("created_at"),
        "risk_level": risk_level,
        "risk_score": float(record.get("risk_score", 0)),
        "confidence": confidence,
        "confidence_percent": confidence_percent,
        "title": f"{risk_level.title()} drought assessment",
        "explanation": str(record.get("summary", "No summary returned.")),
        "drivers": list(record.get("drivers") or []),
        "recommendations": list(record.get("recommendations") or []),
        "risk_factors": dict(record.get("risk_factors") or {}),
        "analysis_source": str(record.get("analysis_source", "Gemini")),
        "requires_immediate_action": bool(
            record.get("requires_immediate_action", False)
        ),
    }


def _build_live_alerts(history: pd.DataFrame) -> pd.DataFrame:
    if history.empty:
        return pd.DataFrame(
            columns=["created_at", "risk_level", "message", "status"]
        )

    message_type = history["message_type"].fillna("data").astype(str)
    risk_level = history["risk_level"].fillna("normal").astype(str)
    alert_sent = history["alert_sent"].fillna(False).astype(bool)
    alert_mask = (
        message_type.str.startswith(("alert", "warning"))
        | risk_level.isin(["high", "critical"])
        | alert_sent
    )
    selected = history.loc[alert_mask].copy()
    if selected.empty:
        return pd.DataFrame(
            columns=["created_at", "risk_level", "message", "status"]
        )

    def display_level(row: pd.Series) -> str:
        status_type = str(row.get("message_type", "data"))
        level = str(row.get("risk_level", "normal"))
        if status_type.startswith("alert"):
            return "critical"
        if status_type.startswith("warning") and level == "normal":
            return "medium"
        return level

    def display_message(row: pd.Series) -> str:
        status_type = str(row.get("message_type", "data"))
        readable = status_type.replace("_", " ").strip().title()
        return (
            f"{readable}: soil moisture {float(row['soil_moisture']):.1f}% "
            f"and water level {float(row['water_level']):.1f}%."
        )

    selected["risk_level"] = selected.apply(display_level, axis=1)
    selected["message"] = selected.apply(display_message, axis=1)
    selected["status"] = selected["alert_sent"].fillna(False).map(
        {True: "Delivered", False: "Not sent"}
    )
    return selected[
        ["created_at", "risk_level", "message", "status"]
    ].reset_index(drop=True)


def _source_description(
    history_live: bool,
    weather_live: bool,
    reports_live: bool,
) -> tuple[str, str]:
    states = {
        "Sensors": "USB Serial" if history_live else "Waiting",
        "Weather": "Open-Meteo" if weather_live else "Waiting",
        "Gemini": "Live session" if reports_live else "Waiting",
    }
    details = " · ".join(f"{name}: {value}" for name, value in states.items())
    if all((history_live, weather_live, reports_live)):
        return "Live sensors + APIs", details
    if any((history_live, weather_live, reports_live)):
        return "Partial live data", details
    return "Waiting for live data", details


def _empty_history() -> pd.DataFrame:
    return _add_missing_sensor_columns(
        pd.DataFrame(
            columns=[
                "id",
                "device_id",
                "soil_moisture",
                "water_level",
                "created_at",
            ]
        )
    )


def _empty_weather() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "observed_at",
            "temperature_c",
            "humidity_percent",
            "precipitation_mm",
            "recent_precipitation_7d_mm",
            "forecast_precipitation_3d_mm",
            "forecast_precipitation_7d_mm",
            "evapotranspiration_mm",
            "forecast_evapotranspiration_7d_mm",
            "forecast_temperature_max_3d_c",
        ]
    )


@st.cache_data(ttl=60, show_spinner=False)
def load_dashboard_snapshot(
    limit: int = 720,
    base_url: str | None = None,
) -> DashboardSnapshot:
    client = BackendClient(base_url=base_url)
    backend_online = False
    history_live = False
    weather_live = False
    reports_live = False
    history = _empty_history()
    weather = _empty_weather()
    reports: list[dict[str, object]] = []

    try:
        backend_online = client.is_online()
    except (httpx.HTTPError, ValueError, KeyError):
        backend_online = False

    if backend_online:
        try:
            history = client.get_history(limit=limit)
            history_live = True
        except (httpx.HTTPError, ValueError, KeyError):
            history = _empty_history()

        try:
            weather = client.get_weather(limit=min(limit, 1000))
            weather_live = True
        except (httpx.HTTPError, ValueError, KeyError):
            try:
                weather = client.get_current_weather()
                weather_live = True
            except (httpx.HTTPError, ValueError, KeyError):
                weather = _empty_weather()

        try:
            reports = client.get_assessments(limit=100)
            reports_live = True
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            reports = []

    if history_live and weather_live:
        history = _merge_weather_into_history(history, weather)

    alerts = _build_live_alerts(history)
    source, source_details = _source_description(
        history_live,
        weather_live,
        reports_live,
    )

    return DashboardSnapshot(
        history=history,
        weather=weather,
        alerts=alerts,
        reports=reports,
        source=source,
        source_details=source_details,
        backend_online=backend_online,
        history_live=history_live,
        weather_live=weather_live,
        reports_live=reports_live,
    )
