#!/bin/bash

# Family Assistant Test Runner
# Comprehensive test execution script for local development

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_CMD="python3"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$PROJECT_DIR/tests"
REPORTS_DIR="$PROJECT_DIR/reports"

# Create necessary directories
mkdir -p "$REPORTS_DIR"/{pytest,coverage}

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
check_dependencies() {
    print_status "Checking dependencies..."

    if ! command_exists "$PYTHON_CMD"; then
        print_error "Python 3 is required but not installed."
        exit 1
    fi

    if ! command_exists "pip"; then
        print_error "pip is required but not installed."
        exit 1
    fi

    # Check if required packages are installed
    if ! $PYTHON_CMD -c "import pytest" 2>/dev/null; then
        print_warning "pytest not found. Installing test dependencies..."
        pip install -r requirements-test.txt
    fi

    print_success "Dependencies check completed"
}

# Function to run specific test suite
run_test_suite() {
    local suite_name=$1
    local test_path=$2
    local additional_args=$3

    print_status "Running $suite_name..."

    cd "$PROJECT_DIR"

    if [ ! -d "$test_path" ]; then
        print_warning "Test directory $test_path not found, skipping..."
        return 0
    fi

    if $PYTHON_CMD -m pytest "$test_path" -v $additional_args --html="$REPORTS_DIR/pytest/${suite_name,,}_report.html" --self-contained-html; then
        print_success "$suite_name passed"
        return 0
    else
        print_error "$suite_name failed"
        return 1
    fi
}

# Function to run coverage analysis
run_coverage() {
    print_status "Running tests with coverage analysis..."

    cd "$PROJECT_DIR"

    if $PYTHON_CMD -m pytest \
        --cov=api \
        --cov=agents \
        --cov=config \
        --cov-report=html:"$REPORTS_DIR/coverage" \
        --cov-report=term-missing \
        --cov-report=xml:"$REPORTS_DIR/coverage/coverage.xml" \
        --cov-fail-under=80 \
        --html="$REPORTS_DIR/pytest/coverage_report.html" \
        --self-contained-html; then
        print_success "Coverage analysis completed"
        print_status "Coverage report available at: $REPORTS_DIR/coverage/index.html"
    else
        print_error "Coverage analysis failed or below threshold"
        return 1
    fi
}

# Function to run quality checks
run_quality_checks() {
    print_status "Running code quality checks..."

    local failed_checks=0

    # Lint with ruff
    if command_exists "ruff"; then
        print_status "Running ruff linter..."
        if ! ruff check .; then
            print_error "Ruff linting failed"
            ((failed_checks++))
        fi
    else
        print_warning "ruff not found, skipping linting"
    fi

    # Type checking with mypy
    if command_exists "mypy"; then
        print_status "Running mypy type checking..."
        if ! mypy .; then
            print_error "MyPy type checking failed"
            ((failed_checks++))
        fi
    else
        print_warning "mypy not found, skipping type checking"
    fi

    # Security check with bandit
    if command_exists "bandit"; then
        print_status "Running bandit security check..."
        if ! bandit -r . -f json -o "$REPORTS_DIR/bandit_report.json"; then
            print_warning "Bandit found security issues (review report)"
        fi
    else
        print_warning "bandit not found, skipping security check"
    fi

    if [ $failed_checks -eq 0 ]; then
        print_success "All quality checks passed"
    else
        print_error "$failed_checks quality check(s) failed"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Family Assistant Test Runner"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  all              Run complete test suite (unit + integration + coverage)"
    echo "  unit             Run unit tests only"
    echo "  integration      Run integration tests only"
    echo "  e2e              Run end-to-end tests only"
    echo "  coverage         Run tests with coverage analysis"
    echo "  quality          Run code quality checks only"
    echo "  fast             Run fast tests only (no e2e, no external services)"
    echo "  watch            Run tests in watch mode"
    echo "  clean            Clean test artifacts and reports"
    echo "  setup            Setup test environment"
    echo "  help             Show this help message"
    echo ""
    echo "Options:"
    echo "  -v, --verbose    Enable verbose output"
    echo "  -q, --quiet      Suppress non-error output"
    echo "  --no-coverage    Skip coverage analysis"
    echo "  --no-quality     Skip quality checks"
    echo ""
    echo "Examples:"
    echo "  $0 all                    # Run all tests with coverage"
    echo "  $0 unit --verbose         # Run unit tests with verbose output"
    echo "  $0 fast                   # Run fast tests only"
    echo "  $0 quality                # Run quality checks only"
}

# Function to clean up artifacts
clean_artifacts() {
    print_status "Cleaning test artifacts and reports..."

    # Remove Python cache files
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

    # Remove pytest cache
    rm -rf .pytest_cache 2>/dev/null || true

    # Remove coverage files
    rm -f .coverage 2>/dev/null || true

    # Remove mypy cache
    rm -rf .mypy_cache 2>/dev/null || true

    # Remove reports directory
    if [ -d "$REPORTS_DIR" ]; then
        rm -rf "$REPORTS_DIR"
    fi

    print_success "Cleanup completed"
}

# Function to setup test environment
setup_environment() {
    print_status "Setting up test environment..."

    # Install dependencies
    if [ -f "requirements.txt" ]; then
        print_status "Installing production dependencies..."
        pip install -r requirements.txt
    fi

    if [ -f "requirements-test.txt" ]; then
        print_status "Installing test dependencies..."
        pip install -r requirements-test.txt
    fi

    # Setup pre-commit hooks if available
    if command_exists "pre-commit"; then
        print_status "Setting up pre-commit hooks..."
        pre-commit install
    fi

    print_success "Environment setup completed"
}

# Function to run tests in watch mode
run_watch_mode() {
    print_status "Starting test watch mode..."
    print_status "Press Ctrl+C to stop watching"

    cd "$PROJECT_DIR"

    if command_exists "watchdog"; then
        watchmedo shell-command --patterns="*.py" --recursive --command='clear && echo "Running tests..." && pytest tests/unit -v'
    else
        # Fallback to pytest watch if available
        if $PYTHON_CMD -m pytest --version | grep -q "watch"; then
            $PYTHON_CMD -m pytest tests/ -f
        else
            print_error "watchdog not installed and pytest watch not available"
            print_status "Install with: pip install watchdog"
            exit 1
        fi
    fi
}

# Main execution logic
main() {
    local command=${1:-help}
    local verbose=false
    local quiet=false
    local no_coverage=false
    local no_quality=false
    local additional_args=""

    # Parse options
    shift
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--verbose)
                verbose=true
                additional_args="$additional_args -v"
                shift
                ;;
            -q|--quiet)
                quiet=true
                additional_args="$additional_args -q"
                shift
                ;;
            --no-coverage)
                no_coverage=true
                shift
                ;;
            --no-quality)
                no_quality=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Set verbosity
    if [ "$quiet" = true ]; then
        exec 1>/dev/null
    elif [ "$verbose" = true ]; then
        additional_args="$additional_args -v"
    fi

    # Check dependencies
    check_dependencies

    # Execute command
    case $command in
        all)
            print_status "Running complete test suite..."
            local exit_code=0

            run_test_suite "Unit Tests" "$TEST_DIR/unit" "$additional_args" || exit_code=1
            run_test_suite "Integration Tests" "$TEST_DIR/integration" "$additional_args" || exit_code=1

            if [ "$no_coverage" = false ]; then
                run_coverage || exit_code=1
            fi

            if [ "$no_quality" = false ]; then
                run_quality_checks || exit_code=1
            fi

            if [ $exit_code -eq 0 ]; then
                print_success "All tests and checks passed!"
            else
                print_error "Some tests or checks failed"
                exit $exit_code
            fi
            ;;
        unit)
            run_test_suite "Unit Tests" "$TEST_DIR/unit" "$additional_args"
            ;;
        integration)
            run_test_suite "Integration Tests" "$TEST_DIR/integration" "$additional_args"
            ;;
        e2e)
            run_test_suite "End-to-End Tests" "$TEST_DIR/e2e" "$additional_args"
            ;;
        coverage)
            run_coverage
            ;;
        quality)
            run_quality_checks
            ;;
        fast)
            print_status "Running fast tests only..."
            run_test_suite "Fast Tests" "$TEST_DIR" "$additional_args -m 'not slow and not external'"
            ;;
        watch)
            run_watch_mode
            ;;
        clean)
            clean_artifacts
            ;;
        setup)
            setup_environment
            ;;
        help)
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"