from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_v1_router
from app.api.ws.task_monitor import ws_router
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize resources on startup, release on shutdown."""
    setup_logging()

    # Initialize Redis
    from app.db.redis import redis_client
    await redis_client.initialize()

    # Initialize Playwright browser pool
    from crawler.action_executor import BrowserPool
    await BrowserPool.initialize(pool_size=settings.BROWSER_POOL_SIZE)

    yield

    # Cleanup
    await BrowserPool.shutdown()
    await redis_client.close()

    from app.db.session import engine
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="W4Agent - Web Accessibility Detection System",
        description="基于智能体技术的Web无障碍检测系统",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(api_v1_router, prefix="/api/v1")
    app.include_router(ws_router, prefix="/ws")

    return app


app = create_app()
