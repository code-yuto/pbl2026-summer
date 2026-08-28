"""
LOCAL MODIFICATION -- not part of the upstream drought-monitoring-system
repo, not pushed there. Swaps Supabase for plain local files (JSON Lines
under `data/`) since this project's data volume doesn't need a hosted
database. Every method keeps the exact same name/signature/return shape
the rest of the app (readings.py, dashboard.py, monitoring_service.py)
already expects, so no other file needs to change.
"""
import json
import threading
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import PROJECT_ROOT


DATA_DIR = PROJECT_ROOT / "data"

_write_lock = threading.Lock()


class MonitoringRepository:
    """Each 'table' is one append-only JSON Lines file under `data/`."""

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _table_file(self, table: str) -> Path:
        return self.data_dir / f"{table}.jsonl"

    def _read_all(self, table: str) -> list[dict[str, Any]]:
        path = self._table_file(table)
        if not path.exists():
            return []
        records = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def _insert(self, table: str, record: dict[str, Any]) -> dict[str, Any]:
        with _write_lock:
            existing = self._read_all(table)
            next_id = max((row.get("id", 0) for row in existing), default=0) + 1

            saved = dict(record)
            saved.setdefault("id", next_id)
            saved.setdefault("created_at", datetime.now(timezone.utc).isoformat())

            with self._table_file(table).open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(saved, default=str) + "\n")

            return saved

    def _update(
        self,
        table: str,
        record_id: int,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        with _write_lock:
            records = self._read_all(table)
            updated_record = None
            for record in records:
                if record.get("id") == record_id:
                    record.update(updates)
                    updated_record = record
                    break

            if updated_record is None:
                raise ValueError(
                    f"No record with id {record_id} in table {table!r}"
                )

            with self._table_file(table).open("w", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record, default=str) + "\n")

            return updated_record

    def _history(
        self,
        table: str,
        limit: int,
        order_by: str = "created_at",
    ) -> list[dict[str, Any]]:
        records = self._read_all(table)
        records.sort(key=lambda row: row.get(order_by, ""), reverse=True)
        return records[:limit]

    # -- Sensor readings ----------------------------------------------

    def save_reading(self, reading: dict[str, Any]) -> dict[str, Any]:
        return self._insert("monitoring_data", reading)

    def get_latest_reading(self) -> dict[str, Any] | None:
        history = self._history("monitoring_data", limit=1)
        return history[0] if history else None

    def update_reading_analysis(
        self,
        reading_id: int,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        return self._update("monitoring_data", reading_id, updates)

    def get_reading_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._history("monitoring_data", limit)

    # -- Weather --------------------------------------------------------

    def save_weather_data(self, weather: dict[str, Any]) -> dict[str, Any]:
        return self._insert("weather_data", weather)

    def get_weather_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._history("weather_data", limit, order_by="observed_at")

    # -- Drought assessments ---------------------------------------------

    def save_drought_assessment(self, assessment: dict[str, Any]) -> dict[str, Any]:
        return self._insert("drought_assessments", assessment)

    def get_drought_assessment_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._history("drought_assessments", limit)

    def get_latest_drought_assessment(self) -> dict[str, Any] | None:
        history = self._history("drought_assessments", limit=1)
        return history[0] if history else None

    def get_drought_chat_context(
        self,
        assessment_id: int | None = None,
    ) -> dict[str, Any] | None:
        assessments = self._read_all("drought_assessments")
        if not assessments:
            return None

        if assessment_id is None:
            assessment = max(assessments, key=lambda row: row.get("id", 0))
        else:
            assessment = next(
                (row for row in assessments if row.get("id") == assessment_id),
                None,
            )
        if assessment is None:
            return None

        readings = self._read_all("monitoring_data")
        sensor = next(
            (
                row
                for row in readings
                if row.get("id") == assessment.get("monitoring_id")
            ),
            None,
        )
        weather_records = self._read_all("weather_data")
        weather = next(
            (
                row
                for row in weather_records
                if row.get("id") == assessment.get("weather_id")
            ),
            None,
        )
        if sensor is None or weather is None:
            return None

        return {"sensor": sensor, "weather": weather, "assessment": assessment}


@lru_cache
def get_monitoring_repository() -> MonitoringRepository:
    return MonitoringRepository()
