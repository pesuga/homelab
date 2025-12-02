"""
Test suite for Family Assistant application.

This test suite provides comprehensive coverage for:
- Unit tests for individual components
- Integration tests for service interactions
- End-to-end tests for complete family workflows
- Multimodal content handling tests
- Telegram integration tests

Test Categories:
- unit: Fast tests for individual functions/classes
- integration: Tests for component interactions
- e2e: Complete workflow tests
- family: Family member interaction tests
- multimodal: Text/image/audio content tests
- telegram: Telegram-specific functionality
"""

import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))