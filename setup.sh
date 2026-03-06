#!/bin/bash
# OpenClaw Memory Manager - Complete Setup
# A + B + C + D = Default ChromaDB + Migration + Telegram Commands + Bot

set -e

echo "========================================"
echo "  OpenClaw Memory Manager Setup"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Step 1: Installing dependencies...${NC}"
pip install chromadb --break-system-packages --quiet 2>/dev/null || pip install chromadb --quiet
pip install python-telegram-bot --break-system-packages --quiet 2>/dev/null || pip install python-telegram-bot --quiet
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

echo -e "${BLUE}Step 2: Setting up directories...${NC}"
mkdir -p ~/.openclaw/memory/chromadb
mkdir -p ~/.openclaw/extensions/memory-manager
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

echo -e "${BLUE}Step 3: Testing memory system...${NC}"
python3 << 'EOF'
import sys
sys.path.insert(0, '/root/.openclaw/extensions/memory-manager')
from memory_manager import get_memory

memory = get_memory()
print(f"Backend: {memory.backend_type}")

# Test
mid = memory.remember("Test memory from setup", source="setup")
print(f"Test memory: {mid}")

results = memory.recall("test memory")
print(f"Search works: {len(results) > 0}")

print(f"Stats: {memory.stats()}")
EOF
echo -e "${GREEN}✓ Memory system working${NC}"
echo ""

echo -e "${BLUE}Step 4: Migration check...${NC}"
if [ -d "$HOME/.openclaw/workspace/memory" ]; then
    echo "Found existing memory files. Run migration with:"
    echo "  python3 ~/.openclaw/extensions/memory-manager/migrate.py"
else
    echo "No existing memory files to migrate"
fi
echo ""

echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "Usage:"
echo ""
echo "  CLI:"
echo "    python3 ~/.openclaw/extensions/memory-manager/memory_manager.py remember -c 'text'"
echo "    python3 ~/.openclaw/extensions/memory-manager/memory_manager.py recall -q 'query'"
echo ""
echo "  Python:"
echo "    from memory_manager import get_memory"
echo "    memory = get_memory()"
echo "    memory.remember('text')"
echo "    memory.recall('query')"
echo ""
echo "  Telegram Bot:"
echo "    export TELEGRAM_BOT_TOKEN='your-token'"
echo "    python3 ~/.openclaw/extensions/memory-manager/telegram_bot.py"
echo ""
echo "  Commands in Telegram:"
echo "    /remember [text] - Store memory"
echo "    /recall [query]  - Search memories"
echo "    /forget [id]     - Delete memory"
echo "    /memory          - Show stats"
echo "    /know [topic]    - What I know"
echo ""
echo "========================================"
