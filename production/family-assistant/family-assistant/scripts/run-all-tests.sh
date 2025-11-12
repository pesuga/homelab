#!/bin/bash

# Comprehensive test runner for Family Assistant
# Runs all backend and frontend tests with coverage reporting

set -e  # Exit on error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if services are running
check_services() {
    print_info "Checking required services..."

    # Check PostgreSQL
    if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        print_error "PostgreSQL is not running on localhost:5432"
        print_info "Start PostgreSQL or update DATABASE_URL environment variable"
        exit 1
    fi

    # Check Redis
    if ! redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
        print_error "Redis is not running on localhost:6379"
        print_info "Start Redis or update REDIS_URL environment variable"
        exit 1
    fi

    print_success "All required services are running"
}

# Run backend unit tests
run_backend_unit_tests() {
    print_info "Running backend unit tests..."
    cd "$BACKEND_DIR"

    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found. Run: python3 -m venv venv"
        exit 1
    fi

    source venv/bin/activate

    pytest tests/unit/ \
        -v \
        --cov=api \
        --cov-report=xml:coverage-unit.xml \
        --cov-report=html:htmlcov-unit \
        --cov-report=term-missing \
        --junitxml=junit-unit.xml \
        -n auto

    UNIT_EXIT_CODE=$?
    deactivate

    if [ $UNIT_EXIT_CODE -eq 0 ]; then
        print_success "Backend unit tests passed"
    else
        print_error "Backend unit tests failed"
        return $UNIT_EXIT_CODE
    fi
}

# Run backend integration tests
run_backend_integration_tests() {
    print_info "Running backend integration tests..."
    cd "$BACKEND_DIR"

    source venv/bin/activate

    pytest tests/integration/ \
        -v \
        --cov=api \
        --cov-append \
        --cov-report=xml:coverage-integration.xml \
        --cov-report=html:htmlcov-integration \
        --cov-report=term-missing \
        --junitxml=junit-integration.xml

    INTEGRATION_EXIT_CODE=$?
    deactivate

    if [ $INTEGRATION_EXIT_CODE -eq 0 ]; then
        print_success "Backend integration tests passed"
    else
        print_error "Backend integration tests failed"
        return $INTEGRATION_EXIT_CODE
    fi
}

# Generate combined backend coverage report
generate_backend_coverage() {
    print_info "Generating combined backend coverage report..."
    cd "$BACKEND_DIR"

    source venv/bin/activate

    # Combine coverage data
    coverage combine 2>/dev/null || true
    coverage xml -o coverage-combined.xml
    coverage html -d htmlcov-combined
    coverage report

    deactivate

    print_success "Backend coverage report generated: htmlcov-combined/index.html"
}

# Run frontend E2E tests
run_frontend_e2e_tests() {
    print_info "Running frontend E2E tests..."
    cd "$FRONTEND_DIR"

    if [ ! -d "node_modules" ]; then
        print_error "Node modules not found. Run: npm install"
        exit 1
    fi

    # Check if Playwright browsers are installed
    if ! npx playwright --version > /dev/null 2>&1; then
        print_warning "Playwright not found. Installing..."
        npx playwright install --with-deps chromium firefox
    fi

    # Run Playwright tests
    npx playwright test --reporter=html,json,list

    E2E_EXIT_CODE=$?

    if [ $E2E_EXIT_CODE -eq 0 ]; then
        print_success "Frontend E2E tests passed"
    else
        print_error "Frontend E2E tests failed"
        print_info "View report: cd frontend && npm run test:e2e:report"
        return $E2E_EXIT_CODE
    fi
}

# Run linting and type checks
run_linting() {
    print_info "Running linting and type checks..."

    # Backend linting
    cd "$BACKEND_DIR"
    source venv/bin/activate

    print_info "Running Python linting (ruff)..."
    ruff check api/ tests/ || print_warning "Ruff linting found issues"

    print_info "Running Python type checking (mypy)..."
    mypy api/ --ignore-missing-imports || print_warning "MyPy found type issues"

    deactivate

    # Frontend linting
    cd "$FRONTEND_DIR"

    print_info "Running TypeScript type check..."
    npm run build:check

    print_info "Running ESLint..."
    npm run lint

    print_success "Linting and type checks completed"
}

# Generate test summary
generate_test_summary() {
    print_info "Generating test summary..."

    cd "$PROJECT_ROOT"

    SUMMARY_FILE="test-summary.md"

    cat > "$SUMMARY_FILE" << EOF
# Test Summary Report

**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Project**: Family Assistant

## Test Results

### Backend Tests

#### Unit Tests
- **Location**: \`tests/unit/\`
- **Coverage Report**: \`htmlcov-unit/index.html\`
- **JUnit XML**: \`junit-unit.xml\`

#### Integration Tests
- **Location**: \`tests/integration/\`
- **Coverage Report**: \`htmlcov-integration/index.html\`
- **JUnit XML**: \`junit-integration.xml\`

#### Combined Coverage
- **Report**: \`htmlcov-combined/index.html\`
- **XML**: \`coverage-combined.xml\`

### Frontend Tests

#### E2E Tests (Playwright)
- **Location**: \`frontend/e2e/\`
- **HTML Report**: \`frontend/playwright-report/index.html\`
- **JSON Results**: \`frontend/playwright-results.json\`

## Coverage Reports

### Backend Coverage
$(cd "$BACKEND_DIR" && source venv/bin/activate && coverage report 2>/dev/null || echo "Coverage data not available")

### View Reports

**Backend Coverage (Combined)**:
\`\`\`bash
open htmlcov-combined/index.html
\`\`\`

**Frontend E2E Report**:
\`\`\`bash
cd frontend && npm run test:e2e:report
\`\`\`

## Next Steps

- Review failing tests
- Address coverage gaps
- Fix linting issues
- Update documentation

EOF

    print_success "Test summary generated: $SUMMARY_FILE"
    cat "$SUMMARY_FILE"
}

# Main execution
main() {
    print_info "Starting comprehensive test suite..."
    print_info "Project: $PROJECT_ROOT"
    echo ""

    FAILED_TESTS=0

    # Check services (skip if SKIP_SERVICE_CHECK=1)
    if [ "${SKIP_SERVICE_CHECK:-0}" != "1" ]; then
        check_services
    else
        print_warning "Skipping service checks (SKIP_SERVICE_CHECK=1)"
    fi

    echo ""

    # Run backend unit tests
    if ! run_backend_unit_tests; then
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    echo ""

    # Run backend integration tests
    if ! run_backend_integration_tests; then
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    echo ""

    # Generate backend coverage
    generate_backend_coverage

    echo ""

    # Run frontend E2E tests (skip if SKIP_E2E=1)
    if [ "${SKIP_E2E:-0}" != "1" ]; then
        if ! run_frontend_e2e_tests; then
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    else
        print_warning "Skipping E2E tests (SKIP_E2E=1)"
    fi

    echo ""

    # Run linting (skip if SKIP_LINT=1)
    if [ "${SKIP_LINT:-0}" != "1" ]; then
        run_linting || print_warning "Linting completed with warnings"
    else
        print_warning "Skipping linting (SKIP_LINT=1)"
    fi

    echo ""

    # Generate summary
    generate_test_summary

    echo ""

    # Final result
    if [ $FAILED_TESTS -eq 0 ]; then
        print_success "All tests passed! 🎉"
        exit 0
    else
        print_error "$FAILED_TESTS test suite(s) failed"
        exit 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-services)
            export SKIP_SERVICE_CHECK=1
            shift
            ;;
        --skip-e2e)
            export SKIP_E2E=1
            shift
            ;;
        --skip-lint)
            export SKIP_LINT=1
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-services  Skip service availability checks"
            echo "  --skip-e2e       Skip E2E tests"
            echo "  --skip-lint      Skip linting and type checks"
            echo "  --help           Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

# Run main function
main
