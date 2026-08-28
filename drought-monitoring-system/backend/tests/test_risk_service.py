import pytest

from app.models.weather_models import WeatherSnapshot
from app.services.risk_service import (
    RiskThresholds,
    calculate_drought_risk,
    calculate_risk_level,
)


@pytest.fixture
def thresholds() -> RiskThresholds:
    return RiskThresholds(
        soil_critical=20,
        soil_high=25,
        soil_medium=40,
        water_critical=5,
        water_high=8,
        water_medium=12,
    )


@pytest.mark.parametrize(
    ("soil_moisture", "water_level", "expected"),
    [
        (60, 20, "normal"),
        (35, 20, "medium"),
        (60, 10, "medium"),
        (23, 20, "high"),
        (60, 7, "high"),
        (18, 20, "critical"),
        (60, 4, "critical"),
    ],
)
def test_calculate_risk_level(
    soil_moisture: float,
    water_level: float,
    expected: str,
    thresholds: RiskThresholds,
) -> None:
    result = calculate_risk_level(
        soil_moisture,
        water_level,
        thresholds,
    )

    assert result == expected


def test_weather_increases_drought_risk(
    thresholds: RiskThresholds,
) -> None:
    weather = WeatherSnapshot(
        latitude=21.0278,
        longitude=105.8342,
        observed_at="2026-08-27T10:00:00+07:00",
        temperature_c=35,
        humidity_percent=35,
        precipitation_mm=0,
        recent_precipitation_7d_mm=2,
        forecast_precipitation_3d_mm=0,
        forecast_precipitation_7d_mm=1,
        evapotranspiration_mm=6,
        forecast_evapotranspiration_7d_mm=42,
        forecast_temperature_max_3d_c=38,
    )

    result = calculate_drought_risk(
        soil_moisture=30,
        water_level=10,
        weather=weather,
        thresholds=thresholds,
    )

    assert result.score >= 50
    assert result.level in {"high", "critical"}
    assert result.factors["rainfall_deficit"] > 90
