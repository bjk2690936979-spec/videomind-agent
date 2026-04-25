from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes_digest import router as digest_router
from backend.api.routes_health import router as health_router
from backend.api.routes_trace import router as trace_router


def create_app() -> FastAPI:
    app = FastAPI(title="VideoMind Agent", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(digest_router)
    app.include_router(trace_router)

    return app


app = create_app()
