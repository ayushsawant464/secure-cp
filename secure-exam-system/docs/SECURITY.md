# Security Model

## Overview

This document provides a comprehensive analysis of the Secure Exam System's security model, including threat detection capabilities, limitations, and recommendations for deployment.

---

## Cheating Detection Capabilities

### ✅ Detected Threats

#### 1. Unauthorized Application Execution

**Detection Method**: Process allowlist + Kernel module auditing

**How it works**:
- Kernel module logs all `execve` syscalls
- Process monitor compares running processes against allowlist
- Unauthorized processes are terminated immediately

**Example**:
```bash
# Student attempts to open VS Code
$ code

# System response:
# - execve syscall logged to audit.log
# - Process monitor detects "code" not in allowlist
# - Process terminated within 1 second
# - Event logged with timestamp, user, PID
```

**Effectiveness**: ⭐⭐⭐⭐⭐ (Very High)

**Bypass difficulty**: Very Hard (requires kernel exploit)

---

#### 2. Unauthorized Network Access

**Detection Method**: iptables domain filtering + VPN tunneling

**How it works**:
- All traffic routed through VPN tunnel
- iptables rules drop packets to non-whitelisted domains
- DNS queries monitored and filtered

**Example**:
```bash
# Student attempts to access Google
$ curl https://google.com

# System response:
# - DNS query allowed (1.1.1.1)
# - IP resolved: 142.250.185.46
# - iptables DROP rule matches (not in allowlist)
# - Packet dropped, logged to kernel
```

**Effectiveness**: ⭐⭐⭐⭐⭐ (Very High)

**Bypass difficulty**: Very Hard (requires kernel network stack manipulation)

---

#### 3. Browser Escape Attempts

**Detection Method**: Kiosk mode + Key blocking + Window manager lockdown

**How it works**:
- Browser runs in fullscreen kiosk mode
- Critical keyboard shortcuts disabled via `xmodmap`
- Window manager prevents focus changes

**Blocked shortcuts**:
- `Alt+F4` (Close window)
- `Alt+Tab` (Switch windows)
- `F11` (Exit fullscreen)
- `Ctrl+Alt+F1-F6` (Virtual console switch)
- `Ctrl+Shift+Esc` (Task manager)
- `Super+L` (Lock screen)

**Effectiveness**: ⭐⭐⭐⭐ (High)

**Bypass difficulty**: Medium-Hard (requires X11 knowledge)

---

#### 4. Virtual Console Switching

**Detection Method**: TTY access control (production mode)

**How it works**:
- Virtual console switching disabled in production
- TTY devices have restricted permissions
- Attempts logged to audit

**Effectiveness**: ⭐⭐⭐ (Medium)

**Bypass difficulty**: Medium (can be bypassed with physical access)

**Note**: Disabled in testing mode to prevent developer lockout

---

#### 5. File System Modifications

**Detection Method**: Integrity checker with inotify

**How it works**:
- Critical files monitored for changes
- Modifications logged in real-time
- Checksums verified periodically

**Monitored files**:
- System binaries (`/usr/bin/*`)
- Configuration files (`/etc/*`)
- Exam system files

**Effectiveness**: ⭐⭐⭐⭐ (High)

**Bypass difficulty**: Hard (requires root access)

---

#### 6. Clipboard Manipulation

**Detection Method**: Clipboard clearing on start/stop

**How it works**:
- Clipboard wiped when exam starts
- Clipboard wiped when exam ends
- Prevents pre-loaded solutions

**Effectiveness**: ⭐⭐⭐ (Medium)

**Bypass difficulty**: Easy (can copy during exam)

**Limitation**: Does not prevent copying during exam

---

#### 7. Browser Cache Exploitation

**Detection Method**: Cache clearing before exam

**How it works**:
- Browser cache deleted on startup
- Prevents accessing cached solutions
- Fresh browser profile created

**Effectiveness**: ⭐⭐⭐⭐ (High)

**Bypass difficulty**: Hard (requires browser exploit)

---

### ❌ Undetected Threats

#### 1. Physical Notes/Books

**Why not detected**: No camera or visual monitoring

**Risk level**: Medium

**Mitigation**:
- Physical proctoring required
- Desk inspection before exam
- Clear desk policy

---

#### 2. Second Device Usage

**Why not detected**: No device detection or network scanning

**Risk level**: High

**Mitigation**:
- Physical proctoring required
- Phone collection before exam
- Signal jamming (if legal)

**Example scenarios**:
- Student uses phone to search solutions
- Student uses tablet to communicate with others
- Student uses smartwatch to view notes

---

#### 3. Screen Sharing

**Why not detected**: No screen capture or network traffic analysis

**Risk level**: High

**Mitigation**:
- Physical proctoring required
- Camera monitoring
- Network traffic analysis (advanced)

**Example scenarios**:
- Student shares screen via Discord/Zoom
- Student uses screen mirroring to another device
- Student records screen for later review

---

#### 4. Camera-Based Cheating

**Why not detected**: No camera monitoring

**Risk level**: Medium

**Mitigation**:
- Physical proctoring required
- Camera placement to monitor student
- Anti-camera policies

**Example scenarios**:
- Student photographs screen
- Student uses hidden camera
- Student uses glasses with camera

---

#### 5. Collusion Between Students

**Why not detected**: No communication monitoring

**Risk level**: High

**Mitigation**:
- Physical separation of students
- Randomized question sets
- Different exam versions

**Example scenarios**:
- Students whisper answers
- Students use hand signals
- Students share solutions verbally

---

#### 6. Pre-Downloaded Solutions

**Why not detected**: No memory inspection or file system search

**Risk level**: Medium

**Mitigation**:
- Randomized questions
- Time-limited questions
- Novel problem sets

**Example scenarios**:
- Student memorizes solutions
- Student has solutions in browser bookmarks
- Student has solutions in allowed website

---

#### 7. Hardware Keyloggers

**Why not detected**: No hardware inspection

**Risk level**: Low

**Mitigation**:
- Physical inspection of machines
- Use of trusted hardware
- USB port blocking

---

## Threat Model

### Assumptions

1. **Physical Security**: Exam conducted in controlled environment
2. **Trusted Administrator**: Person running system is trustworthy
3. **Network Security**: Local network is not compromised
4. **Hardware Integrity**: Student machines are not pre-compromised
5. **Software Integrity**: Operating system is not backdoored

### Attack Vectors

#### High Risk

| Attack Vector | Likelihood | Impact | Detection | Mitigation |
|---------------|------------|--------|-----------|------------|
| Second device usage | High | High | None | Physical proctoring |
| Screen sharing | Medium | High | None | Physical proctoring |
| Collusion | Medium | High | None | Physical separation |

#### Medium Risk

| Attack Vector | Likelihood | Impact | Detection | Mitigation |
|---------------|------------|--------|-----------|------------|
| Physical notes | Medium | Medium | None | Desk inspection |
| Pre-downloaded solutions | Low | Medium | None | Randomized questions |
| Camera-based | Low | Medium | None | Camera monitoring |

#### Low Risk

| Attack Vector | Likelihood | Impact | Detection | Mitigation |
|---------------|------------|--------|-----------|------------|
| Browser exploit | Very Low | High | Partial | Keep browser updated |
| Kernel exploit | Very Low | High | None | Keep kernel updated |
| Hardware keylogger | Very Low | Low | None | Hardware inspection |

---

## Security Layers

### Layer 1: Network Isolation

**Technology**: WireGuard VPN + iptables

**Threat Coverage**:
- ✅ Unauthorized website access
- ✅ Local network exploitation
- ✅ DNS tunneling
- ❌ Second device usage

**Bypass Methods**:
- Kernel network stack exploit
- VPN credential theft
- Physical network tap

**Recommended Hardening**:
- Use strong VPN credentials
- Enable VPN kill switch
- Monitor VPN connection status

---

### Layer 2: Process Control

**Technology**: Process allowlist + Kernel module

**Threat Coverage**:
- ✅ Unauthorized application execution
- ✅ Background processes
- ✅ Script execution
- ❌ In-browser exploits

**Bypass Methods**:
- Kernel module unloading (requires root)
- Process injection
- Privilege escalation

**Recommended Hardening**:
- Sign kernel module
- Enable kernel module signing verification
- Use AppArmor to confine processes

---

### Layer 3: Browser Lockdown

**Technology**: Kiosk mode + Key blocking

**Threat Coverage**:
- ✅ Keyboard shortcut escape
- ✅ Window switching
- ✅ DevTools access
- ❌ Browser exploits

**Bypass Methods**:
- X11 window manager tricks
- Browser extension exploit
- JavaScript escape

**Recommended Hardening**:
- Use minimal window manager
- Disable browser extensions
- Keep browser updated

---

### Layer 4: System Hardening

**Technology**: AppArmor + Environment cleanup

**Threat Coverage**:
- ✅ File system access
- ✅ System call restrictions
- ✅ Clipboard exploitation
- ❌ Kernel exploits

**Bypass Methods**:
- AppArmor profile bypass
- Kernel vulnerability
- Privilege escalation

**Recommended Hardening**:
- Regularly update AppArmor profiles
- Enable kernel hardening features
- Use SELinux (alternative to AppArmor)

---

## Deployment Recommendations

### Minimum Security (Low Stakes Exam)

- ✅ Network filtering
- ✅ Process monitoring (log-only)
- ✅ Kiosk browser
- ❌ Physical proctoring

**Use case**: Practice exams, low-stakes quizzes

---

### Standard Security (Medium Stakes Exam)

- ✅ Network filtering
- ✅ Process monitoring (enforcement)
- ✅ Kiosk browser with key blocking
- ✅ Basic physical proctoring
- ✅ Audit logging

**Use case**: Regular exams, assignments

---

### Maximum Security (High Stakes Exam)

- ✅ All technical controls enabled
- ✅ Strict physical proctoring
- ✅ Camera monitoring
- ✅ Phone collection
- ✅ Desk inspection
- ✅ Physical separation
- ✅ Real-time monitoring dashboard

**Use case**: Final exams, certification tests

---

## Audit and Compliance

### Logging

All security events are logged to multiple locations:

1. **Kernel Audit Log** (`/var/log/audit/audit.log`)
   - Process execution (`execve` syscalls)
   - File access attempts
   - Network connections

2. **System Log** (`/var/log/secure-exam/exam.log`)
   - VPN status changes
   - Domain filter events
   - Process terminations

3. **iptables Log** (kernel ring buffer)
   - Dropped packets
   - Allowed connections

### Log Retention

- **Minimum**: 30 days
- **Recommended**: 90 days
- **High-stakes exams**: 1 year

### Log Analysis

Use the provided log analyzer:

```bash
python3 monitoring/log_analyzer.py --date 2025-11-26 --report
```

---

## Known Limitations

1. **No webcam monitoring**: Cannot detect physical cheating
2. **No keystroke analysis**: Cannot detect typing patterns
3. **No screen recording**: Cannot review exam session
4. **No AI proctoring**: Cannot detect suspicious behavior
5. **No biometric verification**: Cannot verify student identity

---

## Future Enhancements

1. **Webcam Integration**: Monitor student via webcam
2. **AI Proctoring**: Detect suspicious behavior
3. **Screen Recording**: Record exam session for review
4. **Biometric Verification**: Verify student identity
5. **Network Traffic Analysis**: Deep packet inspection
6. **Browser Fingerprinting**: Detect browser tampering

---

## Conclusion

The Secure Exam System provides **strong technical controls** against common cheating methods, but **cannot replace physical proctoring** for high-stakes exams. It is most effective when combined with:

- Physical proctoring
- Camera monitoring
- Randomized questions
- Time pressure
- Novel problem sets

**Recommended use**: Medium to high-stakes exams with physical proctoring.

---

**Last Updated**: 2025-11-26  
**Version**: 1.0.0
