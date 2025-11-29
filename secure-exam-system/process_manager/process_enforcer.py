#!/usr/bin/env python3
"""
Process Enforcer
Enforces the process allowlist by terminating unauthorized processes.
"""

import psutil
import logging
import signal
import sys
from pathlib import Path
from typing import Dict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from process_manager.allowlist_manager import AllowlistManager
from process_manager.process_monitor import ProcessMonitor

logger = logging.getLogger(__name__)


class ProcessEnforcer(ProcessMonitor):
    def __init__(self, config_path="/home/savvy19/Desktop/product/secure-exam-system/config/system_config.json"):
        """Initialize process enforcer."""
        super().__init__(config_path)
        self.kill_count = 0
        self.enforcement_enabled = False
        
        logger.info("Process Enforcer initialized (extends ProcessMonitor)")
    
    def _terminate_process(self, proc_info: Dict, graceful: bool = True):
        """Terminate an unauthorized process."""
        pid = proc_info['pid']
        name = proc_info['name']
        
        try:
            proc = psutil.Process(pid)
            
            if graceful:
                # Try SIGTERM first (graceful)
                logger.info(f"Terminating process {name} (PID {pid}) gracefully...")
                proc.terminate()
                
                # Wait briefly for process to exit
                try:
                    proc.wait(timeout=2)
                    logger.info(f"  Process {name} (PID {pid}) terminated successfully")
                    self.kill_count += 1
                    return True
                except psutil.TimeoutExpired:
                    # If still running, force kill
                    logger.warning(f"  Process {name} (PID {pid}) did not terminate, forcing...")
                    proc.kill()
                    logger.info(f"  Process {name} (PID {pid}) killed")
                    self.kill_count += 1
                    return True
            else:
                # Force kill immediately
                logger.info(f"Killing process {name} (PID {pid}) forcefully...")
                proc.kill()
                logger.info(f"  Process {name} (PID {pid}) killed")
                self.kill_count += 1
                return True
                
        except psutil.NoSuchProcess:
            logger.debug(f"Process {pid} already terminated")
            return True
        except psutil.AccessDenied:
            logger.error(f"Access denied when trying to terminate PID {pid}")
            return False
        except Exception as e:
            logger.error(f"Failed to terminate PID {pid}: {str(e)}")
            return False
    
    def _handle_violation(self, proc_info: Dict):
        """Handle a process allowlist violation."""
        # Log the violation
        self._log_violation(proc_info)
        
        # Terminate if enforcement is enabled
        if self.enforcement_enabled:
            self._terminate_process(proc_info, graceful=True)
        else:
            logger.info("  (Enforcement disabled - logging only)")
    
    def scan_processes(self):
        """Scan all running processes and enforce allowlist."""
        current_pids = set()
        
        for proc in psutil.process_iter():
            try:
                current_pids.add(proc.pid)
                
                # Check if this is a new process
                if proc.pid not in self.known_pids:
                    proc_info = self._get_process_info(proc)
                    
                    if proc_info and not self._is_process_allowed(proc_info):
                        self._handle_violation(proc_info)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Update known PIDs
        self.known_pids = current_pids
    
    def enable_enforcement(self):
        """Enable automatic termination of unauthorized processes."""
        self.enforcement_enabled = True
        logger.warning("Process enforcement ENABLED - unauthorized processes will be terminated")
    
    def disable_enforcement(self):
        """Disable automatic termination (logging only)."""
        self.enforcement_enabled = False
        logger.info("Process enforcement DISABLED - logging only")
    
    def get_status(self) -> Dict:
        """Get current enforcer status."""
        status = super().get_status()
        status.update({
            'enforcement_enabled': self. enforcement_enabled,
            'terminated_processes': self.kill_count
        })
        return status


def main():
    """Test process enforcer."""
    import argparse
    import time
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description='Process Enforcer for secure exam system')
    parser.add_argument('--enforce', action='store_true',
                       help='Enable enforcement (kill unauthorized processes)')
    parser.add_argument('--log-only', action='store_true',
                       help='Log only mode (default)')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    enforcer = ProcessEnforcer()
    
    print("\n" + "="*60)
    print("PROCESS ENFORCER")
    print("="*60)
    
    if args.enforce:
        print("\n⚠️  ENFORCEMENT MODE ACTIVE")
        print("Unauthorized processes will be TERMINATED!\n")
        enforcer.enable_enforcement()
    else:
        print("\nLOG-ONLY MODE (Safe)")
        print("Unauthorized processes will be logged but NOT terminated\n")
        enforcer.disable_enforcement()
    
    print("Press Ctrl+C to stop\n")
    
    if enforcer.start():
        try:
            while True:
                time.sleep(5)
                status = enforcer.get_status()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"Processes: {status['known_processes']}, "
                      f"Violations: {status['violations']}, "
                      f"Terminated: {status['terminated_processes']}")
        except KeyboardInterrupt:
            print("\n\nStopping enforcer...")
            enforcer.stop()
    else:
        print("Failed to start enforcer")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
