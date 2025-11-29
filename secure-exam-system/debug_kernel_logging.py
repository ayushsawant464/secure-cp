#!/usr/bin/env python3
"""
Debug Kernel Logging
A robust Python script to verify kernel logging (iptables/dmesg)
without relying on fragile shell scripts or missing auditd tools.
"""

import os
import sys
import json
import subprocess
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_root():
    if os.geteuid() != 0:
        logger.error("❌ Must run as sudo")
        sys.exit(1)

def verify_config():
    """Verify config/system_config.json is valid JSON."""
    config_path = "config/system_config.json"
    logger.info(f"Checking {config_path}...")
    try:
        with open(config_path, 'r') as f:
            json.load(f)
        logger.info("✅ Config file is valid JSON")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"❌ Config file JSON Error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Config file Error: {e}")
        return False

def load_kernel_module():
    """Load the proc_monitor kernel module if available."""
    logger.info("\nChecking kernel module...")
    ko_path = "/home/savvy19/Desktop/product/secure-exam-system/process_manager/kernel_monitor/proc_monitor.ko"
    
    if not os.path.exists(ko_path):
        logger.warning(f"⚠️ Kernel module not found at {ko_path}")
        return

    # Check if loaded
    result = subprocess.run(['lsmod'], capture_output=True, text=True)
    if 'proc_monitor' in result.stdout:
        logger.info("✅ proc_monitor module is already loaded")
    else:
        logger.info("Loading proc_monitor module...")
        res = subprocess.run(['insmod', ko_path], capture_output=True)
        if res.returncode == 0:
            logger.info("✅ Module loaded successfully")
        else:
            logger.error(f"❌ Failed to load module: {res.stderr.decode()}")

def add_iptables_logging():
    """Add a temporary iptables rule to log outgoing traffic."""
    logger.info("\nAdding temporary iptables logging rule...")
    # Log new connections to 8.8.8.8
    cmd = ['iptables', '-I', 'OUTPUT', '1', '-d', '8.8.8.8', '-p', 'icmp', '-j', 'LOG', '--log-prefix', 'EXAM_DEBUG: ']
    subprocess.run(cmd, capture_output=True)
    logger.info("✅ Logging rule added for 8.8.8.8 ICMP")

def remove_iptables_logging():
    """Remove the temporary logging rule."""
    logger.info("Removing temporary logging rule...")
    cmd = ['iptables', '-D', 'OUTPUT', '-d', '8.8.8.8', '-p', 'icmp', '-j', 'LOG', '--log-prefix', 'EXAM_DEBUG: ']
    subprocess.run(cmd, capture_output=True)
    logger.info("✅ Logging rule removed")

def check_dmesg_logs():
    """Check dmesg for relevant logs."""
    logger.info("\nChecking kernel logs (dmesg)...")
    
    # Keywords to look for
    keywords = ["EXAM_FILTER", "IPTables", "WireGuard", "audit", "EXECVE", "proc_monitor", "EXAM_DEBUG"]
    
    found_any = False
    try:
        # Get last 100 lines of dmesg
        result = subprocess.run(['dmesg'], capture_output=True, text=True)
        lines = result.stdout.splitlines()[-100:]
        
        for line in lines:
            for kw in keywords:
                if kw in line:
                    logger.info(f"  Found log: {line.strip()}")
                    found_any = True
                    break
        
        if not found_any:
            logger.warning("  No recent relevant kernel logs found.")
            
    except Exception as e:
        logger.error(f"Failed to read dmesg: {e}")

def trigger_network_event():
    """Trigger a network event that should be logged."""
    logger.info("\nTriggering network event (ping to 8.8.8.8)...")
    try:
        # Just a simple ping
        subprocess.run(['ping', '-c', '1', '-W', '1', '8.8.8.8'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
    except Exception:
        pass

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   KERNEL LOGGING DEBUG (PYTHON)                            ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    check_root()
    
    if not verify_config():
        sys.exit(1)
        
    load_kernel_module()
    add_iptables_logging()
    
    # Trigger event
    trigger_network_event()
    
    # Check logs after
    logger.info("\n--- Post-Test Logs ---")
    check_dmesg_logs()
    
    remove_iptables_logging()
    
    print("\n✅ Debug complete.")

if __name__ == "__main__":
    main()
