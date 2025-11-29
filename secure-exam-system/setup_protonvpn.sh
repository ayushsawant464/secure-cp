#!/bin/bash
#
# ProtonVPN WireGuard Setup Guide for Secure Exam System
#

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   ProtonVPN WireGuard Configuration Guide                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "Step 1: Download WireGuard Config from ProtonVPN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Open browser and go to:"
echo "   https://account.protonvpn.com/downloads"
echo ""
echo "2. Login with your ProtonVPN account"
echo ""
echo "3. Select: 'WireGuard configuration'"
echo ""
echo "4. Choose a server (preferably close to your location)"
echo "   - For testing: Any free server works"
echo "   - For exam: Choose a stable, fast server"
echo ""
echo "5. Download the .conf file (e.g., protonvpn-XX.conf)"
echo ""
echo "6. The file will look like:"
echo "   [Interface]"
echo "   PrivateKey = <your private key>"
echo "   Address = 10.2.0.2/32"
echo "   DNS = 10.2.0.1"
echo "   "
echo "   [Peer]"
echo "   PublicKey = <server public key>"
echo "   AllowedIPs = 0.0.0.0/0"
echo "   Endpoint = <server-ip>:51820"
echo ""
read -p "Press Enter once you've downloaded the .conf file..."
echo ""

echo "Step 2: Copy Config to Exam System"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Where is your downloaded ProtonVPN config?"
read -p "Enter full path (e.g., ~/Downloads/protonvpn-xx.conf): " PROTON_CONF

if [ -f "$PROTON_CONF" ]; then
    echo "✓ Found: $PROTON_CONF"
    
    # Backup if exists
    if [ -f "/etc/wireguard/exam.conf" ]; then
        sudo cp /etc/wireguard/exam.conf /etc/wireguard/exam.conf.backup
        echo "  (Backed up existing config)"
    fi
    
    # Copy to system location
    sudo mkdir -p /etc/wireguard
    sudo cp "$PROTON_CONF" /etc/wireguard/exam.conf
    sudo chmod 600 /etc/wireguard/exam.conf
    
    echo "✓ Config copied to: /etc/wireguard/exam.conf"
    echo "✓ Permissions set to 600 (secure)"
else
    echo "✗ File not found: $PROTON_CONF"
    echo "Please download the config first and run this script again."
    exit 1
fi
echo ""

echo "Step 3: Test VPN Connection (Manual Test)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Let's test the VPN connection before integrating with exam system."
echo ""
read -p "Test VPN now? (yes/no): " test_vpn

if [ "$test_vpn" = "yes" ]; then
    echo ""
    echo "Starting VPN..."
    sudo wg-quick up exam
    
    echo ""
    echo "VPN Status:"
    sudo wg show
    
    echo ""
    echo "Checking IP address..."
    echo "Your IP (via VPN):"
    curl -s https://api.ipify.org
    echo ""
    
    echo ""
    read -p "VPN working? Press Enter to stop VPN..."
    
    echo "Stopping VPN..."
    sudo wg-quick down exam
    echo "✓ VPN stopped"
fi
echo ""

echo "Step 4: Update Exam System Config"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Config file location verified:"
echo "  /etc/wireguard/exam.conf ✓"
echo ""
echo "The exam system will use this config automatically."
echo ""

echo "Step 5: Test with Exam System"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Now test the VPN with the exam system in testing mode:"
echo ""
echo "  cd /home/savvy19/Desktop/product/secure-exam-system"
echo "  sudo python3 main_controller.py --dry-run"
echo ""
echo "This will:"
echo "  • Check VPN config"
echo "  • Validate all components"
echo "  • NOT actually start the exam (dry-run mode)"
echo ""
read -p "Run dry-run test now? (yes/no): " run_test

if [ "$run_test" = "yes" ]; then
    cd /home/savvy19/Desktop/product/secure-exam-system
    sudo python3 main_controller.py --dry-run
fi
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   SETUP COMPLETE!                                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "What's configured:"
echo "  ✓ ProtonVPN WireGuard config at /etc/wireguard/exam.conf"
echo "  ✓ Exam system will use this VPN"
echo "  ✓ Testing mode enabled (safe)"
echo ""
echo "Next steps:"
echo "  1. Test with: sudo python3 main_controller.py --dry-run"
echo "  2. If all good, run full test: sudo ./exam_launcher.sh --dry-run"
echo "  3. For actual exam: sudo ./exam_launcher.sh"
echo ""
echo "Note: VPN will route ALL traffic through ProtonVPN"
echo "      Only codeforces.com will be accessible"
echo ""
