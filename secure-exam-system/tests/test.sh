#!/bin/bash
# ----------------------------------------------------------------------
# Production‑Level Application‑Launch Kernel‑Logging Test
# Uses the same testing flow as the other production tests:
#   1️⃣ Switch to production mode (temporarily)
#   2️⃣ Start ProtonVPN (WireGuard)
#   3️⃣ Apply domain filtering (production style)
#   4️⃣ Launch allowed & disallowed apps
#   5️⃣ Verify kernel logs contain execve entries for those launches
#   6️⃣ Automatic cleanup (restore mode, stop VPN, remove filter)
# ----------------------------------------------------------------------
if [ "$EUID" -ne 0 ]; then
    echo "❌ Must run as sudo"
    exit 1
fi
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   APP‑LAUNCH KERNEL LOGGING TEST (PRODUCTION)            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
# ------------------------------------------------------------------
# Save original mode & switch to production
# ------------------------------------------------------------------
ORIG_MODE=$(grep '"mode"' config/system_config.json | grep -o 'testing\|production')
echo "Original mode: $ORIG_MODE"
sed -i 's/"mode": ".*"/"mode": "production"/' config/system_config.json
echo "Mode set to production for this test"
# ------------------------------------------------------------------
# Cleanup function (runs on EXIT/INT/TERM)
# ------------------------------------------------------------------
cleanup() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   CLEANUP                                               ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo "Stopping domain filter..."
    sudo -u "$SUDO_USER" python3 <<'PYEOF'
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
    echo "Done."
}
trap cleanup EXIT INT TERM
# ------------------------------------------------------------------
# STEP 1 – Show current IP (pre‑VPN)
# ------------------------------------------------------------------
echo "STEP 1: Current IP (before VPN)"
BEFORE_IP=$(curl -s --max-time 5 https://api.ipify.org || echo "none")
echo "IP before VPN: $BEFORE_IP"
# ------------------------------------------------------------------
# STEP 2 – Start VPN
# ------------------------------------------------------------------
echo ""
echo "STEP 2: Starting VPN (WireGuard)"
wg-quick up exam
if [ $? -ne 0 ]; then
    echo "❌ VPN failed to start – aborting"
    exit 1
fi
echo "✓ VPN started"
sleep 3
VPN_IP=$(curl -s --max-time 5 https://api.ipify.org || echo "none")
echo "IP after VPN start: $VPN_IP"
if [ "$BEFORE_IP" != "$VPN_IP" ]; then
    echo "✓ Traffic now routed through VPN"
else
    echo "⚠️  IP unchanged – VPN may not be routing correctly"
fi
# ------------------------------------------------------------------
# STEP 3 – Apply domain filter (production)
# ------------------------------------------------------------------
echo ""
echo "STEP 3: Applying domain filter (production mode)"
sudo -u "$SUDO_USER" python3 <<'PYEOF'
import sys, logging
sys.path.insert(0, '/home/savvy19/Desktop/product/secure-exam-system')
from network.domain_filter import DomainFilter
logging.basicConfig(level=logging.INFO, format='%(message)s')
DomainFilter().start()
PYEOF
echo "✓ Domain filter active"
# ------------------------------------------------------------------
# STEP 4 – Launch applications
# ------------------------------------------------------------------
echo ""
echo "STEP 4: Launching test applications"
echo "  • Allowed app (google‑chrome) – should start"
sudo -u "$SUDO_USER" DISPLAY=:0 google-chrome \
    --kiosk https://codeforces.com \
    --no-first-run \
    --disable-dev-tools \
    --user-data-dir=/tmp/app-log-test 2>/dev/null &
CHROME_PID=$!
sleep 5   # give it a moment to start
echo "  • Disallowed app (xterm) – should be blocked by process monitor"
sudo -u "$SUDO_USER" xterm &
XTERM_PID=$!
sleep 2   # short wait; we only need the execve event
# ------------------------------------------------------------------
# STEP 5 – Kernel‑logging verification
# ------------------------------------------------------------------
echo ""
echo "STEP 5: Verifying kernel logs for execve events"
echo "Fetching recent dmesg entries (last 200 lines) that contain 'execve'..."
dmesg | tail -n 200 | grep -i execve | grep -E "chrome|xterm" || echo "No execve entries found for the launched apps."
# ------------------------------------------------------------------
# STEP 6 – Manual verification prompt (optional)
# ------------------------------------------------------------------
read -p "Press Enter to stop the browsers and finish the test…" dummy
# ------------------------------------------------------------------
# END – cleanup will run automatically via trap
# ------------------------------------------------------------------
echo ""
echo "All steps completed – cleanup will now run automatically."

