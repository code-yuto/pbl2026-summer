import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.database.monitoring_repository import (
    MonitoringRepository,
    get_monitoring_repository,
)
from app.models.sensor_models import (
    SerialSensorPayload,
    SerialSensorReadingResponse,
    SensorReadingCreate,
    SensorReadingResponse,
)
from app.services.calibration_service import SensorCalibration
from app.services.risk_service import RiskThresholds, calculate_risk_level


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Readings"])


@router.post(
    "/readings/serial",
    response_model=SerialSensorReadingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_serial_reading(
    payload: SerialSensorPayload,
    device_id: str | None = Query(default=None, min_length=1, max_length=100),
    repository: MonitoringRepository = Depends(get_monitoring_repository),
) -> SerialSensorReadingResponse:
    settings = get_settings()
    calibration = SensorCalibration.from_settings(settings)
    calibrated = calibration.calibrate(
        soil_moisture_raw=payload.soil_moisture,
        water_level_raw=payload.water_level,
    )
    thresholds = RiskThresholds.from_settings(settings)
    risk_level = calculate_risk_level(
        soil_moisture=calibrated.soil_moisture_percent,
        water_level=calibrated.water_level_percent,
        thresholds=thresholds,
    )
    selected_device_id = (device_id or settings.serial_device_id).strip()
    raw_payload = payload.model_dump(by_alias=True)
    sensor_record = {
        "device_id": selected_device_id,
        "message_type": payload.message_type,
        "sensor_transport": "usb_serial",
        "soil_moisture_raw": payload.soil_moisture,
        "water_level_raw": payload.water_level,
        "device_timestamp_ms": payload.timestamp_ms,
        "led_color": payload.led_color,
        "soil_moisture": calibrated.soil_moisture_percent,
        "water_level": calibrated.water_level_percent,
        "risk_level": risk_level,
        "raw_payload": raw_payload,
        "alert_sent": False,
    }

    try:
        saved_record = await run_in_threadpool(
            repository.save_reading,
            sensor_record,
        )
    except Exception as error:
        logger.exception("Unable to save serial sensor reading")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to save the serial sensor reading",
        ) from error

    return SerialSensorReadingResponse(
        **saved_record,
        device_alert=payload.message_type.startswith("alert"),
        saved=True,
    )


@router.post(
    "/readings",
    response_model=SensorReadingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_reading(
    reading: SensorReadingCreate,
    repository: MonitoringRepository = Depends(get_monitoring_repository),
) -> SensorReadingResponse:
    settings = get_settings()
    thresholds = RiskThresholds.from_settings(settings)

    risk_level = calculate_risk_level(
        soil_moisture=reading.soil_moisture,
        water_level=reading.water_level,
        thresholds=thresholds,
    )

    sensor_record = {
        **reading.model_dump(),
        "risk_level": risk_level,
        "alert_sent": False,
    }

    try:
        saved_record = await run_in_threadpool(
            repository.save_reading,
            sensor_record,
        )
    except Exception as error:
        logger.exception("Unable to save sensor reading")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to save the sensor reading",
        ) from error

    return SensorReadingResponse(**saved_record, saved=True)


@router.get(
    "/readings/latest",
    response_model=SensorReadingResponse,
)
async def get_latest_reading(
    repository: MonitoringRepository = Depends(get_monitoring_repository),
) -> SensorReadingResponse:
    try:
        record = await run_in_threadpool(repository.get_latest_reading)
    except Exception as error:
        logger.exception("Unable to retrieve latest sensor reading")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve the latest sensor reading",
        ) from error

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sensor readings found",
        )

    return SensorReadingResponse(**record, saved=True)


@router.get(
    "/readings/history",
    response_model=list[SensorReadingResponse],
)
async def get_reading_history(
    limit: int = Query(default=100, ge=1, le=1000),
    repository: MonitoringRepository = Depends(get_monitoring_repository),
) -> list[SensorReadingResponse]:
    try:
        records = await run_in_threadpool(
            repository.get_reading_history,
            limit,
        )
    except Exception as error:
        logger.exception("Unable to retrieve sensor history")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve sensor history",
        ) from error

    return [SensorReadingResponse(**record, saved=True) for record in records]
