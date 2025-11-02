"""
FastAPI Resume Parser - Main Application Entry Point
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from contextlib import asynccontextmanager

from app.config import settings
from app.api import routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown events
    """
    # Startup: Create uploads directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    print(f"✓ Upload directory created/verified at: {settings.UPLOAD_DIR}")
    
    # Verify Ollama connection
    try:
        import requests
        response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            print(f"✓ Connected to Ollama at: {settings.OLLAMA_BASE_URL}")
            print(f"✓ Using model: {settings.OLLAMA_MODEL}")
        else:
            print(f"⚠ Warning: Could not verify Ollama connection")
    except Exception as e:
        print(f"⚠ Warning: Ollama might not be running - {str(e)}")
        print(f"  Please start Ollama with: ollama serve")
    
    yield
    
    # Shutdown: Cleanup (optional)
    print("Shutting down Resume Parser API...")


# Initialize FastAPI app
app = FastAPI(
    title="Resume Parser API",
    description="Parse PDF resumes using Ollama LLM models",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"] for stricter policy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes
app.include_router(routes.router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "message": "Resume Parser API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API and Ollama status
    """
    health_status = {
        "api": "healthy",
        "ollama": "unknown"
    }
    
    try:
        import requests
        response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            health_status["ollama"] = "healthy"
            health_status["ollama_url"] = settings.OLLAMA_BASE_URL
            health_status["model"] = settings.OLLAMA_MODEL
        else:
            health_status["ollama"] = "unhealthy"
    except Exception as e:
        health_status["ollama"] = "unreachable"
        health_status["error"] = str(e)
    
    return health_status


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Custom HTTP exception handler
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    General exception handler for unhandled errors
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )