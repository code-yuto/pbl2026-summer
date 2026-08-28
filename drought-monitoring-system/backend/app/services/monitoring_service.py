from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.database.monitoring_repository import MonitoringRepository
from app.models.report_models import (
    DroughtAnalysisRequest,
    DroughtAnalysisResponse,
    DroughtRiskResult,
)
from app.models.sensor_models import SensorReadingCreate
from app.services.gemini_service import GeminiService
from app.services.risk_service import (
    RiskThresholds,
    calculate_drought_risk,
)
from app.services.weather_service import WeatherService


DATA_SOURCES = {
    "soil_moisture": "physical sensor",
    "water_level": "physical sensor",
    "precipitation": "Open-Meteo API",
    "forecast_precipitation": "Open-Meteo API",
    "temperature": "Open-Meteo API",
    "evapotranspiration": "Open-Meteo API",
    "humidity": "Open-Meteo API",
    "risk_score": "deterministic backend calculation",
    "explanation": "Gemini API",
}


class MonitoringPersistenceError(RuntimeError):
    pass


class MonitoringService:
    def __init__(
        self,
        repository: MonitoringRepository,
        weather_service: WeatherService,
        gemini_service: GeminiService,
        settings: Settings,
    ) -> None:
        self.repository = repository
        self.weather_service = weather_service
        self.gemini_service = gemini_service
        self.settings = settings

    async def analyze_and_store(
        self,
        request: DroughtAnalysisRequest,
    ) -> DroughtAnalysisResponse:
        latitude = (
            request.latitude
            if request.latitude is not None
            else self.settings.farm_latitude
        )
        longitude = (
            request.longitude
            if request.longitude is not None
            else self.settings.farm_longitude
        )
        sensor = SensorReadingCreate(
            device_id=request.device_id,
            soil_moisture=request.soil_moisture,
            water_level=request.water_level,
        )

        weather = await self.weather_service.fetch_snapshot(
            latitude,
            longitude,
        )
        risk = calculate_drought_risk(
            soil_moisture=sensor.soil_moisture,
            water_level=sensor.water_level,
            weather=weather,
            thresholds=RiskThresholds.from_settings(self.settings),
        )
        gemini = await self.gemini_service.analyze(sensor, weather, risk)

        try:
            saved_sensor = await run_in_threadpool(
                self.repository.save_reading,
                {
                    **sensor.model_dump(),
                    "temperature": weather.temperature_c,
                    "humidity": weather.humidity_percent,
                    "risk_level": risk.level,
                    "llm_explanation": gemini.summary,
                    "recommendation": "\n".join(gemini.recommendations),
                    "alert_sent": False,
                },
            )
            saved_weather = await run_in_threadpool(
                self.repository.save_weather_data,
                {
                    "monitoring_id": saved_sensor["id"],
                    **weather.model_dump(mode="json"),
                },
            )
            saved_assessment = await run_in_threadpool(
                self.repository.save_drought_assessment,
                {
                    "monitoring_id": saved_sensor["id"],
                    "weather_id": saved_weather["id"],
                    "risk_score": risk.score,
                    "risk_level": risk.level,
                    "risk_factors": risk.factors,
                    "analysis_source": self.gemini_service.model,
                    "summary": gemini.summary,
                    "drivers": gemini.drivers,
                    "recommendations": gemini.recommendations,
                    "confidence": gemini.confidence,
                    "requires_immediate_action": (
                        gemini.requires_immediate_action
                    ),
                },
            )
        except Exception as error:
            raise MonitoringPersistenceError(
                "Unable to store the drought assessment"
            ) from error

        return DroughtAnalysisResponse(
            sensor_reading_id=saved_sensor["id"],
            weather_id=saved_weather["id"],
            assessment_id=saved_assessment["id"],
            data_sources=DATA_SOURCES,
            sensor=sensor,
            weather=weather,
            risk=DroughtRiskResult(
                score=risk.score,
                level=risk.level,
                factors=risk.factors,
            ),
            gemini=gemini,
        )
