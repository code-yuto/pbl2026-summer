from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    settings = get_settings()
    service_key = settings.supabase_service_key.get_secret_value()

    if not settings.supabase_url or not service_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be configured"
        )

    return create_client(settings.supabase_url, service_key)
