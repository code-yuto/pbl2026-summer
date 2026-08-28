# Google Colab runner

This folder lets you run the Python parts of the Drought Monitoring System in
Google Colab without changing the existing backend or dashboard files.

## Quick start

1. Upload `Agricultural_Analytics_Colab.ipynb` to
   [Google Colab](https://colab.research.google.com/).
2. Run the notebook from top to bottom.
3. When prompted, upload the complete `drought-monitoring-system.zip` file.
4. Add credentials in **Colab > Secrets** when you need live services.

## Colab Secrets

| Secret | Required | Purpose |
| --- | --- | --- |
| `SUPABASE_URL` | For live data | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | For live data | Supabase service-role key |
| `FARM_LATITUDE` | Optional | Farm latitude; defaults to the Hanoi demo location |
| `FARM_LONGITUDE` | Optional | Farm longitude; defaults to the Hanoi demo location |
| `SERIAL_DEVICE_ID` | Optional | Name assigned to the USB-connected ESP32 |
| `SOIL_SENSOR_DRY_RAW` | Before field use | Soil sensor value measured in dry soil |
| `SOIL_SENSOR_WET_RAW` | Before field use | Soil sensor value measured in wet soil |
| `WATER_SENSOR_EMPTY_RAW` | Before field use | Water sensor value measured when empty |
| `WATER_SENSOR_FULL_RAW` | Before field use | Water sensor value measured when full |
| `NGROK_AUTH_TOKEN` | For public links | Exposes FastAPI and Streamlit outside Colab |
| `GEMINI_API_KEY` | For drought analysis | Gemini explanation and recommendations |
| `LINE_CHANNEL_ACCESS_TOKEN` | Later integration | LINE push alerts |
| `LINE_CHANNEL_SECRET` | Later integration | LINE webhook verification |

Before using live Supabase data, run the SQL files in
`supabase/migrations/` through the Supabase SQL Editor.

## What Colab can run

- FastAPI backend
- Streamlit and Plotly dashboard
- Supabase, Open-Meteo, Gemini, and LINE API calls
- Simulated sensor requests

The ESP32 `.ino` firmware still needs Arduino IDE or PlatformIO. Colab sessions
also stop when the runtime disconnects, so this setup is for development and
demonstrations rather than permanent deployment.
