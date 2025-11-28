#!/bin/bash

# Script to verify the project is ready for Vercel deployment
# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   DCF Valuation Platform - Deployment Check${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Function to print check result
check() {
    local name=$1
    local status=$2
    local message=$3

    if [ "$status" = "OK" ]; then
        echo -e "  ${GREEN}✓${NC} $name"
    elif [ "$status" = "WARN" ]; then
        echo -e "  ${YELLOW}⚠${NC} $name - $message"
        ((WARNINGS++))
    else
        echo -e "  ${RED}✗${NC} $name - $message"
        ((ERRORS++))
    fi
}

echo -e "${BLUE}Frontend Checks:${NC}"
echo "─────────────────"

# Check if frontend directory exists
if [ -d "frontend" ]; then
    check "Frontend directory exists" "OK"
else
    check "Frontend directory exists" "ERROR" "frontend/ directory not found"
fi

# Check if package.json exists
if [ -f "frontend/package.json" ]; then
    check "package.json exists" "OK"

    # Check if required scripts exist
    if grep -q '"dev":' frontend/package.json && \
       grep -q '"build":' frontend/package.json && \
       grep -q '"start":' frontend/package.json; then
        check "Required scripts in package.json" "OK"
    else
        check "Required scripts in package.json" "ERROR" "Missing dev, build, or start script"
    fi
else
    check "package.json exists" "ERROR" "frontend/package.json not found"
fi

# Check if node_modules exists (should be in .gitignore)
if [ -d "frontend/node_modules" ]; then
    if grep -q "node_modules" .gitignore; then
        check "node_modules in .gitignore" "OK"
    else
        check "node_modules in .gitignore" "WARN" "Add node_modules to .gitignore"
    fi
fi

# Check if next.config.js exists
if [ -f "frontend/next.config.js" ]; then
    check "next.config.js exists" "OK"
elif [ -f "frontend/next.config.ts" ]; then
    check "next.config exists" "WARN" "Consider renaming next.config.ts to next.config.js for better compatibility"
else
    check "next.config exists" "ERROR" "No next.config.js or next.config.ts found"
fi

# Check if .env.example exists
if [ -f "frontend/.env.example" ]; then
    check ".env.example exists" "OK"
else
    check ".env.example exists" "WARN" "Create frontend/.env.example for documentation"
fi

echo ""
echo -e "${BLUE}Backend Checks:${NC}"
echo "───────────────"

# Check if api directory exists
if [ -d "api" ]; then
    check "API directory exists" "OK"
else
    check "API directory exists" "ERROR" "api/ directory not found"
fi

# Check if main.py exists
if [ -f "api/main.py" ]; then
    check "api/main.py exists" "OK"
else
    check "api/main.py exists" "ERROR" "api/main.py not found"
fi

# Check if requirements file exists
if [ -f "requirements-api.txt" ]; then
    check "requirements-api.txt exists" "OK"
elif [ -f "requirements.txt" ]; then
    check "requirements file exists" "WARN" "Consider renaming to requirements-api.txt"
else
    check "requirements file exists" "ERROR" "No requirements file found"
fi

# Check if src directory exists
if [ -d "src" ]; then
    check "src/ directory exists" "OK"
else
    check "src/ directory exists" "ERROR" "src/ directory not found"
fi

echo ""
echo -e "${BLUE}Configuration Checks:${NC}"
echo "────────────────────"

# Check if vercel.json exists
if [ -f "vercel.json" ]; then
    check "vercel.json exists" "OK"
else
    check "vercel.json exists" "WARN" "Create vercel.json for optimal configuration"
fi

# Check if .gitignore exists and has required entries
if [ -f ".gitignore" ]; then
    check ".gitignore exists" "OK"

    if grep -q ".vercel" .gitignore && \
       grep -q "node_modules" .gitignore && \
       grep -q "\.env" .gitignore; then
        check "Essential .gitignore entries" "OK"
    else
        check "Essential .gitignore entries" "WARN" "Add .vercel, node_modules, .env to .gitignore"
    fi
else
    check ".gitignore exists" "ERROR" ".gitignore not found"
fi

# Check if .env files are NOT in git
if [ -f ".env" ] || [ -f "frontend/.env.local" ]; then
    if git ls-files .env &>/dev/null || git ls-files frontend/.env.local &>/dev/null; then
        check ".env files not in git" "ERROR" "Remove .env files from git!"
    else
        check ".env files not in git" "OK"
    fi
fi

echo ""
echo -e "${BLUE}Data & Files Checks:${NC}"
echo "───────────────────"

# Check if data directory exists
if [ -d "data" ]; then
    check "data/ directory exists" "OK"

    # Check if companies.json exists
    if [ -f "data/companies.json" ]; then
        check "companies.json exists" "OK"
    else
        check "companies.json exists" "WARN" "Run: python scripts/convert_companies_to_json.py"
    fi
else
    check "data/ directory exists" "WARN" "Create data/ directory"
fi

# Check if database files are in .gitignore
if grep -q "\.db" .gitignore; then
    check "Database files in .gitignore" "OK"
else
    check "Database files in .gitignore" "WARN" "Add *.db to .gitignore"
fi

echo ""
echo -e "${BLUE}Git Checks:${NC}"
echo "──────────"

# Check if git repo exists
if [ -d ".git" ]; then
    check "Git repository initialized" "OK"

    # Check if there are uncommitted changes
    if git diff-index --quiet HEAD --; then
        check "No uncommitted changes" "OK"
    else
        check "No uncommitted changes" "WARN" "You have uncommitted changes"
    fi

    # Check if remote exists
    if git remote | grep -q "origin"; then
        check "Git remote configured" "OK"

        # Get remote URL
        REMOTE_URL=$(git remote get-url origin 2>/dev/null)
        if [[ $REMOTE_URL == *"github.com"* ]]; then
            check "GitHub remote detected" "OK"
        else
            check "GitHub remote" "WARN" "Remote is not GitHub: $REMOTE_URL"
        fi
    else
        check "Git remote configured" "ERROR" "No git remote configured"
    fi
else
    check "Git repository initialized" "ERROR" "Not a git repository"
fi

echo ""
echo -e "${BLUE}Build Test:${NC}"
echo "───────────"

# Test if frontend builds (optional, can be slow)
if [ "$1" = "--full" ]; then
    echo "Running full build test..."
    cd frontend
    if npm run build &>/dev/null; then
        check "Frontend builds successfully" "OK"
    else
        check "Frontend builds successfully" "ERROR" "Build failed - run 'npm run build' to see errors"
    fi
    cd ..
else
    echo -e "  ${YELLOW}ℹ${NC} Skipping build test (use --full for complete check)"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Summary:${NC}"
echo "────────"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo -e "${GREEN}✓ Your project is ready for deployment${NC}"
    echo ""
    echo -e "Next steps:"
    echo -e "  1. Push your code: ${BLUE}git push${NC}"
    echo -e "  2. Go to: ${BLUE}https://vercel.com/new${NC}"
    echo -e "  3. Import your repository"
    echo -e "  4. Set Root Directory: ${BLUE}frontend${NC}"
    echo -e "  5. Add env var: ${BLUE}NEXT_PUBLIC_API_URL${NC}"
    echo -e "  6. Deploy! 🚀"
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    echo -e "${GREEN}✓ No critical errors${NC}"
    echo -e "${YELLOW}  Consider fixing warnings before deployment${NC}"
else
    echo -e "${RED}✗ $ERRORS error(s) found${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    fi
    echo -e "${RED}  Fix errors before deploying${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
