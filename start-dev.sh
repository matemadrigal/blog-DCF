#!/bin/bash

# DCF Valuation Platform v2.0 - Development Startup Script
# This script starts both the FastAPI backend and Next.js frontend

echo "🚀 Starting DCF Valuation Platform v2.0..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo "📦 Activating Python virtual environment..."
source venv/bin/activate

# Check if backend dependencies are installed
if ! pip show fastapi &> /dev/null; then
    echo -e "${YELLOW}⚠️  Backend dependencies not installed. Installing...${NC}"
    pip install -r requirements-api.txt
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Frontend dependencies not installed. Installing...${NC}"
    cd frontend
    npm install
    cd ..
fi

# Check if .env files exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Copying from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file. Please update with your API keys if needed.${NC}"
fi

if [ ! -f "frontend/.env.local" ]; then
    echo -e "${YELLOW}⚠️  frontend/.env.local file not found. Creating...${NC}"
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > frontend/.env.local
    echo -e "${GREEN}✅ Created frontend/.env.local file.${NC}"
fi

# Generate companies.json if it doesn't exist
if [ ! -f "data/companies.json" ]; then
    echo -e "${YELLOW}⚠️  companies.json not found. Generating...${NC}"
    python3 scripts/convert_companies_to_json.py
fi

echo ""
echo -e "${GREEN}✅ All checks passed!${NC}"
echo ""
echo "Starting services..."
echo ""

# Function to kill background processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup EXIT INT TERM

# Start backend
echo -e "${GREEN}🔧 Starting FastAPI backend on http://localhost:8000${NC}"
python3 -m uvicorn api.main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend
echo -e "${GREEN}🎨 Starting Next.js frontend on http://localhost:3000${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo -e "${GREEN}✅ Services started successfully!${NC}"
echo ""
echo "📱 Access the application:"
echo "   - Frontend:  http://localhost:3000"
echo "   - API:       http://localhost:8000"
echo "   - API Docs:  http://localhost:8000/api/docs"
echo "   - Health:    http://localhost:8000/api/health"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait
