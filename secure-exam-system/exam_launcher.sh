#!/bin/bash
#
# Secure Exam System Launcher
# Production launcher with comprehensive checks and monitoring
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "SECURE EXAM SYSTEM - PRODUCTION LAUNCHER"
echo "============================================================"
echo ""

# Check for root privileges
if [ "$EUID" -ne 0 ]; then 
    echo "❌ This script must be run as root"
    echo "Usage: sudo ./exam_launcher.sh"
    exit 1
fi

echo "✓ Running as root"

# Check dependencies
echo ""
echo "Checking dependencies..."

command -v python3 >/dev/null 2>&1 || { echo "❌ python3 not found"; exit 1; }
echo "  ✓ python3"

command -v ip >/dev/null 2>&1 || { echo "❌ iproute2 not found"; exit 1; }
echo "  ✓ iproute2"

command -v iptables >/dev/null 2>&1 || { echo "❌ iptables not found"; exit 1; }
echo "  ✓ iptables"

python3 -c "import psutil" 2>/dev/null || { echo "❌ python3-psutil not found"; exit 1; }
echo "  ✓ psutil"

echo ""
echo "✓ All dependencies satisfied"

# Parse arguments
DRY_RUN=false
if [ "$1" == "--dry-run" ]; then
    DRY_RUN=true
    echo ""
    echo "DRY RUN MODE - Will run pre-flight checks only"
fi

# Build allowlist if it doesn't exist
if [ ! -f "config/process_allowlist.json" ]; then
    echo ""
    echo "Process allowlist not found. Building..."
    python3 process_manager/allowlist_builder.py
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to build allowlist"
        exit 1
    fi
fi

# Create integrity baseline if it doesn't exist
if [ ! -f "config/integrity.json" ]; then
    echo ""
    echo "Integrity baseline not found. Creating..."
    python3 security/integrity_checker.py baseline
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create integrity baseline"
        exit  1
    fi
fi

# Run main controller
echo ""
echo "============================================================"
echo "LAUNCHING EXAM SYSTEM"
echo "============================================================"
echo ""

if [ "$DRY_RUN" = true ]; then
    python3 main_controller.py --dry-run
else
    python3 main_controller.py
fi

exit_code=$?

echo ""
echo "============================================================"
echo "EXAM SESSION ENDED"
echo "============================================================"

exit $exit_code
