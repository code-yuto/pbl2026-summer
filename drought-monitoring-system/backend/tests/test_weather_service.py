import asyncio
from typing import Any

import httpx

from app.services.weather_service import WeatherService


def test_fetches_and_summarizes_open_meteo_weather() -> None:
    async def run_test() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.params["latitude"] == "21.0278"
            assert "et0_fao_evapotranspiration" in request.url.params[
                "daily"
            ]
            return httpx.Response(
                200,
                json={
                    "utc_offset_seconds": 25200,
                    "current": {
                        "time": "2026-08-27T10:00",
                        "temperature_2m": 34.5,
                        "relative_humidity_2m": 42,
                        "precipitation": 0.2,
                    },
                    "daily": {
                        "time": [
                            "2026-08-20",
                            "2026-08-21",
                            "2026-08-22",
                            "2026-08-23",
                            "2026-08-24",
                            "2026-08-25",
                            "2026-08-26",
                            "2026-08-27",
                            "2026-08-28",
                            "2026-08-29",
                            "2026-08-30",
                            "2026-08-31",
                            "2026-09-01",
                            "2026-09-02",
                        ],
                        "precipitation_sum": list(range(1, 15)),
                        "temperature_2m_max": list(range(30, 44)),
                        "et0_fao_evapotranspiration": [4.0] * 14,
                    },
                },
            )

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            service = WeatherService(
                base_url="https://weather.test/forecast",
                client=client,
            )
            result = await service.fetch_snapshot(21.0278, 105.8342)

        assert result.source == "open-meteo"
        assert result.recent_precipitation_7d_mm == 28
        assert result.forecast_precipitation_3d_mm == 27
        assert result.forecast_precipitation_7d_mm == 77
        assert result.evapotranspiration_mm == 4
        assert result.forecast_evapotranspiration_7d_mm == 28
        assert result.forecast_temperature_max_3d_c == 39
        assert result.observed_at.utcoffset().total_seconds() == 25200

    asyncio.run(run_test())
