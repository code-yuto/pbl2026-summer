# TerraPulse Drought Monitoring System

TerraPulse uses live ESP32 readings, Open-Meteo weather data and Gemini
explanations without requiring a database. FastAPI keeps recent data in memory
while it is running, and Streamlit reads that live session through the API.

## Live data flow

```text
ESP32 -> USB Serial -> Python bridge -> FastAPI session memory
Open-Meteo --------------------------> FastAPI -> Streamlit dashboard
Gemini <------------------------------ FastAPI -> Forecast chat
```

No dummy data is loaded automatically. If a live source is unavailable, the
dashboard shows a waiting message. Data is cleared whenever FastAPI restarts.

## 1. Configure the project

Copy `.env.example` to `.env` in the main project folder. The database-free
settings are:

```env
STORAGE_BACKEND=memory
MEMORY_HISTORY_LIMIT=10000
GEMINI_API_KEY=your-gemini-api-key
FARM_LATITUDE=21.0278
FARM_LONGITUDE=105.8342
```

Open-Meteo does not require an API key. Supabase credentials and SQL migrations
are not required in memory mode.

## 2. Start FastAPI on Windows

From the `backend` folder:

```powershell
python -m venv .backend-venv
.\.backend-venv\Scripts\python.exe -m pip install --upgrade pip
.\.backend-venv\Scripts\python.exe -m pip install -r requirements.txt
.\.backend-venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000/docs`. The health response should contain:

```json
{"status":"healthy","storage":"memory"}
```

## 3. Send real ESP32 data

Upload `esp32/drought_monitor.ino`, close Arduino Serial Monitor and run from
the main project folder:

```powershell
backend\.backend-venv\Scripts\python.exe scripts\serial_bridge.py --port COM3 --backend-url http://127.0.0.1:8000
```

Replace `COM3` with the actual ESP32 port. The bridge reads JSON at `9600` baud
and forwards calibrated sensor data to FastAPI.

## 4. Start Streamlit in a separate environment

From the `dashboard` folder:

```powershell
python -m venv .dashboard-venv
.\.dashboard-venv\Scripts\python.exe -m pip install --upgrade pip
.\.dashboard-venv\Scripts\python.exe -m pip install -r requirements.txt
.\.dashboard-venv\Scripts\python.exe -m streamlit run app.py
```

Open `http://localhost:8501`, enter `http://127.0.0.1:8000` as the FastAPI URL
and select **Connect and refresh**.

## 5. Generate and discuss a forecast

Open **Forecast AI chat** and select **Generate latest forecast**. FastAPI will:

1. Use the newest live ESP32 sensor reading.
2. Fetch current and forecast weather from Open-Meteo.
3. Calculate a deterministic drought score.
4. Ask Gemini for an explanation and recommended actions.
5. Keep the linked result in memory for dashboard charts and chat.

Gemini chat receives only the selected sensor reading, Open-Meteo snapshot and
calculated assessment. It cannot change the deterministic risk level.

## Use FastAPI through ngrok

Keep FastAPI running and start another terminal:

```powershell
ngrok http 8000
```

Paste the HTTPS ngrok URL into **FastAPI URL** in the Streamlit sidebar. The
dashboard sends the required ngrok browser-warning bypass header automatically.

## Main endpoints

- `POST /api/readings/serial` receives ESP32 USB Serial data.
- `GET /api/weather` fetches Open-Meteo directly.
- `POST /api/drought/analyze/latest` analyzes the newest live sensor reading.
- `POST /api/drought/chat` explains a current-session forecast with Gemini.
- `GET /api/dashboard/readings` returns in-memory sensor history.
- `GET /api/dashboard/weather` returns in-memory analyzed weather snapshots.
- `GET /api/dashboard/assessments` returns in-memory forecast history.

Before field use, replace the example raw calibration values in `.env` with
measurements from dry soil, wet soil, an empty water container and a full water
container.
