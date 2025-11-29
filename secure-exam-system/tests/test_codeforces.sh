#!/bin/bash
#
# Manual Codeforces Test
# Test the exam system by manually browsing codeforces.com
#

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   MANUAL CODEFORCES TEST                                  ║"
echo "║   Testing Mode - Safe                                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd /home/savvy19/Desktop/product/secure-exam-system

echo "This will:"
echo "  1. Start VPN (in network namespace - safe)"
echo "  2. Enable domain filtering (only codeforces.com)"
echo "  3. Open browser in kiosk mode"
echo "  4. You can manually test browsing"
echo ""
echo "What you can test:"
echo "  ✓ Access codeforces.com (should work)"
echo "  ✗ Access google.com (should be blocked)"
echo "  ✓ Browse within codeforces.com"
echo ""
read -p "Start manual test? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo "Starting components..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start with Python
sudo python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/home/savvy19/Desktop/product/secure-exam-system')

from network.vpn_manager import VPNManager
from network.domain_filter import DomainFilter
from network.kiosk_browser import KioskBrowser
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

print("\n1. Starting VPN...")
vpn = VPNManager()
if not vpn.start():
    print("❌ VPN failed to start (this is OK if no VPN configured)")
    print("   Continuing without VPN for testing...")
    vpn_started = False
else:
    print("✓ VPN started")
    vpn_started = True

print("\n2. Starting domain filter...")
df = DomainFilter()
if not df.start():
    print("⚠️  Domain filter warning (may work anyway)")
else:
    print("✓ Domain filter active - Only codeforces.com accessible")

print("\n3. Opening browser in kiosk mode...")
print("="*60)
print("BROWSER TESTING:")
print("  - Try accessing: https://codeforces.com ✓")
print("  - Try accessing: https://google.com ✗ (should fail)")
print("  - Press Alt+F4 to close browser when done")
print("="*60)
print("")

kb = KioskBrowser()
kb.start()

print("\nWaiting for browser to close...")
kb.wait()

print("\n4. Cleaning up...")
df.stop()
if vpn_started:
    vpn.stop()

print("\n✓ Test complete!")
print("\nWhat did you observe?")
print("  - Could you access codeforces.com?")
print("  - Was google.com blocked?")
print("  - Did the kiosk mode prevent escaping?")
print("")

PYTHON_EOF

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   MANUAL TEST COMPLETE                                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
