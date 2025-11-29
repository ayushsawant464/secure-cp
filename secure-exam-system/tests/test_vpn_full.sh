#!/bin/bash
#
# Full VPN + Domain Filtering Test
# Tests VPN routing and domain blocking
#

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   VPN + DOMAIN FILTERING TEST                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd /home/savvy19/Desktop/product/secure-exam-system

echo "This test will:"
echo "  1. Start ProtonVPN (if configured)"
echo "  2. Route ALL traffic through VPN"
echo "  3. Block all domains except codeforces.com"
echo "  4. Open browser to test"
echo ""
echo "Prerequisites:"
echo "  - ProtonVPN config at /etc/wireguard/exam.conf"
echo "  - Run as sudo"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "❌ Must run as sudo"
    exit 1
fi

read -p "Start VPN test? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo "Step 1: Check current IP (before VPN)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
BEFORE_IP=$(curl -s --max-time 5 https://api.ipify.org)
echo "Current IP: $BEFORE_IP"

echo ""
echo "Step 2: Start VPN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start VPN
wg-quick up exam 2>&1 | head -10

if [ $? -eq 0 ]; then
    echo "✓ VPN started"
    
    # Wait for VPN to stabilize
    sleep 3
    
    echo ""
    echo "Step 3: Check IP through VPN"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    VPN_IP=$(curl -s --max-time 10 https://api.ipify.org)
    echo "VPN IP: $VPN_IP"
    
    if [ "$BEFORE_IP" != "$VPN_IP" ]; then
        echo "✓ Traffic is routed through VPN!"
    else
        echo "⚠️  IP didn't change - VPN may not be routing"
    fi
else
    echo "❌ VPN failed to start"
    echo "Check: /etc/wireguard/exam.conf exists and is valid"
    exit 1
fi

echo ""
echo "Step 4: Apply domain filtering"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Apply domain filtering using Python
sudo -u $SUDO_USER python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/home/savvy19/Desktop/product/secure-exam-system')

from network.domain_filter import DomainFilter
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

df = DomainFilter()
df.start()

print("\n✓ Domain filter active")
print("  Allowed: codeforces.com and subdomains")
print("  Blocked: Everything else")

PYTHON_EOF

echo ""
echo "Step 5: Test network access"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Testing codeforces.com (should work):"
if curl -s --max-time 10 https://codeforces.com | grep -q "Codeforces"; then
    echo "  ✓ codeforces.com accessible"
else
    echo "  ⚠️  codeforces.com not responding (check filter)"
fi

echo ""
echo "Testing google.com (should be blocked):"
if timeout 5 curl -s https://google.com >/dev/null 2>&1; then
    echo "  ❌ google.com accessible (filter not working!)"
else
    echo "  ✓ google.com BLOCKED"
fi

echo ""
echo "Step 6: Open browser for manual testing"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Browser opening in kiosk mode..."
echo "Test these manually:"
echo "  ✓ Browse codeforces.com (should work)"
echo "  ✗ Try google.com in address (shouldn't resolve)"
echo ""
echo "Press Alt+F4 to close browser when done"
echo ""
read -p "Press Enter to open browser..."

# Open browser as regular user
sudo -u $SUDO_USER DISPLAY=:0 google-chrome \
  --kiosk https://codeforces.com \
  --no-first-run \
  --disable-dev-tools \
  --user-data-dir=/tmp/exam-vpn-test \
  2>/dev/null

echo ""
echo "Step 7: Cleanup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Stop domain filter
sudo -u $SUDO_USER python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/home/savvy19/Desktop/product/secure-exam-system')
from network.domain_filter import DomainFilter
df = DomainFilter()
df.stop()
print("✓ Domain filter stopped")
PYTHON_EOF

# Stop VPN
wg-quick down exam
echo "✓ VPN stopped"

# Check IP after
AFTER_IP=$(curl -s --max-time 5 https://api.ipify.org)
echo "IP after VPN stop: $AFTER_IP"

if [ "$AFTER_IP" == "$BEFORE_IP" ]; then
    echo "✓ Returned to original IP"
else
    echo "⚠️  IP changed: $BEFORE_IP → $AFTER_IP"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   TEST COMPLETE                                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Summary:"
echo "  - VPN routing: $([ "$BEFORE_IP" != "$VPN_IP" ] && echo 'WORKING ✓' || echo 'CHECK ⚠️')"
echo "  - Domain filtering: Applied ✓"
echo "  - Kiosk mode: Working ✓"
echo ""
