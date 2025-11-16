# Python Module Structure Documentation

**Purpose**: Document Python import structure and dependencies for Family Assistant
**Target**: Developers working on Python containerization and deployment
**Updated**: 2025-11-15

---

## 📁 Project Structure

```
family-assistant/
├── api/                          # FastAPI application package
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # Main FastAPI application entry point
│   ├── database.py              # Database connection utilities
│   ├── dependencies.py          # FastAPI dependency injection
│   ├── startup.py               # Application startup/shutdown events
│   ├── middleware/              # Custom middleware
│   │   ├── __init__.py
│   │   ├── rate_limit.py        # Rate limiting middleware
│   │   └── security.py          # Security headers middleware
│   ├── models/                  # Pydantic models and schemas
│   │   ├── __init__.py
│   │   ├── database.py          # Database ORM models
│   │   ├── multimodal.py        # Multimodal content models
│   │   ├── memory.py            # Memory management models
│   │   └── user_management.py   # User profile models
│   ├── routes/                  # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── family.py            # Family management endpoints
│   │   └── phase2_routes.py     # Phase 2 feature endpoints
│   ├── services/                # Business logic services
│   │   ├── __init__.py
│   │   ├── content_processor.py # Multimodal content processing
│   │   └── telegram_service.py  # Telegram bot integration
│   └── observability/           # Monitoring and observability
│       ├── __init__.py
│       ├── logging.py           # Structured logging setup
│       ├── metrics.py           # Prometheus metrics
│       └── tracing.py           # OpenTelemetry tracing
├── agents/                      # AI agent implementations
│   ├── __init__.py
│   └── memory_agent.py          # Memory-enabled AI agent
├── config/                      # Configuration management
│   ├── __init__.py
│   ├── settings.py              # Application settings
│   ├── feature_flags.py         # Feature flag management
│   └── permissions.py           # User permissions configuration
├── migrations/                  # Database migration files
│   ├── __init__.py
│   └── 001_multimodal_schema.py  # Multimodal content schema
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py              # pytest configuration
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── e2e/                     # End-to-end tests
├── frontend/                    # React frontend application
└── requirements.txt             # Python dependencies
```

---

## 🔗 Import Dependencies

### Core Application Imports (api/main.py)

```python
# System imports
import uuid
import asyncpg
import psutil
import subprocess
import json
import asyncio
from pathlib import Path
from datetime import datetime

# FastAPI imports
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# Configuration imports
from config.settings import settings
from config.feature_flags import feature_flags

# Model imports
from api.models.multimodal import (
    MultimodalChatRequest, MultimodalChatResponse, ChatMessage,
    ContentType, ProcessingStatus, MultimodalContent,
    TextContent, ImageContent, AudioContent, DocumentContent,
    FamilyMemberProfile
)
from api.models.database import *  # Database models
from api.models.user_management import *  # User management models

# Service imports
from api.services.content_processor import ContentProcessor, ContentProcessorError, content_processor
from api.services.telegram_service import create_telegram_service

# Route imports
from api.routes.phase2_routes import router as phase2_router
from api.routes.family import router as family_router
from api.routes.auth import router as auth_router

# Middleware and observability imports
from api.middleware.rate_limit import setup_rate_limiting
from api.middleware.security import SecurityHeadersMiddleware
from api.observability.tracing import setup_tracing
from api.observability.logging import setup_logging
from api.observability.metrics import setup_metrics

# Application lifecycle
from api.startup import startup_event, shutdown_event
```

### Import Dependencies Analysis

#### Critical Dependencies
1. **pydantic** (^2.10.6) - Required for all model definitions
2. **fastapi** (^0.115.6) - Core web framework
3. **asyncpg** (^0.30.0) - PostgreSQL async driver
4. **psutil** (^6.1.1) - System monitoring utilities
5. **python-multipart** (^0.0.20) - File upload support

#### Optional Dependencies (with graceful degradation)
1. **aiohttp** (^3.11.10) - HTTP client for service discovery
2. **Pillow** (^11.0.0) - Image processing
3. **pytesseract** (^0.3.13) - OCR functionality
4. **speechrecognition** (^3.10.4) - Audio transcription
5. **python-magic** (^0.4.27) - File type detection

#### Development Dependencies
1. **pytest** (^8.3.4) - Testing framework
2. **mypy** (^1.14.1) - Static type checking
3. **ruff** (^0.8.5) - Linting and formatting
4. **black** (^24.10.0) - Code formatting

---

## 🐍 PYTHONPATH Configuration

### Docker Container PYTHONPATH
```dockerfile
# Set Python path to include app root and all necessary directories
ENV PYTHONPATH=/app:/app/api:/app/config:/app/agents:/app/services:/app/models
```

### Local Development PYTHONPATH
```bash
# Set from project root
export PYTHONPATH=/path/to/family-assistant:/path/to/family-assistant/api:/path/to/family-assistant/config
```

### Dynamic Import Resolution
```python
import sys
from pathlib import Path

# Add project root to Python path dynamically
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "api"))
sys.path.insert(0, str(PROJECT_ROOT / "config"))
```

---

## 🔧 Import Resolution Strategies

### 1. Relative Imports (Preferred)
```python
# Within api/ package
from .models.multimodal import MultimodalChatRequest
from .services.content_processor import ContentProcessor
from .routes.auth import router as auth_router

# Within routes/ package
from ..models.database import User
from ..services.content_processor import ContentProcessor
from ..config.settings import settings
```

### 2. Absolute Imports (Required for FastAPI)
```python
# Always use absolute imports for top-level modules
from api.models.multimodal import MultimodalChatRequest
from api.services.content_processor import ContentProcessor
from config.settings import settings
```

### 3. Conditional Imports (for optional dependencies)
```python
# Optional multimodal processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Optional OCR
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
```

---

## 📦 Package Dependencies Mapping

### Core API Package Dependencies
```
api/
├── main.py → config/, api/models/, api/services/, api/routes/
├── models/ → pydantic, sqlalchemy, asyncpg
├── services/ → aiohttp, Pillow, pytesseract, speechrecognition
├── routes/ → fastapi, python-jose, passlib
├── middleware/ → slowapi, prometheus-client
└── observability/ → opentelemetry, prometheus-client
```

### Configuration Package Dependencies
```
config/
├── settings.py → pydantic-settings, python-dotenv
├── feature_flags.py → None (pure Python)
└── permissions.py → None (pure Python)
```

### Agents Package Dependencies
```
agents/
└── memory_agent.py → langchain-core, mem0ai, qdrant-client
```

---

## 🚨 Common Import Issues & Solutions

### Issue 1: ModuleNotFoundError for api.models
**Cause**: PYTHONPATH not including project root
**Solution**:
```dockerfile
ENV PYTHONPATH=/app:/app/api:/app/config
```

### Issue 2: Optional dependency import failures
**Cause**: Missing system dependencies (ffmpeg, tesseract)
**Solution**:
```dockerfile
RUN apt-get install -y ffmpeg tesseract-ocr libmagic1
```

### Issue 3: Circular imports
**Cause**: Models importing each other
**Solution**: Use dependency injection or move common imports to separate module

### Issue 4: Relative vs Absolute import confusion
**Cause**: Mixing import styles
**Solution**: Use absolute imports for cross-package, relative for same package

---

## 🧪 Import Testing Script

```python
#!/usr/bin/env python3
"""
test_imports.py - Test all critical imports
"""

import sys
import traceback
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_import(module_name, description):
    """Test importing a module and report results."""
    try:
        __import__(module_name)
        print(f"✅ {description}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {description}: {e}")
        return False

def main():
    """Run all import tests."""
    print("🧪 Testing Python imports...\n")

    tests = [
        ("config.settings", "Configuration settings"),
        ("api.models.multimodal", "Multimodal models"),
        ("api.models.database", "Database models"),
        ("api.services.content_processor", "Content processor"),
        ("api.main", "Main FastAPI application"),
        ("agents.memory_agent", "Memory agent"),
    ]

    passed = 0
    total = len(tests)

    for module, description in tests:
        if test_import(module, description):
            passed += 1

    print(f"\n📊 Results: {passed}/{total} imports successful")

    if passed == total:
        print("🎉 All imports working correctly!")
        return 0
    else:
        print("💥 Some imports failed - check dependencies")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## 🔍 Dependency Management

### Requirements Organization
```txt
# requirements.txt organized by dependency type

# Core Framework - Always Required
langgraph==0.2.56
fastapi==0.115.6
pydantic==2.10.6
uvicorn[standard]==0.34.0

# Database - Always Required
asyncpg==0.30.0
psycopg2-binary==2.9.10

# Multimodal Processing - Optional with fallbacks
Pillow==11.0.0                    # Image processing
pytesseract==0.3.13              # OCR
speechrecognition==3.10.4        # Audio transcription
python-magic==0.4.27              # File type detection

# Development - Not required in production
pytest==8.3.4
mypy==1.14.1
black==24.10.0
```

### Dependency Installation Strategy
```dockerfile
# Install core dependencies first
COPY requirements-core.txt .
RUN pip install --no-cache-dir -r requirements-core.txt

# Install optional dependencies with error handling
COPY requirements-optional.txt .
RUN pip install --no-cache-dir -r requirements-optional.txt || echo "Optional deps failed"

# Install development dependencies only in dev builds
ARG BUILD_ENV=production
COPY requirements-dev.txt .
RUN if [ "$BUILD_ENV" = "development" ]; then \
        pip install --no-cache-dir -r requirements-dev.txt; \
    fi
```

---

## 🔄 Continuous Integration

### GitHub Actions Import Testing
```yaml
- name: Test Python imports
  run: |
    python test_imports.py

- name: Check for circular imports
  run: |
    python -m pyflakes **/*.py || true

- name: Validate module structure
  run: |
    python -c "
import sys
sys.path.append('.')
import api.main
print('✅ Main application imports successfully')
"
```

---

## 📚 Best Practices

### 1. Import Organization
```python
# 1. Standard library imports
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict

# 2. Third-party imports
import fastapi
from fastapi import FastAPI
from pydantic import BaseModel

# 3. Local imports
from config.settings import settings
from api.models.multimodal import MultimodalChatRequest
```

### 2. Lazy Loading for Heavy Dependencies
```python
def get_content_processor():
    """Lazy load content processor only when needed."""
    from api.services.content_processor import ContentProcessor
    return ContentProcessor()

# Usage in endpoint
@app.post("/upload")
async def upload_file():
    processor = get_content_processor()  # Only loaded when needed
```

### 3. Error Handling for Optional Dependencies
```python
def process_image(image_data):
    """Process image with graceful degradation."""
    try:
        from PIL import Image
        return Image.open(image_data)
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="Image processing not available - install Pillow"
        )
```

---

**Remember**: Clear import structure prevents deployment issues and makes maintenance easier. 🐍✨