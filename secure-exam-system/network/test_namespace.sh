#!/bin/bash
#
# Testing Mode Script
# Creates isolated network namespace and tests all Phase 2 components safely
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "================================================"
echo "Secure Exam System - Testing Mode"
echo "================================================"
echo ""

# Check for root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ This script must be run as root (sudo)"
    exit 1
fi

echo "✓ Running as root"

# Check dependencies
echo "Checking dependencies..."
command -v ip >/dev/null 2>&1 || { echo "❌ 'ip' command not found. Install iproute2"; exit 1; }
command -v wg >/dev/null 2>&1 || { echo "❌ 'wg' command not found. Install wireguard-tools"; exit 1; }
command -v iptables >/dev/null 2>&1 || { echo "❌ 'iptables' not found"; exit 1; }
echo "✓ All dependencies found"

# Configuration
NAMESPACE="exam_ns"
VPN_INTERFACE="wg0"

echo ""
echo "Creating network namespace: $NAMESPACE"

# Create namespace
if ip netns list | grep -q "$NAMESPACE"; then
    echo "  Namespace already exists, deleting..."
    ip netns del "$NAMESPACE" 2>/dev/null || true
fi

ip netns add "$NAMESPACE"
echo "✓ Namespace created"

# Bring up loopback in namespace
ip netns exec "$NAMESPACE" ip link set lo up
echo "✓ Loopback enabled in namespace"

echo ""
echo "================================================"
echo "Network namespace '$NAMESPACE' is ready for testing"
echo "================================================"
echo ""
echo "You can now run the Python modules which will"
echo "automatically use this namespace when in testing mode."
echo ""
echo "Example commands:"
echo "  sudo python3 $PROJECT_ROOT/network/vpn_manager.py"
echo "  sudo python3 $PROJECT_ROOT/network/domain_filter.py"
echo "  sudo python3 $PROJECT_ROOT/network/kiosk_browser.py"
echo ""
echo "To run commands manually in the namespace:"
echo "  sudo ip netns exec $NAMESPACE <command>"
echo ""
echo "To clean up when done:"
echo "  sudo ip netns del $NAMESPACE"
echo ""
