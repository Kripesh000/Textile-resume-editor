# TeXTile Testing Strategy - 100% Coverage Implementation Guide

**Status**: 🚀 **IMPLEMENTATION IN PROGRESS**
**Target Coverage**: 100% (Line, Branch, Function, Statement)
**Estimated Effort**: 40-50 hours total
**Timeline**: 4-5 weeks

---

## Executive Summary

This document outlines the complete strategy for implementing 100% test coverage across the TeXTile backend (FastAPI + SQLAlchemy) and frontend (Next.js + React).

### Current State
- **Backend**: 7 scattered integration tests (~0.2% coverage)
- **Frontend**: 0 tests, 0% coverage
- **Testing Framework**: pytest 8.3.3, pytest-asyncio (backend only)
- **No Frontend Test Infrastructure**: Need to setup Jest/Vitest from scratch

### Target State
- **Backend**: 100+ unit/integration/E2E tests across 20+ test files
- **Frontend**: 60+ component/hook/util tests across 15+ test files
- **Coverage**: All functions, branches, statements tested
- **Infrastructure**: pytest-cov, Jest/Vitest with coverage reports
- **CI/CD Ready**: Coverage thresholds enforced

---

## Implementation Roadmap

### Phase 1: Backend Infrastructure (Week 1)
**Deliverables**: pytest.ini, conftest.py, fixtures, dependencies

### Phase 2: Backend Unit Tests (Weeks 2-3)
**Deliverables**: Service layer tests (100+ tests), 60% coverage

### Phase 3: Backend Integration/E2E (Week 3-4)
**Deliverables**: Router tests, E2E workflows, 95%+ coverage

### Phase 4: Frontend Infrastructure (Week 4)
**Deliverables**: Jest/Vitest setup, testing library config

### Phase 5: Frontend Tests (Week 5)
**Deliverables**: Component and hook tests, 100% coverage

### Phase 6: Reporting & CI/CD (Week 5+)
**Deliverables**: Coverage reports, thresholds, GitHub Actions

---

## Backend Testing Strategy

### Test Organization Structure
```
backend/
├── tests/                          # Main test directory
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures
│   ├── fixtures/
│   │   ├── __init__.py
│   │   ├── db.py                   # Database fixtures
│   │   ├── users.py                # User/auth fixtures
│   │   └── resumes.py              # Resume fixtures
│   ├── unit/
│   │   ├── test_auth_service.py
│   │   ├── test_profile_service.py
│   │   ├── test_latex_service.py
│   │   ├── test_resume_service.py
│   │   ├── test_pdf_parser_service.py
│   │   ├── test_latex_parser_service.py
│   │   ├── test_template_service.py
│   │   ├── test_ai_service.py
│   │   ├── test_models.py
│   │   └── test_config.py
│   ├── integration/
│   │   ├── test_auth_router.py
│   │   ├── test_profile_router.py
│   │   ├── test_variant_router.py
│   │   ├── test_template_router.py
│   │   └── test_database.py
│   └── e2e/
│       ├── test_user_signup_flow.py
│       ├── test_resume_creation_flow.py
│       ├── test_resume_import_flow.py
│       └── test_concurrent_operations.py
├── pytest.ini
├── conftest.py
└── requirements.txt
```

### Test Files to Create (20 files, 200+ tests)

#### Infrastructure Files
1. **pytest.ini** - Pytest configuration
2. **conftest.py** (root) - Root-level fixtures
3. **tests/conftest.py** - Shared test fixtures

#### Unit Tests (10 files)
1. **tests/unit/test_auth_service.py** - 12 tests
2. **tests/unit/test_profile_service.py** - 14 tests
3. **tests/unit/test_latex_service.py** - 16 tests
4. **tests/unit/test_resume_service.py** - 14 tests
5. **tests/unit/test_pdf_parser_service.py** - 12 tests
6. **tests/unit/test_latex_parser_service.py** - 12 tests
7. **tests/unit/test_template_service.py** - 10 tests
8. **tests/unit/test_ai_service.py** - 10 tests
9. **tests/unit/test_models.py** - 20 tests
10. **tests/unit/test_config.py** - 8 tests

#### Integration Tests (5 files)
1. **tests/integration/test_auth_router.py** - 14 tests
2. **tests/integration/test_profile_router.py** - 16 tests
3. **tests/integration/test_variant_router.py** - 18 tests
4. **tests/integration/test_template_router.py** - 12 tests
5. **tests/integration/test_database.py** - 10 tests

#### E2E Tests (4 files)
1. **tests/e2e/test_user_signup_flow.py** - 6 tests
2. **tests/e2e/test_resume_creation_flow.py** - 8 tests
3. **tests/e2e/test_resume_import_flow.py** - 6 tests
4. **tests/e2e/test_concurrent_operations.py** - 4 tests

**Total Backend Tests**: ~200 tests across 20+ files

### Dependencies to Add

```bash
# pytest plugins
pytest-cov==4.1.0           # Coverage reporting
pytest-mock==3.14.0         # Mocking support
pytest-timeout==2.2.0       # Timeout protection
pytest-xdist==3.5.0         # Parallel test execution

# Testing utilities
faker==24.0.0               # Fake data generation
factory-boy==3.3.0          # Object factories

# Code quality
coverage==7.4.0             # Coverage analysis
```

### Backend Coverage Targets

| Metric | Target | Threshold |
|--------|--------|-----------|
| Line Coverage | 100% | ≥98% |
| Branch Coverage | 100% | ≥95% |
| Function Coverage | 100% | ≥99% |
| Statement Coverage | 100% | ≥98% |

### Test Execution

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_auth_service.py

# Run with parallelization
pytest -n auto

# Run with verbose output
pytest -v

# Run with timeout
pytest --timeout=30
```

---

## Frontend Testing Strategy

### Test Organization Structure
```
frontend/
├── jest.config.ts          # Jest configuration
├── jest.setup.ts           # Jest setup/globals
├── src/
│   ├── __tests__/
│   │   ├── setup.ts        # Test utilities
│   │   ├── unit/
│   │   │   ├── hooks/
│   │   │   │   ├── useResume.test.ts
│   │   │   │   ├── useProfile.test.ts
│   │   │   │   └── useDebounce.test.ts
│   │   │   ├── lib/
│   │   │   │   ├── api.test.ts
│   │   │   │   └── types.test.ts
│   │   │   └── context/
│   │   │       └── AuthContext.test.tsx
│   │   ├── components/
│   │   │   ├── Editor/
│   │   │   │   ├── EditorShell.test.tsx
│   │   │   │   ├── TileList.test.tsx
│   │   │   │   ├── Tile.test.tsx
│   │   │   │   └── fields/
│   │   │   │       ├── HeaderFields.test.tsx
│   │   │   │       ├── ExperienceFields.test.tsx
│   │   │   │       ├── EducationFields.test.tsx
│   │   │   │       ├── ProjectFields.test.tsx
│   │   │   │       ├── SkillsFields.test.tsx
│   │   │   │       └── GenericFields.test.tsx
│   │   │   ├── Preview/
│   │   │   │   └── PdfPreview.test.tsx
│   │   │   └── AI/
│   │   │       └── ImproviseButton.test.tsx
│   │   ├── pages/
│   │   │   ├── page.test.tsx       # Home
│   │   │   ├── editor.test.tsx     # Editor page
│   │   │   ├── login.test.tsx      # Login page
│   │   │   ├── register.test.tsx   # Register page
│   │   │   └── profile.test.tsx    # Profile page
│   │   └── integration/
│   │       ├── auth-flow.test.tsx
│   │       ├── editor-flow.test.tsx
│   │       └── import-flow.test.tsx
│   └── package.json
```

### Frontend Framework Selection: Jest

**Reasoning**:
- De-facto standard for React projects
- Excellent TypeScript support
- Works with Next.js out of the box
- Great coverage reporting
- Fast parallel execution

### Test Files to Create (20 files, 150+ tests)

#### Unit Tests (3 files)
1. **__tests__/unit/hooks/useResume.test.ts** - 12 tests
2. **__tests__/unit/hooks/useProfile.test.ts** - 12 tests
3. **__tests__/unit/hooks/useDebounce.test.ts** - 8 tests

#### Library Tests (2 files)
1. **__tests__/unit/lib/api.test.ts** - 30 tests (all API methods)
2. **__tests__/unit/lib/types.test.ts** - 8 tests

#### Context Tests (1 file)
1. **__tests__/unit/context/AuthContext.test.tsx** - 12 tests

#### Component Tests (14 files)
1. **__tests__/components/Editor/EditorShell.test.tsx** - 12 tests
2. **__tests__/components/Editor/TileList.test.tsx** - 10 tests
3. **__tests__/components/Editor/Tile.test.tsx** - 10 tests
4. **__tests__/components/Editor/fields/HeaderFields.test.tsx** - 8 tests
5. **__tests__/components/Editor/fields/ExperienceFields.test.tsx** - 10 tests
6. **__tests__/components/Editor/fields/EducationFields.test.tsx** - 10 tests
7. **__tests__/components/Editor/fields/ProjectFields.test.tsx** - 10 tests
8. **__tests__/components/Editor/fields/SkillsFields.test.tsx** - 8 tests
9. **__tests__/components/Editor/fields/GenericFields.test.tsx** - 8 tests
10. **__tests__/components/Preview/PdfPreview.test.tsx** - 10 tests
11. **__tests__/components/AI/ImproviseButton.test.tsx** - 8 tests
12. **__tests__/pages/page.test.tsx** - 8 tests (Home)
13. **__tests__/pages/editor.test.tsx** - 12 tests (Editor page)
14. **__tests__/pages/login.test.tsx** - 10 tests

#### Integration Tests (3 files)
1. **__tests__/integration/auth-flow.test.tsx** - 12 tests
2. **__tests__/integration/editor-flow.test.tsx** - 14 tests
3. **__tests__/integration/import-flow.test.tsx** - 10 tests

**Total Frontend Tests**: ~220+ tests across 20+ files

### Dependencies to Add

```bash
# Testing frameworks
jest@^29.0.0
@testing-library/react@^14.0.0
@testing-library/jest-dom@^6.1.4
@testing-library/user-event@^14.5.1
jest-environment-jsdom@^29.0.0

# TypeScript support
@types/jest@^29.5.0
ts-jest@^29.1.0

# Utilities
jest-mock-extended@^3.0.5
msw@^2.0.0           # Mock Service Worker for API mocking
faker@^8.0.0         # Fake data generation
```

### Frontend Coverage Targets

| Metric | Target | Threshold |
|--------|--------|-----------|
| Line Coverage | 100% | ≥98% |
| Branch Coverage | 100% | ≥95% |
| Function Coverage | 100% | ≥99% |
| Statement Coverage | 100% | ≥98% |

### Test Execution

```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Watch mode
npm test -- --watch

# Update snapshots
npm test -- -u

# Run specific file
npm test -- useResume.test.ts

# Run with parallel workers
npm test -- --maxWorkers=4
```

---

## Mocking Strategy

### Backend Mocking

#### External Dependencies to Mock
1. **Tectonic (LaTeX Compiler)** - Mock in tests to avoid system dependency
2. **Ollama (AI Service)** - Mock responses or skip tests if unavailable
3. **PDF Parsers** - Mock file reading
4. **File System** - Mock file I/O operations

#### Database Mocking
- Use in-memory SQLite (`sqlite:///:memory:`)
- Create fixtures for common objects
- Use rollback after each test for isolation

#### Mock Examples
```python
# Mock Tectonic binary
@pytest.fixture
def mock_tectonic(monkeypatch):
    def mock_compile(*args, **kwargs):
        return b'%PDF-1.4\n...'  # Minimal PDF bytes
    monkeypatch.setattr('app.services.latex_service.run_tectonic', mock_compile)
```

### Frontend Mocking

#### API Mocking
- Use Mock Service Worker (MSW) for intercepting API calls
- Mock all `/api/v1/*` endpoints
- Provide realistic response payloads

#### Component Mocking
- Mock Next.js router
- Mock next/image
- Mock external libraries (if any)

---

## Test Data Management

### Backend

#### Fixtures (conftest.py)
```python
@pytest.fixture
async def test_user(db_session):
    """Create a test user"""
    user = UserDB(id="test-user-1", email="test@example.com", ...)
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture
async def test_profile(db_session, test_user):
    """Create a test profile with experiences, education, etc."""
    profile = ProfileDB(user_id=test_user.id, data={...})
    db_session.add(profile)
    await db_session.commit()
    return profile
```

#### Test Resumes
- Sample PDF files for parser testing
- Sample LaTeX files for parser testing
- Various resume formats (simple, complex, edge cases)

### Frontend

#### Mock Data Factories
```typescript
// Create consistent test data
const mockUser = userFactory.build({
  email: 'test@example.com',
  name: 'John Doe'
});

const mockProfile = profileFactory.build({
  userId: mockUser.id,
  experiences: [
    experienceFactory.build(),
    experienceFactory.build()
  ]
});
```

---

## Coverage Reporting

### Backend Coverage Report
```bash
pytest --cov=app --cov-report=html --cov-report=term-missing

# Output: htmlcov/index.html
```

### Frontend Coverage Report
```bash
npm test -- --coverage

# Output: coverage/ directory with lcov reports
```

### Combined Report
- Generate both reports
- Track coverage over time
- Set up coverage badges for README

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Test Coverage

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: 3.10
      - run: pip install -r backend/requirements.txt
      - run: pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npm test -- --coverage
      - uses: codecov/codecov-action@v3
```

---

## Success Criteria

### Backend
- ✅ 100% line coverage
- ✅ ≥95% branch coverage
- ✅ All services tested
- ✅ All routers tested
- ✅ All error paths tested
- ✅ Concurrent operation safety verified
- ✅ Database integrity verified
- ✅ Tests run in <30 seconds

### Frontend
- ✅ 100% component coverage
- ✅ 100% hook coverage
- ✅ 100% utility coverage
- ✅ All user interactions tested
- ✅ All error states tested
- ✅ All loading states tested
- ✅ Responsive design verified
- ✅ Tests run in <20 seconds

### Overall
- ✅ >98% combined coverage
- ✅ All tests pass locally
- ✅ All tests pass in CI/CD
- ✅ Coverage reports generated
- ✅ No flaky tests
- ✅ Documentation complete

---

## Quick Reference

### Run Commands

```bash
# Backend
cd backend
pytest                          # Run all tests
pytest --cov=app              # With coverage
pytest -v                      # Verbose
pytest -k test_auth           # Specific tests
pytest tests/unit/            # Specific directory

# Frontend
cd frontend
npm test                        # Run all tests
npm test -- --coverage        # With coverage
npm test -- --watch           # Watch mode
npm test -- HeaderFields      # Specific component
```

### Test Examples

**Backend (pytest)**:
```python
@pytest.mark.asyncio
async def test_create_user_success(client, db_session):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "SecurePass123"}
    )
    assert response.status_code == 201
    assert "access_token" in response.json()
```

**Frontend (Jest)**:
```typescript
describe('EditorShell', () => {
  it('renders the editor with initial state', () => {
    render(<EditorShell />);
    expect(screen.getByRole('textbox', { name: /name/i })).toBeInTheDocument();
  });
});
```

---

## Next Steps

1. **Install dependencies** (both backend and frontend)
2. **Create infrastructure files** (conftest.py, jest.config.ts)
3. **Start writing unit tests** (services first, then components)
4. **Set up coverage reporting**
5. **Integrate with CI/CD**
6. **Monitor and maintain** coverage over time

---

**Document Version**: 1.0
**Last Updated**: March 25, 2026
**Maintainer**: Claude AI
**Status**: 🚀 Ready for Implementation
