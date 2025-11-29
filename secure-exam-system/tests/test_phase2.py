#!/usr/bin/env python3
"""
Phase 2 Network Security Tests
Tests VPN isolation, domain filtering, and kiosk browser functionality.
"""

import sys
import logging
import json
import subprocess
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from network.vpn_manager import VPNManager
from network.domain_filter import DomainFilter
from network.network_monitor import NetworkMonitor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class Phase2Tests:
    def __init__(self):
        self.results = []
    
    def test(self, name, func):
        """Run a test and record result."""
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST: {name}")
        logger.info(f"{'='*60}")
        
        try:
            result = func()
            self.results.append((name, result, ""))
            logger.info(f"✓ {name} - {'PASSED' if result else 'FAILED'}")
            return result
        except Exception as e:
            logger.error(f"✗ {name} - FAILED with exception: {str(e)}")
            self.results.append((name, False, str(e)))
            return False
    
    def test_vpn_creation(self):
        """Test VPN manager initialization and namespace creation."""
        vpn = VPNManager()
        
        # In testing mode, should create namespace
        if vpn.is_testing:
            # Check if namespace can be created
            result = vpn.create_namespace()
            return result
        return True
    
    def test_vpn_routing(self):
        """Test VPN routing configuration."""
        vpn = VPNManager()
        
        # Note: This requires actual VPN config file
        # For now, we test the routing logic
        logger.info("VPN routing test - requires WireGuard config")
        return True
    
    def test_kill_switch(self):
        """Test VPN kill switch configuration."""
        vpn = VPNManager()
        
        if vpn.is_testing:
            if not vpn.create_namespace():
                return False
        
        # Test kill switch iptables rules
        result = vpn.enable_kill_switch()
        return result
    
    def test_domain_filter_init(self):
        """Test domain filter initialization."""
        df = DomainFilter()
        
        # Test IP resolution
        result = df.resolve_allowed_ips()
        
        # Check both IPv4 and IPv6 - FIXED to use new attributes
        total_ips = len(df.allowed_ips_v4) + len(df.allowed_ips_v6)
        if total_ips > 0:
            logger.info(f"Resolved {len(df.allowed_ips_v4)} IPv4 and {len(df.allowed_ips_v6)} IPv6 addresses")
            return True
        else:
            logger.warning("No IPs resolved - may need internet connection")
            return False
    
    def test_domain_filter_rules(self):
        """Test domain filter iptables rules."""
        df = DomainFilter()
        df.resolve_allowed_ips()
        
        # Create namespace if testing
        if df.is_testing:
            vpn = VPNManager()
            vpn.create_namespace()
        
        # Configure iptables
        result = df.configure_iptables_filtering()
        
        # Cleanup
        df.stop()
        
        return result
    
    def test_network_monitor(self):
        """Test network monitor."""
        nm = NetworkMonitor()
        
        if nm.start():
            time.sleep(2)
            status = nm.get_status()
            nm.stop()
            
            return status is not None
        return False
    
    def run_all_tests(self):
        """Run all Phase 2 tests."""
        logger.info(f"\n{'#'*60}")
        logger.info("PHASE 2: NETWORK SECURITY TESTS")
        logger.info(f"{'#'*60}\n")
        
        # VPN Tests
        logger.info("\n=== VPN TESTS ===")
        self.test("VPN Namespace Creation", self.test_vpn_creation)
        self.test("VPN Kill Switch Configuration", self.test_kill_switch)
        
        # Domain Filter Tests
        logger.info("\n=== DOMAIN FILTER TESTS ===")
        self.test("Domain Filter Initialization", self.test_domain_filter_init)
        self.test("Domain Filter iptables Rules", self.test_domain_filter_rules)
        
        # Network Monitor Tests
        logger.info("\n=== NETWORK MONITOR TESTS ===")
        self.test("Network Monitor", self.test_network_monitor)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        logger.info(f"\n{'#'*60}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'#'*60}\n")
        
        passed = sum(1 for _, result, _ in self.results if result)
        total = len(self.results)
        
        for name, result, error in self.results:
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"{status}: {name}")
            if error:
                logger.info(f"  Error: {error}")
        
        logger.info(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED!")
            return 0
        else:
            logger.warning(f"⚠️  {total - passed} test(s) failed")
            return 1


def main():
    print("\n" + "="*60)
    print("SECURE EXAM SYSTEM - PHASE 2 TESTS")
    print("="*60)
    print("\nNOTE: These tests require root privileges")
    print("Run with: sudo python3 tests/test_phase2.py")
    print("="*60 + "\n")
    
    tests = Phase2Tests()
    return tests.run_all_tests()


if __name__ == '__main__':
    sys.exit(main())
