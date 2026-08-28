# Implementation Rules: USB Serial Transport (current)

This is the transport currently implemented in
`esp32_water_soil_sensor/esp32_water_soil_sensor.ino`. No Wi-Fi, no
network setup -- the ESP32 stays connected to a PC by USB cable.

Payload examples: [json-payload-serial.json](json-payload-serial.json)

## Rules

1. **Baud rate**: 9600. Must match `Serial.begin(9600)` in the `.ino`
   file. Whatever reads the port must use the same baud rate or the
   bytes will be garbled.
2. **One JSON object per line.** Each reading is printed as a single
   line ending in `\n` (see `printReading()` in the `.ino` file).
3. **The sketch also prints human-readable debug lines**, e.g.
   `>>> TRẠNG THÁI: Nước đầy - Đất độ ẩm vừa (Lý tưởng) | LED: XANH LÁ`.
   Any reader must skip lines that don't start with `{` before trying to
   parse JSON.
4. **Only one process can hold the serial port open at a time.** Close
   the Arduino IDE's Serial Monitor before running any other program
   against the same port, or the second program will fail to open it.
5. **Payload fields and `type` values**: see
   [JSON-interface.md](JSON-interface.md) for the full contract.

## Connecting to the real Backend

The real Backend (`drought-monitoring-system`) ships its own bridge
script for exactly this transport:
`drought-monitoring-system/scripts/serial_bridge.py`. It reads the
serial port and forwards each reading to
`POST /api/readings/serial` on the FastAPI backend -- sending
immediately when the status changes, and every 30 seconds while
unchanged.

1. `cd drought-monitoring-system/backend && pip install -r requirements.txt`
2. `uvicorn app.main:app --reload` (serves at `http://localhost:8000`)
3. Flash the `.ino` file to the ESP32 and note which serial port it
   shows up as (Windows: `COMx` in the Arduino IDE's Tools > Port menu).
4. Close the Arduino Serial Monitor (rule 4 above).
5. From `drought-monitoring-system`:
   ```
   python scripts/serial_bridge.py --port COMx --backend-url http://127.0.0.1:8000
   ```
6. The bridge prints `Saved row ... | <type> | soil ...% | water ...%`
   for each forwarded reading.

## Trying the illustrative reference instead

`python-reference-example/reference_receiver_serial.py` is a minimal
stand-in (prints what it would do, doesn't call a real backend) --
useful only if the real backend isn't set up yet. See
[JSON-interface.md](JSON-interface.md).
