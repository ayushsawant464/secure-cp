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
# Helper: Safe JSON Edit using Python
# ------------------------------------------------------------------
set_mode() {
    local new_mode="$1"
    python3 -c "import json; f=open('config/system_config.json','r'); d=json.load(f); f.close(); d['mode']='$new_mode'; f=open('config/system_config.json','w'); json.dump(d, f, indent=2); f.close()"
}

get_mode() {
    python3 -c "import json; print(json.load(open('config/system_config.json'))['mode'])"
}

# ------------------------------------------------------------------
# Save original mode & switch to production
# ------------------------------------------------------------------
ORIG_MODE=$(get_mode)
echo "Original mode: $ORIG_MODE"
set_mode "production"
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
try:
    DomainFilter().stop()
except Exception as e:
    print(f"Error stopping filter: {e}")
PYEOF
    echo "✓ Domain filter stopped"

    echo "Stopping VPN..."
    wg-quick down exam 2>/dev/null || true
    echo "✓ VPN stopped"

    echo "Restoring original mode ($ORIG_MODE)..."
    set_mode "$ORIG_MODE"
    echo "✓ Mode restored"
    
    # Remove audit rule if auditctl exists
    if command -v auditctl &> /dev/null; then
        auditctl -D -k app_exec 2>/dev/null
        echo "✓ Audit rules cleaned up"
    fi

    echo "Done."
}
trap cleanup EXIT INT TERM

# ------------------------------------------------------------------
# STEP 0 – Enable Audit Logging (if available)
# ------------------------------------------------------------------
echo "STEP 0: Enabling Audit Logging for execve"
if command -v auditctl &> /dev/null; then
    if ! systemctl is-active --quiet auditd; then
        echo "Starting auditd..."
        systemctl start auditd || echo "Warning: Failed to start auditd"
    fi
    # Add rule to log execve
    auditctl -D -k app_exec 2>/dev/null
    auditctl -a always,exit -F arch=b64 -S execve -k app_exec
    auditctl -a always,exit -F arch=b32 -S execve -k app_exec
    echo "✓ Audit rules added"
else
    echo "⚠️  auditctl not found. Skipping audit rule configuration."
    echo "   Will rely on dmesg/syslog for kernel logs."
    
    # Try to load our custom kernel module if auditd is missing
    KO_PATH="/home/savvy19/Desktop/product/secure-exam-system/process_manager/kernel_monitor/proc_monitor.ko"
    if [ -f "$KO_PATH" ]; then
        echo "Loading custom kernel module (proc_monitor) for logging..."
        if lsmod | grep -q "proc_monitor"; then
            echo "✓ proc_monitor already loaded"
        else
            insmod "$KO_PATH"
            if [ $? -eq 0 ]; then
                echo "✓ proc_monitor loaded successfully"
            else
                echo "❌ Failed to load proc_monitor"
            fi
        fi
    else
        echo "⚠️  proc_monitor.ko not found at $KO_PATH"
    fi
fi

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
try:
    DomainFilter().start()
except Exception as e:
    print(f"Error starting filter: {e}")
    sys.exit(1)
PYEOF
if [ $? -eq 0 ]; then
    echo "✓ Domain filter active"
else
    echo "❌ Domain filter failed to start"
    exit 1
fi

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

echo "  • Disallowed app (xterm) – should be blocked by process monitor (if running)"
# Try running a command that exists if xterm is missing
if command -v xterm &> /dev/null; then
    sudo -u "$SUDO_USER" xterm &
else
    echo "    (xterm not found, trying 'sleep 10' as a dummy process)"
    sudo -u "$SUDO_USER" sleep 10 &
fi
APP_PID=$!
sleep 2   # short wait; we only need the execve event

# ------------------------------------------------------------------
# STEP 5 – Kernel‑logging verification
# ------------------------------------------------------------------
echo ""
echo "STEP 5: Verifying kernel logs for execve events"

if command -v ausearch &> /dev/null; then
    echo "Fetching recent audit entries (last 20) that contain 'execve'..."
    ausearch -k app_exec -ts recent -i | tail -n 20 || echo "No audit entries found via ausearch."
else
    echo "⚠️  ausearch not found. Skipping audit log check."
fi

echo ""
echo "Checking dmesg for any audit/exec logs..."
# Look for audit logs or custom module logs
dmesg | tail -n 50 | grep -E "audit|EXECVE|ProcMonitor" || echo "No relevant logs found in dmesg."

# ------------------------------------------------------------------
# STEP 6 – Manual verification prompt (optional)
# ------------------------------------------------------------------
read -p "Press Enter to stop the browsers and finish the test…" dummy

# ------------------------------------------------------------------
# END – cleanup will run automatically via trap
# ------------------------------------------------------------------
echo ""
echo "All steps completed – cleanup will now run automatically."
