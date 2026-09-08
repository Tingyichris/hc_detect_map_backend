from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import (
    anomalies,
    cameras,
    classes,
    corrections,
    health,
    ingest,
    maps,
    pickups,
    review,
    sessions,
)
from .settings import settings

ROUTERS = (
    ingest.router,
    maps.router,
    sessions.router,
    pickups.router,
    cameras.router,
    classes.router,
    anomalies.router,
    review.router,
    corrections.router,
    health.router,
)


def create_app() -> FastAPI:
    app = FastAPI(title="hcdmap-backend", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in ROUTERS:
        app.include_router(router)
    return app


app = create_app()
