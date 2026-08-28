"""Forward newline-delimited ESP32 Serial JSON to the FastAPI backend."""

import argparse
import json
import time
from typing import Any

import httpx
import serial


REQUIRED_FIELDS = {
    "type",
    "water_level",
    "soil_moisture",
    "timestamp_ms",
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read ESP32 JSON from USB Serial and forward it to FastAPI."
    )
    parser.add_argument(
        "--port",
        required=True,
        help="Serial port, for example COM3 or /dev/ttyUSB0.",
    )
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument(
        "--backend-url",
        default="http://127.0.0.1:8000",
        help="FastAPI base URL without a trailing slash.",
    )
    parser.add_argument("--device-id", default="ESP32_SERIAL_01")
    parser.add_argument(
        "--send-interval",
        type=float,
        default=30,
        help="Seconds between unchanged readings. Status changes send immediately.",
    )
    return parser.parse_args()


def parse_json_line(line: str) -> dict[str, Any] | None:
    stripped = line.strip()
    if not stripped.startswith("{"):
        return None

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        print(f"Ignored invalid JSON: {stripped}")
        return None

    missing = REQUIRED_FIELDS.difference(payload)
    if missing:
        print(f"Ignored JSON missing fields: {sorted(missing)}")
        return None
    return payload


def run_bridge(args: argparse.Namespace) -> None:
    endpoint = f"{args.backend_url.rstrip('/')}/api/readings/serial"
    headers = {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true",
    }
    last_attempted_type: str | None = None
    last_attempt_time = 0.0

    print(f"Opening {args.port} at {args.baud} baud...")
    print(f"Forwarding readings to {endpoint}")
    print("Press Ctrl+C to stop.")

    with serial.Serial(args.port, args.baud, timeout=1) as device:
        # Most ESP32 boards restart when the serial port is opened.
        time.sleep(2)
        device.reset_input_buffer()

        with httpx.Client(timeout=10, trust_env=False) as client:
            while True:
                line = device.readline().decode("utf-8", errors="replace")
                if not line:
                    continue

                payload = parse_json_line(line)
                if payload is None:
                    continue

                message_type = str(payload["type"])
                now = time.monotonic()
                status_changed = message_type != last_attempted_type
                interval_elapsed = now - last_attempt_time >= args.send_interval
                if not status_changed and not interval_elapsed:
                    continue

                last_attempted_type = message_type
                last_attempt_time = now

                try:
                    response = client.post(
                        endpoint,
                        params={"device_id": args.device_id},
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    saved = response.json()
                    print(
                        f"Saved row {saved['id']} | {message_type} | "
                        f"soil {saved['soil_moisture']:.1f}% | "
                        f"water {saved['water_level']:.1f}%"
                    )
                except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
                    print(f"Upload failed: {error}")


def main() -> None:
    try:
        run_bridge(parse_arguments())
    except serial.SerialException as error:
        raise SystemExit(f"Serial port error: {error}") from error
    except KeyboardInterrupt:
        print("\nSerial bridge stopped.")


if __name__ == "__main__":
    main()
