from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd


def create_demo_history(hours: int = 30 * 24) -> pd.DataFrame:
    rng = np.random.default_rng(27)
    hours = max(hours, 48)
    timestamps = pd.date_range(
        end=pd.Timestamp.now(tz="UTC").floor("h"),
        periods=hours,
        freq="h",
    )
    index = np.arange(hours)
    hour_of_day = timestamps.hour.to_numpy()

    drying_rate = 30 * (index / max(hours - 1, 1))
    daily_soil_cycle = 2.4 * np.sin(2 * np.pi * hour_of_day / 24)
    soil_moisture = 56 - drying_rate + daily_soil_cycle + rng.normal(0, 0.8, hours)

    water_level = 22 - 13 * (index / max(hours - 1, 1))
    water_level += 0.8 * np.sin(2 * np.pi * index / (24 * 4))
    water_level += rng.normal(0, 0.22, hours)

    temperature = 29 + 4.5 * np.sin(2 * np.pi * (hour_of_day - 8) / 24)
    temperature += rng.normal(0, 0.45, hours)
    humidity = 68 - 15 * np.sin(2 * np.pi * (hour_of_day - 8) / 24)
    humidity += rng.normal(0, 1.5, hours)

    rain_probability = np.clip(
        15 + 20 * np.sin(2 * np.pi * index / (24 * 5)) + rng.normal(0, 7, hours),
        0,
        85,
    )

    risk_level = np.select(
        [
            (soil_moisture <= 20) | (water_level <= 5),
            (soil_moisture <= 25) | (water_level <= 8),
            (soil_moisture <= 40) | (water_level <= 12),
        ],
        ["critical", "high", "medium"],
        default="normal",
    )

    data = pd.DataFrame(
        {
            "id": index + 1,
            "device_id": "SIMULATED_01",
            "soil_moisture": np.round(np.clip(soil_moisture, 12, 70), 1),
            "water_level": np.round(np.clip(water_level, 2, 30), 1),
            "temperature": np.round(temperature, 1),
            "humidity": np.round(np.clip(humidity, 30, 95), 1),
            "rain_probability": np.round(rain_probability, 0),
            "risk_level": risk_level,
            "alert_sent": np.isin(risk_level, ["high", "critical"]),
            "created_at": timestamps,
        }
    )

    return data


def create_demo_weather(days: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(81)
    dates = pd.date_range(
        start=pd.Timestamp.now(tz="UTC").normalize(),
        periods=days,
        freq="D",
    )

    return pd.DataFrame(
        {
            "date": dates,
            "minimum_temperature": [25, 25, 24, 25, 26, 25, 24][:days],
            "maximum_temperature": [35, 36, 34, 33, 35, 34, 32][:days],
            "rain_probability": [10, 8, 18, 42, 56, 35, 62][:days],
            "rain_mm": np.round(rng.uniform(0, 8, days), 1),
            "evapotranspiration": [5.2, 5.5, 4.9, 4.2, 4.5, 4.1, 3.8][:days],
        }
    )


def create_demo_alerts(history: pd.DataFrame) -> pd.DataFrame:
    alerts = history.loc[history["alert_sent"]].copy()

    if alerts.empty:
        return pd.DataFrame(
            columns=["created_at", "risk_level", "message", "status"]
        )

    alerts = alerts.iloc[::6].tail(12).copy()
    alerts["message"] = alerts.apply(
        lambda row: (
            f"{str(row['risk_level']).title()} drought risk: "
            f"soil moisture {row['soil_moisture']:.1f}% and "
            f"water level {row['water_level']:.1f} cm."
        ),
        axis=1,
    )
    alerts["status"] = "Delivered"
    return alerts[["created_at", "risk_level", "message", "status"]]


def create_demo_reports() -> list[dict[str, object]]:
    now = datetime.now(timezone.utc)
    return [
        {
            "created_at": now,
            "risk_level": "high",
            "confidence": 91,
            "title": "Drying trend requires controlled irrigation",
            "explanation": (
                "Soil moisture has fallen steadily while the water reserve is "
                "approaching the high-risk threshold. Low rainfall probability "
                "and elevated daytime temperature will likely accelerate moisture loss."
            ),
            "recommendations": [
                "Begin controlled irrigation during the early morning period.",
                "Inspect the water source and confirm that the level sensor is unobstructed.",
                "Review moisture readings again after six hours before increasing flow.",
            ],
        },
        {
            "created_at": now - timedelta(hours=6),
            "risk_level": "medium",
            "confidence": 86,
            "title": "Moisture decline detected across the latest cycle",
            "explanation": (
                "The field remains stable, but the decline rate is higher than the "
                "seven-day average and no meaningful rainfall is expected today."
            ),
            "recommendations": [
                "Maintain observation frequency.",
                "Prepare irrigation equipment for possible activation.",
            ],
        },
        {
            "created_at": now - timedelta(hours=24),
            "risk_level": "normal",
            "confidence": 94,
            "title": "Field conditions remained within operating range",
            "explanation": (
                "Soil moisture and stored water were sufficient for the observed "
                "temperature and humidity conditions."
            ),
            "recommendations": ["Continue the normal monitoring schedule."],
        },
    ]
