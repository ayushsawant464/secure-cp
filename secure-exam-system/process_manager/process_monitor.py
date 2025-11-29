#!/usr/bin/env python3
"""
Process Monitor
Monitors all running processes and logs unauthorized process creation.
Uses userspace /proc monitoring for cross-platform compatibility.
"""

import psutil
import logging
import time
import threading
import sys
from pathlib import Path
from datetime import datetime
from typing import Set, Dict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from process_manager.allowlist_manager import AllowlistManager

logger = logging.getLogger(__name__)


class ProcessMonitor:
    def __init__(self, config_path="/home/savvy19/Desktop/product/secure-exam-system/config/system_config.json"):
        """Initialize process monitor."""
        self.allowlist = AllowlistManager(config_path)
        self.monitoring = False
        self.monitor_thread = None
        self.known_pids: Set[int] = set()
        self.violation_count = 0
        self.baseline_taken = False
        
        logger.info("Process Monitor initialized (Red Team Hardened)")
    
    def _get_process_info(self, proc):
        """Get detailed process information."""
        try:
            return {
                'pid': proc.pid,
                'name': proc.name(),
                'exe': proc.exe(),
                'cmdline': ' '.join(proc.cmdline()),
                'username': proc.username(),
                'create_time': datetime.fromtimestamp(proc.create_time()).isoformat()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
    
    def _is_process_allowed(self, proc_info: Dict) -> bool:
        """Check if a process is allowed (Red Team Hardened)."""
        if not proc_info:
            return True  # Can't check, assume allowed
        
        name = proc_info['name']
        exe = proc_info['exe']
        cmdline = proc_info.get('cmdline', '')
        
        # SECURITY PATCH: Detect Python subprocess attacks
        if 'python' in name.lower():
            # Check if running interactive Python or subprocess tricks
            dangerous_patterns = [
                'os.system',
                'subprocess',
                'import subprocess',
                'import os',
                '__import__',
                'exec(',
                'eval(',
                '-c "',
                "-c '"
            ]
            
            for pattern in dangerous_patterns:
                if pattern in cmdline:
                    logger.error(f"🚨 PYTHON ATTACK DETECTED: {pattern} in {cmdline}")
                    return False
        
        # SECURITY PATCH: Resolve symlinks before checking
        if exe:
            try:
                resolved_exe = str(Path(exe).resolve())
                if resolved_exe != exe:
                    logger.warning(f"Symlink detected: {exe} -> {resolved_exe}")
                    exe = resolved_exe
            except:
                pass
        
        # Check allowlist
        if self.allowlist.is_allowed(name=name, path=exe):
            return True
        
        return False
    
    def _log_violation(self, proc_info: Dict):
        """Log a process allowlist violation."""
        self.violation_count += 1
        
        logger.warning(f"[VIOLATION #{self.violation_count}] Unauthorized process detected:")
        logger.warning(f"  PID:      {proc_info['pid']}")
        logger.warning(f"  Name:     {proc_info['name']}")
        logger.warning(f"  Exe:      {proc_info['exe']}")
        logger.warning(f"  Cmdline:  {proc_info['cmdline']}")
        logger.warning(f"  User:     {proc_info['username']}")
        logger.warning(f"  Started:  {proc_info['create_time']}")
    
    def scan_processes(self):
        """Scan all running processes."""
        current_pids = set()
        
        for proc in psutil.process_iter():
            try:
                current_pids.add(proc.pid)
                
                # Check if this is a new process
                if proc.pid not in self.known_pids:
                    proc_info = self._get_process_info(proc)
                    
                    if proc_info and not self._is_process_allowed(proc_info):
                        self._log_violation(proc_info)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Update known PIDs
        self.known_pids = current_pids
    
    def take_baseline(self):
        """Take process baseline AFTER security is enabled.
        
        SECURITY PATCH: Prevents pre-exam process launch attack.
        Student can't start unauthorized processes before exam and have
        them in the baseline.
        """
        logger.info("Taking process baseline AFTER security lockdown...")
        self.known_pids.clear()
        
        for proc in psutil.process_iter():
            try:
                self.known_pids.add(proc.pid)
            except:
                pass
        
        self.baseline_taken = True
        logger.info(f"✓ Baseline: {len(self.known_pids)} processes (POST-LOCKDOWN)")
    
    def monitor_loop(self):
        """Main monitoring loop."""
        logger.info("Starting process monitoring loop...")
        
        # Wait for explicit baseline call
        if not self.baseline_taken:
            logger.warning("Baseline not taken yet, taking now...")
            self.take_baseline()
        
        # Monitoring loop
        while self.monitoring:
            self.scan_processes()
            time.sleep(1)  # Check every second
    
    def start(self):
        """Start process monitoring."""
        if self.monitoring:
            logger.warning("Process monitor already running")
            return False
        
        logger.info("Starting Process Monitor...")
        
        # Ensure allowlist is loaded
        if not self.allowlist.get_processes():
            logger.error("Allowlist is empty! Please build allowlist first.")
            return False
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"Process Monitor started with {len(self.allowlist.get_processes())} allowed processes")
        return True
    
    def stop(self):
        """Stop process monitoring."""
        logger.info("Stopping Process Monitor...")
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info(f"Process Monitor stopped. Total violations: {self.violation_count}")
        return True
    
    def get_status(self) -> Dict:
        """Get current monitoring status."""
        return {
            'monitoring': self.monitoring,
            'known_processes': len(self.known_pids),
            'violations': self.violation_count,
            'allowlist_size': len(self.allowlist.get_processes())
        }


def main():
    """Test process monitor."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    monitor = ProcessMonitor()
    
    print("\n" + "="*60)
    print("PROCESS MONITOR TEST")
    print("="*60)
    print("\nThis will monitor for new processes...")
    print("Try starting unauthorized applications in another terminal")
    print("Press Ctrl+C to stop\n")
    
    if monitor.start():
        try:
            while True:
                time.sleep(5)
                status = monitor.get_status()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] " 
                      f"Monitoring: {status['known_processes']} processes, "
                      f"Violations: {status['violations']}")
        except KeyboardInterrupt:
            print("\n\nStopping monitor...")
            monitor.stop()
    else:
        print("Failed to start monitor")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
