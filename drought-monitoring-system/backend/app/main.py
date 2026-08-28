from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analysis import router as analysis_router
from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.api.readings import router as readings_router
from app.api.weather import router as weather_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
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
