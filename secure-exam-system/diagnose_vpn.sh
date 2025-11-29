#!/bin/bash
#
# VPN Diagnostic Tool
# Checks why WireGuard VPN failed
#

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   VPN DIAGNOSTIC                                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "❌ Must run as sudo"
    exit 1
fi

echo "Checking WireGuard VPN configuration..."
echo ""

# 1. Check if config exists
echo "1. Config file check:"
if [ -f /etc/wireguard/exam.conf ]; then
    echo "  ✓ Config exists: /etc/wireguard/exam.conf"
    echo "  Permissions: $(stat -c %a /etc/wireguard/exam.conf)"
else
    echo "  ❌ Config not found at /etc/wireguard/exam.conf"
    exit 1
fi

# 2. Check if interface already exists
echo ""
echo "2. Interface check:"
if ip link show wg0 2>/dev/null; then
    echo "  ⚠️  Interface wg0 already exists!"
    echo "  This might be blocking the start"
    echo ""
    read -p "  Remove existing interface? (yes/no): " remove
    if [ "$remove" == "yes" ]; then
        wg-quick down exam
        echo "  ✓ Removed"
    fi
else
    echo "  ✓ No existing interface"
fi

# 3. Try to start VPN with verbose output
echo ""
echo "3. Attempting to start VPN (verbose):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
wg-quick up exam
EXIT_CODE=$?
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ VPN started successfully!"
    
    # Check status
    echo ""
    echo "4. VPN Status:"
    wg show
    
    echo ""
    echo "5. IP Check:"
    VPN_IP=$(curl -s --max-time 10 https://api.ipify.org)
    echo "  Current IP: $VPN_IP"
    
    echo ""
    read -p "Stop VPN? (yes/no): " stop
    if [ "$stop" == "yes" ]; then
        wg-quick down exam
        echo "✓ VPN stopped"
    fi
else
    echo "❌ VPN failed to start (exit code: $EXIT_CODE)"
    echo ""
    echo "Common issues:"
    echo "  • Interface already exists (run: sudo wg-quick down exam)"
    echo "  • Invalid config file"
    echo "  • Missing WireGuard kernel module"
    echo ""
    echo "Check kernel logs:"
    echo "  sudo dmesg | grep -i wireguard | tail -20"
    echo ""
    echo "Check system logs:"
    echo "  sudo journalctl -xe | grep -i wireguard | tail -20"
fi
