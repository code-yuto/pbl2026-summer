# Drought Monitoring System

The backend accepts sensor readings, fetches current and forecast weather from
Open-Meteo, calculates an auditable drought-risk score, asks Gemini for a
structured explanation and stores the linked results in Supabase.

## Setup

1. Run all SQL files in `supabase/migrations` in filename order using the
   Supabase SQL Editor.
2. Copy `.env.example` to `.env` and enter the Supabase credentials.
3. Install the backend packages:

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # macOS or Linux
   .venv\Scripts\activate     # Windows PowerShell
   pip install -r requirements.txt
   ```

4. Start FastAPI:

   ```bash
   uvicorn app.main:app --reload
   ```

5. Open `http://localhost:8000/docs` to test the API.

Important endpoints:

- `GET /api/weather` gets Open-Meteo data. Optional `latitude` and `longitude`
  query parameters override the configured farm location.
- `POST /api/drought/analyze` accepts sensor data, calculates risk, calls
  Gemini and stores the complete assessment.
- `POST /api/readings` stores a sensor-only reading with fixed thresholds.
- `POST /api/readings/serial` accepts the exact raw JSON object printed by the
  ESP32 and preserves both raw and calibrated values.

Set `FARM_LATITUDE`, `FARM_LONGITUDE` and `GEMINI_API_KEY` in `.env`. Open-Meteo
does not require an API key.

Before using real sensor readings, replace the example raw calibration values
in `.env` with measurements taken from the actual dry soil, wet soil, empty
water container and full water container.

## ESP32 USB Serial upload

The ESP32 firmware uses USB Serial only and prints one JSON object per line at
`9600` baud. Run `scripts/serial_bridge.py` on the connected computer to send a
row immediately when the status changes and every 30 seconds while it remains
unchanged. See `docs/sensor_calibration.md` for commands and calibration.

## Run the dashboard

Open a second terminal from the project root:

```bash
cd dashboard
python -m venv .venv
source .venv/bin/activate  # macOS or Linux
.venv\Scripts\activate     # Windows PowerShell
pip install -r requirements.txt
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`. It loads full sensor rows,
Open-Meteo snapshots and Gemini drought assessments from Supabase through
FastAPI. Every page labels whether each section is live or demonstration data.
Use **Refresh live data** in the sidebar after inserting a new reading or
generating an assessment.

## Example request

Complete drought analysis:

```bash
curl -X POST http://localhost:8000/api/drought/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "SIMULATED_01",
    "soil_moisture": 18,
    "water_level": 4,
    "latitude": 21.0278,
    "longitude": 105.8342
  }'
```

Sensor data only:

```json
{
  "device_id": "SIMULATED_01",
  "soil_moisture": 18,
  "water_level": 4
}
```
