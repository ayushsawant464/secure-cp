#!/usr/bin/env python3
"""
WireGuard VPN Manager
Manages VPN tunnel creation and routing with support for testing/production modes.
"""

import subprocess
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class VPNManager:
    def __init__(self, config_path="/home/savvy19/Desktop/product/secure-exam-system/config/system_config.json"):
        """Initialize VPN manager with configuration."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.mode = self.config['mode']
        self.vpn_config = self.config['vpn']
        self.interface = self.vpn_config['interface']
        self.namespace = self.vpn_config.get('namespace', 'exam_ns')
        self.is_testing = (self.mode == 'testing')
        
        logger.info(f"VPN Manager initialized in {self.mode} mode")
    
    def create_namespace(self):
        """Create network namespace for testing mode."""
        if not self.is_testing:
            logger.info("Production mode - skipping namespace creation")
            return True
        
        try:
            # Create network namespace
            logger.info(f"Creating network namespace: {self.namespace}")
            subprocess.run(['ip', 'netns', 'add', self.namespace], 
                          check=True, capture_output=True)
            
            # Bring up loopback in namespace
            subprocess.run(['ip', 'netns', 'exec', self.namespace, 
                           'ip', 'link', 'set', 'lo', 'up'],
                          check=True, capture_output=True)
            
            logger.info(f"Namespace {self.namespace} created successfully")
            return True
        except subprocess.CalledProcessError as e:
            if b'File exists' in e.stderr:
                logger.warning(f"Namespace {self.namespace} already exists")
                return True
            logger.error(f"Failed to create namespace: {e.stderr.decode()}")
            return False
    
    def setup_vpn_tunnel(self):
        """Setup WireGuard VPN tunnel."""
        try:
            wg_config = self.vpn_config.get('config_path', '/etc/wireguard/exam.conf')
            
            if self.is_testing:
                # In testing mode, bring up WireGuard in namespace
                logger.info(f"Setting up VPN in namespace {self.namespace}")
                
                # Bring up WireGuard interface in namespace
                cmd = ['ip', 'netns', 'exec', self.namespace, 
                       'wg-quick', 'up', wg_config]
            else:
                # In production mode, bring up on host
                logger.info("Setting up VPN on host system")
                cmd = ['wg-quick', 'up', wg_config]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("VPN tunnel established successfully")
                return True
            else:
                logger.error(f"Failed to setup VPN: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Exception during VPN setup: {str(e)}")
            return False
    
    def configure_routing(self):
        """Configure routing to route ALL traffic through VPN."""
        try:
            if self.is_testing:
                ns_exec = ['ip', 'netns', 'exec', self.namespace]
            else:
                ns_exec = []
            
            # Get VPN gateway from config
            vpn_gateway = self.vpn_config.get('vpn_gateway', '10.8.0.1')
            
            # Delete default route
            logger.info("Configuring routes to force all traffic through VPN")
            subprocess.run(ns_exec + ['ip', 'route', 'del', 'default'], 
                          capture_output=True)
            
            # Add default route through VPN
            subprocess.run(ns_exec + ['ip', 'route', 'add', 'default', 
                                     'via', vpn_gateway, 'dev', self.interface],
                          check=True, capture_output=True)
            
            logger.info(f"All traffic now routes through VPN gateway {vpn_gateway}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure routing: {e.stderr.decode()}")
            return False
    
    def enable_kill_switch(self):
        """
        Enable VPN kill switch - block all traffic if VPN goes down.
        Uses iptables to drop all traffic except through VPN interface.
        """
        if not self.vpn_config.get('kill_switch_enabled', True):
            logger.info("Kill switch disabled in config")
            return True
        
        try:
            if self.is_testing:
                ns_exec = ['ip', 'netns', 'exec', self.namespace]
            else:
                ns_exec = []
            
            logger.info("Enabling VPN kill switch")
            
            # Flush existing rules
            subprocess.run(ns_exec + ['iptables', '-F'], capture_output=True)
            subprocess.run(ns_exec + ['iptables', '-X'], capture_output=True)
            
            # Set default policies to DROP
            subprocess.run(ns_exec + ['iptables', '-P', 'INPUT', 'DROP'], 
                          check=True, capture_output=True)
            subprocess.run(ns_exec + ['iptables', '-P', 'FORWARD', 'DROP'], 
                          check=True, capture_output=True)
            subprocess.run(ns_exec + ['iptables', '-P', 'OUTPUT', 'DROP'], 
                          check=True, capture_output=True)
            
            # Allow loopback
            subprocess.run(ns_exec + ['iptables', '-A', 'INPUT', '-i', 'lo', 
                                     '-j', 'ACCEPT'], check=True, capture_output=True)
            subprocess.run(ns_exec + ['iptables', '-A', 'OUTPUT', '-o', 'lo', 
                                     '-j', 'ACCEPT'], check=True, capture_output=True)
            
            # Allow traffic through VPN interface only
            subprocess.run(ns_exec + ['iptables', '-A', 'INPUT', '-i', 
                                     self.interface, '-j', 'ACCEPT'], 
                          check=True, capture_output=True)
            subprocess.run(ns_exec + ['iptables', '-A', 'OUTPUT', '-o', 
                                     self.interface, '-j', 'ACCEPT'], 
                          check=True, capture_output=True)
            
            # Allow established connections
            subprocess.run(ns_exec + ['iptables', '-A', 'INPUT', '-m', 'state', 
                                     '--state', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'],
                          check=True, capture_output=True)
            
            # Log dropped packets
            subprocess.run(ns_exec + ['iptables', '-A', 'OUTPUT', '-j', 'LOG', 
                                     '--log-prefix', '[EXAM-KILLSWITCH] '],
                          capture_output=True)
            
            logger.info("Kill switch enabled - all non-VPN traffic will be blocked")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to enable kill switch: {e.stderr.decode()}")
            return False
    
    def start(self):
        """Start VPN with all configurations."""
        logger.info("Starting VPN Manager...")
        
        if self.is_testing:
            if not self.create_namespace():
                return False
        
        if not self.setup_vpn_tunnel():
            return False
        
        if not self.configure_routing():
            return False
        
        if not self.enable_kill_switch():
            return False
        
        logger.info("VPN Manager started successfully")
        return True
    
    def stop(self):
        """Stop VPN and cleanup."""
        logger.info("Stopping VPN Manager...")
        
        try:
            if self.is_testing:
                # Stop VPN in namespace
                subprocess.run(['ip', 'netns', 'exec', self.namespace, 
                               'wg-quick', 'down', self.vpn_config.get('config_path')],
                              capture_output=True)
                
                # Delete namespace
                subprocess.run(['ip', 'netns', 'del', self. namespace],
                              capture_output=True)
                logger.info(f"Namespace {self.namespace} deleted")
            else:
                # Stop VPN on host
                subprocess.run(['wg-quick', 'down', 
                               self.vpn_config.get('config_path')],
                              capture_output=True)
            
            logger.info("VPN Manager stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping VPN: {str(e)}")
            return False
    
    def get_status(self):
        """Get VPN status information."""
        try:
            if self.is_testing:
                result = subprocess.run(['ip', 'netns', 'exec', self.namespace,
                                        'wg', 'show', self.interface],
                                       capture_output=True, text=True)
            else:
                result = subprocess.run(['wg', 'show', self.interface],
                                       capture_output=True, text=True)
            
            return {
                'active': result.returncode == 0,
                'mode': self.mode,
                'interface': self.interface,
                'details': result.stdout if result.returncode == 0 else result.stderr
            }
        except Exception as e:
            return {
                'active': False,
                'error': str(e)
            }


def main():
    """Test VPN manager."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    vpn = VPNManager()
    
    print("Starting VPN...")
    if vpn.start():
        print("VPN started successfully!")
        print("\nVPN Status:")
        status = vpn.get_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
    else:
        print("Failed to start VPN")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
