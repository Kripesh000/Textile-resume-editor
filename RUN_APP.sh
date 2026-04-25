#!/bin/bash

# TeXTile Resume Editor - Local Setup & Run Script
# This script sets up and runs the TeXTile application locally
# Usage: ./RUN_APP.sh or bash RUN_APP.sh

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}→${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}        TeXTile Resume Editor - Local Setup${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Check Python
print_status "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION found"

# Check Node.js
print_status "Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    print_warning "Node.js is not installed. Frontend setup will skip."
    SKIP_FRONTEND=true
else
    NODE_VERSION=$(node --version)
    print_success "Node.js $NODE_VERSION found"
fi

echo ""
print_status "Setting up backend..."

# Navigate to backend directory
if [ ! -d "backend" ]; then
    print_error "backend directory not found. Run this script from the project root."
    exit 1
fi

cd backend

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv .venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source .venv/bin/activate
print_success "Virtual environment activated"

# Check if requirements are installed
print_status "Checking dependencies..."
if ! python -c "import fastapi" 2>/dev/null; then
    print_status "Installing dependencies (this may take a minute)..."
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    print_success "Dependencies installed"
else
    print_success "Dependencies already installed"
fi

# Check for .env file
if [ ! -f ".env" ]; then
    print_warning ".env file not found"
    if [ -f ".env.example" ]; then
        print_status "Creating .env from .env.example..."
        cp .env.example .env
        print_success ".env created (using defaults)"
    else
        print_status "Creating .env with default SQLite configuration..."
        cat > .env << 'EOF'
DATABASE_URL=sqlite+aiosqlite:///./textile.db
SECRET_KEY=change-me-to-a-random-secret-key
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
TECTONIC_PATH=../frontend/tectonic
ACCESS_TOKEN_EXPIRE_HOURS=24
EOF
        print_success ".env created with SQLite configuration"
    fi
else
    print_success ".env file exists"
fi

# Check database file
if [ -f "textile.db" ]; then
    print_success "SQLite database found (textile.db)"
else
    print_warning "SQLite database will be created on first run"
fi

echo ""
print_success "Backend setup complete!"
echo ""

# Return to root directory
cd ..

# Setup frontend if Node.js is available
if [ "$SKIP_FRONTEND" != "true" ]; then
    echo ""
    print_status "Setting up frontend..."

    if [ ! -d "frontend" ]; then
        print_error "frontend directory not found."
        exit 1
    fi

    cd frontend

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_status "Installing frontend dependencies..."
        npm install --silent
        print_success "Frontend dependencies installed"
    else
        print_success "Frontend dependencies already installed"
    fi

    cd ..
    print_success "Frontend setup complete!"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}            Setup Complete! Ready to Run${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Print next steps
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. Start the backend server (Terminal 1):"
echo "   cd backend"
echo "   source .venv/bin/activate  # or: .venv\\Scripts\\activate (Windows)"
echo "   uvicorn app.main:app --reload"
echo ""
echo "   The backend will be available at: http://localhost:8000"
echo "   API docs at: http://localhost:8000/docs"
echo ""

if [ "$SKIP_FRONTEND" != "true" ]; then
    echo "2. Start the frontend server (Terminal 2):"
    echo "   cd frontend"
    echo "   npm run dev"
    echo ""
    echo "   The frontend will be available at: http://localhost:3000"
    echo ""
    echo "3. Open your browser to http://localhost:3000"
else
    echo "2. Open your browser to http://localhost:8000/docs"
    echo "   Use the interactive API documentation to test endpoints"
fi

echo ""
echo "4. Create an account and start building your resume!"
echo ""
echo -e "${YELLOW}Note:${NC} The SQLite database (textile.db) is stored in backend/"
echo "      and persists across application restarts."
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
