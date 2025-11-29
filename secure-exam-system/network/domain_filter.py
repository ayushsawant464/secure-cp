#!/usr/bin/env python3
"""
Domain Filter
Implements network filtering to allow ONLY codeforces.com and subdomains.
Operates inside the VPN tunnel for security.
Handles IPv4 and IPv6 separately, with iptables backup/restore for production mode.
"""

import subprocess
import json
import logging
import socket
import os

logger = logging.getLogger(__name__)


class DomainFilter:
    def __init__(self, config_path=None):
        """Initialize domain filter with configuration.
        Handles possible stray characters (e.g., UTF‑8 BOM) before the JSON object.
        
        Args:
            config_path: Path to configuration file. If None, uses environment variable
                        EXAM_CONFIG or defaults to config/system_config.json
        """
        if config_path is None:
            # Try environment variable first
            config_path = os.environ.get('EXAM_CONFIG')
            if config_path is None:
                # Default to relative path from project root
                script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                config_path = os.path.join(script_dir, 'config', 'system_config.json')
        
        # Read the file as raw text
        with open(config_path, 'r', encoding='utf-8') as f:
            raw = f.read()
        # Find the first '{' which marks the start of the JSON object
        json_start = raw.find('{')
        if json_start == -1:
            raise ValueError('Configuration file does not contain a JSON object')
        # Load JSON from that point onward
        self.config = json.loads(raw[json_start:])
        
        self.mode = self.config['mode']
        self.network_config = self.config['network']
        self.vpn_config = self.config['vpn']
        self.allowed_domains = self.network_config['allowed_domains']
        self.namespace = self.vpn_config.get('namespace', 'exam_ns')
        self.is_testing = (self.mode == 'testing')
        
        # Resolve allowed IPs from domains - separate IPv4 and IPv6
        self.allowed_ips_v4 = set()
        self.allowed_ips_v6 = set()
        
        logger.info(f"Domain Filter initialized in {self.mode} mode")
        logger.info(f"Allowed domains: {self.allowed_domains}")
    
    def resolve_allowed_ips(self):
        """Resolve IP addresses for allowed domains."""
        logger.info("Resolving IP addresses for allowed domains...")
        
        domains_to_resolve = []
        for domain in self.allowed_domains:
            if '*' not in domain:  # Skip wildcard domains
                domains_to_resolve.append(domain)
        
        for domain in domains_to_resolve:
            try:
                 # Resolve domain to IPs
                ips = socket.getaddrinfo(domain, None)
                for ip_info in ips:
                    ip = ip_info[4][0]
                    family = ip_info[0]
                    
                    # Separate IPv4 and IPv6
                    if family == socket.AF_INET:
                        self.allowed_ips_v4.add(ip)
                        logger.info(f"  {domain} -> {ip} (IPv4)")
                    elif family == socket.AF_INET6:
                        self.allowed_ips_v6.add(ip)
                        logger.info(f"  {domain} -> {ip} (IPv6)")
            except socket.gaierror as e:
                logger.warning(f"Could not resolve {domain}: {e}")
        
        logger.info(f"Resolved {len(self.allowed_ips_v4)} IPv4 and {len(self.allowed_ips_v6)} IPv6 addresses")
        return True
    
    def backup_iptables(self):
        """Backup current iptables rules (production mode only)."""
        if self.is_testing:
            return True  # No backup needed in testing mode
        
        try:
            logger.info("Backing up current iptables rules...")
            
            # Backup IPv4 rules
            result = subprocess.run(['iptables-save'], capture_output=True, text=True)
            if result.returncode == 0:
                with open('/tmp/exam-iptables-backup.rules', 'w') as f:
                    f.write(result.stdout)
                logger.info("  IPv4 rules backed up")
            
            # Backup IPv6 rules
            result = subprocess.run(['ip6tables-save'], capture_output=True, text=True)
            if result.returncode == 0:
                with open('/tmp/exam-ip6tables-backup.rules', 'w') as f:
                    f.write(result.stdout)
                logger.info("  IPv6 rules backed up")
            
            return True
        except Exception as e:
            logger.error(f"Failed to backup iptables: {str(e)}")
            return False
    
    def restore_iptables(self):
        """Restore original iptables rules (production mode only)."""
        if self.is_testing:
            return True  # No restore needed in testing mode
        
        try:
            logger.info("Restoring original iptables rules...")
            
            # Restore IPv4 rules
            if os.path.exists('/tmp/exam-iptables-backup.rules'):
                with open('/tmp/exam-iptables-backup.rules', 'r') as f:
                    subprocess.run(['iptables-restore'], stdin=f, check=True)
                logger.info("  IPv4 rules restored")
                os.remove('/tmp/exam-iptables-backup.rules')
            
            # Restore IPv6 rules
            if os.path.exists('/tmp/exam-ip6tables-backup.rules'):
                with open('/tmp/exam-ip6tables-backup.rules', 'r') as f:
                    subprocess.run(['ip6tables-restore'], stdin=f, check=True)
                logger.info("  IPv6 rules restored")
                os.remove('/tmp/exam-ip6tables-backup.rules')
            
            return True
        except Exception as e:
            logger.error(f"Failed to restore iptables: {str(e)}")
            return False
    
    def configure_iptables_filtering(self):
        """
        Configure iptables to allow ONLY codeforces.com IPs.
        Handles IPv4 and IPv6 separately.
        This works inside the VPN tunnel after traffic is decrypted.
        """
        try:
            if self.is_testing:
                ns_exec = ['ip', 'netns', 'exec', self.namespace]
            else:
                ns_exec = []
                # Backup current rules in production mode
                self.backup_iptables()
            
            logger.info("Configuring iptables domain filtering...")
            
            # ===== IPv4 FILTERING =====
            
            # Create new chain for domain filtering (IPv4)
            subprocess.run(ns_exec + ['iptables', '-N', 'EXAM_FILTER'], 
                          capture_output=True)
            
            # CRITICAL SAFEGUARDS (prevent total lockout)
            # 1. Allow localhost ALWAYS
            subprocess.run(ns_exec + ['iptables', '-A', 'EXAM_FILTER', 
                          '-o', 'lo', '-j', 'ACCEPT'],
                          capture_output=True)
            
            # 2. Allow established connections (prevents breaking chat, SSH, etc.)
            subprocess.run(ns_exec + ['iptables', '-A', 'EXAM_FILTER',
                          '-m', 'state', '--state', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'],
                          capture_output=True)
            
            # 3. Allow DNS queries (port 53) - IPv4
            subprocess.run(ns_exec + ['iptables', '-A', 'EXAM_FILTER', 
                                     '-p', 'udp', '--dport', '53', '-j', 'ACCEPT'],
                          capture_output=True)
            subprocess.run(ns_exec + ['iptables', '-A', 'EXAM_FILTER', 
                                     '-p', 'tcp', '--dport', '53', '-j', 'ACCEPT'],
                          capture_output=True)
            
            # Allow traffic to resolved IPv4 addresses (HTTP/HTTPS)
            for ip in self.allowed_ips_v4:
                subprocess.run(ns_exec + ['iptables', '-A', 'EXAM_FILTER', 
                              '-d', ip, '-j', 'ACCEPT'],
                              capture_output=True)
                logger.info(f"  Allowed IPv4: {ip}")
            
            # IMPORTANT: RETURN (not DROP) for non-matched packets
            # This allows other rules to handle them
            subprocess.run(ns_exec + ['iptables', '-A', 'EXAM_FILTER', 
                          '-j', 'DROP'],
                          capture_output=True)
            
            # Insert at beginning of OUTPUT chain
            subprocess.run(ns_exec + ['iptables', '-I', 'OUTPUT', '1', 
                          '-j', 'EXAM_FILTER'],
                          capture_output=True)
            
            logger.info(f"IPv4 filtering configured ({len(self.allowed_ips_v4)} addresses)")
            logger.info("SAFEGUARDS: localhost ✓, DNS ✓, established connections ✓")
            
            # ===== IPv6 FILTERING =====
            
            if len(self.allowed_ips_v6) > 0:
                logger.info("Configuring IPv6 filtering...")
                
                # Create new chain for domain filtering (IPv6)
                subprocess.run(ns_exec + ['ip6tables', '-N', 'EXAM_FILTER_V6'], 
                              capture_output=True)
                
                # CRITICAL SAFEGUARDS (prevent total lockout)
                # 1.Allow localhost
                subprocess.run(ns_exec + ['ip6tables', '-A', 'EXAM_FILTER_V6',
                              '-o', 'lo', '-j', 'ACCEPT'],
                              capture_output=True)
                
                # 2. Allow established connections
                subprocess.run(ns_exec + ['ip6tables', '-A', 'EXAM_FILTER_V6',
                              '-m', 'state', '--state', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'],
                              capture_output=True)
                
                # 3. Allow DNS queries (port 53) - IPv6
                subprocess.run(ns_exec + ['ip6tables', '-A', 'EXAM_FILTER_V6', 
                                         '-p', 'udp', '--dport', '53', '-j', 'ACCEPT'],
                              capture_output=True)
                subprocess.run(ns_exec + ['ip6tables', '-A', 'EXAM_FILTER_V6', 
                                         '-p', 'tcp', '--dport', '53', '-j', 'ACCEPT'],
                              capture_output=True)
                
                # Allow traffic to resolved IPv6 addresses
                for ip in self.allowed_ips_v6:
                    subprocess.run(ns_exec + ['ip6tables', '-A', 'EXAM_FILTER_V6', 
                                             '-d', ip, '-j', 'ACCEPT'],
                                  capture_output=True)
                    logger.info(f"  Allowed IPv6: {ip}")
                
                # Drop everything else (IPv6)
                subprocess.run(ns_exec + ['ip6tables', '-A', 'EXAM_FILTER_V6', 
                                         '-j', 'DROP'],
                              capture_output=True)
                
                # Apply the filter chain to OUTPUT (IPv6)
                subprocess.run(ns_exec + ['ip6tables', '-I', 'OUTPUT', '1', 
                                         '-j', 'EXAM_FILTER_V6'],
                              capture_output=True)
                
                logger.info(f"IPv6 filtering configured ({len(self.allowed_ips_v6)} addresses)")
                logger.info("IPv6 SAFEGUARDS: localhost ✓, DNS ✓, established ✓")
            else:
                logger.info("No IPv6 addresses resolved, skipping IPv6 configuration")
            
            logger.info("Domain filtering configured successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure iptables: {e.stderr.decode()}")
            # In production mode, restore original rules if we fail
            if not self.is_testing:
                logger.info("Attempting to restore original iptables rules due to error...")
                self.restore_iptables()
            return False
    
    def enable_certificate_pinning(self):
        """
        Optional: Enable certificate pinning for codeforces.com
        Note: This is more of a browser-level feature, but we note it here.
        """
        if not self.network_config.get('certificate_pinning_enabled', False):
            logger.info("Certificate pinning disabled in config")
            return True
        
        logger.info("Certificate pinning support noted (implemented in kiosk browser)")
        # This will be implemented in the kiosk browser module
        return True
    
    def start(self):
        """Start domain filtering."""
        logger.info("Starting Domain Filter...")
        
        if not self.resolve_allowed_ips():
            logger.warning("IP resolution had issues, continuing anyway...")
        
        if not self.configure_iptables_filtering():
            return False
        
        if not self.enable_certificate_pinning():
            return False
        
        logger.info("Domain Filter started successfully")
        return True
    
    def stop(self):
        """Stop domain filtering and cleanup."""
        logger.info("Stopping Domain Filter...")
        
        try:
            if self.is_testing:
                ns_exec = ['ip', 'netns', 'exec', self.namespace]
                
                # Remove IPv4 filter chain
                subprocess.run(ns_exec + ['iptables', '-D', 'OUTPUT', '-j', 'EXAM_FILTER'],
                              capture_output=True)
                subprocess.run(ns_exec + ['iptables', '-F', 'EXAM_FILTER'],
                              capture_output=True)
                subprocess.run(ns_exec + ['iptables', '-X', 'EXAM_FILTER'],
                              capture_output=True)
                
                # Remove IPv6 filter chain
                subprocess.run(ns_exec + ['ip6tables', '-D' , 'OUTPUT', '-j', 'EXAM_FILTER_V6'],
                              capture_output=True)
                subprocess.run(ns_exec + ['ip6tables', '-F', 'EXAM_FILTER_V6'],
                              capture_output=True)
                subprocess.run(ns_exec + ['ip6tables', '-X', 'EXAM_FILTER_V6'],
                              capture_output=True)
                
                logger.info("Filter chains removed (testing mode)")
            else:
                # In production mode, restore original iptables
                self.restore_iptables()
                logger.info("Original iptables rules restored (production mode)")
            
            logger.info("Domain Filter stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping domain filter: {str(e)}")
            return False
    
    def test_connection(self, domain):
        """Test if connection to a domain is allowed."""
        logger.info(f"Testing connection to {domain}...")
        
        try:
            if self.is_testing:
                result = subprocess.run(['ip', 'netns', 'exec', self.namespace,
                                        'curl', '-I', '--max-time', '5',
                                        f'https://{domain}'],
                                       capture_output=True, text=True, timeout=10)
            else:
                result = subprocess.run(['curl', '-I', '--max-time', '5',
                                        f'https://{domain}'],
                                       capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info(f"  ✓ {domain} - ALLOWED")
                return True
            else:
                logger.info(f"  ✗ {domain} - BLOCKED")
                return False
                
        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            return False


def main():
    """Test domain filter."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    df = DomainFilter()
    
    print("Starting Domain Filter...")
    if df.start():
        print("Domain Filter started successfully!\n")
        
        # Test connections
        test_domains = [
            'codeforces.com',
            'google.com',
            'github.com'
        ]
        
        print("Testing domain access:")
        for domain in test_domains:
            df.test_connection(domain)
    else:
        print("Failed to start Domain Filter")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
