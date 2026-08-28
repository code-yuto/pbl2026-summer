# Live drought data sources

| Variable | Source | Temporary location | Use |
| --- | --- | --- | --- |
| Soil moisture raw | Physical sensor | FastAPI memory | Original ESP32 ADC reading |
| Soil moisture percent | Backend calibration | FastAPI memory | Current soil dryness |
| Water level raw | Physical sensor | FastAPI memory | Original ESP32 ADC reading |
| Water level percent | Backend calibration | FastAPI memory | Available stored water |
| Device status and LED | ESP32 rules | FastAPI memory | Immediate local condition |
| Temperature | Open-Meteo API | FastAPI memory after analysis | Heat stress |
| Humidity | Open-Meteo API | FastAPI memory after analysis | Drying pressure |
| Recent precipitation | Open-Meteo API | FastAPI memory after analysis | Recent water input |
| Forecast precipitation | Open-Meteo API | FastAPI memory after analysis | Expected water input |
| Evapotranspiration | Open-Meteo API | FastAPI memory after analysis | Expected water loss |
| Risk score | Deterministic backend | FastAPI memory | Reproducible drought severity |
| Explanation | Gemini API | FastAPI memory | Clear drivers and actions |

The dashboard also calls `GET /api/weather` directly when no analyzed weather
snapshot exists yet. No generated dummy data is inserted. The backend risk
level remains authoritative, and Gemini cannot change it.
