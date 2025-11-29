#!/bin/bash
#
# Production‑level Network Test with Safeguards
# This script runs the VPN and domain filter in *production* mode
# but keeps essential safeguards (localhost, DNS, established connections)
# so your chat/SSH session stays alive.
#

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   PRODUCTION NETWORK TEST (WITH SAFEGUARDS)               ║"
echo "╚════════════════════════════════════════════════════════════╝"

echo ""

# ---------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------
if [ "$EUID" -ne 0 ]; then
    echo "❌ Must run as sudo"
    exit 1
fi

# ---------------------------------------------------------------------
# Save current mode and switch to production
# ---------------------------------------------------------------------
ORIG_MODE=$(grep '"mode"' config/system_config.json | grep -o 'testing\|production')
echo "Original mode: $ORIG_MODE"

# Switch to production (temporarily)
sed -i 's/"mode": ".*"/"mode": "production"/' config/system_config.json

echo "Mode set to production for this test"

# ---------------------------------------------------------------------
# Helper: cleanup on exit or interrupt
# ---------------------------------------------------------------------
cleanup() {
    echo "\n╔════════════════════════════════════════════════════════════╗"
    echo "║   CLEANUP                                               ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    
    echo "Stopping domain filter..."
    sudo -u $SUDO_USER python3 <<'PYEOF'
import sys
sys.path.insert(0, '/home/savvy19/Desktop/product/secure-exam-system')
from network.domain_filter import DomainFilter
DomainFilter().stop()
PYEOF
    echo "✓ Domain filter stopped"
    
    echo "Stopping VPN..."
    wg-quick down exam 2>/dev/null || true
    echo "✓ VPN stopped"
    
    echo "Restoring original mode ($ORIG_MODE)..."
    sed -i "s/\"mode\": .*/\"mode\": \"$ORIG_MODE\"/" config/system_config.json
    echo "✓ Mode restored"
    
    echo "Verifying network connectivity..."
    IP_AFTER=$(curl -s --max-time 5 https://api.ipify.org || echo "none")
    echo "Current IP after cleanup: $IP_AFTER"
    echo "Cleanup complete"
}
trap cleanup EXIT INT TERM

# ---------------------------------------------------------------------
# Step 1 – Show current IP (pre‑VPN)
# ---------------------------------------------------------------------
echo "\nStep 1: Current IP (before VPN)"
BEFORE_IP=$(curl -s --max-time 5 https://api.ipify.org || echo "none")
echo "IP before VPN: $BEFORE_IP"

# ---------------------------------------------------------------------
# Step 2 – Start VPN
# ---------------------------------------------------------------------
echo "\nStep 2: Starting VPN (WireGuard)"
wg-quick up exam
if [ $? -ne 0 ]; then
    echo "❌ VPN failed to start – aborting"
    exit 1
fi

echo "✓ VPN started"
# Give it a moment to acquire IP
sleep 3
VPN_IP=$(curl -s --max-time 5 https://api.ipify.org || echo "none")
echo "IP after VPN start: $VPN_IP"
if [ "$BEFORE_IP" != "$VPN_IP" ]; then
    echo "✓ Traffic is now routed through VPN"
else
    echo "⚠️  IP unchanged – VPN may not be routing correctly"
fi

# ---------------------------------------------------------------------
# Step 3 – Apply domain filter (production mode)
# ---------------------------------------------------------------------
echo "\nStep 3: Applying domain filter (production)"
sudo -u $SUDO_USER python3 <<'PYEOF'
import sys
sys.path.insert(0, '/home/savvy19/Desktop/product/secure-exam-system')
from network.domain_filter import DomainFilter
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
DomainFilter().start()
PYEOF

echo "✓ Domain filter active (production)"

# ---------------------------------------------------------------------
# Step 4 – Test allowed / blocked domains
# ---------------------------------------------------------------------
echo "\nStep 4: Testing network access"

# Allowed – codeforces.com
echo "Testing allowed domain (codeforces.com)…"
if curl -s --max-time 10 https://codeforces.com | grep -q "Codeforces"; then
    echo "  ✅ codeforces.com reachable"
else
    echo "  ⚠️  codeforces.com NOT reachable (filter issue)"
fi

# Blocked – google.com
echo "Testing blocked domain (google.com)…"
if timeout 5 curl -s https://google.com >/dev/null 2>&1; then
    echo "  ❌ google.com reachable – filter FAILED"
else
    echo "  ✅ google.com correctly blocked"
fi

# ---------------------------------------------------------------------
# Step 5 – Optional manual browser test (kiosk mode)
# ---------------------------------------------------------------------
read -p "Open browser for manual testing? (yes/no): " open_browser
if [ "$open_browser" = "yes" ]; then
    echo "Launching Chrome in kiosk mode (codeforces.com)…"
    sudo -u $SUDO_USER DISPLAY=:0 google-chrome \
        --kiosk https://codeforces.com \
        --no-first-run \
        --disable-dev-tools \
        --user-data-dir=/tmp/exam-prod-test \
        2>/dev/null &
    echo "Press Alt+F4 in the browser when finished"
    read -p "Press Enter when you have finished manual testing…" dummy
    pkill -u $SUDO_USER -f google-chrome || true
    echo "✓ Browser closed"
fi

# ---------------------------------------------------------------------
# End – Cleanup will run automatically via trap
# ---------------------------------------------------------------------

echo "\nAll steps completed – cleanup will now run automatically."
