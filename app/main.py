import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.db import init_db, engine, SessionLocal
from app.scraping.scheduler import ScrapeScheduler
from app.api.routes_index import router as index_router
from app.api.routes_audit import router as audit_router
from app.api.routes_export import router as export_router
from app.api.routes_validation import router as validation_router
from app.api.routes_harvest import router as harvest_router
from app.api.routes_auth import router as auth_router, seed_default_users

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("mospi-airfare-index")

scheduler_instance = ScrapeScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting MoSPI Airfare Index backend in [{settings.ENVIRONMENT}] mode...")
    try:
        init_db()
        logger.info("Database schema initialized successfully.")
        
        # Auto-seed default MoSPI official accounts
        with SessionLocal() as db_session:
            seed_default_users(db_session)
    except Exception as e:
        logger.error(f"Database initialization warning: {e}")
    
    # Start APScheduler background scraping job
    logger.info("Starting background APScheduler...")
    scheduler_instance.start_scheduler()
    logger.info("MoSPI Airfare Index backend initialized successfully.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down background scheduler and resources...")
    scheduler_instance.stop_scheduler()
    engine.dispose()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="MoSPI Domestic Airfare Index System",
    description=(
        "Automated high-frequency civil aviation airfare scraper, outlier filter, "
        "and Dutot/Jevons price index computation engine for MoSPI / NSO CPI aggregation (COICOP 07.3.3.1)."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip Compression (Reduces payload transfer sizes by ~80%)
app.add_middleware(GZipMiddleware, minimum_size=500)

# Custom Global Exception Handler (Prevents stack trace leaks in production)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=settings.DEBUG)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred processing your request. Details have been logged.",
            "path": request.url.path
        }
    )

# Include all API Routers
app.include_router(auth_router)
app.include_router(index_router)
app.include_router(harvest_router)
app.include_router(audit_router)
app.include_router(export_router)
app.include_router(validation_router)


@app.get("/", tags=["Health & Status"])
def root():
    return {
        "status": "online",
        "service": "MoSPI Airfare Index Engine",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "routes_monitored": settings.routes_list,
        "booking_horizons_days": settings.horizons_list,
        "endpoints": {
            "latest_index": "/index",
            "route_history": "/index/{route}",
            "audit_overview": "/audit",
            "sources_health": "/audit/sources/health",
            "scrape_runs": "/audit/runs",
            "backtest_validation": "/validation/backtest",
            "validation_metrics": "/validation/metrics",
            "validation_coverage": "/validation/coverage",
            "route_validation": "/validation/routes",
            "validation_runs": "/validation/runs",
            "export_table": "/export?format=csv|json",
            "health_liveness": "/health",
            "health_readiness": "/health/ready",
            "swagger_docs": "/docs"
        }
    }


@app.get("/health", tags=["Health & Status"])
def health_liveness():
    """Liveness check verifying the application process is running."""
    return {"status": "healthy", "timestamp": "ok"}


@app.get("/health/ready", tags=["Health & Status"])
def health_readiness():
    """Readiness check verifying database connectivity and connection pool status."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unready", "database": "disconnected"}
        )
