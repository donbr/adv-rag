#!/bin/bash
# MCP Inspector Development Helper Script
# Launches MCP Inspector for testing Advanced RAG MCP servers

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
echo -e "${BLUE}MCP Inspector Development Tool${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if npx is available
if ! command -v npx &> /dev/null; then
    echo -e "${RED}❌ Error: npx not found${NC}"
    echo -e "${YELLOW}Please install Node.js and npm first:${NC}"
    echo -e "  Ubuntu/Debian: ${CYAN}sudo apt install nodejs npm${NC}"
    echo -e "  macOS: ${CYAN}brew install node${NC}"
    exit 1
fi

# Check if Python virtual environment exists
if [ ! -f ".venv/bin/python" ]; then
    echo -e "${RED}❌ Error: Virtual environment not found at .venv/${NC}"
    echo -e "${YELLOW}Run: ${CYAN}uv sync --dev${NC}"
    exit 1
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
echo -e "${BLUE}Which MCP server do you want to inspect?${NC}"
echo -e "  ${GREEN}1)${NC} MCP Tools Server (Command Pattern - Full RAG pipeline)"
echo -e "  ${GREEN}2)${NC} MCP Resources Server (Query Pattern - Direct data access)"
echo -e "  ${GREEN}3)${NC} Both servers (separate inspector instances)"
echo ""
read -p "Enter choice [1-3]: " choice

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
    3)
        echo -e "${GREEN}Launching inspector for both servers...${NC}"
        echo -e "${YELLOW}Note: This will open two browser tabs${NC}"
        echo ""

        # Launch first inspector for Tools server
        echo -e "${CYAN}Starting inspector for MCP Tools Server...${NC}"
        npx @modelcontextprotocol/inspector &
        INSPECTOR_PID_1=$!
        sleep 2

        # Open browser for first inspector
        if command -v xdg-open &> /dev/null; then
            xdg-open http://localhost:6274 &
        elif command -v open &> /dev/null; then
            open http://localhost:6274 &
        fi

        echo -e "${GREEN}✅ Inspector 1 running at: ${CYAN}http://localhost:6274${NC}"
        echo -e "${YELLOW}   Configure for MCP Tools Server:${NC}"
        echo -e "     Transport: ${CYAN}STDIO${NC}"
        echo -e "     Command: ${CYAN}$PROJECT_ROOT/.venv/bin/python${NC}"
        echo -e "     Args: ${CYAN}src/mcp/server.py${NC}"
        echo -e "     Working Directory: ${CYAN}$PROJECT_ROOT${NC}"
        echo ""

        # For second server, we can only provide instructions since
        # MCP Inspector uses a fixed port
        echo -e "${CYAN}For MCP Resources Server:${NC}"
        echo -e "${YELLOW}   Open a new terminal and run:${NC}"
        echo -e "     ${CYAN}npx @modelcontextprotocol/inspector${NC}"
        echo -e "${YELLOW}   Then configure for MCP Resources Server:${NC}"
        echo -e "     Transport: ${CYAN}STDIO${NC}"
        echo -e "     Command: ${CYAN}$PROJECT_ROOT/.venv/bin/python${NC}"
        echo -e "     Args: ${CYAN}src/mcp/resources.py${NC}"
        echo -e "     Working Directory: ${CYAN}$PROJECT_ROOT${NC}"
        echo ""
        echo -e "${YELLOW}Press Ctrl+C to stop the first inspector${NC}"

        trap "kill $INSPECTOR_PID_1 2>/dev/null" EXIT
        wait $INSPECTOR_PID_1
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Starting MCP Inspector for: ${CYAN}$SERVER_NAME${NC}"
echo ""

# Display configuration info
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Inspector Configuration:${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}Transport:${NC} STDIO"
echo -e "  ${GREEN}Command:${NC} $PROJECT_ROOT/.venv/bin/python"
echo -e "  ${GREEN}Args:${NC} $SERVER_SCRIPT"
echo -e "  ${GREEN}Working Directory:${NC} $PROJECT_ROOT"
echo -e "  ${GREEN}Server Logs:${NC} $SERVER_LOG"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

# Start MCP Inspector
echo -e "${CYAN}Launching MCP Inspector...${NC}"
npx @modelcontextprotocol/inspector &
INSPECTOR_PID=$!

# Wait for inspector to start
sleep 3

# Try to open browser
INSPECTOR_URL="http://localhost:6274"
echo -e "${GREEN}✅ MCP Inspector started${NC}"
echo -e "${CYAN}Inspector URL: ${INSPECTOR_URL}${NC}"
echo ""

if command -v xdg-open &> /dev/null; then
    echo -e "${YELLOW}Opening browser...${NC}"
    xdg-open "$INSPECTOR_URL" &
elif command -v open &> /dev/null; then
    echo -e "${YELLOW}Opening browser...${NC}"
    open "$INSPECTOR_URL" &
else
    echo -e "${YELLOW}Please open manually: ${CYAN}$INSPECTOR_URL${NC}"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Quick Setup in Inspector UI:${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "  1. Select ${CYAN}STDIO${NC} transport"
echo -e "  2. Click ${CYAN}Connect${NC}"
echo -e "  3. Enter command: ${CYAN}$PROJECT_ROOT/.venv/bin/python${NC}"
echo -e "  4. Enter args: ${CYAN}$SERVER_SCRIPT${NC}"
echo -e "  5. Enter working dir: ${CYAN}$PROJECT_ROOT${NC}"
echo -e "  6. Click ${CYAN}Connect${NC} to start server"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

if [ "$SERVER_SCRIPT" = "src/mcp/server.py" ]; then
    echo -e "${YELLOW}Available Tools (6 retrieval strategies + 2 utilities):${NC}"
    echo -e "  • ${CYAN}naive_retriever${NC} - Fast baseline vector similarity"
    echo -e "  • ${CYAN}bm25_retriever${NC} - Traditional keyword search"
    echo -e "  • ${CYAN}semantic_retriever${NC} - Advanced semantic with context"
    echo -e "  • ${CYAN}contextual_compression_retriever${NC} - AI reranking"
    echo -e "  • ${CYAN}multi_query_retriever${NC} - Query expansion"
    echo -e "  • ${CYAN}ensemble_retriever${NC} - Hybrid approach"
    echo ""
    echo -e "${YELLOW}Available Resources (5 CQRS Qdrant endpoints):${NC}"
    echo -e "  • ${CYAN}qdrant://collections${NC} - List all collections"
    echo -e "  • ${CYAN}qdrant://collections/{collection_name}${NC} - Collection info"
    echo -e "  • ${CYAN}qdrant://collections/{name}/documents/{id}${NC} - Get document"
    echo -e "  • ${CYAN}qdrant://collections/{name}/search${NC} - Direct search"
    echo -e "  • ${CYAN}qdrant://collections/{name}/stats${NC} - Statistics"
else
    echo -e "${YELLOW}Available Resources (6 retrieval + 1 health):${NC}"
    echo -e "  • ${CYAN}retriever://naive_retriever/{query}${NC} - Fast vector similarity"
    echo -e "  • ${CYAN}retriever://bm25_retriever/{query}${NC} - Keyword search"
    echo -e "  • ${CYAN}retriever://semantic_retriever/{query}${NC} - Semantic search"
    echo -e "  • ${CYAN}retriever://contextual_compression_retriever/{query}${NC} - Reranked"
    echo -e "  • ${CYAN}retriever://multi_query_retriever/{query}${NC} - Expanded"
    echo -e "  • ${CYAN}retriever://ensemble_retriever/{query}${NC} - Hybrid"
    echo -e "  • ${CYAN}system://health${NC} - System health check"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Example Test Queries:${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"

if [ "$SERVER_SCRIPT" = "src/mcp/server.py" ]; then
    echo -e "${CYAN}Test a Tool:${NC}"
    echo -e '  Tool: semantic_retriever'
    echo -e '  Input: {"question": "What makes John Wick movies popular?"}'
    echo ""
    echo -e "${CYAN}Test a Resource:${NC}"
    echo -e '  Resource: qdrant://collections'
    echo -e '  Expected: List of available collections'
else
    echo -e "${CYAN}Test a Resource:${NC}"
    echo -e '  Resource: retriever://semantic_retriever/{query}'
    echo -e '  Query: John Wick action sequences'
    echo -e '  Expected: Raw documents with metadata'
fi

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Monitor server logs in another terminal:${NC}"
echo -e "  ${CYAN}tail -f $SERVER_LOG${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the inspector${NC}"
echo ""

# Trap Ctrl+C and cleanup
trap "echo -e '\n${YELLOW}Stopping MCP Inspector...${NC}'; kill $INSPECTOR_PID 2>/dev/null; echo -e '${GREEN}✅ Inspector stopped${NC}'; exit 0" SIGINT SIGTERM

# Wait for inspector process
wait $INSPECTOR_PID
