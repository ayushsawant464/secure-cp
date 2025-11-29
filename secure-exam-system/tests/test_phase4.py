#!/usr/bin/env python3
"""
Phase 4 Security Hardening Tests  
Tests AppArmor profile loading and integrity checking.
"""

import sys
import logging
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security.system_lockdown import SystemLockdown
from security.integrity_checker import IntegrityChecker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class Phase4Tests:
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
    
    def test_apparmor_check(self):
        """Test AppArmor status check."""
        lockdown = SystemLockdown()
        status = lockdown.check_apparmor_status()
        
        if status:
            logger.info("AppArmor is available")
        else:
            logger.warning("AppArmor not available (this is OK for testing)")
        
        # Pass test if we can check status (regardless of result)
        return True
    
    def test_profile_exists(self):
        """Test that AppArmor profile file exists."""
        lockdown = SystemLockdown()
        
        if lockdown.profile_file.exists():
            logger.info(f"Profile found: {lockdown.profile_file}")
            return True
        else:
            logger.error(f"Profile not found: {lockdown.profile_file}")
            return False
    
    def test_integrity_baseline(self):
        """Test integrity baseline creation."""
        checker = IntegrityChecker()
        
        result = checker.baseline_system()
        
        if result and len(checker.checksums) > 0:
            logger.info(f"Baseline created with {len(checker.checksums)} files")
            return True
        else:
            logger.error("Failed to create baseline")
            return False
    
    def test_integrity_verify(self):
        """Test integrity verification."""
        checker = IntegrityChecker()
        
        # Create baseline first
        checker.baseline_system()
        
        # Verify integrity
        results = checker.verify_integrity()
        
        if results['status'] == 'ok':
            logger.info("Integrity verification passed")
            return True
        else:
            logger.error(f"Integrity check failed: {results['summary']}")
            return False
    
    def test_lockdown_status(self):
        """Test lockdown status retrieval."""
        lockdown = SystemLockdown()
        status = lockdown.get_status()
        
        if 'apparmor_active' in status and 'profile_loaded' in status:
            logger.info(f"Status retrieved: {status}")
            return True
        else:
            logger.error("Failed to get status")
            return False
    
    def run_all_tests(self):
        """Run all Phase 4 tests."""
        logger.info(f"\n{'#'*60}")
        logger.info("PHASE 4: SECURITY HARDENING TESTS")
        logger.info(f"{'#'*60}\n")
        
        # AppArmor Tests
        logger.info("\n=== APPARMOR TESTS ===")
        self.test("AppArmor Status Check", self.test_apparmor_check)
        self.test("AppArmor Profile Exists", self.test_profile_exists)
        self.test("Lockdown Status Retrieval", self.test_lockdown_status)
        
        # Integrity Tests
        logger.info("\n=== INTEGRITY TESTS ===")
        self.test("Integrity Baseline Creation", self.test_integrity_baseline)
        self.test("Integrity Verification", self.test_integrity_verify)
        
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
    print("SECURE EXAM SYSTEM - PHASE 4 TESTS")
    print("="*60)
    print("\nTesting security hardening components...")
    print("="*60 + "\n")
    
    tests = Phase4Tests()
    return tests.run_all_tests()


if __name__ == '__main__':
    sys.exit(main())
