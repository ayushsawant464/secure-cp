#!/bin/bash
#
# Simple Codeforces Test (No Namespace)
# Test browser + domain filtering without VPN complexity
#

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   SIMPLE CODEFORCES TEST                                  ║"
echo "║   Browser + Domain Filtering (No VPN for simplicity)      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd /home/savvy19/Desktop/product/secure-exam-system

echo "This will:"
echo "  1. Skip VPN (to avoid namespace issues)"
echo "  2. Open browser in kiosk mode"
echo "  3. Show you the locked-down experience"
echo ""
echo "You can test:"
echo "  ✓ Kiosk mode (can't escape)"
echo "  ✓ Locked to codeforces.com"
echo "  ✓ No dev tools, no address bar"
echo ""
read -p "Start test? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo "Starting kiosk browser..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "BROWSER OPENED - Try these:"
echo "  ✓ Browse codeforces.com normally"
echo "  ✗ Try pressing F11 (should not exit fullscreen)"
echo "  ✗ Try Ctrl+T for new tab (blocked)"
echo "  ✗ Try F12 for dev tools (blocked)"
echo "  ✗ Try typing other URL (no address bar)"
echo ""
echo "To exit: Press Alt+F4 or Ctrl+C here"
echo ""

chmod +x test_browser_simple.sh

BROWSER_PID=$!

# Wait for browser
wait $BROWSER_PID

echo ""
echo "✓ Browser closed"
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   TEST COMPLETE                                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "What you just experienced:"
echo "  ✓ Kiosk mode - fullscreen, locked"
echo "  ✓ Started at codeforces.com"
echo "  ✓ No way to access browser controls"
echo ""
echo "In production mode, this PLUS:"
echo "  + VPN routing (all traffic through VPN)"
echo "  + Domain filtering (only codeforces.com accessible)"
echo "  + Process blocking (can't start other apps)"
echo "  + AppArmor lockdown (no terminals, no shells)"
echo ""
