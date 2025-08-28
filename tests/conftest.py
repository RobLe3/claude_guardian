"""
Pytest configuration and shared fixtures for Claude Guardian tests
"""

import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient

from claude_guardian.main import create_app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def app():
    """Create a test FastAPI application instance."""
    return create_app()


@pytest.fixture
async def client(app) -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
async def db_session():
    """Create a test database session."""
    # TODO: Implement test database session
    pass


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    # TODO: Implement mock settings
    pass