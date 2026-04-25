from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes_digest import router as digest_router
from backend.api.routes_health import router as health_router
from backend.api.routes_trace import router as trace_router


def create_app() -> FastAPI:
    app = FastAPI(title="VideoMind Agent", version="0.1.0")

    # Streamlit 前端和本地调试会跨端口访问 API，先开放 CORS。
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 路由注册集中在 app factory，测试和生产入口复用同一套应用。
    app.include_router(health_router)
    app.include_router(digest_router)
    app.include_router(trace_router)

    return app


app = create_app()
