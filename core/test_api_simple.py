"""
Simple test for the Family AI Platform API
Tests basic functionality without complex dependencies.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List
import os

# Simple models for testing
class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

class SimpleFamily(BaseModel):
    name: str
    members: List[str]
    language: str

# Create FastAPI app
app = FastAPI(
    title="Family AI Platform - Test",
    description="Simple test version of the Family AI Platform API",
    version="1.0.0-test"
)

@app.get("/")
async def root():
    """Root endpoint."""
    return JSONResponse({
        "message": "Family AI Platform API - Test Version",
        "status": "healthy",
        "version": "1.0.0-test"
    })

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Family AI Platform is running in test mode",
        version="1.0.0-test"
    )

@app.get("/api/v1/family/sample")
async def get_sample_family():
    """Get sample family data for testing."""
    sample_family = SimpleFamily(
        name="García Family",
        members=["María", "Juan", "Sofía", "Carlos"],
        language="es"
    )
    return sample_family

@app.post("/api/v1/family/sample")
async def create_sample_family(family: SimpleFamily):
    """Create sample family for testing."""
    return {
        "status": "created",
        "family": family.dict(),
        "message": "Sample family created successfully"
    }

@app.get("/api/v1/test/deps")
async def test_dependencies():
    """Test basic dependencies."""
    deps = {
        "fastapi": "✓ Available",
        "pydantic": "✓ Available",
        "python": "✓ Available"
    }

    # Test for optional dependencies
    try:
        import fastapi
        deps["fastapi"] = "✓ Working"
    except ImportError:
        deps["fastapi"] = "✗ Missing"

    try:
        import pydantic
        deps["pydantic"] = "✓ Working"
    except ImportError:
        deps["pydantic"] = "✗ Missing"

    return deps

if __name__ == "__main__":
    import uvicorn

    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))

    print(f"🚀 Starting Family AI Platform Test API on port {port}")
    print("📍 Health check: http://localhost:{port}/health")
    print("📖 API docs: http://localhost:{port}/docs")

    uvicorn.run(app, host="0.0.0.0", port=port)