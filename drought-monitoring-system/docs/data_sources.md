# Drought data sources

| Variable | Source | Stored in | Use in drought assessment |
| --- | --- | --- | --- |
| Soil moisture raw | Physical sensor | `monitoring_data.soil_moisture_raw` | Preserves the original 0-4095 ADC reading |
| Soil moisture percent | Backend calibration | `monitoring_data.soil_moisture` | Measures current soil dryness on a 0-100 scale |
| Water level raw | Physical sensor | `monitoring_data.water_level_raw` | Preserves the original 0-4095 ADC reading |
| Water level percent | Backend calibration | `monitoring_data.water_level` | Measures available stored water on a 0-100 scale |
| Message type | Physical sensor | `monitoring_data.message_type` | Preserves whether the device sent `data` or `alert` |
| LED colour | ESP32 decision rules | `monitoring_data.led_color` | Records the local status colour shown to the user |
| Device uptime | Physical sensor | `monitoring_data.device_timestamp_ms` | Preserves milliseconds since the ESP32 started |
| Precipitation | Open-Meteo API | `weather_data.precipitation_mm` | Measures current rainfall |
| Recent precipitation | Open-Meteo API | `weather_data.recent_precipitation_7d_mm` | Measures rain received during the previous 7 days |
| Forecast precipitation | Open-Meteo API | `weather_data.forecast_precipitation_3d_mm` and `forecast_precipitation_7d_mm` | Estimates future water supply |
| Temperature | Open-Meteo API | `weather_data.temperature_c` | Indicates heat stress and faster water loss |
| Evapotranspiration | Open-Meteo API | `weather_data.evapotranspiration_mm` and `forecast_evapotranspiration_7d_mm` | Estimates water loss from soil and plants |
| Humidity | Open-Meteo API | `weather_data.humidity_percent` | Low humidity indicates faster drying |
| Risk score | Backend calculation | `drought_assessments.risk_score` | Produces a reproducible 0-100 drought score |
| Explanation | Gemini API | `drought_assessments.summary` | Explains drivers and recommends actions |

The backend calculation determines the risk level. Gemini is not allowed to
change or downgrade this level. Initial thresholds are development defaults
and must be calibrated for the actual crop, soil and sensor placement.
