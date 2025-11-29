#!/bin/bash
#
# EMERGENCY NETWORK RESTORE
# Run this if domain filtering blocks all traffic
#

echo "EMERGENCY NETWORK RESTORE"
echo "=========================="

if [ "$EUID" -ne 0 ]; then
    echo "Must run as sudo"
    exit 1
fi

echo "Removing ALL exam-related iptables rules..."

# Remove exam filter chain from OUTPUT
iptables -D OUTPUT -j EXAM_FILTER 2>/dev/null
ip6tables -D OUTPUT -j EXAM_FILTER_V6 2>/dev/null

# Flush exam chains
iptables -F EXAM_FILTER 2>/dev/null
ip6tables -F EXAM_FILTER_V6 2>/dev/null

# Delete exam chains
iptables -X EXAM_FILTER 2>/dev/null
ip6tables -X EXAM_FILTER_V6 2>/dev/null

# Set default policies to ACCEPT
iptables -P INPUT ACCEPT 2>/dev/null
iptables -P OUTPUT ACCEPT 2>/dev/null
iptables -P FORWARD ACCEPT 2>/dev/null

ip6tables -P INPUT ACCEPT 2>/dev/null
ip6tables -P OUTPUT ACCEPT 2>/dev/null
ip6tables -P FORWARD ACCEPT 2>/dev/null

echo "✓ Network restored"
echo ""
echo "Testing internet:"
if curl -s --max-time 5 https://google.com >/dev/null; then
    echo "✓ Internet working"
else
    echo "Still blocked - try restarting network:"
    echo "  sudo systemctl restart NetworkManager"
fi
