#!/bin/bash
#
# VPN Config Checker
# Diagnoses WireGuard configuration issues
#

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   VPN Configuration Checker                               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "❌ Must run as sudo"
    exit 1
fi

echo "Checking VPN configuration..."
echo ""

# Check if config exists
if [ ! -f /etc/wireguard/exam.conf ]; then
    echo "❌ Config file not found: /etc/wireguard/exam.conf"
    echo ""
    echo "Solutions:"
    echo "  1. Download ProtonVPN WireGuard config"
    echo "  2. Run: sudo cp ~/Downloads/protonvpn-*.conf /etc/wireguard/exam.conf"
    echo "  3. Run: sudo chmod 600 /etc/wireguard/exam.conf"
    exit 1
fi

echo "✓ Config file exists"
echo ""

# Show config (sanitized)
echo "Config file contents (line 10 highlighted):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat -n /etc/wireguard/exam.conf | head -15
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check line 10 specifically
LINE10=$(sed -n '10p' /etc/wireguard/exam.conf)
echo "Line 10 content:"
echo "  '$LINE10'"
echo ""

# Common issues
echo "Checking for common issues..."

# Check for Windows line endings
if file /etc/wireguard/exam.conf | grep -q CRLF; then
    echo "⚠️  Found Windows line endings (CRLF)"
    echo "   Fix: dos2unix /etc/wireguard/exam.conf"
fi

# Check for empty  lines
EMPTY_LINES=$(grep -c '^$' /etc/wireguard/exam.conf || true)
if [ "$EMPTY_LINES" -gt 5 ]; then
    echo "⚠️  Found $EMPTY_LINES empty lines (might be too many)"
fi

# Check for required sections
if ! grep -q "\[Interface\]" /etc/wireguard/exam.conf; then
    echo "❌ Missing [Interface] section"
fi

if ! grep -q "\[Peer\]" /etc/wireguard/exam.conf; then
    echo "❌ Missing [Peer] section"
fi

# Check permissions
PERMS=$(stat -c %a /etc/wireguard/exam.conf)
if [ "$PERMS" != "600" ]; then
    echo "⚠️  Permissions are $PERMS (should be 600)"
    echo "   Fix: sudo chmod 600 /etc/wireguard/exam.conf"
fi

echo ""
echo "Suggested fixes:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# If line 10 is problematic
if [ -z "$LINE10" ] || [[ "$LINE10" =~ ^[[:space:]]*$ ]]; then
    echo "Line 10 appears to be empty or whitespace only"
    echo ""
    echo "Options:"
    echo "  1. Edit the file: sudo nano /etc/wireguard/exam.conf"
    echo "  2. Remove empty lines around line 10"
    echo "  3. Or replace with fresh ProtonVPN config"
else
    echo "Line 10 looks like: $LINE10"
    echo ""
    echo "If this line is causing errors, it might be malformed."
    echo "Edit with: sudo nano /etc/wireguard/exam.conf"
fi

echo ""
echo "To test after fixing:"
echo "  sudo wg-quick up exam"
