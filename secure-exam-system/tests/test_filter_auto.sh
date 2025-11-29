#!/bin/bash
#
# Simple Filtering Test - No Input Required
#

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   DOMAIN FILTERING TEST v3 (Auto-cleanup)                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "❌ Must run as sudo"
    exit 1
fi

cd /home/savvy19/Desktop/product/secure-exam-system

echo "This will:"
echo "  1. Apply domain filter for 10 seconds"
echo "  2. Test codeforces.com (should work)"
echo "  3. Test google.com (should be blocked)"
echo "  4. Auto-cleanup after 10 seconds"
echo ""
echo "NEW SAFEGUARDS:"
echo "  ✓ Localhost always allowed"
echo "  ✓ Established connections kept (chat won't break)"
echo "  ✓ DNS always works"
echo ""
read -p "Start test? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

# Backup config
cp config/system_config.json config/system_config.json.tmpbackup

# Switch to production
sed -i 's/"mode": "testing"/"mode": "production"/' config/system_config.json

echo ""
echo "Starting filter..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start filter in background
python3 -c "
import sys
sys.path.insert(0, '.')
from network.domain_filter import DomainFilter
import time

df = DomainFilter()
if df.start():
    print('\n✓ Domain filter active with safeguards')
    print('  Testing for 10 seconds...\n')
    time.sleep(10)
    df.stop()
    print('\n✓ Filter stopped automatically')
else:
    print('❌ Failed to start filter')
" &

FILTER_PID=$!

# Wait for filter to start
sleep 2

echo ""
echo "Filter is running. Testing..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test 1: codeforces
echo "Test 1: codeforces.com (should work)"
if timeout 10 curl -s https://codeforces.com | head -1 >/dev/null 2>&1; then
    echo "  ✓ codeforces.com ACCESSIBLE"
else
    echo "  ⚠️  codeforces.com not accessible"
fi

# Test 2: google
echo ""
echo "Test 2: google.com (should be blocked)"
if timeout 5 curl -s https://google.com >/dev/null 2>&1; then
    echo "  ❌ google.com ACCESSIBLE (filter may not be working)"
else
    echo "  ✓ google.com BLOCKED"
fi

echo ""
echo "Waiting for auto-cleanup..."

# Wait for filter to stop
wait $FILTER_PID

# Restore config
mv config/system_config.json.tmpbackup config/system_config.json

# Extra cleanup just in case
sudo iptables -D OUTPUT -j EXAM_FILTER 2>/dev/null
sudo iptables -F EXAM_FILTER 2>/dev/null
sudo iptables -X EXAM_FILTER 2>/dev/null
sudo ip6tables -D OUTPUT -j EXAM_FILTER_V6 2>/dev/null
sudo ip6tables -F EXAM_FILTER_V6 2>/dev/null
sudo ip6tables -X EXAM_FILTER_V6 2>/dev/null

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   TEST COMPLETE                                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "✓ Back to testing mode"
echo "✓ All filters removed"
echo "✓ Network restored"
echo ""

# Verify network works
echo "Verifying network..."
if curl -s --max-time 5 https://google.com >/dev/null 2>&1; then
    echo "✓ Network fully restored"
else
    echo "⚠️  If network still blocked, run:"
    echo "   sudo ./EMERGENCY_RESTORE_NETWORK.sh"
fi
