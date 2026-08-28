from pathlib import Path

from streamlit.testing.v1 import AppTest

from components.charts import (
    risk_distribution_chart,
    soil_moisture_chart,
    water_level_chart,
    weather_forecast_chart,
)
from services.demo_data import (
    create_demo_alerts,
    create_demo_history,
    create_demo_reports,
    create_demo_weather,
)


DASHBOARD_ROOT = Path(__file__).resolve().parents[1]


def test_demo_data_and_charts() -> None:
    history = create_demo_history()
    weather = create_demo_weather()
    alerts = create_demo_alerts(history)
    reports = create_demo_reports()

    assert len(history) == 720
    assert len(weather) == 7
    assert not alerts.empty
    assert len(reports) == 3
    assert len(soil_moisture_chart(history).data) == 1
    assert len(water_level_chart(history).data) == 1
    assert len(weather_forecast_chart(weather).data) == 2
    assert len(risk_distribution_chart(history["risk_level"]).data) == 1


def test_dashboard_entrypoint() -> None:
    app = AppTest.from_file(DASHBOARD_ROOT / "app.py").run(timeout=30)
    assert not app.exception
