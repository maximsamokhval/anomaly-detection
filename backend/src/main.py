"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response as StarletteResponse

from src.api.routes import analysis, anomalies, heatmap, sources, timeseries
from src.infrastructure.logging import logger
from src.ui.templates import templates


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup: initialize database if needed
    db_path = Path(__file__).parent.parent / "data" / "anomaly_detection.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("🚀 Starting Financial Anomaly Detection Service")
    logger.info(f"📊 Database: {db_path}")
    logger.debug("Debug mode enabled - loguru logging active")
    yield
    # Shutdown: cleanup if needed
    logger.info("👋 Shutting down Financial Anomaly Detection Service")


app = FastAPI(
    title="Financial Anomaly Detection Service",
    description="Detect and visualize anomalies in financial data from 1C registers",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware (for internal network, allow all origins in MVP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent.parent / "ui" / "static"
static_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include API routers
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(anomalies.router, prefix="/api/v1/anomalies", tags=["Anomalies"])
app.include_router(sources.router, prefix="/api/v1/sources", tags=["Data Sources"])
app.include_router(heatmap.router, prefix="/api/v1/heatmap", tags=["Heat Map"])
app.include_router(timeseries.router, prefix="/api/v1/timeseries", tags=["Time Series"])


# Exception handlers
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


# UI Routes (Server-Rendered)
@app.get("/")
async def dashboard(request: Request) -> StarletteResponse:
    """Dashboard - main landing page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/heatmap")
async def heatmap_page(request: Request) -> StarletteResponse:
    """Heat Map visualization page."""
    return templates.TemplateResponse("heatmap.html", {"request": request})


@app.get("/table")
async def table_page(request: Request) -> StarletteResponse:
    """Anomaly Table page."""
    return templates.TemplateResponse("table.html", {"request": request})


@app.get("/drilldown")
async def drilldown_page(request: Request) -> StarletteResponse:
    """Drill-down detail page."""
    return templates.TemplateResponse("drilldown.html", {"request": request})


@app.get("/sources")
async def sources_page(request: Request) -> StarletteResponse:
    """Data Sources configuration page."""
    return templates.TemplateResponse("sources.html", {"request": request})


# Health check
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
