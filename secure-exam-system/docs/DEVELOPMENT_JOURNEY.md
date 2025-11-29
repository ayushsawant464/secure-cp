# Development Journey - Secure Exam System

## Project Overview

**Project Name**: Secure Exam System  
**Duration**: November 2025  
**Purpose**: Multi-layered Linux-based lockdown system for conducting secure online programming exams  
**Final Status**: ✅ Production-ready

---

## Table of Contents

1. [SDLC Overview](#sdlc-overview)
2. [Implementation Journey](#implementation-journey)
3. [Bugs Encountered & Solutions](#bugs-encountered--solutions)
4. [Lessons Learned](#lessons-learned)
5. [Tips for Future Projects](#tips-for-future-projects)
6. [Technical Achievements](#technical-achievements)

---

## SDLC Overview

### Phase 1: Planning & Requirements (Week 1)

**Objectives**:
- Define security requirements
- Identify threat model
- Design system architecture
- Choose technology stack

**Deliverables**:
- ✅ Architecture design document
- ✅ Component breakdown
- ✅ Technology selection (WireGuard, iptables, Python, AppArmor)

**Key Decisions**:
- **VPN**: WireGuard (modern, fast, secure)
- **Filtering**: iptables (kernel-level, reliable)
- **Language**: Python (rapid development, maintainability)
- **Browser**: Chrome/Chromium (kiosk mode support)

---

### Phase 2: Network Layer Implementation

**Components Built**:
1. **VPN Manager** (`network/vpn_manager.py`)
   - WireGuard tunnel management
   - ProtonVPN integration
   - Kill switch implementation

2. **Domain Filter** (`network/domain_filter.py`)
   - iptables-based domain whitelisting
   - IPv4 and IPv6 support
   - DNS resolution and filtering

3. **Kiosk Browser** (`network/kiosk_browser.py`)
   - Fullscreen browser lockdown
   - Keyboard shortcut blocking
   - DevTools disabling

**Testing**:
- Created `test_phase2.py` for automated testing
- Manual testing with `test_vpn_production.sh`

**Challenges**:
- IPv6 handling (separate iptables chains needed)
- DNS resolution timing issues
- Browser escape prevention

---

### Phase 3: Process Management Implementation

**Components Built**:
1. **Process Monitor** (`process_manager/process_monitor.py`)
   - Process allowlist enforcement
   - Real-time process scanning
   - Unauthorized app termination

2. **Kernel Module** (`process_manager/kernel_monitor/proc_monitor.c`)
   - `execve` syscall logging
   - Kernel-level audit trail
   - Integration with auditd

3. **Process Enforcer** (`process_manager/process_enforcer.py`)
   - Policy enforcement
   - Process termination logic

**Testing**:
- Created `test_phase3.py`
- Kernel module compilation and loading
- Audit log verification

**Challenges**:
- Kernel module compilation for different kernel versions
- auditd integration and configuration
- Process allowlist maintenance

---

### Phase 4: Security Hardening

**Components Built**:
1. **Security Patcher** (`security/security_patcher.py`)
   - Environment cleanup
   - Clipboard clearing
   - Browser cache deletion

2. **System Lockdown** (`security/system_lockdown.py`)
   - AppArmor profile management
   - Virtual console lockdown
   - System-wide restrictions

3. **Integrity Checker** (`security/integrity_checker.py`)
   - File system monitoring
   - Checksum verification
   - Tamper detection

**Testing**:
- Created `test_phase4.py`
- Red team security analysis
- Penetration testing

**Challenges**:
- Virtual console lockdown (risk of developer lockout)
- AppArmor profile complexity
- Balance between security and usability

---

### Phase 5: Integration & Testing

**Activities**:
1. **Main Controller** (`main_controller.py`)
   - Orchestrated all components
   - Startup/shutdown sequences
   - Error handling

2. **Integration Testing**
   - Created `test_complete.sh`
   - End-to-end testing
   - Production simulation

3. **Documentation**
   - Initial README
   - Safety guidelines
   - Bug tracking

**Challenges**:
- Component initialization order
- Error propagation
- Cleanup on failure

---

### Phase 6: Production testing Readiness

**Activities**:
1. **Dynamic Configuration**
   - Enhanced `system_config.json`
   - Path variable support
   - Configuration validator

2. **Comprehensive Documentation**
   - README rewrite
   - Security model documentation
   - User and admin guides

3. **Code Refactoring**
   - Environment variable support
   - Improved maintainability

**Deliverables**:
- ✅ Production-ready system
- ✅ Complete documentation suite
- ✅ Deployment guides

---

## Implementation Journey

### Day 1-15

**What I did**
- Learn the requirements and possible problems/solutions, learn technology, tools, concepts
- Go through existing implementation, technical blogs
- Go through github repos for example linux src code 
- Compare tradeoffs between selected implementation based on complexity vs features

## Day 16

**Find domains and subdomains of codeforces.com usig subfinder**

**Use antigravity to make a POC**

**What we built**:
- Project structure
- Configuration system
- VPN manager basics

**Key moment**: Successfully established first WireGuard tunnel

**Learning**: VPN configuration is critical - spent significant time understanding WireGuard config format


**What we built**:
- Domain filter with iptables
- DNS resolution
- IPv4/IPv6 support

**Key moment**: First successful block of unauthorized domain

**Challenge**: IPv6 was initially forgotten, leading to bypass vulnerability

**Solution**: Implemented separate IPv6 iptables chains


**What we built**:
- Kiosk browser implementation
- Keyboard shortcut blocking
- DevTools disabling

**Key moment**: Successfully blocked Alt+F4 and Alt+Tab

**Challenge**: Finding the right combination of Chrome flags

**Solution**: Extensive testing with different flag combinations

**What we built**:
- Process allowlist
- Kernel module for execve logging
- Integration with auditd

**Key moment**: First execve event logged to audit.log

**Challenge**: Kernel module compilation errors

**Solution**: Installed correct kernel headers, fixed Makefile


**What we built**:
- Security patcher
- AppArmor profiles
- Integrity checker

**Key moment**: Successfully confined browser with AppArmor

**Challenge**: Virtual console lockdown caused developer lockout

**Solution**: Implemented testing mode with lockdown disabled

**Activities**:
- Comprehensive testing
- Bug fixing
- Performance optimization

**Major bugs found**: See [Bugs Encountered](#bugs-encountered--solutions)

**Activities**:
- Documentation writing
- Configuration enhancement
- Code refactoring

**Key moment**: System validated as production-ready

---

## Bugs Encountered & Solutions

### Bug #1: JSON Configuration Corruption

**Symptom**: `JSONDecodeError: Expecting ',' delimiter`

**Root Cause**: 
- Shell script using `sed` to modify JSON
- `sed` command didn't preserve commas
- Resulted in malformed JSON

**Impact**: System couldn't start, all components failed

**Solution**:
```python
# Before (shell script)
sed -i 's/"mode": "testing"/"mode": "production"/' config.json

# After (Python helper)
def set_mode(new_mode):
    with open('config.json', 'r') as f:
        config = json.load(f)
    config['mode'] = new_mode
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
```

**Lesson**: Never use `sed` to modify JSON - always use proper JSON parser

**Files affected**: 
- `test_app_kernel_logging.sh`
- `config/system_config.json`

---

### Bug #2: IPv6 Bypass Vulnerability

**Symptom**: Students could access blocked sites via IPv6

**Root Cause**: 
- Only implemented IPv4 iptables rules
- Forgot about IPv6 entirely
- Modern browsers prefer IPv6

**Impact**: Critical security vulnerability

**Solution**:
```python
# Added separate IPv6 handling
self.allowed_ips_v6 = set()

# Separate ip6tables rules
subprocess.run(['ip6tables', '-A', 'EXAM_FILTER', '-d', ipv6, '-j', 'ACCEPT'])
```

**Lesson**: Always consider both IPv4 and IPv6 in network security

**Files affected**: `network/domain_filter.py`

---

### Bug #3: Virtual Console Lockout

**Symptom**: Developers locked out of system during testing

**Root Cause**:
- Virtual console lockdown too aggressive
- No escape mechanism in testing mode
- Required hard reboot to recover

**Impact**: Development workflow disrupted

**Solution**:
```python
# Disable virtual console lockdown in testing mode
if self.mode == 'testing':
    logger.info("Testing mode: Virtual console lockdown DISABLED")
    return
```

**Lesson**: Always have a "safe mode" for development

**Files affected**: `security/system_lockdown.py`

---

### Bug #4: DNS Resolution Race Condition

**Symptom**: Intermittent failures to resolve allowed domains

**Root Cause**:
- DNS resolution happened before VPN established
- Timing issue with network initialization
- DNS queries went to wrong server

**Impact**: Students couldn't access exam site

**Solution**:
```python
# Wait for VPN to be fully established
time.sleep(3)  # Allow VPN routing to stabilize

# Then resolve domains
for domain in self.allowed_domains:
    ips = self._resolve_domain(domain)
```

**Lesson**: Network operations need proper sequencing and delays

**Files affected**: `network/domain_filter.py`

---

### Bug #5: Browser Cache Persistence

**Symptom**: Students could access cached solutions from previous exams

**Root Cause**:
- Browser cache not cleared between exams
- Persistent user profile
- Cached pages accessible offline

**Impact**: Cheating vulnerability

**Solution**:
```python
# Clear cache before exam
cache_dir = os.path.expanduser('~/.cache/google-chrome')
if os.path.exists(cache_dir):
    shutil.rmtree(cache_dir)

# Use temporary profile
args.append(f'--user-data-dir=/tmp/exam-browser-{uuid.uuid4()}')
```

**Lesson**: Always clean up persistent state between sessions

**Files affected**: `security/security_patcher.py`

---

### Bug #6: auditd Not Installed

**Symptom**: No audit logs generated, `ausearch` command not found

**Root Cause**:
- auditd not installed by default on some systems
- Scripts assumed auditd availability
- No fallback mechanism

**Impact**: No audit trail for security events

**Solution**:
```bash
# Check if auditctl exists before using
if command -v auditctl &> /dev/null; then
    auditctl -a always,exit -F arch=b64 -S execve
else
    echo "⚠️ auditctl not found. Skipping audit configuration."
fi
```

**Lesson**: Never assume system tools are installed - always check

**Files affected**: `test_app_kernel_logging.sh`

---

### Bug #7: Hardcoded Paths

**Symptom**: System only worked in specific installation directory

**Root Cause**:
- Paths hardcoded in Python modules
- No configuration flexibility
- Not portable across systems

**Impact**: Difficult to deploy on different machines

**Solution**:
```python
# Before
config_path = "/home/savvy19/Desktop/product/secure-exam-system/config/system_config.json"

# After
if config_path is None:
    config_path = os.environ.get('EXAM_CONFIG')
    if config_path is None:
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(script_dir, 'config', 'system_config.json')
```

**Lesson**: Always use relative paths or configuration

**Files affected**: 
- `network/domain_filter.py`
- `network/kiosk_browser.py`
- `network/vpn_manager.py`

---

### Bug #8: iptables Rule Accumulation

**Symptom**: iptables rules accumulated on repeated starts

**Root Cause**:
- Rules not cleaned up on stop
- Multiple exam sessions added duplicate rules
- Performance degradation over time

**Impact**: Network slowdown, rule conflicts

**Solution**:
```python
def stop(self):
    # Flush our custom chain
    subprocess.run(['iptables', '-F', 'EXAM_FILTER'])
    subprocess.run(['iptables', '-X', 'EXAM_FILTER'])
```

**Lesson**: Always clean up resources on shutdown

**Files affected**: `network/domain_filter.py`

---

## Lessons Learned

### Technical Lessons

#### 1. Defense in Depth Works

**What we learned**: Multiple security layers are essential

**Evidence**:
- Network layer (VPN + iptables)
- Process layer (allowlist + kernel module)
- Browser layer (kiosk + key blocking)
- System layer (AppArmor + cleanup)

**Takeaway**: No single layer is perfect - combine multiple approaches

---

#### 2. Testing Mode is Critical

**What we learned**: Need safe mode for development

**Evidence**:
- Virtual console lockdown caused lockouts
- Production mode too restrictive for testing
- Need to iterate quickly

**Takeaway**: Always implement a "safe mode" or "testing mode"

---

#### 3. Configuration Over Code

**What we learned**: Hardcoded values are technical debt

**Evidence**:
- Hardcoded paths made deployment difficult
- Configuration changes required code edits
- Not portable across systems

**Takeaway**: Make everything configurable from day one

---

#### 4. Validate Everything

**What we learned**: Assumptions lead to bugs

**Evidence**:
- Assumed auditd was installed (it wasn't)
- Assumed IPv4 was enough (IPv6 bypass)
- Assumed JSON was valid (sed corruption)

**Takeaway**: Validate all assumptions with checks

---

#### 5. Documentation is Not Optional

**What we learned**: Good docs save time and prevent errors

**Evidence**:
- Users needed clear instructions
- Admins needed operational procedures
- Developers needed architecture understanding

**Takeaway**: Write documentation as you build, not after

---

### Process Lessons

#### 1. Incremental Development

**What worked**:
- Built in phases (network → process → security)
- Tested each phase before moving on
- Could isolate bugs to specific components

**What didn't work**:
- Trying to build everything at once
- Integration issues were harder to debug

**Takeaway**: Build incrementally, test continuously

---

#### 2. Real-World Testing

**What worked**:
- Testing on actual hardware
- Simulating real exam scenarios
- Red team security analysis

**What didn't work**:
- Only testing in ideal conditions
- Not testing edge cases

**Takeaway**: Test in realistic conditions early

---

#### 3. User-Centric Design

**What worked**:
- Separate guides for students vs. admins
- Clear error messages
- Emergency procedures

**What didn't work**:
- Technical jargon in user-facing docs
- Assuming users know Linux

**Takeaway**: Design for your actual users, not yourself

---

### Security Lessons

#### 1. Know Your Threat Model

**What we learned**: Can't protect against everything

**Evidence**:
- Physical cheating requires physical proctoring
- Second devices can't be detected
- Camera-based cheating needs cameras

**Takeaway**: Be honest about what you can and can't detect

---

#### 2. Usability vs. Security Trade-offs

**What we learned**: Too much security breaks usability

**Evidence**:
- Virtual console lockdown locked out developers
- Overly restrictive network broke legitimate use
- Too many restrictions frustrated users

**Takeaway**: Balance security with usability

---

#### 3. Audit Everything

**What we learned**: Logs are your evidence

**Evidence**:
- Kernel audit logs proved cheating attempts
- Network logs showed bypass attempts
- Process logs identified unauthorized apps

**Takeaway**: Log all security-relevant events

---

## Tips for Future Projects

### Planning Phase

1. **Define Clear Requirements**
   - Write down exactly what you need to protect
   - Identify your threat model
   - Know your limitations

2. **Choose Proven Technologies**
   - Don't reinvent the wheel
   - Use established tools (iptables, WireGuard, AppArmor)
   - Leverage existing security frameworks

3. **Design for Failure**
   - Plan emergency procedures
   - Have rollback mechanisms
   - Include recovery tools

---

### Development Phase

1. **Start with Configuration**
   - Make everything configurable
   - Use environment variables
   - Support multiple deployment scenarios

2. **Build Testing Mode First**
   - Safe mode for development
   - Disable dangerous features
   - Easy to iterate

3. **Validate Early and Often**
   - Check assumptions immediately
   - Validate inputs
   - Test edge cases

4. **Document as You Go**
   - Write docs while building
   - Include code comments
   - Explain design decisions

---

### Testing Phase

1. **Test in Realistic Conditions**
   - Use actual hardware
   - Simulate real scenarios
   - Include network issues

2. **Automate Testing**
   - Write test scripts
   - Continuous integration
   - Regression testing

3. **Security Testing**
   - Red team analysis
   - Penetration testing
   - Threat modeling

---

### Deployment testing Phase

1. **Create Deployment Guides**
   - Step-by-step instructions
   - Troubleshooting section
   - Emergency procedures

2. **Provide Multiple Guides**
   - User guide (students)
   - Admin guide (operators)
   - Developer guide (maintainers)

3. **Include Validation Tools**
   - Configuration validators
   - Health checks
   - Diagnostic scripts

---

### Maintenance Phase

1. **Monitor in Production**
   - Real-time monitoring
   - Log analysis
   - Performance metrics

2. **Collect Feedback**
   - User feedback
   - Admin feedback
   - Bug reports

3. **Iterate and Improve**
   - Fix bugs promptly
   - Add features based on feedback
   - Update documentation

---

## Technical Achievements

### What We Built

1. **Multi-Layer Security System**
   - 4 independent security layers
   - Defense in depth architecture
   - Comprehensive threat coverage

3. **Robust Testing Framework**
   - Automated tests
   - Integration tests
   - Security tests

---

### Technologies Mastered

- **Networking**: WireGuard, iptables, IPv4/IPv6
- **Linux Security**: AppArmor, auditd, kernel modules
- **Python**: Subprocess management, JSON handling, logging
- **Shell Scripting**: Bash automation, system integration
- **Documentation**: Markdown, technical writing, user guides

---

### Metrics

- **Lines of Code**: ~5,000+ lines (Python + Shell + C)
- **Documentation**: 15,000+ words across 5 documents
- **Components**: 15+ modules
- **Test Scripts**: 10+ automated tests
- **Security Layers**: 4 independent layers
- **Threat Detection**: 8 categories covered

---

## Conclusion

### Project Success Factors

1. ✅ **Incremental Development** - Built in phases
2. ✅ **Comprehensive Testing** - Tested each component
3. ✅ **User-Centric Design** - Guides for all user types
4. ✅ **Security Focus** - Multiple layers of protection
5. ✅ **Documentation** - Complete guide suite

### What Made This Project Successful

- **Clear Requirements**: Knew exactly what to build
- **Proven Technologies**: Used established tools
- **Iterative Approach**: Built incrementally, tested continuously
- **User Focus**: Designed for actual users
- **Documentation**: Wrote comprehensive guides

### Final Thoughts

Building a secure exam system taught us that **security is a journey, not a destination**. Every layer we added revealed new challenges. Every bug we fixed taught us something new. Every test we ran made the system stronger.

The key to success was:
1. **Humility** - Knowing we can't protect against everything
2. **Transparency** - Being honest about limitations
3. **Iteration** - Continuously improving
4. **Documentation** - Sharing knowledge

This project is now production-ready, but it will continue to evolve based on real-world usage and feedback.

---

**Project Status**: ✅ Test-Ready  
**Documentation**: ✅ Complete  
**Testing**: ✅ Comprehensive  



---

**Last Updated**: 2025-11-26  
**Version**: 1.0.0  
