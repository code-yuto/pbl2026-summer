# Full Environment Setup Guide

This guide is for anyone who clones this repository from GitHub and wants
to run the **whole system end-to-end**: ESP32 sensor -> USB Serial bridge
-> FastAPI backend -> Weather API + Gemini LLM -> (optional) dashboard.

**Short answer to "is `pip install -r requirements.txt` enough?": no.**
That only installs Python packages for one of the two Python projects.
You also need: API keys in a `.env` file, the Arduino IDE with ESP32
board support to flash the microcontroller, and two Python processes
running at the same time (backend + serial bridge). All steps are below.

## 0. Repository layout

As of commit `ba6d922` ("Integrate drought monitoring system"), the
backend + dashboard are vendored directly inside this repo under
`drought-monitoring-system/` -- there is nothing else to clone.
`python-reference-example/` is a separate, non-authoritative stand-in,
useful only to see the JSON contract in action without the real
backend.

```text
pbl2026-summer/                 <- this repo, clone only this
  esp32_water_soil_sensor/
  docs/
  drought-monitoring-system/     <- backend + dashboard, already inside
    backend/
    dashboard/
    scripts/
```

```bash
git clone <this-repo-url> pbl2026-summer
```

If you previously cloned `drought-monitoring-system` as a separate
sibling folder (following an older version of this guide), delete that
standalone clone -- it is a duplicate of the one already inside
`pbl2026-summer/`. Always run the commands below from
`pbl2026-summer/drought-monitoring-system`.

## 1. Flash the ESP32 (Edge side)

1. Install the [Arduino IDE](https://www.arduino.cc/en/software) and add
   ESP32 board support (Boards Manager -> search "esp32" -> install).
2. Open `esp32_water_soil_sensor/esp32_water_soil_sensor.ino`.
3. Wire the hardware per this pinout (also in the top-level
   [README.md](../README.md)):

   | Component                   | ESP32 Pin |
   | ---------------------------- | --------- |
   | Soil moisture sensor (AOUT)  | GPIO36    |
   | Water level sensor (signal)  | GPIO34    |
   | RGB status LED -- Red        | GPIO26    |
   | RGB status LED -- Green      | GPIO27    |
   | RGB status LED -- Blue       | GPIO25    |

4. Select your board and port in Tools, then Upload.
5. Note the COM port (Windows: Tools > Port, e.g. `COM3`). Close the
   Serial Monitor afterward -- only one program can hold the port open
   at a time (Arduino IDE Serial Monitor OR the bridge script, not both).

The ESP32 does its own threshold check locally and prints one JSON
object per line over USB Serial at 9600 baud, e.g.:

```json
{"type":"data_ideal","water_level":1800,"soil_moisture":2000,"led_color":"GREEN","timestamp_ms":123456}
```

See [JSON-interface.md](JSON-interface.md) for the full field/`type`
reference.

## 2. Set up and run the backend (Python)

```bash
cd drought-monitoring-system/backend
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

Then configure environment variables -- this is the step that
`pip install` alone does not cover:

1. `cd drought-monitoring-system` (repo root) and copy
   `.env.example` to `.env`.
2. Set `GEMINI_API_KEY` to a real [Google AI Studio](https://aistudio.google.com/)
   key -- without it, `/api/drought/analyze` fails.
3. Set `FARM_LATITUDE` / `FARM_LONGITUDE` to your location (defaults to
   Hanoi). No key is needed for the weather API (Open-Meteo).
4. Supabase is **not** required for local use -- readings are appended
   to JSON Lines files under `drought-monitoring-system/data/` instead.

Start the API:

```bash
uvicorn app.main:app --reload
```

Serves at `http://localhost:8000` (`/docs` for interactive Swagger UI).
Keep this process running.

## 3. Connect the ESP32 to the backend (the bridge)

In a **second** terminal, from `drought-monitoring-system`:

```bash
python scripts/serial_bridge.py --port COM3 --backend-url http://127.0.0.1:8000
```

Replace `COM3` with the port noted in step 1. The bridge reads each
JSON line the ESP32 prints and forwards it to
`POST /api/readings/serial`, sending immediately on a status change and
every 30 seconds otherwise. You should see:

```text
Saved row 1 | data_ideal | soil 55.0% | water 66.7%
```

## 4. (Optional) Run the dashboard

In a **third** terminal:

```bash
cd drought-monitoring-system/dashboard
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`, reading data from the backend.

## How the IoT device and the LLM are actually integrated

There is no direct network link between the ESP32 and the LLM. The
integration happens in three stages, split across the two repos:

1. **Edge (ESP32, this repo)** -- reads both sensors every second and
   runs a purely local threshold check (see the constants in
   `esp32_water_soil_sensor.ino`). This decides the `type` string
   (`alert_*`, `warning_*`, or `data_*`) and picks the RGB LED color.
   The ESP32 itself never calls any API -- it only prints JSON to
   Serial.

2. **Bridge + storage (`serial_bridge.py` -> `POST /api/readings/serial`)**
   -- every reading is calibrated and stored, but **no LLM call happens
   here**. This keeps continuous sensor polling cheap.

3. **LLM analysis (`POST /api/drought/analyze`, `gemini_service.py`)**
   -- a separate, throttled call that: fetches live/forecast weather
   from Open-Meteo, computes a deterministic drought-risk score, then
   sends sensor + weather + risk data to Gemini
   (`gemini-2.5-flash-lite` by default) asking it to explain the
   already-computed risk in plain English and suggest actions. Gemini
   is explicitly instructed not to change the risk level -- it only
   explains and recommends, it does not decide anomaly vs. normal.
   Readings whose `type` starts with `alert_` are meant to bypass this
   step entirely and notify the user immediately instead.

In short: **the microcontroller decides urgency locally and cheaply;
the LLM is only consulted afterward, and only to turn numbers into a
human-readable explanation/recommendation**, not to make the anomaly
decision itself.
