# Google Colab database-free runner

The notebook runs FastAPI and Streamlit in one temporary Colab runtime using
in-memory storage. Supabase is not required.

## Quick start

1. Upload `Agricultural_Analytics_Colab.ipynb` to Google Colab.
2. Run the notebook from top to bottom.
3. Upload the complete `drought-monitoring-system.zip` when prompted.
4. Add the required keys under **Colab > Secrets**.

| Secret | Required | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | For AI reports and chat | Gemini explanation service |
| `NGROK_AUTH_TOKEN` | For public URLs | Exposes FastAPI and Streamlit |
| `FARM_LATITUDE` | Optional | Farm latitude |
| `FARM_LONGITUDE` | Optional | Farm longitude |
| Sensor calibration values | Before field use | Converts ADC readings to percentages |

Open-Meteo requires no API key. The notebook sets `STORAGE_BACKEND=memory`.
Readings, weather snapshots and Gemini assessments disappear when the runtime
stops.

An ESP32 connected to your own computer cannot be read directly by Colab. Run
`scripts/serial_bridge.py` locally and set its `--backend-url` to the FastAPI
ngrok URL printed by the notebook.
