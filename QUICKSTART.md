# TeXTile - Quick Start Guide

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Python 3.10+
- Node.js 18+
- That's it! No database server needed!

---

## Backend Setup

```bash
# Navigate to backend
cd backend

# Create & activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
uvicorn app.main:app --reload

# ✅ Backend is now running at http://localhost:8000
# 📚 API documentation at http://localhost:8000/docs
```

**What happens on first run:**
- SQLite database `textile.db` is created automatically
- All tables are initialized
- Server is ready to handle requests

---

## Frontend Setup

**In a new terminal:**

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev

# ✅ Frontend is now running at http://localhost:3000
```

---

## Testing the Application

### 1. Open the Web Interface
- Go to http://localhost:3000

### 2. Create an Account
- Click "Sign Up"
- Enter email and password
- Click "Create Account"

### 3. Create a Resume
- Fill in your profile information
- Add experiences, education, projects, skills
- Create a resume variant
- Preview and download as PDF

### 4. Test Drag & Drop
- Reorder sections using drag and drop
- Customize section visibility
- Change templates

---

## Environment Configuration

The `.env` file in `backend/` contains all configuration:

```env
# Database - LOCAL SQLite (no server needed!)
DATABASE_URL=sqlite+aiosqlite:///./textile.db

# Security
SECRET_KEY=change-me-to-a-random-secret-key

# CORS - allows frontend to connect
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# LaTeX Compiler
TECTONIC_PATH=/path/to/tectonic/binary

# Optional: AI Resume Parsing (requires Ollama)
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama3.2:3b
```

---

## Database

**Where is my data stored?**
- File: `backend/textile.db`
- Format: SQLite (single local file)
- Data persists automatically

**Backing up:**
```bash
# Copy the database file to backup
cp backend/textile.db backend/textile.db.backup
```

**Resetting (deletes all data):**
```bash
# Remove the database file
rm backend/textile.db

# Database recreates on next app start
```

---

## Common Tasks

### Accessing API Documentation
```
http://localhost:8000/docs
```
Interactive Swagger UI - test all endpoints here

### Registering Test User (via curl)
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

### Logging In
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

### Running Tests
```bash
cd backend
pytest
```

---

## Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Error**: `CORS error from frontend`
```bash
# Solution: Verify CORS_ORIGINS in .env includes frontend URL
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**Error**: `Tectonic not found`
```bash
# Solution: Set correct path in .env
TECTONIC_PATH=/absolute/path/to/tectonic/binary
```

### Frontend won't connect to backend

**Error**: `Network error` or `Failed to fetch`
```bash
# Solution: Ensure backend is running on port 8000
# Terminal 1: cd backend && uvicorn app.main:app --reload
# Terminal 2: cd frontend && npm run dev
```

### Database issues

**Error**: `database is locked`
```bash
# Solution: Only one app instance should access database
# Kill other uvicorn processes:
pkill -f uvicorn
# Then restart: uvicorn app.main:app --reload
```

**Error**: `No such table`
```bash
# Solution: Database recreates on app startup
# Just restart the backend: uvicorn app.main:app --reload
```

---

## Development Tips

### Hot Reload
- **Backend**: Enabled by default with `--reload` flag
- **Frontend**: Enabled by default with `npm run dev`

### Debugging
```bash
# Backend with debug info
uvicorn app.main:app --reload --log-level debug

# Frontend with source maps (already enabled)
npm run dev
```

### Database Inspection
```bash
# Install sqlite3 CLI tool if not available
# View tables
sqlite3 backend/textile.db ".tables"

# View schema
sqlite3 backend/textile.db ".schema users"

# Run queries
sqlite3 backend/textile.db "SELECT COUNT(*) FROM users;"
```

---

## Project Structure

```
resumeeditor/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # SQLite setup
│   │   ├── db_models.py         # Database models
│   │   ├── routers/             # API endpoints
│   │   └── services/            # Business logic
│   ├── alembic/                 # Database migrations
│   ├── .env                     # Configuration file
│   ├── requirements.txt         # Python dependencies
│   └── textile.db               # SQLite database (auto-created)
│
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js app
│   │   ├── components/          # React components
│   │   └── lib/                 # Utilities
│   ├── package.json            # Node dependencies
│   └── tsconfig.json           # TypeScript config
│
└── docker-compose.yml          # Optional Docker config (not needed for SQLite)
```

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Create account
- `POST /api/v1/auth/login` - Login

### Profile
- `GET /api/v1/profile` - Get your profile
- `PUT /api/v1/profile` - Update profile
- `POST /api/v1/profile/import` - Import resume from file

### Resumes
- `GET /api/v1/variants` - List all resume variants
- `POST /api/v1/variants` - Create new variant
- `GET /api/v1/variants/{id}` - Get specific variant
- `PUT /api/v1/variants/{id}` - Update variant
- `DELETE /api/v1/variants/{id}` - Delete variant
- `POST /api/v1/variants/{id}/render` - Render to PDF

### Templates
- `GET /api/v1/templates` - List available templates
- `POST /api/v1/templates` - Create custom template

---

## Next Steps

1. ✅ **Start Development**
   - Follow the Backend Setup above
   - Follow the Frontend Setup above

2. 📝 **Create Your First Resume**
   - Open http://localhost:3000
   - Sign up for an account
   - Create a profile with your information

3. 🎨 **Customize**
   - Choose different templates
   - Reorder sections
   - Export as PDF

4. 🚀 **Deploy** (When Ready)
   - See MIGRATION_COMPLETE.md for deployment options
   - Single server deployment is easy with SQLite!

---

## Need Help?

- **API Docs**: http://localhost:8000/docs (interactive Swagger)
- **Issues**: Check backend console output for errors
- **Database**: Check `backend/textile.db` exists after first run

---

## What's New in This Version

✅ **Switched from PostgreSQL to SQLite**
- No database server needed
- Setup is simpler
- Perfect for single-server deployments
- Data stored locally in `textile.db`

✅ **Zero Code Changes**
- Application works exactly the same
- All features work identically
- Easy to switch back to PostgreSQL if needed

---

**Happy resume building! 🚀**
