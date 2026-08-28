from fastapi import APIRouter

from app.core.config import get_settings


router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "storage": settings.storage_backend,
    }
