#!/bin/bash
# MCP Server startup script for development and testing

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MCP_SERVER_PATH="$PROJECT_ROOT/src/mcp_server/main.py"
LOG_DIR="$PROJECT_ROOT/logs"
PYTHON_PATH="$PROJECT_ROOT"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v python &> /dev/null; then
        log_error "Python not found. Please install Python 3.13+"
        exit 1
    fi
    
    if ! python -c "import sys; exit(0 if sys.version_info >= (3, 13) else 1)" 2>/dev/null; then
        log_error "Python 3.13+ required"
        exit 1
    fi
    
    if [ ! -f "$MCP_SERVER_PATH" ]; then
        log_error "MCP server not found at $MCP_SERVER_PATH"
        exit 1
    fi
    
    log_info "Dependencies check passed"
}

setup_environment() {
    log_info "Setting up environment..."
    
    # Create logs directory
    mkdir -p "$LOG_DIR"
    
    # Set Python path
    export PYTHONPATH="$PYTHON_PATH:$PYTHONPATH"
    
    # Load environment variables
    if [ -f "$PROJECT_ROOT/.env" ]; then
        log_info "Loading environment from .env"
        set -a
        source "$PROJECT_ROOT/.env"
        set +a
    else
        log_warn "No .env file found. Using defaults."
    fi
    
    log_info "Environment setup complete"
}

run_server() {
    local mode="${1:-stdio}"
    
    log_info "Starting MCP server in $mode mode..."
    
    cd "$PROJECT_ROOT"
    
    case "$mode" in
        "stdio")
            log_info "Running MCP server for Claude Desktop integration"
            python "$MCP_SERVER_PATH"
            ;;
        "inspector")
            log_info "Running MCP server with Inspector for testing"
            if command -v npx &> /dev/null; then
                npx @modelcontextprotocol/inspector python "$MCP_SERVER_PATH"
            else
                log_error "npx not found. Install Node.js to use Inspector mode."
                exit 1
            fi
            ;;
        "dev")
            log_info "Running MCP server in development mode with auto-reload"
            # Use watchdog or similar for auto-reload in development
            python "$MCP_SERVER_PATH"
            ;;
        *)
            log_error "Unknown mode: $mode. Use 'stdio', 'inspector', or 'dev'"
            exit 1
            ;;
    esac
}

show_help() {
    cat << EOF
MCP Server Management Script

Usage: $0 [OPTIONS] [MODE]

MODES:
    stdio      Run in stdio mode for Claude Desktop (default)
    inspector  Run with MCP Inspector for testing
    dev        Run in development mode

OPTIONS:
    -h, --help     Show this help message
    -c, --check    Check dependencies only
    -v, --verbose  Enable verbose logging

Examples:
    $0                    # Run in stdio mode
    $0 inspector          # Run with Inspector
    $0 dev                # Run in development mode
    $0 --check            # Check dependencies only

Environment Variables:
    OPENAI_API_KEY       OpenAI API key (required)
    QDRANT_URL          Qdrant database URL
    COLLECTION_NAME     Vector collection name
    LOG_LEVEL           Logging level (DEBUG, INFO, WARN, ERROR)

EOF
}

# Main script
main() {
    local mode="stdio"
    local check_only=false
    local verbose=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--check)
                check_only=true
                shift
                ;;
            -v|--verbose)
                verbose=true
                set -x
                shift
                ;;
            stdio|inspector|dev)
                mode="$1"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Execute based on options
    if [ "$check_only" = true ]; then
        check_dependencies
        log_info "Dependencies check complete"
        exit 0
    fi
    
    # Full startup sequence
    check_dependencies
    setup_environment
    run_server "$mode"
}

# Error handling
trap 'log_error "Script failed on line $LINENO"' ERR

# Run main function
main "$@" 