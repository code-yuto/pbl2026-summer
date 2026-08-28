from dataclasses import dataclass

from app.core.config import Settings
from app.models.sensor_models import RiskLevel
from app.models.weather_models import WeatherSnapshot


@dataclass(frozen=True)
class RiskThresholds:
    soil_critical: float
    soil_high: float
    soil_medium: float
    water_critical: float
    water_high: float
    water_medium: float

    def __post_init__(self) -> None:
        if not self.soil_critical <= self.soil_high <= self.soil_medium:
            raise ValueError("Soil thresholds must increase by risk level")

        if not self.water_critical <= self.water_high <= self.water_medium:
            raise ValueError("Water thresholds must increase by risk level")

    @classmethod
    def from_settings(cls, settings: Settings) -> "RiskThresholds":
        return cls(
            soil_critical=settings.soil_critical_threshold,
            soil_high=settings.soil_high_threshold,
            soil_medium=settings.soil_medium_threshold,
            water_critical=settings.water_critical_threshold,
            water_high=settings.water_high_threshold,
            water_medium=settings.water_medium_threshold,
        )


def calculate_risk_level(
    soil_moisture: float,
    water_level: float,
    thresholds: RiskThresholds,
) -> RiskLevel:
    if (
        soil_moisture <= thresholds.soil_critical
        or water_level <= thresholds.water_critical
    ):
        return "critical"

    if (
        soil_moisture <= thresholds.soil_high
        or water_level <= thresholds.water_high
    ):
        return "high"

    if (
        soil_moisture <= thresholds.soil_medium
        or water_level <= thresholds.water_medium
    ):
        return "medium"

    return "normal"


@dataclass(frozen=True)
class DroughtRiskAssessment:
    score: float
    level: RiskLevel
    factors: dict[str, float]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _shortage(value: float, critical: float, safe: float) -> float:
    if safe <= critical:
        raise ValueError("Safe level must be greater than critical level")
    return _clamp((safe - value) / (safe - critical))


def calculate_drought_risk(
    soil_moisture: float,
    water_level: float,
    weather: WeatherSnapshot,
    thresholds: RiskThresholds,
) -> DroughtRiskAssessment:
    """Combine local sensors and weather into an auditable 0-100 score.

    Constants are initial agronomic defaults. They must be calibrated for the
    actual crop, soil, water-level sensor and local climate after field tests.
    """

    soil_dryness = _shortage(
        soil_moisture,
        thresholds.soil_critical,
        max(60.0, thresholds.soil_medium),
    )
    water_shortage = _shortage(
        water_level,
        thresholds.water_critical,
        max(20.0, thresholds.water_medium),
    )

    weighted_rainfall = (
        weather.recent_precipitation_7d_mm * 0.4
        + weather.forecast_precipitation_7d_mm * 0.6
    )
    rainfall_deficit = _clamp(1 - weighted_rainfall / 25.0)
    heat_stress = _clamp(
        (weather.forecast_temperature_max_3d_c - 28.0) / 10.0
    )
    evaporative_stress = _clamp(
        (weather.forecast_evapotranspiration_7d_mm / 7.0 - 3.0) / 4.0
    )
    low_humidity = _clamp((70.0 - weather.humidity_percent) / 40.0)

    factors = {
        "soil_dryness": round(soil_dryness * 100, 1),
        "water_shortage": round(water_shortage * 100, 1),
        "rainfall_deficit": round(rainfall_deficit * 100, 1),
        "heat_stress": round(heat_stress * 100, 1),
        "evaporative_stress": round(evaporative_stress * 100, 1),
        "low_humidity": round(low_humidity * 100, 1),
    }

    score = 100 * (
        soil_dryness * 0.40
        + water_shortage * 0.25
        + rainfall_deficit * 0.15
        + heat_stress * 0.08
        + evaporative_stress * 0.07
        + low_humidity * 0.05
    )

    if score >= 70:
        score_level: RiskLevel = "critical"
    elif score >= 50:
        score_level = "high"
    elif score >= 30:
        score_level = "medium"
    else:
        score_level = "normal"

    sensor_level = calculate_risk_level(
        soil_moisture,
        water_level,
        thresholds,
    )
    rank = {"normal": 0, "medium": 1, "high": 2, "critical": 3}
    final_level = (
        sensor_level
        if rank[sensor_level] > rank[score_level]
        else score_level
    )

    minimum_score = {
        "normal": 0,
        "medium": 30,
        "high": 50,
        "critical": 70,
    }[final_level]

    return DroughtRiskAssessment(
        score=round(max(score, minimum_score), 1),
        level=final_level,
        factors=factors,
    )
