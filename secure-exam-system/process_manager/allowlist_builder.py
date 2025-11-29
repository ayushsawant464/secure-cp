#!/usr/bin/env python3
"""
Allowlist Builder
Builds initial process allowlist by scanning system processes.
"""

import psutil
import logging
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from process_manager.allowlist_manager import AllowlistManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Critical system processes that must always be allowed
CRITICAL_PROCESSES = [
    'systemd',
    'systemd-journald',
    'systemd-logind',
    'systemd-udevd',
    'dbus-daemon',
    'dbus-broker',
    'NetworkManager',
    'wpa_supplicant',
    'dhclient',
    'Xorg',
    'X',
    'pulseaudio',
    'pipewire',
    'wireplumber',
    'kwin_x11',
    'gnome-shell',
    'plasmashell',
    'xfce4-session',
    'python3',  # Needed for our own scripts
    'bash',
    'sh',
    'kmod'
]


class AllowlistBuilder:
    def __init__(self, config_path="/home/savvy19/Desktop/product/secure-exam-system/config/system_config.json"):
        """Initialize allowlist builder."""
        self.manager = AllowlistManager(config_path)
        
        # Load mode from config
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)
        self.mode = config['mode']
        self.exam_app = config.get('process_allowlist', {}).get('exam_app', {})
        
        logger.info(f"Allowlist Builder initialized in {self.mode} mode")
    
    def scan_running_processes(self):
        """Scan currently running processes."""
        processes = {}
        
        for proc in psutil.process_iter(['name', 'exe', 'cmdline']):
            try:
                pinfo = proc.info
                name = pinfo['name']
                exe = pinfo['exe']
                
                if name and name not in processes:
                    processes[name] = {
                        'name': name,
                        'exe': exe,
                        'count': 1
                    }
                elif name:
                    processes[name]['count'] += 1
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        logger.info(f"Found {len(processes)} unique processes running")
        return processes
    
    def add_critical_processes(self):
        """Add critical system processes to allowlist."""
        logger.info("Adding critical system processes...")
        count = 0
        
        for proc_name in CRITICAL_PROCESSES:
            self.manager.add_process(proc_name)
            count += 1
        
        logger.info(f"Added {count} critical processes")
        return count
    
    def add_exam_app(self, interactive=False):
        """Add exam application to allowlist."""
        if self.mode == 'production' and self.exam_app:
            # Production mode: use pre-configured app
            name = self.exam_app.get('name')
            path = self.exam_app.get('path')
            
            if name and path:
                logger.info(f"Adding exam app from config: {name}")
                self.manager.add_process(name, path, compute_checksum=True)
                return True
            else:
                logger.warning("Exam app not fully configured in config file")
                return False
        
        elif interactive:
            # Testing mode: interactive
            print("\n" + "="*60)
            print("EXAM APPLICATION CONFIGURATION")
            print("="*60)
            
            add_app = input("\nDo you want to add an exam application? (y/n): ").lower()
            
            if add_app == 'y':
                name = input("Enter application name (e.g., chromium-browser): ").strip()
                path = input("Enter full path to executable (e.g., /usr/bin/chromium-browser): ").strip()
                
                if name and path:
                    if os.path.exists(path):
                        self.manager.add_process(name, path, compute_checksum=True)
                        print(f"✓ Added {name} to allowlist")
                        return True
                    else:
                        print(f"✗ Path does not exist: {path}")
                        return False
                else:
                    print("✗ Invalid input")
                    return False
        
        return False
    
    def build_allowlist(self, interactive_mode=None):
        """Build complete allowlist."""
        if interactive_mode is None:
            interactive_mode = (self.mode == 'testing')
        
        logger.info("Building process allowlist...")
        
        # Clear existing allowlist
        self.manager.clear()
        
        # Add critical processes
        self.add_critical_processes()
        
        # Scan running processes to find additional system processes
        running = self.scan_running_processes()
        
        # Auto-add common system processes
        system_keywords = ['systemd', 'dbus', 'network', 'udev', 'journal', 'login', 'session']
        auto_added = 0
        
        for proc_name, proc_info in running.items():
            # Check if it's a system process
            if any(keyword in proc_name.lower() for keyword in system_keywords):
                if not self.manager.is_allowed(name=proc_name):
                    self.manager.add_process(proc_name, proc_info['exe'])
                    auto_added += 1
        
        logger.info(f"Auto-added {auto_added} system processes")
        
        # Add exam application
        self.add_exam_app(interactive=interactive_mode)
        
        # Save allowlist
        self.manager.save()
        
        logger.info("Allowlist building complete")
        return True
    
    def show_allowlist(self):
        """Display current allowlist."""
        processes = self.manager.get_processes()
        paths = self.manager.get_paths()
        
        print("\n" + "="*60)
        print("PROCESS ALLOWLIST")
        print("="*60)
        print(f"\nTotal processes: {len(processes)}")
        print(f"Total paths: {len(paths)}")
        
        print("\nAllowed Processes:")
        for i, proc in enumerate(sorted(processes), 1):
            print(f"  {i:3d}. {proc}")
        
        if paths:
            print("\nAllowed Paths:")
            for i, path in enumerate(sorted(paths), 1):
                print(f"  {i:3d}. {path}")


def main():
    """Build allowlist."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build process allowlist for secure exam system')
    parser.add_argument('--interactive', action='store_true',
                       help='Run in interactive mode (prompt for exam app)')
    parser.add_argument('--show', action='store_true',
                       help='Show current allowlist and exit')
    
    args = parser.parse_args()
    
    builder = AllowlistBuilder()
    
    if args.show:
        builder.show_allowlist()
        return 0
    
    # Build allowlist
    builder.build_allowlist(interactive_mode=args.interactive)
    
    # Show result
    builder.show_allowlist()
    
    print("\n✓ Allowlist saved to: config/process_allowlist.json")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
