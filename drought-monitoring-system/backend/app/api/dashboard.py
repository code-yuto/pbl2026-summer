import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from starlette.concurrency import run_in_threadpool

from app.database.monitoring_repository import (
    MonitoringRepository,
    get_monitoring_repository,
)


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Dashboard"])


async def _repository_call(method, *args) -> Any:
    try:
        return await run_in_threadpool(method, *args)
    except Exception as error:
        logger.exception("Unable to retrieve dashboard data")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve dashboard data from the backend",
        ) from error


@router.get("/dashboard/readings")
async def get_dashboard_readings(
    limit: int = Query(default=720, ge=1, le=5000),
    repository: MonitoringRepository = Depends(get_monitoring_repository),
) -> list[dict[str, Any]]:
    """Return full sensor rows, including raw ESP32 fields."""

    return await _repository_call(
        repository.get_reading_history,
        limit,
    )


@router.get("/dashboard/weather")
async def get_dashboard_weather(
    limit: int = Query(default=100, ge=1, le=1000),
    repository: MonitoringRepository = Depends(get_monitoring_repository),
) -> list[dict[str, Any]]:
    return await _repository_call(
        repository.get_weather_history,
        limit,
    )


@router.get("/dashboard/assessments")
async def get_dashboard_assessments(
    limit: int = Query(default=100, ge=1, le=1000),
    repository: MonitoringRepository = Depends(get_monitoring_repository),
) -> list[dict[str, Any]]:
    return await _repository_call(
        repository.get_drought_assessment_history,
        limit,
    )
