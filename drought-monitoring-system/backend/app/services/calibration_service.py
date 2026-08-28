from dataclasses import dataclass

from app.core.config import Settings


def _percentage(raw_value: int, zero_raw: int, full_raw: int) -> float:
    if zero_raw == full_raw:
        raise ValueError("Calibration endpoints cannot be equal")

    ratio = (raw_value - zero_raw) / (full_raw - zero_raw)
    return round(max(0.0, min(1.0, ratio)) * 100, 2)


@dataclass(frozen=True)
class CalibratedSensorValues:
    soil_moisture_percent: float
    water_level_percent: float


@dataclass(frozen=True)
class SensorCalibration:
    soil_dry_raw: int
    soil_wet_raw: int
    water_empty_raw: int
    water_full_raw: int

    @classmethod
    def from_settings(cls, settings: Settings) -> "SensorCalibration":
        return cls(
            soil_dry_raw=settings.soil_sensor_dry_raw,
            soil_wet_raw=settings.soil_sensor_wet_raw,
            water_empty_raw=settings.water_sensor_empty_raw,
            water_full_raw=settings.water_sensor_full_raw,
        )

    def calibrate(
        self,
        soil_moisture_raw: int,
        water_level_raw: int,
    ) -> CalibratedSensorValues:
        return CalibratedSensorValues(
            soil_moisture_percent=_percentage(
                soil_moisture_raw,
                self.soil_dry_raw,
                self.soil_wet_raw,
            ),
            water_level_percent=_percentage(
                water_level_raw,
                self.water_empty_raw,
                self.water_full_raw,
            ),
        )
