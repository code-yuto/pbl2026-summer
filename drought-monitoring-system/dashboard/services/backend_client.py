import os
from dataclasses import dataclass
from typing import Any

import httpx
import pandas as pd
import streamlit as st

from services.demo_data import (
    create_demo_alerts,
    create_demo_history,
    create_demo_reports,
    create_demo_weather,
)


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
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (
            base_url
            or os.getenv("BACKEND_URL", "http://localhost:8000")
        ).rstrip("/")

    def is_online(self) -> bool:
        with httpx.Client(timeout=2.5, trust_env=False) as client:
            response = client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json().get("status") == "healthy"

    def _get_records(
        self,
        path: str,
        limit: int,
        timeout: float = 8,
    ) -> list[dict[str, Any]]:
        with httpx.Client(timeout=timeout, trust_env=False) as client:
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
            raise ValueError("Backend has no sensor readings")

        frame = pd.DataFrame(records)
        frame["created_at"] = pd.to_datetime(frame["created_at"], utc=True)
        frame = frame.sort_values("created_at").reset_index(drop=True)
        return _add_missing_sensor_columns(frame)

    def get_weather(self, limit: int = 100) -> pd.DataFrame:
        records = self._get_records("/api/dashboard/weather", limit)
        if not records:
            raise ValueError("Backend has no weather snapshots")

        frame = pd.DataFrame(records)
        frame["observed_at"] = pd.to_datetime(frame["observed_at"], utc=True)
        if "fetched_at" in frame:
            frame["fetched_at"] = pd.to_datetime(frame["fetched_at"], utc=True)
        return frame.sort_values("observed_at").reset_index(drop=True)

    def get_assessments(self, limit: int = 100) -> list[dict[str, object]]:
        records = self._get_records("/api/dashboard/assessments", limit)
        if not records:
            raise ValueError("Backend has no Gemini assessments")
        return [_normalize_assessment(record) for record in records]


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
        "Sensors": "Live" if history_live else "Demo",
        "Weather": "Live" if weather_live else "Demo",
        "Gemini": "Live" if reports_live else "Demo",
    }
    details = " · ".join(f"{name}: {value}" for name, value in states.items())
    if all((history_live, weather_live, reports_live)):
        return "Live data + Gemini", details
    if any((history_live, weather_live, reports_live)):
        return "Mixed live/demo data", details
    return "Demo data", details


@st.cache_data(ttl=30, show_spinner=False)
def load_dashboard_snapshot(limit: int = 720) -> DashboardSnapshot:
    client = BackendClient()
    backend_online = False
    history_live = False
    weather_live = False
    reports_live = False

    try:
        backend_online = client.is_online()
    except (httpx.HTTPError, ValueError, KeyError):
        backend_online = False

    if backend_online:
        try:
            history = client.get_history(limit=limit)
            history_live = True
        except (httpx.HTTPError, ValueError, KeyError):
            history = create_demo_history(hours=limit)

        try:
            weather = client.get_weather(limit=min(limit, 1000))
            weather_live = True
        except (httpx.HTTPError, ValueError, KeyError):
            weather = create_demo_weather()

        try:
            reports = client.get_assessments(limit=100)
            reports_live = True
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            reports = create_demo_reports()
    else:
        history = create_demo_history(hours=limit)
        weather = create_demo_weather()
        reports = create_demo_reports()

    if history_live and weather_live:
        history = _merge_weather_into_history(history, weather)

    alerts = (
        _build_live_alerts(history)
        if history_live
        else create_demo_alerts(history)
    )
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
