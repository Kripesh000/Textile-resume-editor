# TeXTile - Resume Editor

A modern full-stack application for creating, editing, and rendering professional resumes with LaTeX-based styling and PDF export capabilities.

## Project Overview

TeXTile is a web-based resume editor that allows users to:
- Create and manage professional profiles with detailed career information
- Design multiple resume variants with customizable templates
- Import resume data from PDF or LaTeX files
- Render resumes to PDF with professional LaTeX templates
- Use drag-and-drop interfaces for content organization
- Support AI-powered resume parsing and improvement suggestions

## Tech Stack

### Backend
- **Framework**: FastAPI 0.115.0
- **Server**: Uvicorn 0.30.6
- **Database**: SQLite (local file-based, no server required) with SQLAlchemy 2.0.35
- **ORM**: SQLAlchemy with async support (aiosqlite)
- **LaTeX Compilation**: Tectonic 0.15.0
- **Template Engine**: Jinja2 3.1.4
- **Authentication**: JWT tokens with python-jose and bcrypt
- **PDF Parsing**: pdfplumber 0.11.4, PyMuPDF 1.24.10
- **Testing**: pytest 8.3.3, pytest-asyncio 0.24.0
- **Database Migrations**: Alembic 1.13.2

### Frontend
- **Framework**: Next.js 16.1.6
- **React**: 19.2.3
- **Styling**: Tailwind CSS 4
- **Drag & Drop**: @dnd-kit (DOM, React, Helpers)
- **Language**: TypeScript 5
- **Linting**: ESLint 9

### DevOps
- **Database**: SQLite (local file-based, no containerization needed)

## Architecture

### Backend Structure
```
backend/app/
├── routers/           # API endpoint handlers
│   ├── auth.py       # Authentication endpoints
│   ├── profile.py    # Profile CRUD and import
│   ├── variant_router.py  # Resume variant management and rendering
│   ├── template_router.py # Template management
│   └── ai.py         # AI-powered features
├── services/          # Business logic
│   ├── latex_service.py    # LaTeX rendering & PDF compilation
│   ├── profile_service.py  # Profile operations
│   ├── resume_service.py   # Resume build logic
│   ├── pdf_parser_service.py    # PDF parsing
│   ├── latex_parser_service.py  # LaTeX parsing
│   ├── ai_parser_service.py     # AI-based parsing
│   └── auth_service.py     # Authentication
├── schemas/           # Pydantic models for validation
├── templates/         # Jinja2 LaTeX templates
└── db_models.py      # SQLAlchemy database models
```

### Frontend Structure
```
frontend/src/
├── app/              # Next.js app directory
├── components/       # React components
├── context/          # React context for state management
├── hooks/            # Custom React hooks
└── lib/              # Utilities and helpers
```

## Key Features

1. **Resume Management**
   - Create multiple resume variants from a single profile
   - Support for experiences, projects, skills, and education
   - Customizable section ordering and visibility

2. **Template System**
   - Multiple built-in LaTeX templates (e.g., `jake_classic`)
   - Support for custom templates
   - Jinja2-based template rendering with safe variable injection

3. **Import Capabilities**
   - PDF resume parsing using pdfplumber and PyMuPDF
   - LaTeX resume parsing
   - AI-powered parsing using Ollama (llama3.2:3b)

4. **PDF Rendering**
   - Real-time LaTeX to PDF compilation
   - Professional styling via Tectonic compiler
   - Direct PDF download capability

5. **Authentication & Security**
   - User registration and login
   - JWT-based session management
   - Role-based access control

6. **UI/UX**
   - Drag-and-drop interface for section ordering
   - Real-time template preview
   - Responsive design with Tailwind CSS

## Challenges Faced

### 1. **Tectonic Binary Not Found (CRITICAL)**
**Problem**: When attempting to render resumes to PDF, the application threw:
```
FileNotFoundError: [Errno 2] No such file or directory: 'tectonic'
```

**Root Cause**: The `tectonic_path` configuration was set to just `"tectonic"` instead of an absolute path, and the binary wasn't in the system PATH.

**Solution**: 
- Located the tectonic binary in `frontend/tectonic` (pre-compiled Mach-O executable for arm64)
- Updated `.env` file with absolute path: `TECTONIC_PATH=/Users/kritikapandit/Downloads/resumeeditor/frontend/tectonic`
- The path is loaded via Pydantic Settings which reads from `.env` file

**Learning**: Always use absolute paths for external binary dependencies or ensure they're properly installed system-wide via package managers.

### 2. **LaTeX Template Flexibility**
**Challenge**: Supporting both directory-based templates (`template_key/template.tex.j2`) and flat-file templates (`template_key.tex.j2`)

**Solution**: Implemented fallback logic in template loading that tries directory structure first, then falls back to flat files.

### 3. **Resume Parsing Complexity**
**Challenge**: Different resume formats (PDF, LaTeX) have different extraction methods and require robust parsing

**Solution**: Multi-strategy approach:
- PDF parsing via pdfplumber + PyMuPDF
- LaTeX parsing with regex patterns
- AI-based parsing using Ollama for semantic extraction

### 4. **Async Database Operations**
**Challenge**: Managing async SQLAlchemy sessions across multiple routers and services

**Solution**: Dependency injection pattern via FastAPI's `Depends()` to provide `AsyncSession` to all endpoints

### 5. **CORS Configuration**
**Challenge**: Frontend and backend on different ports during development

**Solution**: Configured CORS middleware to accept requests from multiple origins specified in `.env`: `CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- macOS/Linux (Tectonic binary is included for arm64 architecture)

### Running the Backend (Local Development)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env — at minimum set TECTONIC_PATH to the absolute path of frontend/tectonic

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

SQLite database (`textile.db`) is created automatically on first run — no setup needed.

### Running the Frontend (Local Development)

```bash
cd frontend
npm install

# Configure environment
cp .env.local.example .env.local
# .env.local.example already points NEXT_PUBLIC_API_URL to http://localhost:8000

npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Backend Environment Variables (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./textile.db` | Database connection string |
| `SECRET_KEY` | *(must change)* | JWT signing secret — use `openssl rand -hex 32` |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Comma-separated exact allowed origins |
| `CORS_ALLOW_ORIGIN_REGEX` | `https://.*\.vercel\.app` | Regex for wildcard origins (Vercel previews) |
| `TECTONIC_PATH` | *(derived from repo)* | Absolute path to tectonic binary |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL (optional) |
| `OLLAMA_MODEL` | `llama3.2:3b` | Ollama model for AI parsing (optional) |
| `ACCESS_TOKEN_EXPIRE_HOURS` | `24` | JWT token lifetime |

---

## Deploy Backend to Render

1. Push the repository to GitHub.

2. Go to [render.com](https://render.com) → **New → Web Service** → connect your repo.

3. Configure the service:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. Set environment variables in the Render dashboard:

   | Key | Value |
   |---|---|
   | `SECRET_KEY` | *(generate with `openssl rand -hex 32`)* |
   | `DATABASE_URL` | `sqlite+aiosqlite:///./textile.db` (SQLite) or your PostgreSQL URL |
   | `CORS_ORIGINS` | `https://your-app.vercel.app` (your production Vercel URL) |
   | `CORS_ALLOW_ORIGIN_REGEX` | `https://.*\.vercel\.app` |
   | `TECTONIC_PATH` | Path to tectonic binary on the server |

   > **SQLite note**: Render's free tier uses an ephemeral filesystem — the SQLite database
   > resets on every deploy. For persistent data, either add a **Render Disk** (paid) or
   > switch to PostgreSQL by changing `DATABASE_URL` to `postgresql+asyncpg://...` (the
   > `asyncpg` driver is already in `requirements.txt`).

   > **Tectonic note**: The `frontend/tectonic` binary is macOS arm64 only and will not run
   > on Render (Linux). Install tectonic on the server:
   > ```bash
   > curl --proto '=https' --tlsv1.2 -fsSL https://drop.example.com/tectonic/install.sh | sh
   > ```
   > Then set `TECTONIC_PATH` to the installed binary path.

5. Deploy. Your backend URL will be `https://your-service-name.onrender.com`.

   Test it: `curl https://your-service-name.onrender.com/api/health`

---

## Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com) → **New Project** → import your GitHub repo.

2. Set the **Root Directory** to `frontend`.

3. Add the environment variable in the Vercel dashboard:

   | Key | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://your-service-name.onrender.com` |

   > This is the Render backend URL from the previous step.

4. Deploy. Vercel auto-detects Next.js and runs `npm run build` + `npm start`.

5. Once deployed, update `CORS_ORIGINS` on Render to include your Vercel production URL:
   ```
   CORS_ORIGINS=https://your-app.vercel.app
   ```

---

## Verify End-to-End Connectivity

After both services are deployed:

```bash
# 1. Health check
curl https://your-service-name.onrender.com/api/health
# Expected: {"status":"ok"}

# 2. Register a user from the frontend and confirm no CORS errors in browser devtools
# 3. Check the Network tab — all /api/v1/* calls should go to the Render URL
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token

### Profile
- `GET /api/v1/profile` - Get user's profile
- `PUT /api/v1/profile` - Update user's profile
- `POST /api/v1/profile/import` - Import resume from PDF/LaTeX

### Resume Variants
- `GET /api/v1/variants` - List all resume variants
- `POST /api/v1/variants` - Create new variant
- `GET /api/v1/variants/{id}` - Get specific variant
- `PUT /api/v1/variants/{id}` - Update variant
- `DELETE /api/v1/variants/{id}` - Delete variant
- `POST /api/v1/variants/{id}/render` - Render variant to PDF

### Templates
- `GET /api/v1/templates` - List available templates
- `POST /api/v1/templates` - Create custom template

### Health
- `GET /api/health` - Health check

## Testing

```bash
cd backend
pytest tests/
pytest --asyncio-mode=auto tests/
```

## Database Schema

### Users (UserDB)
- id, email, hashed_password, name, created_at, updated_at

### Profiles (ProfileDB)
- id, user_id, data (JSON: experiences, projects, skills, education, etc.)

### Resume Variants (ResumeVariantDB)
- id, user_id, profile_id, template_id, name, data (JSON: selected items, section order, etc.)

## Notable Implementation Details

1. **Stateless Resume Parsing**: Multi-format parser that doesn't require server state
2. **Jinja2 Safety**: Custom delimiters (`\VAR{}`, `\BLOCK{}`) prevent LaTeX conflicts
3. **Async-First Backend**: All database operations are async for better performance
4. **Template System**: Supports both built-in and custom LaTeX templates with Jinja2
5. **PDF Compilation**: 30-second timeout on LaTeX compilation with proper error handling

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Tectonic not found | Ensure `TECTONIC_PATH` in `.env` points to correct binary |
| Database file not found | Check `DATABASE_URL` in `.env` - SQLite creates `textile.db` automatically on first run |
| LaTeX compilation timeouts | Check template for infinite loops; increase timeout in `latex_service.py` |
| CORS errors | Verify `CORS_ORIGINS` includes your frontend URL |
| Import parsing fails | Check file format (PDF/LaTeX) and ensure parsers are installed |

## Future Enhancements

- [ ] Real-time collaborative editing
- [ ] More built-in templates and customization options
- [ ] Cloud storage integration for resumes
- [ ] Advanced analytics on resume performance
- [ ] Integration with ATS systems
- [ ] Version history and rollback

## Contributing

1. Create a feature branch
2. Make changes with tests
3. Ensure all tests pass
4. Submit PR with description

