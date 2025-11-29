# Manual Testing Guide - Red Team Patches

## Prerequisites
```bash
cd ~/secure-exam-system

# Ensure you have the allowlist built
python3 process_manager/allowlist_builder.py

# Create integrity baseline
python3 security/integrity_checker.py baseline
```

---

## Test 1: Python Subprocess Attack (PATCHED)

### Attack (Should FAIL now):
```bash
# Try to spawn a shell via Python
python3 -c "import os; os.system('bash')"

# Or subprocess
python3 -c "import subprocess; subprocess.run(['bash'])"
```

**Expected Result:** ❌ Process monitor should detect and block (or log if enforcement disabled)

**Check logs:**
```bash
# You should see: "🚨 PYTHON ATTACK DETECTED: os.system" or "subprocess"
```

---

## Test 2: Pre-Exam Process Launch (PATCHED)

### Before Patch (Old vulnerability):
```bash
# Student starts Firefox BEFORE exam
firefox &

# Then starts exam system
# Old system: Firefox in baseline, allowed to run ❌

# After patch: Baseline taken AFTER lockdown
# Firefox not in baseline, gets terminated ✅
```

### Test:
```bash
# 1. Start some unauthorized process
sleep 9999 &
SLEEP_PID=$!

# 2. Start exam system (it will take baseline AFTER lockdown)
sudo python3 main_controller.py --dry-run

# 3. In another terminal, check if sleep is still running
ps aux | grep "sleep 9999"

# Expected: sleep process should be terminated
```

---

## Test 3: Environment Variable Injection (PATCHED)

### Attack (Should FAIL):
```bash
# Create malicious library
cat > /tmp/evil.c << 'EOF'
#include <stdio.h>
void __attribute__((constructor)) init() {
    printf("PWNED!\n");
    system("/usr/bin/firefox &");
}
EOF

gcc -shared -fPIC /tmp/evil.c -o /tmp/evil.so

# Try to inject
export LD_PRELOAD=/tmp/evil.so
python3 -c "print('test')"
```

**Expected Result:** ❌ Security patcher clears LD_PRELOAD, injection fails

**Verify:**
```bash
# After system starts, check:
echo $LD_PRELOAD
# Should be empty
```

---

## Test 4: /tmp Cheat Files (PATCHED)

### Attack (Should FAIL):
```bash
# Before exam, create cheat file
echo "Solutions: ..." > /tmp/cheats.txt

# Start exam system (patcher clears /tmp)

# Try to read
cat /tmp/cheats.txt
```

**Expected Result:** ❌ File not found (cleared by patcher)

---

## Test 5: Symlink Attack (PATCHED)

### Attack (Should FAIL):
```bash
# Create symlink to bash
ln -s /bin/bash /tmp/my_python
chmod +x /tmp/my_python

# Try to execute
/tmp/my_python
```

**Expected Result:** ❌ Process monitor resolves symlink, detects real path is /bin/bash (not allowed)

---

## Test 6: Browser Cache (PATCHED)

### Verify cache cleared:
```bash
# Check if browser cache exists
ls -la ~/.cache/chromium/
ls -la ~/.config/chromium/Default/Cache/
```

**Expected Result:** Directories should be empty or non-existent after patcher runs

---

## Test 7: Clipboard Cheat Sheet (PATCHED)

### Attack (Should FAIL):
```bash
# Before exam, copy cheat sheet
echo "Quick solutions..." | xclip -selection clipboard

# Start exam (patcher clears clipboard)

# Try to paste
xclip -selection clipboard -o
```

**Expected Result:** ❌ Clipboard empty

---

## Full Integration Test

### Test the complete system:

```bash
# 1. Start the system in dry-run mode
sudo python3 main_controller.py --dry-run

# Should see:
# ✓ Environment sanitized
# ✓ /tmp cleaned
# ✓ Browser cache cleared
# ✓ Clipboard cleared
# ✓ Baseline taken POST-LOCKDOWN
```

### Test with enforcement:

```bash
# Terminal 1: Start system (needs sudo)
sudo python3 main_controller.py

# Terminal 2: Try attacks while system is running
python3 -c "import os; os.system('firefox')"
# Should be detected and logged

# Try to start unauthorized process
gedit &
# Should be terminated immediately
```

---

## Check Security Logs

```bash
# View process violations
grep "VIOLATION" /var/log/syslog

# View Python attack detections  
grep "PYTHON ATTACK" /var/log/syslog

# Check process enforcer status
# (if running) - shows violations count
```

---

## Testing Individual Components

### Test Security Patcher:
```bash
sudo python3 security/security_patcher.py
# Confirm when prompted
# Should see all patches applied
```

### Test Process Monitor:
```bash
 # Build allowlist first
python3 process_manager/allowlist_builder.py

# Run monitor (log-only mode)
python3 process_manager/process_monitor.py

# In another terminal, try to start unauthorized apps
firefox &
gedit &

# Monitor should log violations
```

### Test Process Enforcer:
```bash
# Run with enforcement enabled
python3 process_manager/process_enforcer.py --enforce

# In another terminal
firefox &

# Should be terminated immediately
```

---

## Automated Test Script

Create a quick test script:

```bash
cat > /tmp/test_security.sh << 'EOF'
#!/bin/bash
echo "Testing security patches..."

# Test 1: Python attack
echo -n "Test 1 (Python attack): "
python3 -c "import os; os.system('echo FAIL')" 2>/dev/null && echo "❌ VULNERABLE" || echo "✅ BLOCKED"

# Test 2: /tmp files
echo "test" > /tmp/test_file.txt
if [ -f /tmp/test_file.txt ]; then
    echo "Test 2 (/tmp): File exists (will be cleared on exam start)"
fi

# Test 3: Environment
export LD_PRELOAD=/tmp/evil.so
echo -n "Test 3 (LD_PRELOAD): "
[ -z "$LD_PRELOAD" ] && echo "✅ CLEARED" || echo "⚠️  SET (will be cleared)"

echo "Run 'sudo python3 main_controller.py --dry-run' to test all patches"
EOF

chmod +x /tmp/test_security.sh
/tmp/test_security.sh
```

---

## Expected Output (Secure System)

When properly secured, you should see:
- ✅ Python subprocess attacks blocked
- ✅ Pre-exam processes NOT in baseline
- ✅ LD_PRELOAD cleared
- ✅ /tmp cleaned
- ✅ Browser cache cleared
- ✅ Clipboard cleared
- ✅ Unauthorized processes terminated
- ✅ Symlinks resolved

---

## Troubleshooting

### If patches don't apply:
```bash
# Check if running as root
whoami  # Should be root

# Check Python packages
python3 -c "import psutil; print('OK')"

# Re-run patcher manually
sudo python3 security/security_patcher.py
```

### If process monitoring doesn't work:
```bash
# Rebuild allowlist
python3 process_manager/allowlist_builder.py

# Verify allowlist has entries
cat config/process_allowlist.json | jq '.processes | length'
# Should show > 0
```

---

## Red Team Testing Checklist

- [ ] Python subprocess attack blocked
- [ ] Pre-exam process launch prevented
- [ ] LD_PRELOAD injection blocked
- [ ] /tmp cheat files cleared
- [ ] Symlink attacks detected
- [ ] Browser cache cleared
- [ ] Clipboard cleared
- [ ] Virtual console switch blocked (if supported)
- [ ] Unauthorized processes terminated
- [ ] System locks down successfully

**All items should be checked (✅) for production deployment.**
