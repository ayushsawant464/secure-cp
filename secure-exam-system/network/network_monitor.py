#!/usr/bin/env python3
"""
Network Monitor
Real-time monitoring of network connections and security events.
"""

import subprocess
import json
import logging
import time
import threading
from datetime import datetime

logger = logging.getLogger(__name__)


class NetworkMonitor:
    def __init__(self, config_path="/home/savvy19/Desktop/product/secure-exam-system/config/system_config.json"):
        """Initialize network monitor."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.mode = self.config['mode']
        self.vpn_config = self.config['vpn']
        self.namespace = self.vpn_config.get('namespace', 'exam_ns')
        self.is_testing = (self.mode == 'testing')
        
        self.monitoring = False
        self.monitor_thread = None
        
        logger.info(f"Network Monitor initialized in {self.mode} mode")
    
    def get_active_connections(self):
        """Get list of active network connections."""
        try:
            if self.is_testing:
                result = subprocess.run(['ip', 'netns', 'exec', self.namespace,
                                        'ss', '-tupn'],
                                       capture_output=True, text=True)
            else:
                result = subprocess.run(['ss', '-tupn'],
                                       capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout
            return ""
            
        except Exception as e:
            logger.error(f"Failed to get connections: {str(e)}")
            return ""
    
    def check_vpn_status(self):
        """Check if VPN is active."""
        try:
            if self.is_testing:
                result = subprocess.run(['ip', 'netns', 'exec', self.namespace,
                                        'wg', 'show'],
                                       capture_output=True, text=True)
            else:
                result = subprocess.run(['wg', 'show'],
                                       capture_output=True, text=True)
            
            return result.returncode == 0
            
        except Exception as e:
            return False
    
    def read_iptables_log(self):
        """Read iptables log for blocked connections."""
        try:
            # Read kernel log for our custom markers
            result = subprocess.run(['dmesg', '-T'],
                                   capture_output=True, text=True)
            
            if result.returncode == 0:
                # Filter for our log markers
                lines = result.stdout.split('\n')
                blocked = [l for l in lines if '[EXAM-BLOCKED]' in l]
                killswitch = [l for l in lines if '[EXAM-KILLSWITCH]' in l]
                
                return {
                    'blocked_connections': blocked[-10:],  # Last 10
                    'killswitch_blocks': killswitch[-10:]
                }
            return {}
            
        except Exception as e:
            logger.error(f"Failed to read logs: {str(e)}")
            return {}
    
    def monitor_loop(self):
        """Main monitoring loop."""
        logger.info("Starting monitoring loop...")
        
        while self.monitoring:
            # Check VPN status
            vpn_active = self.check_vpn_status()
            if not vpn_active:
                logger.error("⚠️  VPN IS DOWN! Kill switch should be blocking all traffic")
            
            # Check for blocked connections
            logs = self.read_iptables_log()
            if logs.get('blocked_connections'):
                logger.info(f"Blocked {len(logs['blocked_connections'])} unauthorized connection attempts")
            
            time.sleep(5)  # Check every 5 seconds
    
    def start(self):
        """Start network monitoring."""
        logger.info("Starting Network Monitor...")
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Network Monitor started successfully")
        return True
    
    def stop(self):
        """Stop network monitoring."""
        logger.info("Stopping Network Monitor...")
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        logger.info("Network Monitor stopped successfully")
        return True
    
    def get_status(self):
        """Get current network status."""
        return {
            'vpn_active': self.check_vpn_status(),
            'active_connections': self.get_active_connections(),
            'security_logs': self.read_iptables_log(),
            'timestamp': datetime.now().isoformat()
        }


def main():
    """Test network monitor."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    nm = NetworkMonitor()
    
    print("Starting Network Monitor...")
    nm.start()
    
    print("Monitoring network... Press Ctrl+C to stop\n")
    
    try:
        while True:
            status = nm.get_status()
            print(f"\n{'='*60}")
            print(f"VPN Active: {status['vpn_active']}")
            print(f"Timestamp: {status['timestamp']}")
            print(f"\nActive Connections:")
            print(status['active_connections'][:500])  # First 500 chars
            
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        nm.stop()
    
    return 0


if __name__ == '__main__':
    exit(main())
