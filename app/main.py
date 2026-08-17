import time
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db
from app.services.scheduler_service import get_scheduler_service
from app.providers.registry import get_provider_registry
from app.utils.logging import logger
from app.utils.time import utc_now, format_iso_datetime

# Routers
from app.api.sports import router as sports_router
from app.api.events import router as events_router
from app.api.home import router as home_router
from app.api.providers import router as providers_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    await init_db()
    logger.info("Database initialized.")

    scheduler = get_scheduler_service()
    scheduler.start()

    yield

    # Shutdown
    logger.info("Shutting down services...")
    scheduler.stop()
    registry = get_provider_registry()
    await registry.close_all()
    logger.info("Shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sports schedule and official broadcast metadata API for personal Apple TV IPTV application.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)"
    )
    return response


# Include Routers under API_V1_STR (/api/v1)
api_prefix = settings.API_V1_STR
app.include_router(sports_router, prefix=api_prefix)
app.include_router(events_router, prefix=api_prefix)
app.include_router(home_router, prefix=api_prefix)
app.include_router(providers_router, prefix=api_prefix)


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint verifying system, database, and provider availability.
    """
    registry = get_provider_registry()
    statuses = registry.get_all_statuses()
    all_healthy = any(s.status == "healthy" for s in statuses)

    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": format_iso_datetime(utc_now()),
        "version": settings.VERSION,
        "database": "connected",
        "activeProviders": [s.name for s in statuses if s.enabled],
    }


@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "api": {
            "sports": f"{api_prefix}/sports",
            "live": f"{api_prefix}/events/live",
            "today": f"{api_prefix}/events/today",
            "upcoming": f"{api_prefix}/events/upcoming",
            "home": f"{api_prefix}/home",
            "providers": f"{api_prefix}/providers/status",
        },
    }
