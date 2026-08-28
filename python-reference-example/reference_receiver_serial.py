"""
REFERENCE EXAMPLE ONLY -- not the Backend Team's actual implementation.

The Backend Team owns and maintains the real receiver in their own
repository/environment. This file only illustrates how the JSON payload
printed by the Edge Team's ESP32 (esp32_water_soil_sensor/esp32_water_soil_sensor.ino)
could be read, so both sides can agree on the interface ahead of time. See
docs/JSON-interface.md for the payload contract.

The sketch's primary transport is now Wi-Fi (see reference_receiver_wifi.py),
but it also prints the same JSON line to USB Serial for local debugging.
This script reads that serial output directly -- useful when you don't want
to stand up the Wi-Fi receiver, e.g. while bench-testing sensors.

Run:
    pip install -r python-reference-example/requirements.txt
    python python-reference-example/reference_receiver_serial.py <serial-port>

Example serial port names:
    Windows : COM3
    Mac     : /dev/tty.usbserial-XXXX or /dev/tty.SLAB_USBtoUART
    Linux   : /dev/ttyUSB0
"""
import json
import sys

import serial

BAUD_RATE = 9600  # must match Serial.begin(...) in the .ino file


def handle_alert(payload):
    # "alert_*" types bypass the weather/LLM check per the activity diagram.
    # TODO: notify the user immediately (App / LINE / Discord).
    print(f"ALERT: notify user immediately (bypass LLM) -- {payload}")


def handle_normal_reading(payload):
    # "data_*" / "warning_*" types run the full pipeline.
    # TODO: fetch weather API data, build the LLM prompt, run the
    # consistency check, and notify the user with the result.
    print(f"Reading -- weather/LLM pipeline not implemented yet -- {payload}")


def route(payload):
    reading_type = payload.get("type", "")
    if reading_type.startswith("alert"):
        handle_alert(payload)
    else:
        handle_normal_reading(payload)


def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <serial-port>")
        sys.exit(1)

    port = sys.argv[1]
    with serial.Serial(port, baudrate=BAUD_RATE, timeout=1) as ser:
        print(f"Listening on {port} at {BAUD_RATE} baud...")
        while True:
            line = ser.readline().decode("utf-8", errors="replace").strip()
            if not line.startswith("{"):
                continue  # skip the human-readable debug lines the sketch also prints

            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue

            route(payload)


if __name__ == "__main__":
    main()
