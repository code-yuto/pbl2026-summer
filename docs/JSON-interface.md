# Edge -> Backend JSON Interface

Overview of how the Edge Team's ESP32
(`esp32_water_soil_sensor/esp32_water_soil_sensor.ino`) hands sensor
readings off to the Backend Team. The Backend Team owns and runs their
receiver in their own repository/environment.
`python-reference-example/` in this repo is **not** that implementation --
it is only a reference so both teams can agree on the JSON contract ahead
of time.

This mirrors the Activity Diagram in [README.md](../README.md).

## Transport: USB Serial (current)

The ESP32 stays connected to a PC by USB cable and prints one JSON object
per reading over Serial -- no Wi-Fi, no network troubleshooting. This
matches how the real Backend (`drought-monitoring-system`) expects to
receive data: its own `scripts/serial_bridge.py` reads the serial port
and forwards each reading to `POST /api/readings/serial` on the FastAPI
backend.

- Rules & setup: [implementation-rules-serial.md](implementation-rules-serial.md)
- Payload examples: [json-payload-serial.json](json-payload-serial.json)

We tried switching to Wi-Fi (phone tethering / campus Wi-Fi) and hit real
issues -- ESP32 can't join 5GHz-only networks, and campus Wi-Fi often
blocks device-to-device traffic. Serial avoids all of that, at the cost
of keeping the ESP32 tethered by USB cable.

## Transport: Wi-Fi (documented, not currently used)

The Wi-Fi + HTTP POST approach is still documented in case the team
revisits it later (e.g. to remove the USB tether once deployed in the
field).

- Rules & setup: [implementation-rules-wifi.md](implementation-rules-wifi.md)
- Payload examples: [json-payload-wifi.json](json-payload-wifi.json)

## Payload fields (same for both transports)

| Field           | Type   | Description                                                              |
| --------------- | ------ | ---------------------------------------------------------------------------- |
| `type`          | string | Reading classification, `alert_*` / `warning_*` / `data_*` (see below)   |
| `water_level`   | int    | Raw ADC reading from the water sensor (0-4095, ESP32 12-bit ADC)         |
| `soil_moisture` | int    | Raw ADC reading from the soil moisture sensor (0-4095, LOWER = wetter)   |
| `led_color`     | string | Name of the RGB status LED color shown for this reading                 |
| `timestamp_ms`  | int    | Milliseconds since the ESP32 booted (`millis()`), not wall-clock time    |

## `type` values and routing on the Backend side

`type` follows an `alert_*` / `warning_*` / `data_*` naming convention:

| `type`                          | `led_color`  | Meaning                                    |
| -------------------------------- | ------------ | -------------------------------------------- |
| `alert_hardware_or_flood`        | RED          | Sensor fault or flooding                     |
| `alert_critical_dry_no_water`    | PURPLE       | Reservoir empty AND soil dry (critical)      |
| `warning_dry`                    | YELLOW       | Reservoir full, soil dry (needs watering)    |
| `warning_dry_medium_water`       | ORANGE       | Reservoir medium, soil dry                   |
| `warning_low_water_wet_soil`     | PINK         | Reservoir low, soil wet                      |
| `warning_low_water`              | BLUE         | Reservoir low, soil moderate                 |
| `data_wet`                       | WHITE        | Reservoir full, soil very wet                |
| `data_ideal`                     | GREEN        | Reservoir full, soil moisture ideal          |
| `data_wet_medium_water`          | LIGHT_BLUE   | Reservoir medium, soil wet                   |
| `data_medium`                    | CYAN         | Reservoir medium, soil moderate               |

- `type` starting with `alert` -> bypass the weather fetch / LLM
  consistency check, notify the user immediately.
- Anything else (`warning_*` / `data_*`) -> run the full pipeline: fetch
  weather API data, build the LLM prompt, check consistency, generate the
  report, notify the user.

`POST /api/readings/serial` on the real Backend just calibrates and
stores the reading (no weather/Gemini call), so sending continuously is
cheap. The expensive call, `POST /api/drought/analyze`, is separate and
should be throttled by the Backend on its own (e.g. hourly, or
immediately for `alert_*` readings).

## Threshold constants (Edge side, in the `.ino` file)

| Constant             | Value | Meaning                                  |
| --------------------- | ----- | ------------------------------------------- |
| `WATER_MAX_ANOMALY`   | 3500  | Water too high -> flooding                  |
| `WATER_HIGH_THRESH`   | 1500  | Reservoir full                              |
| `WATER_LOW_THRESH`    | 300   | Reservoir low / near empty                  |
| `MOISTURE_DISCONNECT` | 50    | Anomaly: sensor wire disconnected           |
| `MOISTURE_WET_THRESH` | 1500  | Below this = wet soil                       |
| `MOISTURE_DRY_THRESH` | 2800  | Above this = dry soil                       |
| `MOISTURE_SHORT_CIR`  | 4000  | Anomaly: short circuit                      |

Note the soil moisture sensor is capacitive: a **lower** reading means
**wetter** soil (opposite of the water level sensor).
