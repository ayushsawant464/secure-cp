#!/bin/bash
#
# Kernel Logging Test Script
# Verifies that relevant kernel and system logs are being generated correctly
# for the Secure Exam System components (WireGuard, iptables, domain filter).
#
# Usage: sudo ./test_kernel_logging.sh
#

if [ "$EUID" -ne 0 ]; then
    echo "❌ Must run as sudo"
    exit 1
fi

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   KERNEL LOGGING TEST                                      ║"
echo "╚════════════════════════════════════════════════════════════╝"

echo ""

# ---------------------------------------------------------------------
# Helper to print a header
# ---------------------------------------------------------------------
print_header() {
    echo "\n--- $1 ---"
}

# ---------------------------------------------------------------------
# 1. Recent kernel ring buffer (dmesg)
# ---------------------------------------------------------------------
print_header "Recent kernel messages (dmesg)"
# Show last 100 lines, filter for our components
# WireGuard, iptables, EXAM_FILTER, domain_filter, vpn_manager

dmesg | tail -n 100 | grep -E "wireguard|iptables|EXAM_FILTER|DomainFilter|vpn|exam" || echo "No matching kernel messages found"

# ---------------------------------------------------------------------
# 2. System journal (kernel priority)
# ---------------------------------------------------------------------
print_header "System journal (kernel) – last 100 entries"
journalctl -k -n 100 | grep -E "wireguard|iptables|EXAM_FILTER|DomainFilter|vpn|exam" || echo "No matching journal entries found"

# ---------------------------------------------------------------------
# 3. Verify our custom log messages (INFO level) from the Python modules
# ---------------------------------------------------------------------
print_header "Secure Exam System logs (INFO) – last 200 lines"
# Assuming logs are written to /var/log/secure-exam (as per config)
LOG_DIR="/var/log/secure-exam"
if [ -d "$LOG_DIR" ]; then
    tail -n 200 "$LOG_DIR"/*.log 2>/dev/null | grep -E "DomainFilter|VPN|KioskBrowser|ProcessMonitor|SecurityPatcher" || echo "No custom logs found"
else
    echo "Log directory $LOG_DIR not found"
fi

# ---------------------------------------------------------------------
# 4. Summary
# ---------------------------------------------------------------------
print_header "Summary"
echo "If you see entries above related to WireGuard, iptables, and the Secure Exam System modules, kernel logging is functioning correctly."

echo "\n╔════════════════════════════════════════════════════════════╗"
echo "║   KERNEL LOGGING TEST COMPLETE                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
