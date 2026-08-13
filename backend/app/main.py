from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.http import install_http_middleware


def create_application() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="3.0.1",
        description="Organization-scoped B2B customer relationship management API.",
    )
    install_http_middleware(application, settings)
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_application()
