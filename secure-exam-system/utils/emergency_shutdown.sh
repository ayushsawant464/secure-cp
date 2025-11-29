#!/bin/bash
#
# Emergency Shutdown Script
# Safely stops all exam system components and restores normal system state
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "============================================================"
echo "EMERGENCY SHUTDOWN - SECURE EXAM SYSTEM"
echo "============================================================"
echo ""

# Check for root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ This script must be run as root"
    exit 1
fi

echo "⚠️  This will forcefully stop all exam system components"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo "Shutting down components..."

# Kill kiosk browser
echo "1. Stopping kiosk browser..."
pkill -f "chromium.*--kiosk" || true
echo "   ✓ Done"

# Disable AppArmor profile
echo "2. Disabling AppArmor profile..."
python3 security/system_lockdown.py disable 2>/dev/null || true
echo "   ✓ Done"

# Stop process enforcer
echo "3. Stopping process enforcer..."
pkill -f "process_enforcer" || true
echo "   ✓ Done"

# Cleanup iptables
echo "4. Cleaning up iptables..."
python3 -c "
import sys
sys.path.insert(0, '.')
from network.domain_filter import DomainFilter
from network.vpn_manager import VPNManager

df = DomainFilter()
df.stop()

vpn = VPNManager()
vpn.stop()
" 2>/dev/null || true
echo "   ✓ Done"

# Delete network namespace if exists
echo "5. Cleaning up network namespace..."
ip netns del exam_ns 2>/dev/null || true
echo "   ✓ Done"

echo ""
echo "============================================================"
echo "✓ EMERGENCY SHUTDOWN COMPLETE"
echo "============================================================"
echo ""
echo "System has been returned to normal state"
