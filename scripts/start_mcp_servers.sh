#!/bin/bash
# Start both MCP servers for Advanced RAG system
# Usage: ./scripts/start_mcp_servers.sh

set -e  # Exit on error

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Advanced RAG MCP Server Launcher${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Get the project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
    echo -e "${YELLOW}Attempting to activate .venv...${NC}"
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
    else
        echo -e "${RED}❌ Error: .venv not found. Run 'uv sync --dev' first${NC}"
        exit 1
    fi
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "${BLUE}Python version: $PYTHON_VERSION${NC}"

# Check if required services are running
echo -e "${BLUE}Checking infrastructure services...${NC}"

# Check Qdrant
if curl -s http://localhost:6333 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Qdrant is running${NC}"
else
    echo -e "${RED}❌ Qdrant is not running${NC}"
    echo -e "${YELLOW}Starting Docker services...${NC}"
    docker compose up -d
    sleep 3
fi

# Check Redis
if nc -z localhost 6379 2>/dev/null; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Redis is not running${NC}"
    echo -e "${YELLOW}Starting Docker services...${NC}"
    docker compose up -d
    sleep 3
fi

# Check Phoenix
if curl -s http://localhost:6006 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Phoenix is running${NC}"
else
    echo -e "${YELLOW}⚠️  Phoenix may not be running (optional)${NC}"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

echo ""
echo -e "${BLUE}Starting MCP servers...${NC}"
echo -e "${YELLOW}Note: Servers will run in the foreground. Press Ctrl+C to stop.${NC}"
echo -e "${YELLOW}For background operation, use separate terminals or add '&' to commands.${NC}"
echo ""

# Prompt user for which server to start
echo "Which server(s) do you want to start?"
echo "  1) MCP Tools Server (Command Pattern - Full RAG pipeline)"
echo "  2) MCP Resources Server (Query Pattern - Direct data access)"
echo "  3) Both servers (in separate terminal windows)"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo -e "${GREEN}Starting MCP Tools Server...${NC}"
        echo -e "${BLUE}Logs: logs/mcp_tools.log${NC}"
        echo ""
        python src/mcp/server.py
        ;;
    2)
        echo -e "${GREEN}Starting MCP Resources Server...${NC}"
        echo -e "${BLUE}Logs: logs/mcp_resources.log${NC}"
        echo ""
        python src/mcp/resources.py
        ;;
    3)
        echo -e "${GREEN}Starting both servers...${NC}"
        echo ""
        echo -e "${YELLOW}This will attempt to open new terminal windows.${NC}"
        echo -e "${YELLOW}If this doesn't work, manually run:${NC}"
        echo -e "  Terminal 1: ${BLUE}python src/mcp/server.py${NC}"
        echo -e "  Terminal 2: ${BLUE}python src/mcp/resources.py${NC}"
        echo ""

        # Try different terminal emulators
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal -- bash -c "cd $PROJECT_ROOT && source .venv/bin/activate && python src/mcp/server.py; exec bash"
            gnome-terminal -- bash -c "cd $PROJECT_ROOT && source .venv/bin/activate && python src/mcp/resources.py; exec bash"
            echo -e "${GREEN}✅ Servers started in new terminal windows${NC}"
        elif command -v xterm &> /dev/null; then
            xterm -e "cd $PROJECT_ROOT && source .venv/bin/activate && python src/mcp/server.py" &
            xterm -e "cd $PROJECT_ROOT && source .venv/bin/activate && python src/mcp/resources.py" &
            echo -e "${GREEN}✅ Servers started in new terminal windows${NC}"
        else
            echo -e "${RED}❌ No suitable terminal emulator found${NC}"
            echo -e "${YELLOW}Please manually start servers in separate terminals:${NC}"
            echo -e "  Terminal 1: ${BLUE}python src/mcp/server.py${NC}"
            echo -e "  Terminal 2: ${BLUE}python src/mcp/resources.py${NC}"
        fi

        echo ""
        echo -e "${GREEN}Monitor logs:${NC}"
        echo -e "  ${BLUE}tail -f logs/mcp_tools.log${NC}"
        echo -e "  ${BLUE}tail -f logs/mcp_resources.log${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}MCP Server(s) Started${NC}"
echo -e "${GREEN}================================${NC}"
