```mermaid
flowchart TD
    subgraph HW["Hardware Team (Sensors & Circuit)"]
        S1[Soil moisture sensor\nGPIO36]
        S2[Water level sensor\nGPIO34]
    end

    subgraph Edge["Edge Team (ESP32, esp32_water_soil_sensor.ino)"]
        MCU[Local threshold check\nevery 1s]
        LED[RGB status LED]
        JSON["Print JSON to USB Serial\ntype / water_level / soil_moisture"]
    end

    subgraph Bridge["Bridge (PC, scripts/serial_bridge.py)"]
        SB[Read Serial line\nforward on status change or every 30s]
    end

    subgraph Backend["Backend Team (FastAPI, drought-monitoring-system/backend)"]
        API_R["POST /api/readings/serial"]
        Cal[Calibrate raw -> %\ncalibration_service.py]
        Risk[Risk level from thresholds\nrisk_service.py]
        DB[(JSON Lines storage\nmonitoring_repository.py)]
        Sched[1-min scheduler\nmain.py]
        API_A["POST /api/drought/analyze"]
        Weather[Open-Meteo weather\nweather_service.py, cached]
        Gemini[Gemini: explain + recommend\ndoes not decide risk level]
    end

    subgraph UI["Dashboard (Streamlit)"]
        Dash[Live Monitoring / Historical Data /\nAlerts / LLM Reports]
    end

    S1 --> MCU
    S2 --> MCU
    MCU --> LED
    MCU --> JSON

    JSON -- USB Serial, 9600 baud --> SB
    SB -- HTTP POST --> API_R
    API_R --> Cal --> Risk --> DB

    DB --> Sched
    Sched -- routine reading: hourly --> API_A
    Sched -- alert_* reading: immediately --> API_A
    API_A --> Weather
    API_A --> Risk
    Weather --> Gemini
    Risk --> Gemini
    Gemini --> DB

    DB --> Dash

    %% Styling
    classDef anomaly fill:#fce4e4,stroke:#cc0000,stroke-width:1px;
    classDef normal fill:#e4fce4,stroke:#006600,stroke-width:1px;
    classDef mcu fill:#e4e4fc,stroke:#0000cc,stroke-width:1px;
    classDef api fill:#fcecd4,stroke:#cc6600,stroke-width:1px;

    class LED mcu;
    class MCU mcu;
    class Weather,Gemini api;
    class Risk normal;
```

## Notes

- The Edge device (ESP32) never calls any API directly -- it only prints
  JSON over USB Serial. `serial_bridge.py`, running on a PC, is the only
  thing that talks HTTP to the Backend. See
  [environment-setup.md](environment-setup.md) for why (Wi-Fi was tried
  and dropped -- see [implementation-rules-wifi.md](implementation-rules-wifi.md)).
- `POST /api/readings/serial` is cheap and runs on every reading (it only
  calibrates and stores); `POST /api/drought/analyze` is the expensive
  call (weather + Gemini) and is throttled by the Backend's scheduler,
  not the Edge device.
- Gemini only explains and recommends in plain English -- the
  deterministic risk score/level (`risk_service.py`, driven by the
  `SOIL_*_THRESHOLD` / `WATER_*_THRESHOLD` values in `.env`) is what
  actually decides anomaly vs. normal.
- There is no App/LINE/Discord notification yet -- the Streamlit
  dashboard is the current way to see alerts and reports.
