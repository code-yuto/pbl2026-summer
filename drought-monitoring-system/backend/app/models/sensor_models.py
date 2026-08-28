from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


RiskLevel = Literal["normal", "medium", "high", "critical"]
SensorMessageType = Literal[
    "data",
    "alert",
    "alert_hardware_or_flood",
    "warning_dry",
    "data_wet",
    "data_ideal",
    "warning_dry_medium_water",
    "data_wet_medium_water",
    "data_medium",
    "alert_critical_dry_no_water",
    "warning_low_water_wet_soil",
    "warning_low_water",
]


class SensorReadingCreate(BaseModel):
    device_id: str = Field(min_length=1, max_length=100)
    soil_moisture: float = Field(ge=0, le=100)
    water_level: float = Field(ge=0)

    @field_validator("device_id")
    @classmethod
    def clean_device_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("device_id cannot be empty")
        return cleaned


class SensorReadingResponse(BaseModel):
    id: int
    device_id: str
    soil_moisture: float
    water_level: float
    risk_level: RiskLevel
    alert_sent: bool = False
    created_at: datetime
    saved: bool = True

    model_config = ConfigDict(from_attributes=True)


class SerialSensorPayload(BaseModel):
    """Exact JSON shape printed by the ESP32 over USB Serial."""

    message_type: SensorMessageType = Field(alias="type")
    water_level: int = Field(ge=0, le=4095)
    soil_moisture: int = Field(ge=0, le=4095)
    led_color: str | None = Field(default=None, min_length=1, max_length=32)
    timestamp_ms: int = Field(ge=0)

    model_config = ConfigDict(populate_by_name=True)


class SerialSensorReadingResponse(BaseModel):
    id: int
    device_id: str
    message_type: SensorMessageType
    sensor_transport: Literal["usb_serial"]
    soil_moisture_raw: int
    water_level_raw: int
    device_timestamp_ms: int
    led_color: str | None = None
    soil_moisture: float
    water_level: float
    risk_level: RiskLevel
    device_alert: bool
    alert_sent: bool = False
    raw_payload: dict[str, Any]
    created_at: datetime
    saved: bool = True

    model_config = ConfigDict(from_attributes=True)
