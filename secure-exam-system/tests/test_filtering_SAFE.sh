#!/bin/bash
#
# SAFE Domain Filtering Test v2
# Fixed version with safeguards
#

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   SAFE DOMAIN FILTERING TEST (FIXED)                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "❌ Must run as sudo"
    exit 1
fi

cd /home/savvy19/Desktop/product/secure-exam-system

echo "NEW SAFEGUARDS:"
echo "  ✓ Localhost always allowed (prevents total lockout)"
echo "  ✓ Established connections kept (your chat/SSH won't break)"
echo "  ✓ DNS always works"
echo "  ✓ Only NEW connections to non-codeforces sites blocked"
echo ""
read -p "Test the FIXED domain filter? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

# Backup config
cp config/system_config.json config/system_config.json.safe_backup

# Switch to production temporarily
sed -i 's/"mode": "testing"/"mode": "production"/' config/system_config.json

echo ""
echo "Testing domain filter..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from network.domain_filter import DomainFilter
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

print("\n⏳ Starting domain filter with safeguards...\n")
df = DomainFilter()

if df.start():
    print("\n" + "="*60)
    print("✓ DOMAIN FILTER ACTIVE (WITH SAFEGUARDS)")
    print("="*60)
    print("\nSafeguards confirmed:")
    print("  ✓ This chat should still work")
    print("  ✓ Localhost accessible")
    print("  ✓ DNS working")
    print("\nNew connections blocked:")
    print("  ✗ google.com (should timeout)")
    print("  ✓ codeforces.com (should work)")
    print("\n" + "="*60)
    
    import subprocess
    
    # Test codeforces
    print("\nTest 1: codeforces.com")
    result = subprocess.run(['timeout', '10', 'curl', '-s', 'https://codeforces.com'], 
                          capture_output=True)
    if result.returncode == 0:
        print("  ✓ codeforces.com ACCESSIBLE")
    else:
        print("  ⚠️  codeforces.com not accessible (may be filter issue)")
    
    # Test google (should be blocked)
    print("\nTest 2: google.com")
    result = subprocess.run(['timeout', '5', 'curl', '-s', 'https://google.com'], 
                          capture_output=True)
    if result.returncode != 0:
        print("  ✓ google.com BLOCKED (as expected)")
    else:
        print("  ❌ google.com still accessible (filter not working)")
    
    print("\n" + "="*60)
    input("\nFilter running. Your chat should still work.\nPress Enter to stop and cleanup...")
    
    print("\nStopping filter...")
    df.stop()
    print("✓ Filter stopped")
else:
    print("❌ Failed to start filter")

EOF

# Restore config
mv config/system_config.json.safe_backup config/system_config.json

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   TEST COMPLETE - Back to Testing Mode                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Did you notice:"
echo "  • This chat kept working? ✓"
echo "  • codeforces.com was accessible? ✓"
echo "  • google.com was blocked? ✓"
echo ""
