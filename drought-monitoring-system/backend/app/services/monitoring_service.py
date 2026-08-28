from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.database.monitoring_repository import MonitoringRepository
from app.models.report_models import (
    DroughtAnalysisRequest,
    DroughtAnalysisResponse,
    DroughtRiskResult,
)
from app.models.report_models import GeminiDroughtAnalysis
from app.models.sensor_models import SensorReadingCreate
from app.models.weather_models import WeatherSnapshot
from app.services.gemini_service import GeminiService
from app.services.risk_service import (
    DroughtRiskAssessment,
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
        return await self._analyze_and_store(request)

    async def analyze_existing_and_store(
        self,
        request: DroughtAnalysisRequest,
        sensor_reading_id: int,
    ) -> DroughtAnalysisResponse:
        return await self._analyze_and_store(request, sensor_reading_id)

    async def analyze_latest_reading(self) -> DroughtAnalysisResponse | None:
        """Force-run Gemini on whichever sensor reading is newest right now.

        Used by the manual "analyze now" dashboard action - always runs,
        even if the latest reading was already assessed. Returns None only
        when no sensor reading has ever been saved.
        """
        latest_reading = await run_in_threadpool(
            self.repository.get_latest_reading
        )
        if latest_reading is None:
            return None

        request = DroughtAnalysisRequest(
            device_id=str(
                latest_reading.get("device_id")
                or self.settings.serial_device_id
            ),
            soil_moisture=float(latest_reading["soil_moisture"]),
            water_level=float(latest_reading["water_level"]),
        )
        return await self.analyze_existing_and_store(
            request,
            int(latest_reading["id"]),
        )

    async def poll_latest_reading(self) -> DroughtAnalysisResponse | None:
        """Scheduler entry point: skip when nothing new has arrived.

        Returns None when there is no reading yet, or the newest reading has
        already been assessed - the poller calls this every tick, so this
        keeps it from re-fetching weather / calling Gemini when no new
        sensor data has arrived since the last run.
        """
        latest_reading = await run_in_threadpool(
            self.repository.get_latest_reading
        )
        if latest_reading is None:
            return None

        latest_assessment = await run_in_threadpool(
            self.repository.get_latest_drought_assessment
        )
        if (
            latest_assessment is not None
            and latest_assessment.get("monitoring_id") == latest_reading["id"]
        ):
            return None

        return await self.analyze_latest_reading()

    async def _analyze_and_store(
        self,
        request: DroughtAnalysisRequest,
        sensor_reading_id: int | None = None,
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

        weather, risk, gemini = await self._run_pipeline(
            sensor,
            latitude,
            longitude,
        )

        try:
            analysis_fields = {
                "temperature": weather.temperature_c,
                "humidity": weather.humidity_percent,
                "risk_level": risk.level,
                "llm_explanation": gemini.summary,
                "recommendation": "\n".join(gemini.recommendations),
            }
            if sensor_reading_id is None:
                saved_sensor = await run_in_threadpool(
                    self.repository.save_reading,
                    {
                        **sensor.model_dump(),
                        **analysis_fields,
                        "alert_sent": False,
                    },
                )
            else:
                saved_sensor = await run_in_threadpool(
                    self.repository.update_reading_analysis,
                    sensor_reading_id,
                    analysis_fields,
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

    async def _run_pipeline(
        self,
        sensor: SensorReadingCreate,
        latitude: float,
        longitude: float,
    ) -> tuple[WeatherSnapshot, DroughtRiskAssessment, GeminiDroughtAnalysis]:
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
        return weather, risk, gemini
