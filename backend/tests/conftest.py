"""
Pytest Configuration and Fixtures for TeXTile Backend Tests

This file provides shared fixtures and configuration for all backend tests.
Covers database setup, authentication, test clients, and mock services.
"""

import json
import os
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Import application modules
from app.config import Settings
from app.database import Base, get_db
from app.db_models import ProfileDB, ResumeVariantDB, UserDB
from app.main import app
from app.services.auth_service import AuthService


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def test_settings():
    """Create test settings with in-memory SQLite database"""
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test-secret-key-not-for-production",
        cors_origins="http://localhost:3000",
        tectonic_path="/tmp/fake-tectonic",
        access_token_expire_hours=1,
    )


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create an in-memory SQLite database engine for testing"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test"""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        # Rollback to ensure isolation between tests
        await session.rollback()


@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency with test database"""
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


# ============================================================================
# Client Fixtures
# ============================================================================


@pytest.fixture
def client(override_get_db):
    """Synchronous TestClient for basic HTTP testing"""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Asynchronous AsyncClient for testing async endpoints"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ============================================================================
# User and Authentication Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def test_user(db_session) -> UserDB:
    """Create a test user in the database"""
    user = UserDB(
        id=str(uuid4()),
        email="test@example.com",
        name="Test User",
        hashed_password=AuthService.hash_password("TestPassword123!"),
        created_at=None,
        updated_at=None,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user_2(db_session) -> UserDB:
    """Create a second test user for multi-user scenarios"""
    user = UserDB(
        id=str(uuid4()),
        email="user2@example.com",
        name="Second User",
        hashed_password=AuthService.hash_password("Password456!"),
        created_at=None,
        updated_at=None,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def test_token(test_user):
    """Generate a valid JWT token for a test user"""
    return AuthService.create_access_token(user_id=test_user.id)


@pytest.fixture
def auth_headers(test_token):
    """Create authorization headers with a valid token"""
    return {"Authorization": f"Bearer {test_token}"}


@pytest.fixture
def client_with_auth(client, auth_headers):
    """TestClient with authentication headers pre-configured"""
    client.headers.update(auth_headers)
    return client


@pytest_asyncio.fixture
async def async_client_with_auth(async_client, auth_headers):
    """AsyncClient with authentication headers pre-configured"""
    async_client.headers.update(auth_headers)
    return async_client


# ============================================================================
# Profile and Resume Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def test_profile(db_session, test_user) -> ProfileDB:
    """Create a test profile for a user"""
    profile_data = {
        "header": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1-555-0100",
            "location": "San Francisco, CA",
        },
        "experiences": [
            {
                "id": str(uuid4()),
                "company": "Tech Corp",
                "position": "Senior Engineer",
                "start_date": "2020-01-15",
                "end_date": "2023-12-31",
                "bullets": ["Led team of 5 engineers", "Improved performance by 40%"],
            },
            {
                "id": str(uuid4()),
                "company": "StartUp Inc",
                "position": "Junior Engineer",
                "start_date": "2018-06-01",
                "end_date": "2020-01-14",
                "bullets": ["Built REST APIs", "Implemented database optimizations"],
            },
        ],
        "education": [
            {
                "id": str(uuid4()),
                "school": "MIT",
                "degree": "BS Computer Science",
                "graduation_date": "2018-05-31",
                "bullets": ["GPA: 3.8", "President of CS Club"],
            },
        ],
        "projects": [
            {
                "id": str(uuid4()),
                "name": "Resume Editor",
                "link": "https://github.com/example/resume-editor",
                "bullets": [
                    "Built full-stack resume editor with LaTeX rendering",
                    "50K+ monthly active users",
                ],
            },
        ],
        "skills": [
            "Python",
            "FastAPI",
            "React",
            "TypeScript",
            "PostgreSQL",
            "LaTeX",
        ],
    }

    profile = ProfileDB(
        id=str(uuid4()),
        user_id=test_user.id,
        data=profile_data,
        created_at=None,
        updated_at=None,
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    return profile


@pytest_asyncio.fixture
async def test_variant(db_session, test_user, test_profile) -> ResumeVariantDB:
    """Create a test resume variant"""
    variant_data = {
        "selected_experiences": [test_profile.data["experiences"][0]["id"]],
        "selected_education": [test_profile.data["education"][0]["id"]],
        "selected_projects": [test_profile.data["projects"][0]["id"]],
        "selected_skills": ["Python", "FastAPI", "React"],
        "section_order": ["header", "experiences", "education", "skills", "projects"],
        "sections": {
            "header": {"visible": True},
            "experiences": {"visible": True},
            "education": {"visible": True},
            "skills": {"visible": True},
            "projects": {"visible": True},
        },
    }

    variant = ResumeVariantDB(
        id=str(uuid4()),
        user_id=test_user.id,
        profile_id=test_profile.id,
        template_id="jake_classic",
        name="Professional Resume",
        data=variant_data,
        created_at=None,
        updated_at=None,
    )
    db_session.add(variant)
    await db_session.commit()
    await db_session.refresh(variant)
    return variant


@pytest_asyncio.fixture
async def empty_profile(db_session, test_user) -> ProfileDB:
    """Create an empty profile for testing initialization"""
    profile = ProfileDB(
        id=str(uuid4()),
        user_id=test_user.id,
        data={"header": {}, "experiences": [], "education": [], "projects": [], "skills": []},
        created_at=None,
        updated_at=None,
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    return profile


# ============================================================================
# Mock Service Fixtures
# ============================================================================


@pytest.fixture
def mock_tectonic(monkeypatch):
    """Mock the Tectonic LaTeX compiler"""
    def mock_compile_pdf(latex_content: str, timeout: int = 30) -> bytes:
        # Return minimal valid PDF bytes
        return b"%PDF-1.4\n%test pdf\nendobj\n"

    # Monkeypatch the latex service compile method
    from app.services import latex_service
    monkeypatch.setattr(latex_service, "compile_pdf_with_tectonic", mock_compile_pdf)


@pytest.fixture
def mock_ollama(monkeypatch):
    """Mock the Ollama AI service"""
    def mock_improve_text(text: str, context: str = "") -> str:
        return f"Improved: {text}"

    # Monkeypatch the AI service
    from app.services import ai_service
    monkeypatch.setattr(ai_service, "improve_text_with_ai", mock_improve_text)


@pytest.fixture
def mock_pdf_parser(monkeypatch):
    """Mock PDF parser to avoid file I/O"""
    def mock_parse_pdf(pdf_content: bytes) -> dict:
        return {
            "header": {"name": "John Doe", "email": "john@example.com"},
            "experiences": [{"company": "Test Corp", "position": "Engineer"}],
            "education": [{"school": "Test University"}],
        }

    from app.services import pdf_parser_service
    monkeypatch.setattr(pdf_parser_service, "parse_pdf", mock_parse_pdf)


@pytest.fixture
def mock_latex_parser(monkeypatch):
    """Mock LaTeX parser"""
    def mock_parse_latex(latex_content: str) -> dict:
        return {
            "header": {"name": "John Doe"},
            "experiences": [{"company": "Test Corp"}],
        }

    from app.services import latex_parser_service
    monkeypatch.setattr(latex_parser_service, "parse_latex", mock_parse_latex)


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture
def sample_latex_resume() -> str:
    """Sample LaTeX resume content for testing"""
    return r"""
\documentclass{article}
\usepackage[utf-8]{inputenc}

\title{John Doe's Resume}
\author{john@example.com}

\begin{document}

\section*{Experience}
\subsection*{Tech Corp}
Senior Engineer (2020-2023)
\begin{itemize}
    \item Led team of 5 engineers
    \item Improved performance by 40\%
\end{itemize}

\section*{Education}
\subsection*{MIT}
BS Computer Science (2018)

\end{document}
"""


@pytest.fixture
def sample_profile_json() -> dict:
    """Sample profile data as JSON"""
    return {
        "header": {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "+1-555-0200",
        },
        "experiences": [
            {
                "company": "TechCorp",
                "position": "Principal Engineer",
                "start_date": "2021-01-01",
                "end_date": None,
                "bullets": ["Architected microservices", "Led hiring team"],
            }
        ],
        "education": [
            {"school": "Stanford", "degree": "MS CS", "graduation_date": "2019-06-15"}
        ],
        "projects": [],
        "skills": ["Python", "Go", "Kubernetes"],
    }


# ============================================================================
# Utility Fixtures
# ============================================================================


@pytest.fixture
def clear_database(db_session):
    """Fixture to clear all database tables"""
    async def _clear():
        # Delete all records in order of foreign key dependencies
        await db_session.query(ResumeVariantDB).delete()
        await db_session.query(ProfileDB).delete()
        await db_session.query(UserDB).delete()
        await db_session.commit()

    return _clear


# ============================================================================
# Autouse Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def reset_app_state():
    """Reset FastAPI app state between tests"""
    yield
    # Clear any cached app state if needed
    app.dependency_overrides.clear()
