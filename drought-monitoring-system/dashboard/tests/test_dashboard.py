from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from components.charts import (
    risk_distribution_chart,
    soil_moisture_chart,
    water_level_chart,
    weather_forecast_chart,
)


DASHBOARD_ROOT = Path(__file__).resolve().parents[1]


def test_live_sensor_and_weather_charts() -> None:
    history = pd.DataFrame(
        {
            "created_at": pd.to_datetime(
                ["2026-08-28T08:00:00Z", "2026-08-28T08:01:00Z"]
            ),
            "soil_moisture": [42.0, 41.5],
            "water_level": [68.0, 67.8],
            "risk_level": ["normal", "normal"],
        }
    )
    weather = pd.DataFrame(
        {
            "observed_at": pd.to_datetime(["2026-08-28T08:00:00Z"]),
            "forecast_precipitation_7d_mm": [12.4],
            "forecast_temperature_max_3d_c": [35.2],
        }
    )

    assert len(soil_moisture_chart(history).data) == 1
    assert len(water_level_chart(history).data) == 1
    assert len(weather_forecast_chart(weather).data) == 2
    assert len(risk_distribution_chart(history["risk_level"]).data) == 1


def test_demo_data_module_was_removed() -> None:
    assert not (DASHBOARD_ROOT / "services" / "demo_data.py").exists()


def test_dashboard_entrypoint() -> None:
    app = AppTest.from_file(DASHBOARD_ROOT / "app.py").run(timeout=30)
    assert not app.exception
