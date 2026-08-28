from copy import deepcopy
from datetime import UTC, datetime
from functools import lru_cache
from threading import Lock
from typing import TYPE_CHECKING, Any, Protocol

from app.core.config import get_settings


if TYPE_CHECKING:
    from supabase import Client


class MonitoringRepository(Protocol):
    def save_reading(self, reading: dict[str, Any]) -> dict[str, Any]: ...

    def get_latest_reading(self) -> dict[str, Any] | None: ...

    def update_reading_analysis(
        self,
        reading_id: int,
        updates: dict[str, Any],
    ) -> dict[str, Any]: ...

    def get_reading_history(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...

    def save_weather_data(self, weather: dict[str, Any]) -> dict[str, Any]: ...

    def save_drought_assessment(
        self,
        assessment: dict[str, Any],
    ) -> dict[str, Any]: ...

    def get_weather_history(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...

    def get_drought_assessment_history(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...

    def get_drought_chat_context(
        self,
        assessment_id: int | None = None,
    ) -> dict[str, Any] | None: ...


class InMemoryMonitoringRepository:
    """Keep live sensor and forecast data for the current FastAPI session."""

    def __init__(self, max_records: int = 10000) -> None:
        self.max_records = max_records
        self._readings: list[dict[str, Any]] = []
        self._weather: list[dict[str, Any]] = []
        self._assessments: list[dict[str, Any]] = []
        self._next_ids = {
            "readings": 1,
            "weather": 1,
            "assessments": 1,
        }
        self._lock = Lock()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def _new_id(self, collection: str) -> int:
        record_id = self._next_ids[collection]
        self._next_ids[collection] += 1
        return record_id

    def _append(
        self,
        collection: list[dict[str, Any]],
        record: dict[str, Any],
    ) -> None:
        collection.append(record)
        if len(collection) > self.max_records:
            del collection[: len(collection) - self.max_records]

    def save_reading(self, reading: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            record = {
                "id": self._new_id("readings"),
                **deepcopy(reading),
                "created_at": self._now(),
            }
            self._append(self._readings, record)
            return deepcopy(record)

    def get_latest_reading(self) -> dict[str, Any] | None:
        with self._lock:
            return deepcopy(self._readings[-1]) if self._readings else None

    def update_reading_analysis(
        self,
        reading_id: int,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        with self._lock:
            for record in self._readings:
                if record["id"] == reading_id:
                    record.update(deepcopy(updates))
                    return deepcopy(record)
        raise RuntimeError("The in-memory sensor reading was not found")

    def get_reading_history(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            return deepcopy(list(reversed(self._readings[-limit:])))

    def save_weather_data(self, weather: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            record = {
                "id": self._new_id("weather"),
                **deepcopy(weather),
                "fetched_at": self._now(),
            }
            self._append(self._weather, record)
            return deepcopy(record)

    def save_drought_assessment(
        self,
        assessment: dict[str, Any],
    ) -> dict[str, Any]:
        with self._lock:
            record = {
                "id": self._new_id("assessments"),
                **deepcopy(assessment),
                "created_at": self._now(),
            }
            self._append(self._assessments, record)
            return deepcopy(record)

    def get_weather_history(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            return deepcopy(list(reversed(self._weather[-limit:])))

    def get_drought_assessment_history(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        with self._lock:
            return deepcopy(list(reversed(self._assessments[-limit:])))

    def get_drought_chat_context(
        self,
        assessment_id: int | None = None,
    ) -> dict[str, Any] | None:
        with self._lock:
            if assessment_id is None:
                assessment = (
                    self._assessments[-1] if self._assessments else None
                )
            else:
                assessment = next(
                    (
                        item
                        for item in self._assessments
                        if item["id"] == assessment_id
                    ),
                    None,
                )

            if assessment is None:
                return None

            sensor = next(
                (
                    item
                    for item in self._readings
                    if item["id"] == assessment["monitoring_id"]
                ),
                None,
            )
            weather = next(
                (
                    item
                    for item in self._weather
                    if item["id"] == assessment["weather_id"]
                ),
                None,
            )
            if sensor is None or weather is None:
                return None

            return deepcopy(
                {
                    "sensor": sensor,
                    "weather": weather,
                    "assessment": assessment,
                }
            )


class SupabaseMonitoringRepository:
    """Optional persistent repository retained for future deployment."""

    def __init__(self, client: "Client") -> None:
        self.client = client

    def save_reading(self, reading: dict[str, Any]) -> dict[str, Any]:
        response = self.client.table("monitoring_data").insert(reading).execute()
        if not response.data:
            raise RuntimeError("Supabase did not return the inserted reading")
        return response.data[0]

    def get_latest_reading(self) -> dict[str, Any] | None:
        response = (
            self.client.table("monitoring_data")
            .select("*")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def update_reading_analysis(
        self,
        reading_id: int,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        response = (
            self.client.table("monitoring_data")
            .update(updates)
            .eq("id", reading_id)
            .execute()
        )
        if not response.data:
            raise RuntimeError("Supabase did not return the updated reading")
        return response.data[0]

    def get_reading_history(self, limit: int = 100) -> list[dict[str, Any]]:
        response = (
            self.client.table("monitoring_data")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def save_weather_data(self, weather: dict[str, Any]) -> dict[str, Any]:
        response = self.client.table("weather_data").insert(weather).execute()
        if not response.data:
            raise RuntimeError("Supabase did not return the weather record")
        return response.data[0]

    def save_drought_assessment(
        self,
        assessment: dict[str, Any],
    ) -> dict[str, Any]:
        response = (
            self.client.table("drought_assessments")
            .insert(assessment)
            .execute()
        )
        if not response.data:
            raise RuntimeError("Supabase did not return the assessment")
        return response.data[0]

    def get_weather_history(self, limit: int = 100) -> list[dict[str, Any]]:
        response = (
            self.client.table("weather_data")
            .select("*")
            .order("observed_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def get_drought_assessment_history(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        response = (
            self.client.table("drought_assessments")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def get_drought_chat_context(
        self,
        assessment_id: int | None = None,
    ) -> dict[str, Any] | None:
        query = self.client.table("drought_assessments").select("*")
        if assessment_id is not None:
            assessment_response = query.eq("id", assessment_id).limit(1).execute()
        else:
            assessment_response = (
                query.order("created_at", desc=True).limit(1).execute()
            )
        if not assessment_response.data:
            return None

        assessment = assessment_response.data[0]
        reading_response = (
            self.client.table("monitoring_data")
            .select("*")
            .eq("id", assessment["monitoring_id"])
            .limit(1)
            .execute()
        )
        weather_response = (
            self.client.table("weather_data")
            .select("*")
            .eq("id", assessment["weather_id"])
            .limit(1)
            .execute()
        )
        if not reading_response.data or not weather_response.data:
            return None
        return {
            "sensor": reading_response.data[0],
            "weather": weather_response.data[0],
            "assessment": assessment,
        }


@lru_cache
def get_monitoring_repository() -> MonitoringRepository:
    settings = get_settings()
    if settings.storage_backend == "supabase":
        from app.database.supabase_client import get_supabase_client

        return SupabaseMonitoringRepository(get_supabase_client())
    return InMemoryMonitoringRepository(
        max_records=settings.memory_history_limit
    )
