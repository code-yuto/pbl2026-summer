# Run Commands (in execution order)

Pure command reference, no explanation -- see [environment-setup.md](environment-setup.md)
for details on any step. Run steps 2-4 in **separate terminals** at the
same time; start them in this order.

## 1. Flash the ESP32 (Arduino IDE, not a terminal command)

1. Open `esp32_water_soil_sensor/esp32_water_soil_sensor.ino` in the Arduino IDE.
2. `Tools > Board` -> select your ESP32 board (e.g. "ESP32 Dev Module").
3. `Tools > Port` -> select the ESP32's COM port.
4. Click Upload.
5. Note the COM port -- needed in step 3 below. Close the Serial Monitor
   afterward so the port is free for the bridge script.

## 2. Terminal 1 -- Backend API

```bash
cd drought-monitoring-system/backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Verify: open `http://localhost:8000/docs`. Keep this running.

## 3. Terminal 2 -- Serial bridge (ESP32 -> Backend)

```bash
cd drought-monitoring-system
python scripts/serial_bridge.py --port COM3 --backend-url http://127.0.0.1:8000
```

Replace `COM3` with the port from step 1. Must be started **after**
Terminal 1 is already running. Keep this running.

## 4. Terminal 3 -- Dashboard (optional)

```bash
cd drought-monitoring-system/dashboard
pip install -r requirements.txt
streamlit run app.py
```

Verify: open `http://localhost:8501`.
