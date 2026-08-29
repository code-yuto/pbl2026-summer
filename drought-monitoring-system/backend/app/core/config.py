from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "Drought Monitoring API"
    app_version: str = "0.1.0"
    debug: bool = False

    farm_latitude: float = 21.0278
    farm_longitude: float = 105.8342
    weather_timezone: str = "auto"
    open_meteo_base_url: str = (
        "https://api.open-meteo.com/v1/forecast"
    )

    gemini_api_key: SecretStr = SecretStr("")
    gemini_model: str = "gemini-2.5-flash-lite"
    gemini_base_url: str = (
        "https://generativelanguage.googleapis.com/v1beta"
    )
    external_api_timeout_seconds: float = 20

    analysis_poll_interval_seconds: float = 60
    weather_cache_ttl_seconds: float = 900

    soil_critical_threshold: float = 20
    soil_high_threshold: float = 25
    soil_medium_threshold: float = 40

    water_critical_threshold: float = 5
    water_high_threshold: float = 8
    water_medium_threshold: float = 12

    serial_device_id: str = "ESP32_SERIAL_01"
    soil_sensor_dry_raw: int = 2800
    soil_sensor_wet_raw: int = 1500
    water_sensor_empty_raw: int = 0
    water_sensor_full_raw: int = 1500

    allowed_origins: str = "http://localhost:8501"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]


def get_settings() -> Settings:
    return Settings()
