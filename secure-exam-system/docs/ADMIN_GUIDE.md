# Administrator Guide - Secure Exam System

## For Exam Administrators

This guide provides step-by-step instructions for setting up, running, and managing secure exams.

---

## Table of Contents

1. [Pre-Exam Setup](#pre-exam-setup)
2. [Exam Day Procedures](#exam-day-procedures)
3. [Monitoring During Exam](#monitoring-during-exam)
4. [Handling Issues](#handling-issues)
5. [Post-Exam Procedures](#post-exam-procedures)
6. [Advanced Configuration](#advanced-configuration)

---

## Pre-Exam Setup

### Timeline: 1 Week Before

#### 1. System Installation

```bash
# Install on all student machines
cd /home/savvy19/Desktop/product
git clone <repository-url> secure-exam-system
cd secure-exam-system

# Install dependencies
sudo apt update
sudo apt install -y python3 python3-pip wireguard google-chrome-stable auditd
pip3 install -r requirements.txt

# Validate installation
python3 config_validator.py
```

#### 2. VPN Configuration

```bash
# Set up ProtonVPN
sudo ./setup_protonvpn.sh

# Test VPN connectivity
sudo wg-quick up exam
curl https://api.ipify.org  # Should show VPN IP
sudo wg-quick down exam
```

#### 3. Test Run

```bash
# Run comprehensive test
sudo ./test_complete.sh

# Verify all components work
# - VPN connects
# - Domain filter works
# - Browser launches in kiosk mode
# - Audit logging active
```

---

### Timeline: 1 Day Before

#### 1. Configure Exam Settings

Edit `config/system_config.json`:

```json
{
  "mode": "testing",  // Keep as testing for pre-exam test
  "exam": {
    "duration_minutes": 180,  // Set exam duration
    "start_url": "https://codeforces.com/contest/1234",  // Exam URL
    "exam_name": "Midterm Programming Exam",
    "allow_early_finish": false
  },
  "network": {
    "allowed_domains": [
      "codeforces.com",
      "*.codeforces.com"
      // Add any other required domains
    ]
  }
}
```

#### 2. Validate Configuration

```bash
python3 config_validator.py
```

Expected output:
```
✓ Loaded configuration from config/system_config.json
✓ Project root: /home/savvy19/Desktop/product/secure-exam-system
✓ VPN config: /etc/wireguard/exam.conf
✓ Browser: /usr/bin/google-chrome
✓ Allowed domains: 5 configured
✓ All critical validations passed
```

#### 3. Test with Sample Student

```bash
# Run in testing mode
sudo ./exam_launcher.sh

# Verify:
# - Browser opens to correct URL
# - Only allowed domains accessible
# - Cannot exit browser
# - Cannot open other apps
```

---

### Timeline: 1 Hour Before

#### 1. Final Checks

**On each student machine**:

```bash
# Check system status
python3 config_validator.py

# Check VPN credentials
sudo cat /etc/wireguard/exam.conf | grep PrivateKey

# Check browser
google-chrome --version

# Check disk space
df -h /var/log

# Check internet
ping -c 3 8.8.8.8
```

#### 2. Switch to Production Mode

```bash
# Edit config
nano config/system_config.json

# Change mode to "production"
{
  "mode": "production",
  ...
}

# Validate
python3 config_validator.py
```

#### 3. Prepare Emergency Tools

```bash
# Make emergency scripts accessible
chmod +x EMERGENCY_RESTORE_NETWORK.sh
chmod +x utils/emergency_shutdown.sh

# Test emergency restore (then re-enable)
sudo ./EMERGENCY_RESTORE_NETWORK.sh
# ... verify network restored ...
# Re-enable security for exam
```

---

## Exam Day Procedures

### Starting the Exam

#### Step 1: Verify All Students Ready

**Checklist per student**:
- [ ] Laptop powered on and charged
- [ ] All applications closed
- [ ] VPN disabled (if personal VPN)
- [ ] Desk cleared
- [ ] Student ID verified

#### Step 2: Start Exam System

```bash
# On each student machine (or via automation)
sudo ./exam_launcher.sh
```

**What happens**:
1. VPN tunnel established
2. Domain filter activated
3. Process monitor started
4. Browser launches in kiosk mode
5. Student sees exam platform

#### Step 3: Verify System Status

**On each machine, check**:

```bash
# VPN status
sudo wg show
# Should show: interface: exam, latest handshake: X seconds ago

# iptables rules
sudo iptables -L EXAM_FILTER -v -n
# Should show: ACCEPT rules for allowed domains

# Browser process
ps aux | grep chrome
# Should show: google-chrome --kiosk ...

# Audit logging
sudo ausearch -k app_exec -ts today | tail -n 5
# Should show: recent execve events
```

#### Step 4: Announce Start Time

```bash
# Note start time
echo "Exam started at $(date)" >> /var/log/secure-exam/exam-session.log

# Set timer for exam duration
# (System will auto-stop after duration_minutes)
```

---

## Monitoring During Exam

### Real-Time Monitoring

#### Monitor VPN Status

```bash
# Check VPN on all machines
watch -n 10 'sudo wg show'

# Alert if handshake > 2 minutes old
```

#### Monitor Network Activity

```bash
# Watch for blocked attempts
sudo tail -f /var/log/kern.log | grep "EXAM_FILTER"

# Example output:
# [12345.678] EXAM_FILTER DROP IN= OUT=wg0 SRC=10.2.0.2 DST=142.250.185.46
```

#### Monitor Process Violations

```bash
# Watch for unauthorized app launches
sudo tail -f /var/log/secure-exam/exam.log | grep "BLOCKED"

# Example output:
# 2025-11-26 10:15:23 - BLOCKED: User attempted to launch 'code'
```

#### Monitor Audit Logs

```bash
# Watch for suspicious execve calls
sudo ausearch -k app_exec -ts recent -i | grep -v chrome | grep -v systemd

# Any non-system processes should be investigated
```

### Periodic Checks (Every 15 Minutes)

```bash
# Create monitoring script
cat > monitor_exam.sh << 'EOF'
#!/bin/bash
echo "=== Exam Monitor - $(date) ==="

# Check VPN on all machines
echo "VPN Status:"
sudo wg show | grep -E "interface|latest handshake"

# Check for blocked attempts
echo "Blocked Attempts (last 15 min):"
sudo journalctl -k --since "15 minutes ago" | grep EXAM_FILTER | wc -l

# Check process violations
echo "Process Violations:"
sudo grep BLOCKED /var/log/secure-exam/exam.log | tail -n 5

echo "==================================="
EOF

chmod +x monitor_exam.sh

# Run every 15 minutes
watch -n 900 ./monitor_exam.sh
```

---

## Handling Issues

### Common Issues and Solutions

#### Issue: Student Cannot Access Exam Site

**Symptoms**: Browser shows "Connection refused" or "Cannot reach"

**Diagnosis**:
```bash
# Check VPN
sudo wg show
# If no handshake, VPN is down

# Check domain filter
sudo iptables -L EXAM_FILTER -v -n | grep codeforces
# Should show ACCEPT rules

# Test connectivity
curl -I https://codeforces.com
```

**Solutions**:
1. **VPN down**: Restart VPN
   ```bash
   sudo wg-quick down exam
   sudo wg-quick up exam
   ```

2. **Domain not whitelisted**: Add to config
   ```bash
   # Edit config/system_config.json
   # Add domain to allowed_domains
   # Restart domain filter
   ```

3. **DNS issue**: Check DNS server
   ```bash
   nslookup codeforces.com
   # Should resolve to IP
   ```

---

#### Issue: Student Locked Out (Can't Do Anything)

**Symptoms**: Browser frozen, keyboard not responding

**Emergency Solution**:
```bash
# On affected machine
sudo ./EMERGENCY_RESTORE_NETWORK.sh

# This will:
# - Stop domain filter
# - Stop VPN
# - Restore network access
# - Allow student to continue

# After issue resolved, restart exam system
sudo ./exam_launcher.sh
```

---

#### Issue: Student Trying to Cheat

**Symptoms**: Audit logs show unauthorized app launches

**Investigation**:
```bash
# Check what they tried to launch
sudo ausearch -k app_exec -ts today | grep -v chrome

# Example output:
# type=EXECVE msg=audit(...): argc=1 a0="code"
# This shows student tried to launch VS Code
```

**Actions**:
1. **Document the attempt**:
   ```bash
   echo "$(date) - Student X attempted to launch unauthorized app" >> /var/log/secure-exam/violations.log
   ```

2. **Warn the student** (if first offense)

3. **Flag for review** (academic integrity)

4. **Continue monitoring** that student closely

---

#### Issue: Network Outage

**Symptoms**: All students lose connectivity

**Immediate Actions**:
1. **Pause exam timer** (if platform supports)
2. **Announce to students**: "Network issue, please wait"
3. **Check network**:
   ```bash
   ping 8.8.8.8
   # If fails, network is down
   ```

**Recovery**:
1. **If brief outage** (< 5 min):
   - Wait for network to restore
   - VPN should auto-reconnect
   - Students can continue

2. **If extended outage** (> 5 min):
   - Consider postponing exam
   - Or switch to offline mode (if supported)

---

## Post-Exam Procedures

### Stopping the Exam

#### Automatic Stop

The system will automatically stop after `duration_minutes`:
- Browser closes
- VPN disconnects
- Domain filter removed
- Logs saved

#### Manual Stop

```bash
# If need to stop early
sudo pkill -f exam_launcher.sh

# Or use emergency shutdown
sudo ./utils/emergency_shutdown.sh
```

### Collecting Logs

```bash
# Create log archive
sudo tar -czf exam-logs-$(date +%Y%m%d-%H%M).tar.gz \
    /var/log/secure-exam/ \
    /var/log/audit/audit.log

# Copy to secure location
sudo cp exam-logs-*.tar.gz /path/to/secure/storage/

# Verify archive
tar -tzf exam-logs-*.tar.gz | head -n 20
```

### Log Analysis

```bash
# Analyze audit logs
python3 monitoring/log_analyzer.py \
    --date $(date +%Y-%m-%d) \
    --report \
    --output exam-report.csv

# Review violations
grep BLOCKED /var/log/secure-exam/exam.log > violations.txt

# Count unauthorized attempts per student
# (requires correlation with student IDs)
```

### Cleanup

```bash
# Clear browser profiles
sudo rm -rf /tmp/exam-browser-profile*

# Clear temporary files
sudo rm -rf /tmp/app-log-test*

# Rotate logs (if needed)
sudo logrotate /etc/logrotate.d/secure-exam
```

---

## Advanced Configuration

### Custom Domain Whitelist

```json
{
  "network": {
    "allowed_domains": [
      "example.com",
      "*.example.com",
      "cdn.example.net",
      "api.example.org"
    ]
  }
}
```

**Wildcard support**:
- `*.example.com` matches `sub.example.com`, `api.example.com`
- Does NOT match `example.com` (add separately)

### Custom Process Allowlist

```json
{
  "process_allowlist": {
    "system_processes": [
      "systemd",
      "dbus-daemon",
      "Xorg",
      "custom-app"  // Add custom allowed process
    ]
  }
}
```

### Exam Duration and Auto-Stop

```json
{
  "exam": {
    "duration_minutes": 180,  // 3 hours
    "allow_early_finish": false,  // Students cannot exit early
    "auto_stop": true  // System stops after duration
  }
}
```

### Logging Configuration

```json
{
  "logging": {
    "log_level": "DEBUG",  // INFO, DEBUG, WARNING, ERROR
    "log_to_file": true,
    "log_to_kernel": true,
    "audit_enabled": true
  }
}
```

---

## Troubleshooting Guide

### Quick Diagnostics

```bash
# Run full diagnostic
python3 config_validator.py --verbose

# Check all services
systemctl status auditd
systemctl status NetworkManager

# Check kernel module
lsmod | grep proc_monitor

# Check iptables
sudo iptables -L -v -n | grep EXAM
```

### Log Locations

| Log Type | Location | Purpose |
|----------|----------|---------|
| **System logs** | `/var/log/secure-exam/exam.log` | Main application log |
| **Audit logs** | `/var/log/audit/audit.log` | Kernel audit events |
| **Kernel logs** | `dmesg` | Kernel messages |
| **Network logs** | `/var/log/kern.log` | iptables drops |

### Emergency Contacts

- **Technical Support**: admin@example.com
- **Emergency Phone**: +1-XXX-XXX-XXXX
- **Documentation**: https://support.example.com

---

## Best Practices

### Before Exam
- ✅ Test on identical hardware
- ✅ Have backup machines ready
- ✅ Print emergency procedures
- ✅ Brief students on what to expect

### During Exam
- ✅ Monitor continuously
- ✅ Document all issues
- ✅ Stay calm and professional
- ✅ Have emergency scripts ready

### After Exam
- ✅ Collect all logs immediately
- ✅ Backup logs securely
- ✅ Review for violations
- ✅ Document lessons learned

---

## Appendix

### Exam Day Checklist

**Pre-Exam** (1 hour before):
- [ ] All machines powered on
- [ ] Configuration validated
- [ ] VPN tested
- [ ] Browser tested
- [ ] Emergency scripts ready
- [ ] Backup machines ready

**Start of Exam**:
- [ ] Students seated
- [ ] IDs checked
- [ ] Desks cleared
- [ ] Exam system started
- [ ] All machines verified
- [ ] Start time logged

**During Exam**:
- [ ] Monitor VPN status
- [ ] Monitor network activity
- [ ] Monitor process violations
- [ ] Document issues
- [ ] Assist students as needed

**End of Exam**:
- [ ] System stopped
- [ ] Logs collected
- [ ] Students dismissed
- [ ] Machines cleaned up
- [ ] Logs backed up

---

**Questions?** Contact technical support.

**Last Updated**: 2025-11-26
