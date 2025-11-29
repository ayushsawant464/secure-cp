#!/usr/bin/env python3
"""
Configuration Validator
Validates system_config.json and ensures all required files/directories exist.
"""

import os
import sys
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ConfigValidator:
    def __init__(self, config_path="config/system_config.json"):
        self.config_path = config_path
        self.config = None
        self.errors = []
        self.warnings = []
        
    def load_config(self):
        """Load and parse the configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            logger.info(f"✓ Loaded configuration from {self.config_path}")
            return True
        except FileNotFoundError:
            self.errors.append(f"Configuration file not found: {self.config_path}")
            return False
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in configuration: {e}")
            return False
    
    def resolve_path(self, path_str):
        """Resolve path variables like ${project_root}."""
        if not path_str:
            return path_str
            
        # Get project root from config or use default
        project_root = self.config.get('paths', {}).get('project_root', 
                                                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Replace variables
        resolved = path_str.replace('${project_root}', project_root)
        resolved = os.path.expanduser(resolved)
        resolved = os.path.expandvars(resolved)
        
        return resolved
    
    def validate_paths(self):
        """Validate all path configurations."""
        if 'paths' not in self.config:
            self.warnings.append("No 'paths' section in configuration")
            return
        
        paths = self.config['paths']
        
        # Validate project root
        project_root = paths.get('project_root')
        if not project_root:
            self.errors.append("Missing 'paths.project_root' in configuration")
            return
        
        if not os.path.isdir(project_root):
            self.errors.append(f"Project root directory does not exist: {project_root}")
        else:
            logger.info(f"✓ Project root: {project_root}")
        
        # Validate other paths
        path_checks = {
            'config_dir': ('directory', False),
            'log_dir': ('directory', True),  # Can be created
            'kernel_module': ('file', True),  # Optional
            'apparmor_profiles': ('directory', True)  # Optional
        }
        
        for path_key, (path_type, optional) in path_checks.items():
            if path_key not in paths:
                if not optional:
                    self.errors.append(f"Missing required path: paths.{path_key}")
                continue
            
            resolved_path = self.resolve_path(paths[path_key])
            
            if path_type == 'directory':
                if not os.path.isdir(resolved_path):
                    if optional:
                        self.warnings.append(f"Optional directory not found: {resolved_path}")
                    else:
                        self.errors.append(f"Required directory not found: {resolved_path}")
                else:
                    logger.info(f"✓ {path_key}: {resolved_path}")
            elif path_type == 'file':
                if not os.path.isfile(resolved_path):
                    if optional:
                        self.warnings.append(f"Optional file not found: {resolved_path}")
                    else:
                        self.errors.append(f"Required file not found: {resolved_path}")
                else:
                    logger.info(f"✓ {path_key}: {resolved_path}")
    
    def validate_vpn(self):
        """Validate VPN configuration."""
        if 'vpn' not in self.config:
            self.errors.append("Missing 'vpn' section in configuration")
            return
        
        vpn = self.config['vpn']
        
        # Check required fields
        required_fields = ['interface', 'config_path']
        for field in required_fields:
            if field not in vpn:
                self.errors.append(f"Missing required VPN field: vpn.{field}")
        
        # Check if VPN config file exists
        if 'config_path' in vpn:
            vpn_config = vpn['config_path']
            if not os.path.isfile(vpn_config):
                self.errors.append(f"VPN configuration file not found: {vpn_config}")
            else:
                logger.info(f"✓ VPN config: {vpn_config}")
    
    def validate_browser(self):
        """Validate browser configuration."""
        if 'kiosk' not in self.config:
            self.errors.append("Missing 'kiosk' section in configuration")
            return
        
        kiosk = self.config['kiosk']
        
        # Check browser path
        browser_path = kiosk.get('browser_path')
        if not browser_path:
            self.warnings.append("No browser_path specified, will try to find browser automatically")
        elif not os.path.isfile(browser_path):
            self.errors.append(f"Browser executable not found: {browser_path}")
        else:
            logger.info(f"✓ Browser: {browser_path}")
    
    def validate_network(self):
        """Validate network configuration."""
        if 'network' not in self.config:
            self.errors.append("Missing 'network' section in configuration")
            return
        
        network = self.config['network']
        
        # Check allowed domains
        if 'allowed_domains' not in network or not network['allowed_domains']:
            self.errors.append("No allowed domains configured")
        else:
            logger.info(f"✓ Allowed domains: {len(network['allowed_domains'])} configured")
    
    def validate_permissions(self):
        """Check file permissions on critical files."""
        if not self.config:
            return
        
        # Check if running as root (required for production)
        if self.config.get('mode') == 'production' and os.geteuid() != 0:
            self.warnings.append("Production mode requires root privileges")
        
        # Check log directory permissions
        log_dir = self.config.get('logging', {}).get('log_dir') or \
                  self.resolve_path(self.config.get('paths', {}).get('log_dir', '/var/log/secure-exam'))
        
        if os.path.exists(log_dir):
            if not os.access(log_dir, os.W_OK):
                self.errors.append(f"Log directory is not writable: {log_dir}")
            else:
                logger.info(f"✓ Log directory writable: {log_dir}")
    
    def validate(self):
        """Run all validations."""
        logger.info("=" * 60)
        logger.info("Configuration Validation")
        logger.info("=" * 60)
        
        if not self.load_config():
            return False
        
        self.validate_paths()
        self.validate_vpn()
        self.validate_browser()
        self.validate_network()
        self.validate_permissions()
        
        # Print summary
        logger.info("=" * 60)
        if self.errors:
            logger.error(f"✗ Validation failed with {len(self.errors)} error(s):")
            for error in self.errors:
                logger.error(f"  - {error}")
        else:
            logger.info("✓ All critical validations passed")
        
        if self.warnings:
            logger.warning(f"⚠ {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        logger.info("=" * 60)
        
        return len(self.errors) == 0

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Validate Secure Exam System configuration')
    parser.add_argument('--config', default='config/system_config.json',
                       help='Path to configuration file')
    args = parser.parse_args()
    
    validator = ConfigValidator(args.config)
    if validator.validate():
        logger.info("Configuration is valid")
        return 0
    else:
        logger.error("Configuration validation failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
