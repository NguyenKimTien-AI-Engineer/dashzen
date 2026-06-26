from core.config import get_settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.errors import register_exception_handlers
from api.rate_limit import limiter
from api.routes.artifacts import router as artifacts_router
from api.routes.auth import router as auth_router
from api.routes.compact import router as compact_router
from api.routes.export import router as export_router
from api.routes.gates import router as gates_router
from api.routes.llm import router as llm_router
from api.routes.projects import router as projects_router
from api.routes.stream import router as stream_router
from api.routes.tasks import router as tasks_router
from api.routes.upload import router as upload_router
from api.routes.users import router as users_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="DashZen API", version="0.1.0")

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    cors_kwargs: dict[str, object] = {
        "allow_origins": settings.cors_origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Cookie"],
    }
    if settings.cors_origin_regex:
        cors_kwargs["allow_origin_regex"] = settings.cors_origin_regex
    app.add_middleware(CORSMiddleware, **cors_kwargs)

    register_exception_handlers(app)
    app.include_router(auth_router)
    app.include_router(tasks_router)
    app.include_router(projects_router)
    app.include_router(artifacts_router)
    app.include_router(stream_router)
    app.include_router(llm_router)
    app.include_router(gates_router)
    app.include_router(upload_router)
    app.include_router(compact_router)
    app.include_router(export_router)
    app.include_router(users_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
