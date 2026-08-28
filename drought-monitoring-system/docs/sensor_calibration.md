# ESP32 sensor calibration and USB Serial setup

## Arduino setup

1. Install the ESP32 board package in Arduino IDE.
2. Upload `drought_monitor.ino` to the ESP32.
3. Open Serial Monitor at `9600` baud to inspect the English status and JSON.
4. Close Serial Monitor before starting the Python bridge. Only one program can
   use the serial port at a time.

The ESP32 does not use WiFi. It sends newline-delimited JSON through its USB
serial port. No additional Arduino library is required.

## Python serial bridge

Install the backend requirements, start FastAPI, and run:

```bash
python scripts/serial_bridge.py --port COM3
```

Replace `COM3` with the port shown by Windows Device Manager or Arduino IDE.
For Linux, the port is normally `/dev/ttyUSB0` or `/dev/ttyACM0`.

If FastAPI is running in Colab, run the bridge locally with the FastAPI ngrok
URL:

```bash
python scripts/serial_bridge.py --port COM3 \
  --backend-url https://YOUR-FASTAPI-URL.ngrok-free.app
```

Google Colab cannot directly access a USB serial port attached to your local
computer. The bridge must run on the computer connected to the ESP32.

## Current decision thresholds

| Sensor state | Raw ADC condition |
| --- | --- |
| Possible flood | Water level at least 3500 |
| Full water supply | Water level at least 1500 |
| Low water supply | Water level below 300 |
| Wet soil | Soil reading below 1500 |
| Dry soil | Soil reading above 2800 |
| Possible disconnection | Soil reading at most 50 |
| Possible short circuit | Soil reading at least 4000 |

The capacitive soil sensor is inverted: lower readings mean wetter soil.

## Backend calibration

The backend preserves every original ADC value. It also calculates percentages
using these `.env` settings:

```text
SOIL_SENSOR_DRY_RAW=2800
SOIL_SENSOR_WET_RAW=1500
WATER_SENSOR_EMPTY_RAW=0
WATER_SENSOR_FULL_RAW=1500
```

These values match the initial sketch thresholds, but they are not a substitute
for physical calibration. Record stable values in dry soil, wet soil, an empty
water container and a full water container, then replace the defaults.
