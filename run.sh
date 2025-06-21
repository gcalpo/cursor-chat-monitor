#!/bin/bash

# Cursor Chat Monitor - Simple Run Script
# This script handles all the venv setup and runs the app for you
# Usage: ./run.sh [options...]
# Example: ./run.sh --debug --interval-ms=2000

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Cursor Chat Monitor - Simple Run Script${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed or not in PATH${NC}"
    echo -e "${YELLOW}Please install Python 3 and try again${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}🐍 Found Python $PYTHON_VERSION${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}📦 Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}🔌 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip to latest version
echo -e "${YELLOW}⬆️  Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1

# Install/upgrade dependencies
echo -e "${YELLOW}📚 Installing/upgrading dependencies...${NC}"
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Check if the main script exists
if [ ! -f "cursor_chat_monitor.py" ]; then
    echo -e "${RED}❌ cursor_chat_monitor.py not found${NC}"
    echo -e "${YELLOW}Make sure you're running this script from the project root directory${NC}"
    exit 1
fi

echo -e "${GREEN}🎯 Starting Cursor Chat Monitor...${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"

# Pass all arguments to the main script
python3 cursor_chat_monitor.py "$@"

# Note: The virtual environment remains activated, but when the script exits,
# the shell session that called this script will return to its original state 