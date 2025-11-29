#!/bin/bash
#
# System Logging Checker
# Shows kernel and system logs related to exam system
#

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   SYSTEM LOGGING CHECKER                                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "Note: Run as sudo to see all logs"
    echo ""
fi

echo "1. KERNEL LOGS (dmesg)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "WireGuard kernel messages:"
sudo dmesg | grep -i wireguard | tail -10
echo ""

echo "iptables/netfilter messages:"
sudo dmesg | grep -i "iptables\|netfilter" | tail -10
echo ""

echo "Network interface messages:"
sudo dmesg | grep -i "wg0\|exam" | tail -10
echo ""

echo "2. SYSTEM LOGS (journalctl)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "WireGuard service logs:"
sudo journalctl -u wg-quick@exam -n 20 --no-pager 2>/dev/null || echo "  (No wg-quick service logs)"
echo ""

echo "Recent network errors:"
sudo journalctl -p err -n 20 --no-pager | grep -i "network\|wg\|iptables" || echo "  (No recent network errors)"
echo ""

echo "3. IPTABLES STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Current iptables rules:"
sudo iptables -L -n -v | head -30
echo ""

echo "Exam filter chains:"
sudo iptables -L EXAM_FILTER -n -v 2>/dev/null || echo "  (No EXAM_FILTER chain)"
echo ""

echo "4. WIREGUARD STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "WireGuard interfaces:"
sudo wg show 2>/dev/null || echo "  (No WireGuard interfaces active)"
echo ""

echo "Network interfaces:"
ip link show | grep -E "^[0-9]+:|state" | head -20
echo ""

echo "5. PROCESS LOGS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if [ -f /tmp/monitor.log ]; then
    echo "Process monitor log (last 20 lines):"
    tail -20 /tmp/monitor.log
else
    echo "  (No process monitor log)"
fi
echo ""

echo "6. EXAM SYSTEM LOGS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Recent exam-related logs:"
sudo journalctl -n 50 --no-pager | grep -i "exam\|secure\|filter\|vpn" | tail -20 || echo "  (No recent exam logs)"
echo ""

echo "7. APPARMOR STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
sudo aa-status 2>/dev/null | grep -i exam || echo "  (No exam AppArmor profiles loaded)"
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   DIAGNOSTICS COMPLETE                                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "To see live kernel logs:"
echo "  sudo dmesg -w"
echo ""
echo "To see live system logs:"
echo "  sudo journalctl -f"
echo ""
echo "To see live iptables logs (if LOG rules active):"
echo "  sudo tail -f /var/log/syslog | grep EXAM-BLOCKED"
echo ""
