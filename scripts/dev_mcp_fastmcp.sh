#!/bin/bash
# FastMCP CLI Development Helper Script
# Uses FastMCP's built-in dev command with integrated inspector

set -e  # Exit on error

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}FastMCP Development Mode${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
    echo -e "${YELLOW}Activating .venv...${NC}"
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
    else
        echo -e "${RED}❌ Error: .venv not found. Run 'uv sync --dev' first${NC}"
        exit 1
    fi
fi

# Check if fastmcp is installed
if ! command -v fastmcp &> /dev/null; then
    echo -e "${RED}❌ Error: fastmcp not found${NC}"
    echo -e "${YELLOW}Installing fastmcp...${NC}"
    uv sync --dev
fi

# Check if required infrastructure is running
echo -e "${BLUE}Checking infrastructure services...${NC}"

# Check Qdrant
if curl -s http://localhost:6333 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Qdrant is running${NC}"
else
    echo -e "${YELLOW}⚠️  Qdrant not running, starting Docker services...${NC}"
    docker compose up -d
    sleep 3
fi

# Check Redis
if nc -z localhost 6379 2>/dev/null; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${YELLOW}⚠️  Redis not running, starting Docker services...${NC}"
    docker compose up -d
    sleep 3
fi

echo ""
echo -e "${BLUE}Which MCP server do you want to run in dev mode?${NC}"
echo -e "  ${GREEN}1)${NC} MCP Tools Server (Command Pattern - Full RAG pipeline)"
echo -e "  ${GREEN}2)${NC} MCP Resources Server (Query Pattern - Direct data access)"
echo ""
read -p "Enter choice [1-2]: " choice

case $choice in
    1)
        SERVER_NAME="MCP Tools Server"
        SERVER_SCRIPT="src/mcp/server.py"
        SERVER_LOG="logs/mcp_tools.log"
        ;;
    2)
        SERVER_NAME="MCP Resources Server"
        SERVER_SCRIPT="src/mcp/resources.py"
        SERVER_LOG="logs/mcp_resources.log"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Starting FastMCP dev mode for: ${CYAN}$SERVER_NAME${NC}"
echo ""

# Display configuration info
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}FastMCP Dev Configuration:${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}Server Script:${NC} $SERVER_SCRIPT"
echo -e "  ${GREEN}Inspector URL:${NC} ${CYAN}http://localhost:5173${NC}"
echo -e "  ${GREEN}Server Logs:${NC} $SERVER_LOG"
echo -e "  ${GREEN}Hot Reload:${NC} Enabled (auto-restart on code changes)"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

if [ "$SERVER_SCRIPT" = "src/mcp/server.py" ]; then
    echo -e "${YELLOW}Available Tools (6 retrieval strategies):${NC}"
    echo -e "  • ${CYAN}naive_retriever${NC} - Fast baseline vector similarity"
    echo -e "  • ${CYAN}bm25_retriever${NC} - Traditional keyword search"
    echo -e "  • ${CYAN}semantic_retriever${NC} - Advanced semantic with context"
    echo -e "  • ${CYAN}contextual_compression_retriever${NC} - AI reranking"
    echo -e "  • ${CYAN}multi_query_retriever${NC} - Query expansion"
    echo -e "  • ${CYAN}ensemble_retriever${NC} - Hybrid approach"
    echo ""
    echo -e "${YELLOW}Available Resources (5 CQRS Qdrant endpoints):${NC}"
    echo -e "  • ${CYAN}qdrant://collections${NC}"
    echo -e "  • ${CYAN}qdrant://collections/{collection_name}${NC}"
    echo -e "  • ${CYAN}qdrant://collections/{name}/documents/{id}${NC}"
    echo -e "  • ${CYAN}qdrant://collections/{name}/search${NC}"
    echo -e "  • ${CYAN}qdrant://collections/{name}/stats${NC}"
else
    echo -e "${YELLOW}Available Resources (6 retrieval + 1 health):${NC}"
    echo -e "  • ${CYAN}retriever://naive_retriever/{query}${NC}"
    echo -e "  • ${CYAN}retriever://bm25_retriever/{query}${NC}"
    echo -e "  • ${CYAN}retriever://semantic_retriever/{query}${NC}"
    echo -e "  • ${CYAN}retriever://contextual_compression_retriever/{query}${NC}"
    echo -e "  • ${CYAN}retriever://multi_query_retriever/{query}${NC}"
    echo -e "  • ${CYAN}retriever://ensemble_retriever/{query}${NC}"
    echo -e "  • ${CYAN}system://health${NC}"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Example Test Queries:${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"

if [ "$SERVER_SCRIPT" = "src/mcp/server.py" ]; then
    echo -e "${CYAN}Test a Tool in Inspector UI:${NC}"
    echo -e '  Tool: semantic_retriever'
    echo -e '  Input: {"question": "What makes John Wick movies popular?"}'
else
    echo -e "${CYAN}Test a Resource in Inspector UI:${NC}"
    echo -e '  Resource: retriever://semantic_retriever/{query}'
    echo -e '  Query: John Wick action sequences'
fi

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Monitor server logs in another terminal:${NC}"
echo -e "  ${CYAN}tail -f $SERVER_LOG${NC}"
echo ""
echo -e "${YELLOW}Starting FastMCP dev server...${NC}"
echo -e "${CYAN}Inspector will open automatically at http://localhost:5173${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Run FastMCP dev command
fastmcp dev "$SERVER_SCRIPT"
