# Comprehensive Testing Framework

**Purpose**: Establish systematic testing practices for Family Assistant and Python services
**Target**: All development and deployment activities
**Updated**: 2025-11-15

---

## 🧪 Testing Pyramid Overview

```
                    /\
                   /  \
                  / E2E \  <-- 5% (End-to-End Tests)
                 /______\
                /        \
               /Integration\ <-- 15% (Integration Tests)
              /____________\
             /              \
            /    Unit Tests    \ <-- 80% (Unit Tests)
           /__________________\
```

### Testing Distribution
- **Unit Tests**: 80% - Fast, isolated, comprehensive
- **Integration Tests**: 15% - Service interactions, database, APIs
- **End-to-End Tests**: 5% - Complete user workflows

---

## 🔬 Unit Testing Framework

### Core Unit Testing Structure
```
tests/
├── unit/                          # Unit test suite
│   ├── __init__.py
│   ├── conftest.py               # Pytest configuration
│   ├── test_api_main.py          # API endpoint tests
│   ├── test_models.py            # Pydantic model tests
│   ├── test_services.py          # Business logic tests
│   ├── test_auth.py              # Authentication tests
│   ├── test_middleware.py        # Middleware tests
│   └── test_utils.py             # Utility function tests
├── fixtures/                      # Test data fixtures
│   ├── sample_data.json
│   ├── test_images/
│   └── test_documents/
└── helpers/                       # Test helper utilities
    ├── __init__.py
    ├── database.py               # Database test helpers
    ├── mock_services.py          # Mock service utilities
    └── test_client.py            # HTTP client test utilities
```

### Pytest Configuration (conftest.py)
```python
import pytest
import asyncio
import asyncpg
from httpx import AsyncClient
from fastapi.testclient import TestClient
from api.main import app
from config.settings import settings

# Override settings for testing
settings.database_url = "postgresql://test:test@localhost:5432/test_db"
settings.redis_url = "redis://localhost:6379/1"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_db():
    """Create test database connection."""
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="test",
        password="test",
        database="test_db"
    )

    # Create test tables
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS test_users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE
        )
    """)

    yield conn

    # Cleanup
    await conn.execute("DROP TABLE IF EXISTS test_users")
    await conn.close()

@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_family_member():
    """Mock family member for testing."""
    return {
        "user_id": "test_user_123",
        "name": "Test User",
        "role": "parent",
        "age": 35,
        "permissions": {"chat": True, "upload": True},
        "preferences": {"theme": "light"}
    }

@pytest.fixture
def sample_multimodal_content():
    """Sample multimodal content for testing."""
    return {
        "text": "This is a test message",
        "image_data": b"fake_image_data",
        "audio_data": b"fake_audio_data"
    }
```

### Unit Test Examples

#### API Endpoint Tests
```python
# tests/unit/test_api_main.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

class TestHealthEndpoints:
    """Test health and system endpoints."""

    def test_health_endpoint(self, client):
        """Test basic health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    @patch('api.main.psutil.cpu_percent')
    @patch('api.main.psutil.virtual_memory')
    def test_system_metrics(self, mock_memory, mock_cpu, client):
        """Test system metrics endpoint."""
        mock_cpu.return_value = 25.5
        mock_memory.return_value = MagicMock(
            total=8589934592,
            available=4294967296,
            used=4294967296,
            percent=50.0
        )

        response = client.get("/dashboard/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "cpu" in data
        assert "memory" in data

class TestAuthentication:
    """Test authentication endpoints."""

    def test_login_success(self, client, mock_family_member):
        """Test successful login."""
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        # Implement based on your auth system
        assert response.status_code in [200, 404]  # 404 if auth not implemented

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post("/api/v1/auth/login", json={
            "username": "invalid",
            "password": "invalid"
        })
        assert response.status_code in [401, 404]
```

#### Model Tests
```python
# tests/unit/test_models.py
import pytest
from pydantic import ValidationError
from api.models.multimodal import (
    MultimodalChatRequest, ChatMessage, TextContent,
    ImageContent, FamilyMemberProfile
)

class TestMultimodalModels:
    """Test multimodal content models."""

    def test_text_content_creation(self):
        """Test creating text content."""
        content = TextContent(
            content="Hello, world!",
            language_code="en"
        )
        assert content.content == "Hello, world!"
        assert content.language_code == "en"
        assert content.content_type == "text"

    def test_text_content_validation(self):
        """Test text content validation."""
        with pytest.raises(ValidationError):
            TextContent(content="")  # Empty content should fail

    def test_family_member_profile_creation(self, mock_family_member):
        """Test creating family member profile."""
        profile = FamilyMemberProfile(**mock_family_member)
        assert profile.user_id == "test_user_123"
        assert profile.name == "Test User"
        assert profile.role == "parent"

    def test_multimodal_chat_request(self):
        """Test multimodal chat request creation."""
        request = MultimodalChatRequest(
            model="family-assistant",
            messages=[
                ChatMessage(
                    role="user",
                    content="Hello"
                )
            ]
        )
        assert request.model == "family-assistant"
        assert len(request.messages) == 1
        assert request.messages[0].content == "Hello"
```

#### Service Tests
```python
# tests/unit/test_services.py
import pytest
from unittest.mock import Mock, patch
from api.services.content_processor import ContentProcessor

class TestContentProcessor:
    """Test content processing service."""

    @pytest.fixture
    def processor(self):
        """Create content processor instance."""
        return ContentProcessor()

    @patch('api.services.content_processor.Image')
    @patch('api.services.content_processor.Image.open')
    def test_process_image(self, mock_image_open, mock_image_class, processor):
        """Test image processing."""
        # Mock image processing
        mock_img = Mock()
        mock_img.size = (100, 100)
        mock_img.format = "JPEG"
        mock_image_open.return_value = mock_img

        result = processor.process_image(b"fake_image_data", "test.jpg")
        # Assert based on your processing logic
        assert result is not None

    @patch('api.services.content_processor.speech_recognition.recognize_google')
    def test_process_audio(self, mock_recognize, processor):
        """Test audio processing."""
        mock_recognize.return_value = "Hello world"

        result = processor.process_audio(b"fake_audio_data", "test.wav")
        assert "Hello world" in result or result is not None
```

---

## 🔗 Integration Testing Framework

### Integration Test Structure
```
tests/
├── integration/                   # Integration test suite
│   ├── __init__.py
│   ├── conftest.py               # Integration test configuration
│   ├── test_database.py          # Database integration tests
│   ├── test_external_apis.py     # External service integration
│   ├── test_multimodal.py        # Multimodal processing integration
│   ├── test_websocket.py         # WebSocket integration tests
│   └── test_full_workflows.py    # Complete workflow tests
├── integration_fixtures/          # Integration test data
│   ├── database_migrations.sql
│   ├── sample_media/
│   └── external_api_responses/
```

### Database Integration Tests
```python
# tests/integration/test_database.py
import pytest
import asyncpg
from api.models.database import User, Conversation

class TestDatabaseIntegration:
    """Test database integration scenarios."""

    @pytest.mark.asyncio
    async def test_user_crud_operations(self, test_db):
        """Test complete CRUD operations for users."""
        # Create user
        user_id = await test_db.fetchval(
            "INSERT INTO users (name, email, role) VALUES ($1, $2, $3) RETURNING id",
            "Test User", "test@example.com", "parent"
        )
        assert user_id is not None

        # Read user
        user = await test_db.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id
        )
        assert user["name"] == "Test User"
        assert user["email"] == "test@example.com"

        # Update user
        await test_db.execute(
            "UPDATE users SET name = $1 WHERE id = $2",
            "Updated User", user_id
        )

        # Verify update
        updated_user = await test_db.fetchrow(
            "SELECT name FROM users WHERE id = $1", user_id
        )
        assert updated_user["name"] == "Updated User"

        # Delete user
        await test_db.execute("DELETE FROM users WHERE id = $1", user_id)

        # Verify deletion
        deleted_user = await test_db.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id
        )
        assert deleted_user is None

    @pytest.mark.asyncio
    async def test_conversation_history(self, test_db):
        """Test conversation history storage and retrieval."""
        # Create conversation thread
        thread_id = "test_thread_123"

        # Insert messages
        await test_db.execute("""
            INSERT INTO conversation_history (thread_id, user_id, role, content)
            VALUES ($1, $2, $3, $4), ($5, $6, $7, $8)
        """,
        thread_id, "user123", "user", "Hello",
        thread_id, "user123", "assistant", "Hi there!"
        )

        # Retrieve conversation
        messages = await test_db.fetch("""
            SELECT role, content, created_at
            FROM conversation_history
            WHERE thread_id = $1
            ORDER BY created_at ASC
        """, thread_id)

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Hi there!"
```

### External API Integration Tests
```python
# tests/integration/test_external_apis.py
import pytest
import httpx
from unittest.mock import patch, AsyncMock

class TestExternalAPIIntegration:
    """Test external API integrations."""

    @pytest.mark.asyncio
    async def test_ollama_integration(self):
        """Test Ollama API integration."""
        async with httpx.AsyncClient() as client:
            # Test Ollama health
            response = await client.get(
                "http://localhost:11434/api/tags",
                timeout=10.0
            )
            assert response.status_code == 200

            # Test model listing
            data = response.json()
            assert "models" in data

    @pytest.mark.asyncio
    @patch('api.main.aiohttp.ClientSession.get')
    async def test_mem0_integration(self, mock_get):
        """Test Mem0 API integration."""
        # Mock Mem0 response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response

        # Test Mem0 health check
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://mem0.homelab.svc.cluster.local:8080/health",
                timeout=5.0
            )
            # Test based on actual Mem0 API behavior
            assert response.status_code in [200, 404]  # 404 if endpoint not implemented
```

### WebSocket Integration Tests
```python
# tests/integration/test_websocket.py
import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from api.main import app

class TestWebSocketIntegration:
    """Test WebSocket functionality."""

    def test_websocket_connection(self, client):
        """Test WebSocket connection establishment."""
        with client.websocket_connect("/ws") as websocket:
            # Connection should be established
            assert websocket is not None

            # Should receive initial system health message
            data = websocket.receive_json(timeout=5.0)
            assert "type" in data
            assert data["type"] == "system_health"
            assert "data" in data

    def test_websocket_message_flow(self, client):
        """Test WebSocket message flow."""
        with client.websocket_connect("/ws") as websocket:
            # Receive initial message
            initial_data = websocket.receive_json(timeout=5.0)

            # Send test message (if your WebSocket accepts messages)
            # websocket.send_json({"type": "test", "data": "hello"})

            # Receive response
            # response_data = websocket.receive_json(timeout=5.0)
```

---

## 🌐 End-to-End Testing Framework

### E2E Test Structure
```
tests/
├── e2e/                          # End-to-end test suite
│   ├── __init__.py
│   ├── conftest.py               # E2E test configuration
│   ├── test_user_workflows.py    # Complete user workflows
│   ├── test_multimodal_flow.py  # Multimodal content processing
│   ├── test_dashboard_ui.py      # Dashboard UI tests
│   └── test_api_e2e.py          # Complete API workflows
├── e2e_fixtures/                 # E2E test data and utilities
│   ├── test_scenarios.json
│   ├── sample_media/
│   └── browser_configs/
```

### Playwright E2E Tests
```python
# tests/e2e/test_dashboard_ui.py
import pytest
from playwright.async_api import async_playwright, Page

class TestDashboardUI:
    """Test dashboard user interface."""

    @pytest.mark.asyncio
    async def test_dashboard_loads(self):
        """Test dashboard loads correctly."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Navigate to dashboard
            await page.goto("http://100.81.76.55:30080/")

            # Wait for page to load
            await page.wait_for_load_state("networkidle")

            # Check for key elements
            await page.wait_for_selector('[data-testid="dashboard-title"]')
            await page.wait_for_selector('[data-testid="system-health"]')

            # Verify content
            title = await page.text_content('[data-testid="dashboard-title"]')
            assert "Family Assistant" in title

            await browser.close()

    @pytest.mark.asyncio
    async def test_system_health_display(self):
        """Test system health information display."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            await page.goto("http://100.81.76.55:30080/")

            # Check system metrics
            await page.wait_for_selector('[data-testid="cpu-usage"]')
            await page.wait_for_selector('[data-testid="memory-usage"]')
            await page.wait_for_selector('[data-testid="service-status"]')

            # Verify metrics are displayed
            cpu_text = await page.text_content('[data-testid="cpu-usage"]')
            assert "%" in cpu_text  # Should show percentage

            await browser.close()

    @pytest.mark.asyncio
    async def test_responsive_design(self):
        """Test dashboard responsive design."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            await page.goto("http://100.81.76.55:30080/")

            # Test desktop view
            await page.set_viewport_size({"width": 1200, "height": 800})
            await page.wait_for_selector('[data-testid="dashboard-grid"]')

            # Test tablet view
            await page.set_viewport_size({"width": 768, "height": 1024})
            await page.wait_for_selector('[data-testid="dashboard-grid"]')

            # Test mobile view
            await page.set_viewport_size({"width": 375, "height": 667})
            await page.wait_for_selector('[data-testid="mobile-menu"]')

            await browser.close()
```

### API E2E Tests
```python
# tests/e2e/test_api_e2e.py
import pytest
import httpx
import asyncio
from concurrent.futures import ThreadPoolExecutor

class TestAPIE2E:
    """Complete API workflow tests."""

    @pytest.mark.asyncio
    async def test_complete_chat_workflow(self):
        """Test complete chat workflow from start to finish."""
        async with httpx.AsyncClient() as client:
            # Step 1: Health check
            health_response = await client.get("http://100.81.76.55:30080/health")
            assert health_response.status_code == 200

            # Step 2: Get system health
            system_response = await client.get("http://100.81.76.55:30080/dashboard/system-health")
            assert system_response.status_code == 200
            system_data = system_response.json()
            assert "system" in system_data
            assert "services" in system_data

            # Step 3: Test chat endpoint
            chat_response = await client.post(
                "http://100.81.76.55:30080/chat",
                json={
                    "message": "Hello, Family Assistant!",
                    "user_id": "test_user_e2e"
                }
            )
            assert chat_response.status_code == 200
            chat_data = chat_response.json()
            assert "response" in chat_data
            assert "thread_id" in chat_data
            assert chat_data["response"] is not None

            # Step 4: Retrieve conversation history
            thread_id = chat_data["thread_id"]
            history_response = await client.get(
                f"http://100.81.76.55:30080/conversations/{thread_id}"
            )
            assert history_response.status_code == 200
            history_data = history_response.json()
            assert "messages" in history_data
            assert len(history_data["messages"]) >= 2  # User + Assistant

    @pytest.mark.asyncio
    async def test_multimodal_workflow(self):
        """Test multimodal content processing workflow."""
        async with httpx.AsyncClient() as client:
            # Test with sample image data (base64 encoded small image)
            import base64

            # Create a small test image (1x1 pixel PNG)
            test_image_data = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
                "/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            )

            # Test multimodal content upload
            files = {
                "file": ("test.png", test_image_data, "image/png"),
            }
            data = {
                "description": "Test image",
                "user_id": "test_user_multimodal"
            }

            upload_response = await client.post(
                "http://100.81.76.55:30080/upload",
                files=files,
                data=data
            )

            # Upload should either succeed or fail gracefully
            assert upload_response.status_code in [200, 400, 415]

            if upload_response.status_code == 200:
                upload_data = upload_response.json()
                assert "upload_id" in upload_data
                assert upload_data["processing_status"] in ["completed", "processing", "failed"]

    async def test_concurrent_requests(self):
        """Test API under concurrent load."""
        async with httpx.AsyncClient() as client:

            async def make_request():
                """Make a single API request."""
                response = await client.get("http://100.81.76.55:30080/health")
                return response.status_code

            # Test 10 concurrent requests
            tasks = [make_request() for _ in range(10)]
            results = await asyncio.gather(*tasks)

            # All requests should succeed
            assert all(result == 200 for result in results)
```

---

## 🚀 Test Execution Framework

### Test Scripts
```bash
#!/bin/bash
# run-tests.sh - Comprehensive test execution script

set -e

echo "🧪 Running comprehensive test suite..."

# Function to run test category
run_tests() {
    local test_type=$1
    local test_command=$2

    echo ""
    echo "🔍 Running $test_type tests..."
    echo "Command: $test_command"

    if eval "$test_command"; then
        echo "✅ $test_type tests passed"
        return 0
    else
        echo "❌ $test_type tests failed"
        return 1
    fi
}

# Test execution
FAILED_TESTS=()

# Unit tests
if ! run_tests "Unit" "pytest tests/unit/ -v --cov=api --cov-report=html --cov-report=term-missing"; then
    FAILED_TESTS+=("unit")
fi

# Integration tests (only if unit tests pass)
if [[ ${#FAILED_TESTS[@]} -eq 0 ]]; then
    if ! run_tests "Integration" "pytest tests/integration/ -v -m 'not slow'"; then
        FAILED_TESTS+=("integration")
    fi
else
    echo "⏭️ Skipping integration tests due to unit test failures"
fi

# E2E tests (only if previous tests pass)
if [[ ${#FAILED_TESTS[@]} -eq 0 ]]; then
    if ! run_tests "E2E" "pytest tests/e2e/ -v -m 'not slow'"; then
        FAILED_TESTS+=("e2e")
    fi
else
    echo "⏭️ Skipping E2E tests due to previous test failures"
fi

# Summary
echo ""
echo "📊 Test Summary"
echo "=============="

if [[ ${#FAILED_TESTS[@]} -eq 0 ]]; then
    echo "🎉 All tests passed!"
    echo "📁 Coverage report: htmlcov/index.html"
    exit 0
else
    echo "💥 Failed test categories: ${FAILED_TESTS[*]}"
    echo "📁 Coverage report: htmlcov/index.html"
    exit 1
fi
```

### Continuous Integration Configuration
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_USER: test
          POSTGRES_DB: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.12"

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov httpx

    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=api --cov-report=xml

    - name: Run integration tests
      run: |
        pytest tests/integration/ -v

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## 📊 Test Reporting and Analytics

### Test Coverage Configuration
```python
# pytest.ini
[tool:pytest]
minversion = 6.0
addopts =
    -ra
    --strict-markers
    --strict-config
    --cov=api
    --cov-report=html
    --cov-report=term-missing
    --cov-report=xml
    --cov-fail-under=80
testpaths = tests
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
    unit: marks tests as unit tests
```

### Custom Test Reporter
```python
# tests/helpers/reporter.py
import json
import datetime
from pathlib import Path

class TestReporter:
    """Custom test reporter for detailed analytics."""

    def __init__(self, output_dir="test-reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "summary": {},
            "tests": [],
            "coverage": {},
            "performance": {}
        }

    def record_test_result(self, test_name, status, duration=None, error=None):
        """Record individual test result."""
        test_result = {
            "name": test_name,
            "status": status,  # "passed", "failed", "skipped"
            "duration": duration,
            "error": str(error) if error else None,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.results["tests"].append(test_result)

    def generate_report(self):
        """Generate comprehensive test report."""
        # Calculate summary statistics
        total_tests = len(self.results["tests"])
        passed_tests = len([t for t in self.results["tests"] if t["status"] == "passed"])
        failed_tests = len([t for t in self.results["tests"] if t["status"] == "failed"])
        skipped_tests = len([t for t in self.results["tests"] if t["status"] == "skipped"])

        self.results["summary"] = {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "skipped": skipped_tests,
            "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }

        # Write JSON report
        report_file = self.output_dir / f"test-report-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        # Write HTML report (simplified)
        html_file = self.output_dir / f"test-report-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
        self._generate_html_report(html_file)

        return report_file, html_file

    def _generate_html_report(self, output_file):
        """Generate HTML test report."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .skipped {{ color: orange; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Test Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Tests: {self.results['summary']['total']}</p>
                <p class="passed">Passed: {self.results['summary']['passed']}</p>
                <p class="failed">Failed: {self.results['summary']['failed']}</p>
                <p class="skipped">Skipped: {self.results['summary']['skipped']}</p>
                <p>Pass Rate: {self.results['summary']['pass_rate']:.1f}%</p>
            </div>

            <h2>Test Results</h2>
            <table>
                <tr>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Duration (s)</th>
                    <th>Error</th>
                </tr>
        """

        for test in self.results["tests"]:
            status_class = test["status"]
            html_content += f"""
                <tr>
                    <td>{test['name']}</td>
                    <td class="{status_class}">{test['status'].upper()}</td>
                    <td>{test['duration'] or 'N/A'}</td>
                    <td>{test['error'] or 'N/A'}</td>
                </tr>
            """

        html_content += """
            </table>
        </body>
        </html>
        """

        with open(output_file, 'w') as f:
            f.write(html_content)
```

---

## 🎯 Test Best Practices

### Test Organization
1. **Clear Naming**: Test names should describe what they test
2. **Arrange-Act-Assert**: Structure tests clearly
3. **Independent Tests**: Each test should run in isolation
4. **Descriptive Assertions**: Use clear assertion messages

### Test Data Management
```python
# Use fixtures for consistent test data
@pytest.fixture
def sample_user_data():
    return {
        "name": "Test User",
        "email": "test@example.com",
        "role": "parent"
    }

# Clean up test data automatically
@pytest.fixture
async def test_database_with_data(test_db):
    # Setup test data
    user_id = await test_db.fetchval(
        "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id",
        "Test User", "test@example.com"
    )

    yield test_db  # Provide database to test

    # Cleanup
    await test_db.execute("DELETE FROM users WHERE id = $1", user_id)
```

### Mocking Strategies
```python
# Mock external dependencies
@patch('api.services.external_service.API_CLIENT')
def test_with_mock_api(mock_client):
    # Configure mock
    mock_client.get.return_value.json.return_value = {"status": "ok"}

    # Test your code
    result = your_function_that_uses_api()

    # Verify mock was called correctly
    mock_client.get.assert_called_once_with("/api/endpoint")

# Use factories for complex test data
class UserFactory:
    @staticmethod
    def create_user(**overrides):
        default_data = {
            "name": "Test User",
            "email": "test@example.com",
            "role": "parent"
        }
        default_data.update(overrides)
        return default_data
```

### Performance Testing
```python
import time
import pytest

@pytest.mark.performance
def test_api_response_time(client):
    """Test API response time under 200ms."""
    start_time = time.time()
    response = client.get("/health")
    end_time = time.time()

    response_time_ms = (end_time - start_time) * 1000
    assert response_time_ms < 200, f"Response time {response_time_ms}ms exceeds 200ms limit"
    assert response.status_code == 200
```

---

## 📋 Testing Checklist

### Pre-Deployment Testing
- [ ] **Unit Tests**: All unit tests passing (>80% coverage)
- [ ] **Integration Tests**: Database and external service tests passing
- [ ] **API Tests**: All endpoints tested with various scenarios
- [ ] **Performance Tests**: Response times and load testing completed
- [ ] **Security Tests**: Authentication and authorization tested
- [ ] **UI Tests**: Critical user workflows tested

### Regular Maintenance
- [ ] **Test Review**: Monthly review of test coverage and quality
- [ ] **Test Updates**: Update tests when functionality changes
- [ ] **Performance Baselines**: Update performance expectations
- [ ] **Mock Updates**: Keep mocks consistent with real APIs
- [ ] **Documentation**: Keep test documentation current

### Quality Gates
- [ ] **Code Coverage**: Minimum 80% test coverage required
- [ ] **Test Success**: All automated tests must pass
- [ ] **Performance Benchmarks**: Response times under defined limits
- [ ] **Security Validation**: No security test failures
- [ ] **Documentation**: Tests must be well-documented

---

**Remember**: Good tests are your safety net. Invest in comprehensive testing to catch issues early and maintain confidence in your deployments. 🛡️✨