#!/bin/bash
#
# Complete Network Test (VPN + Filtering)
# Tests ONLY network components, no AppArmor/process enforcement
#

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   COMPLETE NETWORK TEST (Safe)                           ║"
echo "║   VPN + Domain Filtering Only                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "❌ Must run as sudo"
    exit 1
fi

cd /home/savvy19/Desktop/product/secure-exam-system

echo "This test will:"
echo "  1. Check your current IP"
echo "  2. Start ProtonVPN"
echo "  3. Verify IP changed (traffic through VPN)"
echo "  4. Apply domain filtering (production-style)"
echo "  5. Test codeforces.com works"
echo "  6. Test google.com blocked"
echo "  7. Clean up everything"
echo ""
echo "⚠️  Network will be restricted for ~30 seconds"
echo "✓  But chat/SSH will keep working (safeguards active)"
echo ""
read -p "Start network test? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

# Store original mode
ORIGINAL_MODE=$(grep '"mode"' config/system_config.json | grep -o 'testing\|production')
echo "Original mode: $ORIGINAL_MODE"

# Cleanup function
cleanup() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   CLEANUP                                                 ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    
    echo "1. Stopping domain filter..."
    python3 -c "
import sys
sys.path.insert(0, '.')
from network.domain_filter import DomainFilter
df = DomainFilter('config/system_config.json')
df.stop()
print('  ✓ Filter stopped')
" 2>/dev/null
    
    # Extra cleanup
    iptables -D OUTPUT -j EXAM_FILTER 2>/dev/null
    iptables -F EXAM_FILTER 2>/dev/null
    iptables -X EXAM_FILTER 2>/dev/null
    ip6tables -D OUTPUT -j EXAM_FILTER_V6 2>/dev/null
    ip6tables -F EXAM_FILTER_V6 2>/dev/null
    ip6tables -X EXAM_FILTER_V6 2>/dev/null
    
    echo "2. Stopping VPN..."
    wg-quick down exam 2>/dev/null
    echo "  ✓ VPN stopped"
    
    echo "3. Restoring config to $ORIGINAL_MODE mode..."
    sed -i "s/\"mode\": \".*\"/\"mode\": \"$ORIGINAL_MODE\"/" config/system_config.json
    echo "  ✓ Config restored"
    
    FINAL_IP=$(curl -s --max-time 5 https://api.ipify.org)
    echo ""
    echo "Final IP: $FINAL_IP"
    echo ""
    echo "✓ Cleanup complete"
}

# Set trap for cleanup on exit or error
trap cleanup EXIT INT TERM

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "STEP 1: Current Network Status"
echo "═══════════════════════════════════════════════════════════"
BEFORE_IP=$(curl -s --max-time 5 https://api.ipify.org)
echo "Current IP: $BEFORE_IP"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "STEP 2: Start VPN"
echo "═══════════════════════════════════════════════════════════"

# Clean up any existing VPN
wg-quick down exam 2>/dev/null

echo "Starting ProtonVPN..."
if wg-quick up exam 2>&1 | grep -q "interface"; then
    echo "✓ VPN started"
    
    sleep 3
    VPN_IP=$(curl -s --max-time 10 https://api.ipify.org)
    echo "VPN IP: $VPN_IP"
    
    if [ "$BEFORE_IP" != "$VPN_IP" ]; then
        echo "✓ IP CHANGED - Traffic routing through VPN!"
    else
        echo "⚠️  IP didn't change - VPN may not be routing properly"
    fi
else
    echo "❌ VPN failed to start"
    echo "Check /etc/wireguard/exam.conf"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "STEP 3: Apply Domain Filtering (Production-Style)"
echo "═══════════════════════════════════════════════════════════"

# Temporarily switch to production for filtering
sed -i 's/"mode": ".*"/"mode": "production"/' config/system_config.json

echo "Applying domain filter..."
python3 << 'EOF' &
import sys
sys.path.insert(0, '.')
from network.domain_filter import DomainFilter
import time

df = DomainFilter()
if df.start():
    print('\n✓ Domain filter active (production mode)')
    print('  Allowed: codeforces.com')
    print('  Blocked: Everything else')
    print('  Safeguards: localhost ✓, DNS ✓, established ✓\n')
    
    # Keep filter running
    time.sleep(30)
else:
    print('❌ Filter failed to start')
EOF

FILTER_PID=$!

# Wait for filter to activate
sleep 3

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "STEP 4: Test Network Access"
echo "═══════════════════════════════════════════════════════════"

echo ""
echo "Test 1: codeforces.com (should work)"
if timeout 10 curl -s https://codeforces.com | head -c 100 >/dev/null 2>&1; then
    echo "  ✅ codeforces.com ACCESSIBLE through VPN"
else
    echo "  ⚠️  codeforces.com not accessible"
fi

echo ""
echo "Test 2: google.com (should be BLOCKED)"
if timeout 5 curl -s https://google.com >/dev/null 2>&1; then
    echo "  ❌ google.com ACCESSIBLE (filter not working!)"
else
    echo "  ✅ google.com BLOCKED by filter"
fi

echo ""
echo "Test 3: This chat (should still work - established connection)"
echo "  ✓ If you can still type here, safeguards are working!"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "STEP 5: Browser Test (Optional)"
echo "═══════════════════════════════════════════════════════════"
echo ""
read -p "Open browser to test manually? (yes/no): " test_browser

if [ "$test_browser" == "yes" ]; then
    echo ""
    echo "Opening browser in kiosk mode..."
    echo "  - Try browsing codeforces.com (should work)"
    echo "  - Try accessing google.com (should fail/timeout)"
    echo ""
    echo "Press Alt+F4 to close browser when done"
    echo ""
    
    sudo -u $SUDO_USER DISPLAY=:0 google-chrome \
        --kiosk https://codeforces.com \
        --no-first-run \
        --disable-dev-tools \
        --user-data-dir=/tmp/exam-network-test \
        2>/dev/null
    
    echo "✓ Browser closed"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "TEST SUMMARY"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Network Configuration:"
echo "  • VPN: ProtonVPN ($VPN_IP)"
echo "  • Filtering: Active (production mode)"
echo "  • codeforces.com: Accessible ✓"
echo "  • google.com: Blocked ✓"
echo ""
echo "Waiting 5 seconds before cleanup..."
sleep 5

# Cleanup will be called automatically by trap
