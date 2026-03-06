#!/bin/bash
# OpenClaw Memory Manager - One-Line Installer
# Usage: curl -fsSL https://.../install.sh | bash

set -e

REPO_URL="https://github.com/n00n0i/openclaw-memory-manager"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.openclaw/extensions/memory-manager}"
VERSION="${VERSION:-main}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Logging
log_info() { echo -e "${GREEN}✓${NC} $1"; }
log_step() { echo -e "${BLUE}→${NC} ${BOLD}$1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

# Banner
print_banner() {
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🧠 OpenClaw Memory Manager Installer                  ║
║                                                           ║
║     ChromaDB + Telegram Integration                       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

EOF
}

# Check command
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
detect_os() {
    case "$OSTYPE" in
        linux-gnu*) echo "Linux" ;;
        darwin*) echo "macOS" ;;
        msys*) echo "Windows" ;;
        *) echo "Unknown" ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    if ! command_exists python3; then
        log_error "Python 3 not found. Please install Python 3.8+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    log_info "Python version: $PYTHON_VERSION"
    
    log_success "Prerequisites met!"
}

# Install dependencies
install_deps() {
    log_step "Installing dependencies..."
    
    pip install chromadb python-telegram-bot --break-system-packages --quiet 2>/dev/null || \
    pip install chromadb python-telegram-bot --quiet 2>/dev/null || \
    pip3 install chromadb python-telegram-bot
    
    log_success "Dependencies installed"
}

# Download
download_repo() {
    log_step "Downloading Memory Manager..."
    
    if [ -d "$INSTALL_DIR" ]; then
        log_warn "Directory exists: $INSTALL_DIR"
        read -p "  Overwrite? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Installation cancelled"
            exit 0
        fi
        rm -rf "$INSTALL_DIR"
    fi
    
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Download files directly (no git needed)
    curl -fsSL "$REPO_URL/raw/$VERSION/memory_manager.py" -o memory_manager.py
    curl -fsSL "$REPO_URL/raw/$VERSION/migrate.py" -o migrate.py
    curl -fsSL "$REPO_URL/raw/$VERSION/telegram_bot.py" -o telegram_bot.py
    curl -fsSL "$REPO_URL/raw/$VERSION/telegram_commands.py" -o telegram_commands.py
    
    chmod +x migrate.py telegram_bot.py
    
    log_success "Downloaded to $INSTALL_DIR"
}

# Setup directories
setup_dirs() {
    log_step "Setting up directories..."
    
    mkdir -p "$HOME/.openclaw/memory/chromadb"
    
    log_success "Directories created"
}

# Test installation
test_install() {
    log_step "Testing installation..."
    
    cd "$INSTALL_DIR"
    
    python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from memory_manager import get_memory
memory = get_memory()
mid = memory.remember("Test from installer", source="install")
print(f"Test memory: {mid[:16]}...")
results = memory.recall("test installer")
print(f"Search: {len(results)} results")
print("OK")
EOF
    
    log_success "Installation verified!"
}

# Print completion
print_completion() {
    echo ""
    echo "========================================"
    echo "  🎉 Installation Complete!"
    echo "========================================"
    echo ""
    echo -e "${BOLD}📁 Location:${NC} $INSTALL_DIR"
    echo ""
    echo -e "${BOLD}🚀 Quick Start:${NC}"
    echo ""
    echo "  Python:"
    echo "    from memory_manager import get_memory"
    echo "    memory = get_memory()"
    echo "    memory.remember('text')"
    echo "    memory.recall('query')"
    echo ""
    echo "  CLI:"
    echo "    cd $INSTALL_DIR"
    echo "    python3 memory_manager.py remember -c 'text'"
    echo "    python3 memory_manager.py recall -q 'query'"
    echo ""
    echo "  Telegram Bot:"
    echo "    export TELEGRAM_BOT_TOKEN='your-token'"
    echo "    python3 telegram_bot.py"
    echo ""
    echo "  Commands: /remember /recall /forget /memory /know"
    echo ""
    echo "========================================"
}

# Main
main() {
    print_banner
    
    echo "Version: $VERSION"
    echo "OS: $(detect_os)"
    echo "Install: $INSTALL_DIR"
    echo ""
    
    check_prerequisites
    install_deps
    download_repo
    setup_dirs
    test_install
    
    print_completion
}

# Handle interrupt
trap 'echo "" ; log_error "Installation interrupted" ; exit 1' INT TERM

# Run
main
