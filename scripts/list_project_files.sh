#!/bin/bash
# list_project_files.sh - List project files excluding development directories

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}📁 Project Structure (excluding dev directories)${NC}"
echo "=================================================="

# Directories to exclude
EXCLUDE_DIRS=(
    ".venv"
    ".benchmarks" 
    ".cursor"
    ".pytest_cache"
    "build"
    ".git"
    "node_modules"
    ".mypy_cache"
    ".ruff_cache"
    "logs"
)

# Build find command with exclusions
FIND_CMD="find . -type f"
for dir in "${EXCLUDE_DIRS[@]}"; do
    FIND_CMD="$FIND_CMD -not -path \"./$dir/*\""
done

# Exclude all __pycache__ directories and .pyc files
FIND_CMD="$FIND_CMD -not -path \"*/__pycache__/*\" -not -name \"*.pyc\""

# Execute and format output
eval $FIND_CMD | sort | while read -r file; do
    # Get file info
    size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
    modified=$(stat -f%Sm -t%Y-%m-%d "$file" 2>/dev/null || stat -c%y "$file" 2>/dev/null | cut -d' ' -f1)
    
    # Format size
    if [ "$size" -gt 1048576 ]; then
        size_fmt=$(echo "scale=1; $size/1048576" | bc)M
    elif [ "$size" -gt 1024 ]; then
        size_fmt=$(echo "scale=1; $size/1024" | bc)K
    else
        size_fmt="${size}B"
    fi
    
    # Color code by file type
    case "$file" in
        *.py) echo -e "${BLUE}$file${NC} ($size_fmt, $modified)" ;;
        *.md) echo -e "${GREEN}$file${NC} ($size_fmt, $modified)" ;;
        *.toml|*.yaml|*.yml|*.json) echo -e "\033[0;33m$file${NC} ($size_fmt, $modified)" ;;
        *) echo "$file ($size_fmt, $modified)" ;;
    esac
done

echo ""
echo -e "${GREEN}✅ Project listing complete${NC}" 