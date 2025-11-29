#!/usr/bin/env python3
"""
Main Controller
Orchestrates all secure exam system components.
"""

import sys
import json
import logging
import signal
import time
from pathlib import Path
from typing import Dict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from network.vpn_manager import VPNManager
from network.domain_filter import DomainFilter
from network.kiosk_browser import KioskBrowser
from network.network_monitor import NetworkMonitor
from process_manager.process_enforcer import ProcessEnforcer
from security.system_lockdown import SystemLockdown
from security.integrity_checker import IntegrityChecker
from security.security_patcher import SecurityPatcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class MainController:
    def __init__(self, config_path="config/system_config.json"):
        """Initialize main controller."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.mode = self.config['mode']
        
        # Initialize all components
        self.vpn = VPNManager(config_path)
        self.domain_filter = DomainFilter(config_path)
        self.kiosk = KioskBrowser(config_path)
        self.network_monitor = NetworkMonitor(config_path)
        self.process_enforcer = ProcessEnforcer(config_path)
        self.lockdown = SystemLockdown(config_path)
        self.integrity = IntegrityChecker(config_path)
        self.patcher = SecurityPatcher()
        
        self.running = False
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Main Controller initialized in {self.mode} mode")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.warning(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def pre_flight_checks(self) -> bool:
        """Run pre-flight checks before starting."""
        logger.info("Running pre-flight checks...")
        
        checks = []
        
        # Check 1: Integrity baseline exists
        if not self.integrity.integrity_file.exists():
            logger.warning("No integrity baseline found, creating...")
            self.integrity.baseline_system()
        
        # Check 2: Process allowlist exists
        if not self.process_enforcer.allowlist.get_processes():
            logger.error("Process allowlist is empty!")
            logger.error("Run: python3 process_manager/allowlist_builder.py")
            checks.append(False)
        else:
            logger.info(f"✓ Process allowlist loaded ({len(self.process_enforcer.allowlist.get_processes())} processes)")
            checks.append(True)
        
        # Check 3: VPN config exists (if not testing)
        # This is optional for testing
        
        # Check 4: AppArmor status
        if self.lockdown.check_apparmor_status():
            logger.info("✓ AppArmor is active")
            checks.append(True)
        else:
            logger.warning("AppArmor not active (will skip security profile)")
            checks.append(True)  # Not critical
        
        all_passed = all(checks)
        if all_passed:
            logger.info("✓ All pre-flight checks passed")
        else:
            logger.error("✗ Some pre-flight checks failed")
        
        return all_passed
    
    def start_network_security(self) -> bool:
        """Start network security components."""
        logger.info("\n" + "="*60)
        logger.info("STARTING NETWORK SECURITY")
        logger.info("="*60)
        
        # Start VPN
        logger.info("1. Starting VPN...")
        if not self.vpn.start():
            logger.error("Failed to start VPN")
            return False
        logger.info("✓ VPN started")
        
        # Start domain filter
        logger.info("2. Starting domain filter...")
        if not self.domain_filter.start():
            logger.error("Failed to start domain filter")
            return False
        logger.info("✓ Domain filter started")
        
        # Start network monitor
        logger.info("3. Starting network monitor...")
        if not self.network_monitor.start():
            logger.error("Failed to start network monitor")
            return False
        logger.info("✓ Network monitor started")
        
        logger.info("✓ Network security active")
        return True
    
    def start_process_management(self) -> bool:
        """Start process management."""
        logger.info("\n" + "="*60)
        logger.info("STARTING PROCESS MANAGEMENT")
        logger.info("="*60)
        
        # Start process enforcer
        logger.info("1. Starting process enforcer...")
        if not self.process_enforcer.start():
            logger.error("Failed to start process enforcer")
            return False
        
        # SECURITY PATCH: Take baseline AFTER security is enabled
        # This prevents pre-exam process launch attack
        logger.info("2. Taking process baseline (POST-LOCKDOWN)...")
        self.process_enforcer.take_baseline()
        
        # Enable enforcement (will terminate unauthorized processes)
        logger.info("3. Enabling process enforcement...")
        self.process_enforcer.enable_enforcement()
        
        logger.info("✓ Process management active")
        return True
    
    def start_security_hardening(self) -> bool:
        """Start security hardening."""
        logger.info("\n" + "="*60)
        logger.info("STARTING SECURITY HARDENING")
        logger.info("="*60)
        
        # SECURITY PATCHES: Apply all critical fixes
        logger.info("1. Applying security patches...")
        self.patcher.apply_all_patches()
        
        # Enable system lockdown
        logger.info("2. Enabling system lockdown...")
        if not self.lockdown.enable_lockdown():
            logger.warning("Failed to enable lockdown (continuing anyway)")
        else:
            logger.info("✓ System lockdown enabled")
        
        # Verify integrity
        logger.info("3. Verifying system integrity...")
        results = self.integrity.verify_integrity()
        if results['status'] != 'ok':
            logger.error(f"Integrity check failed! {results['summary']}")
            logger.error("System may be compromised!")
            return False
        logger.info("✓ Integrity verified")
        
        logger.info("✓ Security hardening active")
        return True
    
    def start_exam_environment(self) -> bool:
        """Start exam environment (kiosk browser)."""
        logger.info("\n" + "="*60)
        logger.info("STARTING EXAM ENVIRONMENT")
        logger.info("="*60)
        
        # Start kiosk browser
        logger.info("1. Starting kiosk browser...")
        if not self.kiosk.start():
            logger.error("Failed to start kiosk browser")
            return False
        
        logger.info("✓ Exam environment active")
        return True
    
    def start(self) -> bool:
        """Start all components in correct order."""
        logger.info("\n" + "#"*60)
        logger.info("SECURE EXAM SYSTEM - STARTING")
        logger.info("#"*60)
        
        # Pre-flight checks
        if not self.pre_flight_checks():
            logger.error("Pre-flight checks failed, aborting")
            return False
        
        # Start components
        if not self.start_network_security():
            logger.error("Network security failed")
            return False
        
        if not self.start_process_management():
            logger.error("Process management failed")
            return False
        
        if not self.start_security_hardening():
            logger.error("Security hardening failed")
            return False
        
        if not self.start_exam_environment():
            logger.error("Exam environment failed")
            return False
        
        self.running = True
        
        logger.info("\n" + "#"*60)
        logger.info("✓ SECURE EXAM SYSTEM - ACTIVE")
        logger.info("#"*60)
        logger.info("\nSystem is now locked down")
        logger.info("Student can only access codeforces.com in kiosk mode")
        logger.info("\nPress Ctrl+C to stop\n")
        
        return True
    
    def stop(self):
        """Stop all components."""
        if not self.running:
            return
        
        logger.info("\n" + "#"*60)
        logger.info("SECURE EXAM SYSTEM - STOPPING")
        logger.info("#"*60)
        
        # Stop in reverse order
        logger.info("1. Stopping kiosk browser...")
        self.kiosk.stop()
        
        logger.info("2. Disabling security hardening...")
        self.lockdown.disable_lockdown()
        
        logger.info("3. Stopping process management...")
        self.process_enforcer.stop()
        
        logger.info("4. Stopping network security...")
        self.network_monitor.stop()
        self.domain_filter.stop()
        self.vpn.stop()
        
        self.running = False
        
        logger.info("\n✓ SECURE EXAM SYSTEM - STOPPED")
        logger.info("System returned to normal state\n")
    
    def run(self):
        """Run the exam system until stopped."""
        if not self.start():
            logger.error("Failed to start exam system")
            return 1
        
        try:
            # Wait for browser to exit
            self.kiosk.wait()
            logger.info("Browser closed, shutting down...")
        except KeyboardInterrupt:
            logger.info("\nShutdown requested...")
        finally:
            self.stop()
        
        return 0


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Secure Exam System Main Controller')
    parser.add_argument('--config', default='config/system_config.json',
                       help='Path to configuration file')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run pre-flight checks only')
    
    args = parser.parse_args()
    
    controller = MainController(args.config)
    
    if args.dry_run:
        print("\nDRY RUN MODE - Pre-flight checks only\n")
        if controller.pre_flight_checks():
            print("\n✓ System ready for exam mode")
            return 0
        else:
            print("\n✗ System not ready")
            return 1
    
    return controller.run()


if __name__ == '__main__':
    sys.exit(main())
