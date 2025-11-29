#!/usr/bin/env python3
"""
System Lockdown Manager
Manages AppArmor/SELinux profiles for exam mode security.
"""

import subprocess
import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class SystemLockdown:
    def __init__(self, config_path="/home/savvy19/Desktop/product/secure-exam-system/config/system_config.json"):
        """Initialize system lockdown manager."""
        import json
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.security_config = self.config.get('security', {})
        self.use_apparmor = self.security_config.get('use_apparmor', True)
        self.profile_name = self.security_config.get('profile_name', 'exam-lockdown')
        
        self.profile_dir = Path(__file__).parent / "profile_templates"
        self.profile_file = self.profile_dir / "exam_apparmor.profile"
        self.system_profile_path = Path(f"/etc/apparmor.d/{self.profile_name}")
        
        self.profile_loaded = False
        
        logger.info("System Lockdown Manager initialized")
    
    def check_apparmor_status(self):
        """Check if AppArmor is installed and running."""
        try:
            result = subprocess.run(['aa-status'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("AppArmor is active")
                return True
            else:
                logger.warning("AppArmor is not active")
                return False
        except FileNotFoundError:
            logger.error("AppArmor is not installed")
            return False
    
    def load_profile(self):
        """Load AppArmor profile for exam mode."""
        if not self.use_apparmor:
            logger.info("AppArmor disabled in config")
            return True
        
        if not self.check_apparmor_status():
            logger.error("Cannot load profile - AppArmor not available")
            return False
        
        try:
            logger.info("Loading AppArmor profile for exam mode...")
            
            # Copy profile to system location
            logger.info(f"Copying profile to {self.system_profile_path}")
            shutil.copy(self.profile_file, self.system_profile_path)
            
            # Load the profile
            result = subprocess.run(['apparmor_parser', '-r', str(self.system_profile_path)],
                                   capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✓ AppArmor profile loaded successfully")
                self.profile_loaded = True
                
                # Set profile to enforce mode
                result = subprocess.run(['aa-enforce', str(self.system_profile_path)],
                                       capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("✓ AppArmor profile set to enforce mode")
                
                return True
            else:
                logger.error(f"Failed to load profile: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Exception while loading profile: {str(e)}")
            return False
    
    def unload_profile(self):
        """Unload AppArmor profile and cleanup."""
        if not self.use_apparmor:
            return True
        
        try:
            logger.info("Unloading AppArmor profile...")
            
            # Unload the profile
            result = subprocess.run(['apparmor_parser', '-R', str(self.system_profile_path)],
                                   capture_output=True, text=True)
            
            if result.returncode == 0 or 'does not exist' in result.stderr:
                logger.info("✓ AppArmor profile unloaded")
                
                # Remove system profile file
                if self.system_profile_path.exists():
                    self.system_profile_path.unlink()
                    logger.info(f"✓ Removed {self.system_profile_path}")
                
                self.profile_loaded = False
                return True
            else:
                logger.error(f"Failed to unload profile: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Exception while unloading profile: {str(e)}")
            return False
    
    def get_status(self):
        """Get current lockdown status."""
        return {
            'apparmor_active': self.check_apparmor_status(),
            'profile_loaded': self.profile_loaded,
            'profile_name': self.profile_name
        }
    
    def enable_lockdown(self):
        """Enable full system lockdown."""
        logger.info("Enabling system lockdown...")
        
        if not self.load_profile():
            return False
        
        logger.info("✓ System lockdown enabled")
        logger.warning("⚠️  System is now in restricted mode:")
        logger.warning("   - Shells blocked")
        logger.warning("   - Terminals blocked")
        logger.warning("   - Privilege escalation blocked")
        logger.warning("   - System modification blocked")
        
        return True
    
    def disable_lockdown(self):
        """Disable system lockdown."""
        logger.info("Disabling system lockdown...")
        
        if not self.unload_profile():
            return False
        
        logger.info("✓ System lockdown disabled")
        logger.info("✓ System returned to normal mode")
        
        return True


def main():
    """Test system lockdown."""
    import argparse
    
    parser = argparse.ArgumentParser(description='System Lockdown Manager')
    parser.add_argument('action', choices=['enable', 'disable', 'status'],
                       help='Action to perform')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    lockdown = SystemLockdown()
    
    print("\n" + "="*60)
    print("SYSTEM LOCKDOWN MANAGER")
    print("="*60 + "\n")
    
    if args.action == 'enable':
        print("⚠️  WARNING: This will enable strict security restrictions!")
        print("Shells, terminals, and system tools will be blocked.\n")
        confirm = input("Continue? (yes/no): ")
        
        if confirm.lower() == 'yes':
            if lockdown.enable_lockdown():
                print("\n✓ System lockdown ENABLED")
                print("\nTo disable: sudo python3 security/system_lockdown.py disable")
            else:
                print("\n✗ Failed to enable lockdown")
                return 1
        else:
            print("Cancelled")
            return 0
    
    elif args.action == 'disable':
        if lockdown.disable_lockdown():
            print("\n✓ System lockdown DISABLED")
        else:
            print("\n✗ Failed to disable lockdown")
            return 1
    
    elif args.action == 'status':
        status = lockdown.get_status()
        print(f"AppArmor Active: {status['apparmor_active']}")
        print(f"Profile Loaded:  {status['profile_loaded']}")
        print(f"Profile Name:    {status['profile_name']}")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
