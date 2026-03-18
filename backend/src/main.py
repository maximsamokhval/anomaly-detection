"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response as StarletteResponse

from src.api.middleware import LoggingMiddleware
from src.api.routes import analysis, anomalies, heatmap, sources, timeseries
from src.infrastructure.logging import logger
from src.ui.templates import templates


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    db_path = Path(__file__).parent.parent / "data" / "anomaly_detection.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Starting Financial Anomaly Detection Service")
    logger.info(f"Database: {db_path}")
    logger.debug("Debug mode enabled – loguru logging active")
    yield
    logger.info("Shutting down Financial Anomaly Detection Service")


app = FastAPI(
    title="Financial Anomaly Detection Service",
    description=(
        "Detect and visualise anomalies in financial data fetched from 1C accumulation registers.\n\n"
        "## Features\n"
        "- Configure data sources (1C HTTP endpoints)\n"
        "- Trigger anomaly detection analysis over a date range\n"
        "- Browse detected anomalies with filtering\n"
        "- Heat-map and time-series drill-down visualisations\n\n"
        "## Anomaly types\n"
        "| Code | Description |\n"
        "|------|-------------|\n"
        "| `SPIKE` | Value deviates by more than spike_pct % or spike_zscore σ |\n"
        "| `TREND_BREAK` | Monotonic trend reversal detected |\n"
        "| `ZERO_NEG` | Value is zero or negative |\n"
        "| `MISSING` | Expected period is absent from the data |\n"
        "| `RATIO` | Sum/Qty ratio outside allowed bounds |\n"
        "| `MISSING_DATA` | Entire dimension group absent |\n"
    ),
    version="0.1.0",
    contact={"name": "Anomaly Detection Team"},
    license_info={"name": "Proprietary"},
    openapi_tags=[
        {
            "name": "Analysis",
            "description": "Trigger and inspect anomaly detection runs.",
        },
        {
            "name": "Anomalies",
            "description": "Browse detected anomalies with optional filters.",
        },
        {
            "name": "Data Sources",
            "description": "Manage 1C register data source configurations (CRUD).",
        },
        {
            "name": "Heat Map",
            "description": "Retrieve heat-map grid data for a completed analysis run.",
        },
        {
            "name": "Time Series",
            "description": "Drill-down time-series data for a specific dimension slice.",
        },
    ],
    lifespan=lifespan,
)

# CORS – allow all origins for internal network MVP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/response logging (outermost layer – runs first on request, last on response)
app.add_middleware(LoggingMiddleware)

# Static files
static_path = Path(__file__).parent.parent / "ui" / "static"
static_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# API routers
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(anomalies.router, prefix="/api/v1/anomalies", tags=["Anomalies"])
app.include_router(sources.router, prefix="/api/v1/sources", tags=["Data Sources"])
app.include_router(heatmap.router, prefix="/api/v1/heatmap", tags=["Heat Map"])
app.include_router(timeseries.router, prefix="/api/v1/timeseries", tags=["Time Series"])


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Return dict-based HTTPException details directly (no extra 'detail' wrapper)."""
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": f"http_{exc.status_code}", "message": str(exc.detail)},
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"error": "not_found", "message": "Resource not found"},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 500 errors."""
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "An unexpected error occurred"},
    )


# ---------------------------------------------------------------------------
# Server-rendered UI routes
# ---------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
async def dashboard(request: Request) -> StarletteResponse:
    """Dashboard – main landing page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/heatmap", include_in_schema=False)
async def heatmap_page(request: Request) -> StarletteResponse:
    """Heat Map visualisation page."""
    return templates.TemplateResponse("heatmap.html", {"request": request})


@app.get("/table", include_in_schema=False)
async def table_page(request: Request) -> StarletteResponse:
    """Anomaly Table page."""
    return templates.TemplateResponse("table.html", {"request": request})


@app.get("/drilldown", include_in_schema=False)
async def drilldown_page(request: Request) -> StarletteResponse:
    """Drill-down detail page."""
    return templates.TemplateResponse("drilldown.html", {"request": request})


@app.get("/sources", include_in_schema=False)
async def sources_page(request: Request) -> StarletteResponse:
    """Data Sources configuration page."""
    return templates.TemplateResponse("sources.html", {"request": request})


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health", tags=["Health"], summary="Health check")
async def health_check() -> dict:
    """Return service liveness status."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
