#!/bin/bash
#
# Simple Domain Filtering Test (Production Mode)
# Tests ONLY domain filtering on host
#

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   DOMAIN FILTERING TEST (Production Mode)                ║"
echo "║   ⚠️  This will temporarily block non-codeforces sites    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "❌ Must run as sudo"
    exit 1
fi

cd /home/savvy19/Desktop/product/secure-exam-system

echo "This test will:"
echo "  1. Temporarily switch to production mode"
echo "  2. Apply domain filtering on HOST (not namespace)"
echo "  3. Test that google.com is blocked"
echo "  4. Test that codeforces.com works"
echo "  5. Remove filtering and restore testing mode"
echo ""
echo "⚠️  While running, you won't be able to access sites except codeforces.com"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

# Backup config
cp config/system_config.json config/system_config.json.tmp_backup

# Switch to production
sed -i 's/"mode": "testing"/"mode": "production"/' config/system_config.json

echo ""
echo "Step 1: Test BEFORE filtering"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing google.com (should work now):"
if timeout 5 curl -s https://google.com >/dev/null 2>&1; then
    echo "  ✓ google.com accessible (as expected)"
else
    echo "  ⚠️  google.com not accessible (unexpected)"
fi

echo ""
echo "Step 2: Apply domain filtering"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 << 'EOF'
import sys
sys.path.insert(0, '.')

from network.domain_filter import DomainFilter
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

print("Initializing domain filter in production mode...")
df = DomainFilter()

print("\nStarting domain filter...")
if df.start():
    print("✓ Domain filter applied")
    print("\n" + "="*60)
    print("FILTERING ACTIVE")
    print("="*60)
    
    # Save df reference for cleanup
    import pickle
    with open('/tmp/domain_filter.pkl', 'wb') as f:
        pickle.dump(df, f)
    
    print("\nFilter is now active. Press Ctrl+C to stop and cleanup.")
    print("Test in another terminal:")
    print("  curl https://google.com        # Should timeout")
    print("  curl https://codeforces.com    # Should work")
    print("")
    
    try:
        input("Press Enter when done testing...")
    except KeyboardInterrupt:
        print("\n\nInterrupted...")
    
    print("\nStopping domain filter...")
    df.stop()
    print("✓ Filter removed")
else:
    print("❌ Failed to start domain filter")

EOF

# Restore testing mode
echo ""
echo "Restoring testing mode..."
mv config/system_config.json.tmp_backup config/system_config.json

echo ""
echo "Step 3: Test AFTER filtering removed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing google.com (should work again):"
if timeout 5 curl -s https://google.com >/dev/null 2>&1; then
    echo "  ✓ google.com accessible (filtering removed successfully)"
else
    echo "  ⚠️  google.com still blocked (check iptables)"
    echo ""
    echo "Manual cleanup:"
    echo "  sudo iptables -D OUTPUT -j EXAM_FILTER 2>/dev/null"
    echo "  sudo iptables -F EXAM_FILTER 2>/dev/null"
    echo "  sudo iptables -X EXAM_FILTER 2>/dev/null"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   TEST COMPLETE                                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "If filtering worked, you should have seen:"
echo "  ✓ google.com blocked while filter was active"
echo "  ✓ codeforces.com accessible while filter was active"
echo "  ✓ google.com working again after filter removed"
echo ""
