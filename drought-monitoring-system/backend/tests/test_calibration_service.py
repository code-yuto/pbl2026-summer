from app.services.calibration_service import SensorCalibration


def test_calibrates_example_serial_values() -> None:
    calibration = SensorCalibration(
        soil_dry_raw=2800,
        soil_wet_raw=1500,
        water_empty_raw=0,
        water_full_raw=1500,
    )

    result = calibration.calibrate(
        soil_moisture_raw=1800,
        water_level_raw=512,
    )

    assert result.soil_moisture_percent == 76.92
    assert result.water_level_percent == 34.13


def test_calibration_is_clamped_to_valid_percentage() -> None:
    calibration = SensorCalibration(
        soil_dry_raw=3000,
        soil_wet_raw=1200,
        water_empty_raw=100,
        water_full_raw=3900,
    )

    result = calibration.calibrate(
        soil_moisture_raw=4095,
        water_level_raw=4095,
    )

    assert result.soil_moisture_percent == 0
    assert result.water_level_percent == 100
