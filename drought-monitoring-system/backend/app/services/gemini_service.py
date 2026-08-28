import json
from functools import lru_cache

import httpx

from app.core.config import get_settings
from app.models.report_models import GeminiDroughtAnalysis
from app.models.sensor_models import SensorReadingCreate
from app.models.weather_models import WeatherSnapshot
from app.services.risk_service import DroughtRiskAssessment


class GeminiServiceError(RuntimeError):
    pass


class GeminiConfigurationError(GeminiServiceError):
    pass


class GeminiService:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float = 20,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.client = client

    async def analyze(
        self,
        sensor: SensorReadingCreate,
        weather: WeatherSnapshot,
        risk: DroughtRiskAssessment,
    ) -> GeminiDroughtAnalysis:
        if not self.api_key:
            raise GeminiConfigurationError(
                "GEMINI_API_KEY is not configured"
            )

        prompt_data = {
            "sensor_data": sensor.model_dump(),
            "weather_data": weather.model_dump(mode="json"),
            "calculated_risk": {
                "score": risk.score,
                "level": risk.level,
                "factors": risk.factors,
            },
        }
        prompt = (
            "You are an agricultural drought advisory assistant. "
            "Explain the supplied deterministic drought assessment in clear "
            "B2-level English. Do not change or downgrade the supplied risk "
            "level. Use only the supplied measurements. Give practical, safe "
            "recommendations and do not claim certainty. Return JSON only.\n\n"
            + json.dumps(prompt_data)
        )
        response_schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "drivers": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "confidence": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
                "requires_immediate_action": {"type": "boolean"},
            },
            "required": [
                "summary",
                "drivers",
                "recommendations",
                "confidence",
                "requires_immediate_action",
            ],
        }
        request_body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
                "responseJsonSchema": response_schema,
            },
        }
        url = f"{self.base_url}/models/{self.model}:generateContent"

        try:
            if self.client is not None:
                response = await self.client.post(
                    url,
                    headers={"x-goog-api-key": self.api_key},
                    json=request_body,
                )
            else:
                async with httpx.AsyncClient(
                    timeout=self.timeout_seconds,
                    trust_env=False,
                ) as client:
                    response = await client.post(
                        url,
                        headers={"x-goog-api-key": self.api_key},
                        json=request_body,
                    )
            response.raise_for_status()
            text = response.json()["candidates"][0]["content"]["parts"][0][
                "text"
            ]
            return GeminiDroughtAnalysis.model_validate_json(text)
        except (
            httpx.HTTPError,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
        ) as error:
            raise GeminiServiceError(
                "Gemini did not return a valid drought analysis"
            ) from error


@lru_cache
def get_gemini_service() -> GeminiService:
    settings = get_settings()
    return GeminiService(
        api_key=settings.gemini_api_key.get_secret_value(),
        model=settings.gemini_model,
        base_url=settings.gemini_base_url,
        timeout_seconds=settings.external_api_timeout_seconds,
    )
