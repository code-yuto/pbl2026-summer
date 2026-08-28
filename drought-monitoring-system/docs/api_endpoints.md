# API endpoints

## Health

```http
GET /health
```

Checks whether FastAPI is running.

## Current and forecast weather

```http
GET /api/weather?latitude=21.0278&longitude=105.8342
```

Returns current temperature, humidity and precipitation, previous seven-day
precipitation, three-day and seven-day forecast precipitation, and FAO ET0
evapotranspiration from Open-Meteo. Coordinates are optional. When they are
omitted, the backend uses `FARM_LATITUDE` and `FARM_LONGITUDE`.

## Complete drought assessment

```http
POST /api/drought/analyze
Content-Type: application/json
```

```json
{
  "device_id": "SIMULATED_01",
  "soil_moisture": 18,
  "water_level": 4,
  "latitude": 21.0278,
  "longitude": 105.8342
}
```

Processing order:

1. Validate the physical sensor data.
2. Fetch Open-Meteo data.
3. Calculate a deterministic 0-100 drought-risk score.
4. Ask Gemini to explain the fixed risk result.
5. Store linked sensor, weather and assessment records in Supabase.

This endpoint requires the three Supabase migrations and `GEMINI_API_KEY`.

## Sensor-only endpoints

```http
POST /api/readings
GET /api/readings/latest
GET /api/readings/history?limit=100
```

These endpoints use physical sensor data and fixed thresholds without calling
Open-Meteo or Gemini.

## Supabase dashboard feeds

```http
GET /api/dashboard/readings?limit=720
GET /api/dashboard/weather?limit=100
GET /api/dashboard/assessments?limit=100
```

These endpoints provide the Streamlit dashboard with complete Supabase sensor
rows, weather snapshots, deterministic drought scores, and saved Gemini
explanations. The sensor endpoint includes the original ADC values, device
status, LED colour, calibrated percentages and server reception time.

## ESP32 USB Serial payload

```http
POST /api/readings/serial
Content-Type: application/json
```

The endpoint accepts the exact object printed by the ESP32:

```json
{
  "type": "data_medium",
  "water_level": 512,
  "soil_moisture": 1800,
  "led_color": "CYAN",
  "timestamp_ms": 123456
}
```

The incoming sensor values are raw ESP32 ADC readings from 0 to 4095. The
backend preserves the original payload and calculates separate 0-100 values
using the calibration settings in `.env`. `timestamp_ms` is device uptime and
is not converted into a calendar time. Supabase `created_at` records the actual
server reception time.
