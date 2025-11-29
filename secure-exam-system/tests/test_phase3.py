#!/usr/bin/env python3
"""
Phase 3 Process Management Tests
Tests allowlist management, process monitoring, and enforcement.
"""

import sys
import logging
import time
import subprocess
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from process_manager.allowlist_manager import AllowlistManager
from process_manager.allowlist_builder import AllowlistBuilder
from process_manager.process_monitor import ProcessMonitor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class Phase3Tests:
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
    
    def test_allowlist_manager(self):
        """Test allowlist manager basic operations."""
        am = AllowlistManager()
        
        # Test add/remove
        am.add_process("test_proc", "/usr/bin/test")
        if not am.is_allowed(name="test_proc"):
            return False
        
        am.remove_process("test_proc")
        if am.is_allowed(name="test_proc"):
            return False
        
        return True
    
    def test_allowlist_builder(self):
        """Test allowlist builder."""
        builder = AllowlistBuilder()
        
        # Build allowlist non-interactively
        result = builder.build_allowlist(interactive_mode=False)
        
        if not result:
            return False
        
        # Check that some processes were added
        processes = builder.manager.get_processes()
        if len(processes) == 0:
            logger.error("No processes in allowlist")
            return False
        
        logger.info(f"Allowlist contains {len(processes)} processes")
        return True
    
    def test_process_monitor(self):
        """Test process monitor."""
        monitor = ProcessMonitor()
        
        # Start monitor
        if not monitor.start():
            return False
        
        # Let it run briefly
        time.sleep(2)
        
        # Check status
        status = monitor.get_status()
        if not status['monitoring']:
            return False
        
        # Stop monitor
        monitor.stop()
        
        return True
    
    def test_process_detection(self):
        """Test that unauthorized processes are detected."""
        monitor = ProcessMonitor()
        
        # Start monitor
        if not monitor.start():
            return False
        
        # Give it a moment to establish baseline
        time.sleep(1)
        
        # Start an unauthorized process (sleep command)
        logger.info("Starting test process (sleep)...")
        proc = subprocess.Popen(['sleep', '5'])
        
        # Wait for detection
        time.sleep(2)
        
        # Check if violation was logged
        status = monitor.get_status()
        detected = status['violations'] > 0
        
        # Cleanup
        proc.terminate()
        proc.wait()
        monitor.stop()
        
        if detected:
            logger.info("✓ Unauthorized process was detected")
        else:
            logger.warning("✗ Unauthorized process was NOT detected")
        
        return detected
    
    def run_all_tests(self):
        """Run all Phase 3 tests."""
        logger.info(f"\n{'#'*60}")
        logger.info("PHASE 3: PROCESS MANAGEMENT TESTS")
        logger.info(f"{'#'*60}\n")
        
        # Allowlist Tests
        logger.info("\n=== ALLOWLIST TESTS ===")
        self.test("Allowlist Manager Operations", self.test_allowlist_manager)
        self.test("Allowlist Builder", self.test_allowlist_builder)
        
        # Process Monitoring Tests
        logger.info("\n=== PROCESS MONITORING TESTS ===")
        self.test("Process Monitor Start/Stop", self.test_process_monitor)
        self.test("Unauthorized Process Detection", self.test_process_detection)
        
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
    print("SECURE EXAM SYSTEM - PHASE 3 TESTS")
    print("="*60)
    print("\nTesting process management components...")
    print("="*60 + "\n")
    
    tests = Phase3Tests()
    return tests.run_all_tests()


if __name__ == '__main__':
    sys.exit(main())
