from app.core.config import settings
from app.schemas.health import HealthResponse


def build_health_response() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
    )
