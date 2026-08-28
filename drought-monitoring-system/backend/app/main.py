import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analysis import router as analysis_router
from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.api.readings import router as readings_router
from app.api.weather import router as weather_router
from app.core.config import Settings, get_settings
from app.database.monitoring_repository import get_monitoring_repository
from app.services.gemini_service import get_gemini_service
from app.services.monitoring_service import MonitoringService
from app.services.weather_service import get_weather_service


logger = logging.getLogger(__name__)


async def _poll_latest_reading(settings: Settings) -> None:
    """Re-evaluate the newest sensor reading with Gemini, once per tick.

    Runs only while this backend process is alive, and poll_latest_reading
    is a no-op whenever no new sensor reading has arrived since the last
    tick, so this never calls the weather API or Gemini without fresh data.
    A manual "analyze now" dashboard action can still force a fresh run in
    between ticks via MonitoringService.analyze_latest_reading.
    """
    service = MonitoringService(
        repository=get_monitoring_repository(),
        weather_service=get_weather_service(),
        gemini_service=get_gemini_service(),
        settings=settings,
    )

    while True:
        try:
            result = await service.poll_latest_reading()
            if result is not None:
                logger.info(
                    "Scheduled drought analysis stored for reading %s",
                    result.sensor_reading_id,
                )
        except Exception:
            logger.exception("Scheduled drought analysis failed")

        await asyncio.sleep(settings.analysis_poll_interval_seconds)


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    poll_task = asyncio.create_task(_poll_latest_reading(settings))
    try:
        yield
    finally:
        poll_task.cancel()
        try:
            await poll_task
        except asyncio.CancelledError:
            pass


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health_router)
    application.include_router(readings_router, prefix="/api")
    application.include_router(weather_router, prefix="/api")
    application.include_router(analysis_router, prefix="/api")
    application.include_router(dashboard_router, prefix="/api")

    return application


app = create_app()
