# Live API endpoints

## Health

```http
GET /health
```

Returns the service status and active storage mode. Database-free operation
returns `"storage": "memory"`.

## Current Open-Meteo weather

```http
GET /api/weather?latitude=21.0278&longitude=105.8342
```

Fetches weather directly from Open-Meteo. Coordinates are optional and default
to `FARM_LATITUDE` and `FARM_LONGITUDE`.

## Receive ESP32 USB Serial data

```http
POST /api/readings/serial
Content-Type: application/json
```

```json
{
  "type": "data_medium",
  "water_level": 512,
  "soil_moisture": 1800,
  "led_color": "CYAN",
  "timestamp_ms": 123456
}
```

The endpoint preserves raw 0-4095 ADC values, calculates calibrated percentages
and keeps the reading in FastAPI memory.

## Analyze the latest live reading

```http
POST /api/drought/analyze/latest
```

Uses the newest sensor reading, fetches Open-Meteo, calculates drought risk,
calls Gemini and links all three results in the current FastAPI session.

## Chat about a forecast

```http
POST /api/drought/chat
Content-Type: application/json
```

```json
{
  "question": "Why is this risk level high?",
  "assessment_id": 1,
  "history": []
}
```

Gemini receives the selected ESP32 reading, Open-Meteo snapshot and fixed risk
assessment. If `assessment_id` is omitted, the latest assessment is used.

## Dashboard session feeds

```http
GET /api/dashboard/readings?limit=720
GET /api/dashboard/weather?limit=100
GET /api/dashboard/assessments?limit=100
```

These endpoints return only data collected during the current FastAPI process.
They return empty arrays before data arrives and after FastAPI restarts.
