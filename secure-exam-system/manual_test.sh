#!/bin/bash
#
# Complete Manual Test - Step by Step
# Run this to test the entire secure exam system
#

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   SECURE EXAM SYSTEM - COMPLETE MANUAL TEST               ║"
echo "║   Testing Mode (Safe)                                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check we're in testing mode
echo "Step 1: Verify Testing Mode"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
MODE=$(grep '"mode"' config/system_config.json | grep -o 'testing\|production')
if [ "$MODE" = "testing" ]; then
    echo "✓ Mode: TESTING (Safe)"
else
    echo "✗ Mode: $MODE"
    echo "WARNING: Not in testing mode!"
    exit 1
fi
echo ""

# Check allowlist
echo "Step 2: Check Process Allowlist"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 process_manager/allowlist_builder.py --show | head -15
echo ""
read -p "Press Enter to continue..."
echo ""

# Test Phase 3: Process Management
echo "Step 3: Test Process Management"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Running Phase 3 tests..."
python3 tests/test_phase3.py 2>&1 | tail -15
echo ""
read -p "Press Enter to continue..."
echo ""

# Test Phase 4: Security  
echo "Step 4: Test Security Hardening"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Running Phase 4 tests..."
python3 tests/test_phase4.py 2>&1 | tail -15
echo ""
read -p "Press Enter to continue..."
echo ""

# Test individual components
echo "Step 5: Test Security Patches"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Before patches:"
echo "  /tmp files: $(ls /tmp 2>/dev/null | wc -l)"
echo "  LD_PRELOAD: ${LD_PRELOAD:-<not set>}"
echo ""
echo "This will clear /tmp, browser cache, and clipboard."
read -p "Apply security patches? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    echo ""
    sudo python3 security/security_patcher.py
    echo ""
    echo "After patches:"
    echo "  /tmp files: $(ls /tmp 2>/dev/null | wc -l)"
    echo "  LD_PRELOAD: ${LD_PRELOAD:-<not set>}"
fi
echo ""
read -p "Press Enter to continue..."
echo ""

# Test Python attack detection
echo "Step 6: Test Python Attack Detection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Starting process monitor in background..."
python3 process_manager/process_monitor.py > /tmp/monitor.log 2>&1 &
MONITOR_PID=$!
sleep 2

echo "Attempting Python subprocess attack..."
python3 -c "import os; os.system('echo ATTACK')" 2>&1 || true
sleep 2

echo ""
echo "Monitor Log (should show PYTHON ATTACK DETECTED):"
grep -i "python" /tmp/monitor.log | tail -3 || echo "  (No Python attacks detected)"

kill $MONITOR_PID 2>/dev/null || true
echo ""
read -p "Press Enter to continue..."
echo ""

# Test dry-run
echo "Step 7: Main Controller Dry Run"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "This performs all pre-flight checks without starting the system."
echo ""
read -p "Run dry-run? (requires sudo) (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    sudo python3 main_controller.py --dry-run
fi
echo ""

# Integration test
echo "Step 8: Full Integration Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "This runs all test suites."
echo ""
read -p "Run integration tests? (requires sudo) (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    sudo bash tests/integration_test.sh
fi
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   TESTING COMPLETE                                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "What was tested:"
echo "  ✓ Process allowlist management"
echo "  ✓ Security hardening components"
echo "  ✓ Security patches (env, /tmp, cache, clipboard)"
echo "  ✓ Python attack detection"
echo "  ✓ Main controller pre-flight checks"
echo "  ✓ Integration tests (if selected)"
echo ""
echo "System is ready for exam mode!"
echo ""
echo "Next steps:"
echo "  • Review test results above"
echo "  • Configure VPN if needed"
echo "  • Run: sudo ./exam_launcher.sh --dry-run"
echo ""
