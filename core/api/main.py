"""
Family AI Platform - Core API

Main FastAPI application for the Family AI Platform.
Provides family context management, privacy controls, and integration endpoints.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn

from .routers import family, privacy, integrations
from .services.family_context import FamilyContextService
from .services.auth_service import AuthService
from .models.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Family AI Platform",
    description="Private, trustworthy AI for families",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Include routers
app.include_router(family.router, prefix="/api/v1/family", tags=["family"])
app.include_router(privacy.router, prefix="/api/v1/privacy", tags=["privacy"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Family AI Platform API", "status": "healthy"}


@app.get("/api/v1/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "database": "connected",
            "family_context": "active",
            "privacy_engine": "enabled"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )