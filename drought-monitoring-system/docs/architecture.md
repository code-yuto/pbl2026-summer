# Database-free live architecture

The application uses FastAPI process memory instead of a database.

```text
ESP32 -> USB Serial -> serial_bridge.py -> FastAPI memory -> Streamlit
                                             |     |
                                      Open-Meteo  Gemini
```

## Responsibilities

- The ESP32 reads raw soil-moisture and water-level sensor values.
- The Python bridge forwards newline-delimited serial JSON to FastAPI.
- FastAPI calibrates values, assigns rule-based risk and keeps recent rows in
  an in-memory repository.
- Open-Meteo provides current weather, recent rainfall, forecast rainfall,
  temperature, humidity and evapotranspiration.
- The deterministic backend calculates the 0-100 drought score.
- Gemini explains the fixed score and answers questions using the linked live
  context.
- Streamlit requests all values through FastAPI. It does not generate dummy
  records when a source is missing.

## Data lifetime

The default `STORAGE_BACKEND=memory` stores up to `MEMORY_HISTORY_LIMIT` records
inside the running FastAPI process. Restarting FastAPI clears sensor history,
weather snapshots, assessments and chat context. Run Uvicorn with one worker so
all requests share the same in-memory repository.

When FastAPI and Streamlit run on different machines, expose FastAPI with ngrok
and paste its HTTPS URL into the dashboard sidebar.
