"""
REFERENCE EXAMPLE ONLY -- not the Backend Team's actual implementation.

The Backend Team owns and maintains the real receiver in their own
repository/environment. This file only illustrates how the JSON payload
POSTed by the Edge Team's ESP32 (esp32_water_soil_sensor/esp32_water_soil_sensor.ino)
could be received, so both sides can agree on the interface ahead of time.
See docs/JSON-interface.md for the payload contract.

This is the sketch's primary transport: no dedicated server infrastructure
is required, just this plain Python script running locally on a PC. The
ESP32 and this PC must be on the same Wi-Fi network -- phone tethering is
recommended for the prototype (see docs/implementation-rules-wifi.md),
since campus Wi-Fi often blocks device-to-device traffic (client/AP
isolation) or requires enterprise auth the ESP32 can't do out of the box.

Run:
    pip install -r python-reference-example/requirements.txt
    python python-reference-example/reference_receiver_wifi.py
"""
import sys

from flask import Flask, jsonify, request

# Windows consoles default to a codepage (e.g. cp932) that can't encode
# every Unicode character; reconfigure stdout to UTF-8 so prints here
# never crash the request.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

app = Flask(__name__)


def handle_alert(payload):
    # "alert_*" types bypass the weather/LLM check per the activity diagram.
    # TODO: notify the user immediately (App / LINE / Discord).
    print(f"ALERT: notify user immediately (bypass LLM) -- {payload}")


def handle_normal_reading(payload):
    # "data_*" / "warning_*" types run the full pipeline.
    # TODO: fetch weather API data, build the LLM prompt, run the
    # consistency check, and notify the user with the result.
    print(f"Reading -- weather/LLM pipeline not implemented yet -- {payload}")


@app.route("/sensor-data", methods=["POST"])
def sensor_data():
    payload = request.get_json(force=True)
    reading_type = payload.get("type", "")

    if reading_type.startswith("alert"):
        handle_alert(payload)
    else:
        handle_normal_reading(payload)

    return jsonify({"status": "received"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
