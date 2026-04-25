"""
TeXTile Backend Test Suite

This package contains comprehensive unit, integration, and E2E tests for the TeXTile backend.

Test Organization:
- unit/: Service and utility function tests (mocked dependencies)
- integration/: Router and API endpoint tests (with real database)
- e2e/: End-to-end workflow tests (complete user journeys)

Running Tests:
- pytest                          # Run all tests
- pytest --cov=app              # With coverage report
- pytest -v                      # Verbose output
- pytest -k test_auth           # Specific tests
- pytest tests/unit/            # Specific directory
"""
