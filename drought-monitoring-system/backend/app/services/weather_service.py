from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

import httpx

from app.core.config import get_settings
from app.models.weather_models import WeatherSnapshot


class WeatherServiceError(RuntimeError):
    pass


class WeatherService:
    CURRENT_FIELDS = (
        "temperature_2m,relative_humidity_2m,precipitation"
    )
    DAILY_FIELDS = (
        "precipitation_sum,temperature_2m_max,"
        "et0_fao_evapotranspiration"
    )

    def __init__(
        self,
        base_url: str,
        timezone: str = "auto",
        timeout_seconds: float = 20,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url
        self.timezone = timezone
        self.timeout_seconds = timeout_seconds
        self.client = client

    async def fetch_snapshot(
        self,
        latitude: float,
        longitude: float,
    ) -> WeatherSnapshot:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": self.CURRENT_FIELDS,
            "daily": self.DAILY_FIELDS,
            "past_days": 7,
            "forecast_days": 7,
            "timezone": self.timezone,
        }

        try:
            if self.client is not None:
                response = await self.client.get(self.base_url, params=params)
            else:
                async with httpx.AsyncClient(
                    timeout=self.timeout_seconds,
                    trust_env=False,
                ) as client:
                    response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            payload = response.json()
            return self._parse_snapshot(payload, latitude, longitude)
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            raise WeatherServiceError(
                "Unable to retrieve valid weather data from Open-Meteo"
            ) from error

    @staticmethod
    def _parse_snapshot(
        payload: dict[str, Any],
        latitude: float,
        longitude: float,
    ) -> WeatherSnapshot:
        current = payload["current"]
        daily = payload["daily"]

        observed_at = datetime.fromisoformat(current["time"]).replace(
            tzinfo=timezone(
                timedelta(seconds=int(payload.get("utc_offset_seconds", 0)))
            )
        )
        observed_date = observed_at.date()
        dates = [date.fromisoformat(value) for value in daily["time"]]
        precipitation = daily["precipitation_sum"]
        temperatures = daily["temperature_2m_max"]
        evapotranspiration = daily["et0_fao_evapotranspiration"]

        def values_between(
            values: list[float | None],
            start: date,
            end: date,
        ) -> list[float]:
            return [
                float(value or 0)
                for day, value in zip(dates, values, strict=True)
                if start <= day <= end
            ]

        recent_rain = values_between(
            precipitation,
            observed_date - timedelta(days=7),
            observed_date - timedelta(days=1),
        )
        forecast_rain_3d = values_between(
            precipitation,
            observed_date,
            observed_date + timedelta(days=2),
        )
        forecast_rain_7d = values_between(
            precipitation,
            observed_date,
            observed_date + timedelta(days=6),
        )
        forecast_et_7d = values_between(
            evapotranspiration,
            observed_date,
            observed_date + timedelta(days=6),
        )
        forecast_temp_3d = values_between(
            temperatures,
            observed_date,
            observed_date + timedelta(days=2),
        )
        today_et = values_between(
            evapotranspiration,
            observed_date,
            observed_date,
        )

        if not forecast_temp_3d:
            raise ValueError("Open-Meteo did not return a 3-day forecast")

        return WeatherSnapshot(
            latitude=latitude,
            longitude=longitude,
            observed_at=observed_at,
            temperature_c=float(current["temperature_2m"]),
            humidity_percent=float(current["relative_humidity_2m"]),
            precipitation_mm=float(current["precipitation"] or 0),
            recent_precipitation_7d_mm=round(sum(recent_rain), 2),
            forecast_precipitation_3d_mm=round(sum(forecast_rain_3d), 2),
            forecast_precipitation_7d_mm=round(sum(forecast_rain_7d), 2),
            evapotranspiration_mm=round(sum(today_et), 2),
            forecast_evapotranspiration_7d_mm=round(
                sum(forecast_et_7d), 2
            ),
            forecast_temperature_max_3d_c=max(forecast_temp_3d),
        )


@lru_cache
def get_weather_service() -> WeatherService:
    settings = get_settings()
    return WeatherService(
        base_url=settings.open_meteo_base_url,
        timezone=settings.weather_timezone,
        timeout_seconds=settings.external_api_timeout_seconds,
    )
