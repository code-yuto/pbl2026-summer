# Implementation Rules: Wi-Fi Transport (documented, not currently used)

The sketch currently uses USB Serial instead (see
[implementation-rules-serial.md](implementation-rules-serial.md)). We
tried this Wi-Fi approach and hit two real problems: the university
network was 5GHz-only (ESP32 only supports 2.4GHz), and even phone
tethering didn't connect reliably during testing. Serial avoids both
issues entirely. This file is kept in case the team revisits Wi-Fi later
(e.g. to remove the USB tether once deployed in the field) -- the code
below did work against the Backend Team's real FastAPI server
(`drought-monitoring-system/backend`, cloned locally for reference --
it's its own repo, not vendored into this one) when the network
cooperated.

Payload examples: [json-payload-wifi.json](json-payload-wifi.json)

## Network: use phone tethering, not campus Wi-Fi, for the prototype

Campus/university Wi-Fi commonly breaks this setup in two ways:

- **Client/AP isolation**: devices on the same Wi-Fi can't reach each
  other directly, even though they're on the same network. This blocks
  the ESP32 from reaching the Backend PC entirely.
- **Enterprise auth** (e.g. eduroam, WPA2-Enterprise/802.1x): the ESP32's
  standard `WiFi.begin(ssid, password)` can't authenticate against this
  without extra implementation.

A phone's personal hotspot avoids both: it uses a plain WPA2 password and
does not isolate connected clients by default. Test early (a ping or a
POST) before relying on any given network.

## Rules

1. **ESP32 only supports 2.4GHz Wi-Fi.** A 5GHz-only network will not
   work.
2. **The ESP32 and the machine running the Backend must be on the same
   Wi-Fi network.**
3. **Required libraries**: `WiFi.h` and `HTTPClient.h` (both ship with
   the ESP32 Arduino core, no extra install needed).
4. **Config the `.ino` file needs** (top of the file):
   - `WIFI_SSID` / `WIFI_PASSWORD` -- the shared network's credentials.
   - `SERVER_HOST` -- the Backend PC's local IPv4 address (`ipconfig` on
     Windows, `ifconfig` / `ip a` on Mac/Linux -- look for the Wi-Fi/
     hotspot adapter).
   - `SERVER_PORT` / `SERVER_PATH` -- `8000` / `/api/readings/serial` by
     default, matching `uvicorn app.main:app` in
     `drought-monitoring-system/backend`.
   - `DEVICE_ID` -- sent as a `?device_id=` query parameter (the endpoint
     falls back to a server-side default if omitted).
5. **HTTP request shape**:
   - Method: `POST`
   - Header: `Content-Type: application/json`
   - URL: `http://<SERVER_HOST>:8000/api/readings/serial?device_id=<DEVICE_ID>`
   - Body: see [json-payload-wifi.json](json-payload-wifi.json) for the
     full set of `type` values and fields.
6. **Reconnect handling**: `loop()` checks `WiFi.status() != WL_CONNECTED`
   before each reading and reconnects if needed, so a dropped Wi-Fi
   connection doesn't crash the sketch or silently stop sending readings.
7. **Serial output still exists for local debugging** -- `sendReading()`
   prints the same JSON line to Serial before POSTing it. This is not the
   authoritative transport (Wi-Fi is); see
   [implementation-rules-serial.md](implementation-rules-serial.md) if
   you want to also read from Serial.

## No send throttling on the Edge side

Every reading is sent, uncapped, once per second (`delay(1000)` in
`loop()`). This is intentional: `POST /api/readings/serial` on the
Backend only calibrates the values and writes a row to the database --
it does not call the weather API or Gemini (see
`drought-monitoring-system/backend/app/api/readings.py`). Sending
continuously costs bandwidth only, so the frontend/dashboard can always
show live data.

The expensive call is a separate endpoint,
`POST /api/drought/analyze` (`drought-monitoring-system/backend/app/api/analysis.py`),
which fetches weather data and calls Gemini. **That call should be
throttled by the Backend**, not the Edge device -- e.g. run it hourly on
routine (`data_*` / `warning_*`) readings, but immediately whenever an
`alert_*` reading comes in (`device_alert` in the `/readings/serial`
response is already `true` for these). How/where that scheduling lives
is a Backend Team decision; the Edge Team's job ends at sending every
reading.

## How to try it

1. In `drought-monitoring-system/backend`: follow that repo's own
   README (Supabase migrations, `.env`, `pip install -r requirements.txt`,
   `uvicorn app.main:app --reload`).
2. Connect both your PC and the ESP32 to the same phone hotspot.
3. Set `WIFI_SSID` / `WIFI_PASSWORD` / `SERVER_HOST` in the `.ino` file
   to match, and flash it to the ESP32.
4. Watch the ESP32's Serial Monitor for `WiFi connected` and
   `POST ... -> HTTP 201` for each reading (`/readings/serial` returns
   `201 Created` on success).
5. Alternatively, `python-reference-example/reference_receiver_wifi.py`
   is a minimal illustrative stand-in if the real backend isn't running
   yet -- see [JSON-interface.md](JSON-interface.md).
