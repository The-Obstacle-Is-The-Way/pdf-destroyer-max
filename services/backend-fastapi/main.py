# services/backend-fastapi/main.py

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from api.routes import (
    summarization_routes, 
    pdf_routes, 
    health, 
    ocr_routes,
    pipeline_routes
)
import uvicorn
from config.settings import Settings
from utils.logging import logger, setup_logging
from api.middleware import (
    RequestLoggingMiddleware,
    ResponseTimeMiddleware,
    ErrorHandlingMiddleware
)
from api.dependencies import (
    get_pipeline_client,
    get_ocr_client,
    get_storage_client
)

# Setup logging first
setup_logging()

# Load settings
settings = Settings()

def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="PDF Destroyer Max API",
        description="Backend service for PDF processing and analysis",
        version="1.0.0",
        docs_url="/api/docs" if settings.debug_mode else None,
        redoc_url="/api/redoc" if settings.debug_mode else None,
        openapi_url="/api/openapi.json" if settings.debug_mode else None
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middleware
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(ResponseTimeMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # Include routers with proper prefixes
    app.include_router(
        health.router,
        prefix="/api/v1",
        tags=["health"]
    )
    app.include_router(
        pdf_routes.router,
        prefix="/api/v1/pdf",
        tags=["pdf"]
    )
    app.include_router(
        summarization_routes.router,
        prefix="/api/v1/summarize",
        tags=["summarization"]
    )
    app.include_router(
        ocr_routes.router,
        prefix="/api/v1/ocr",
        tags=["ocr"]
    )
    app.include_router(
        pipeline_routes.router,
        prefix="/api/v1/pipeline",
        tags=["pipeline"]
    )

    return app

app = create_application()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting PDF Destroyer Max API")
    # Initialize clients
    await get_pipeline_client()
    await get_ocr_client()
    await get_storage_client()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down PDF Destroyer Max API")
    # Close client connections
    pipeline_client = await get_pipeline_client()
    await pipeline_client.close()

@app.get("/", tags=["root"])
async def root():
    """Root endpoint for basic service information"""
    return {
        "service": "PDF Destroyer Max API",
        "version": "1.0.0",
        "status": "operational",
        "api_docs": "/api/docs" if settings.debug_mode else "disabled"
    }

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(
        f"Validation error on {request.url.path}: {str(exc)}",
        extra={"validation_errors": exc.errors()}
    )
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.exception(
        f"Unhandled exception on {request.url.path}: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else None
        }
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_id": request.state.request_id if hasattr(request.state, 'request_id') else None
        }
    )

if __name__ == "__main__":
    try:
        logger.info(f"Starting server on {settings.host}:{settings.port}")
        uvicorn.run(
            "main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug_mode,
            workers=settings.worker_count,
            log_level=settings.log_level.lower(),
            proxy_headers=True,
            forwarded_allow_ips="*"
        )
    except Exception as e:
        logger.exception(f"Failed to start server: {str(e)}")
        raise