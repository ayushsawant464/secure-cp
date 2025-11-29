#!/usr/bin/env python3
"""
Integrity Checker
Verifies integrity of exam system components.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class IntegrityChecker:
    def __init__(self, config_path="/home/savvy19/Desktop/product/secure-exam-system/config/system_config.json"):
        """Initialize integrity checker."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.security_config = self.config.get('security', {})
        self.integrity_file = Path(__file__).parent.parent / "config" / "integrity.json"
        self.checksums = {}
        
        # Load existing checksums if available
        if self.integrity_file.exists():
            self.load_checksums()
        
        logger.info("Integrity Checker initialized")
    
    def compute_checksum(self, file_path: str) -> str:
        """Compute SHA256 checksum of a file."""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to compute checksum for {file_path}: {str(e)}")
            return ""
    
    def load_checksums(self):
        """Load stored checksums."""
        try:
            with open(self.integrity_file, 'r') as f:
                self.checksums = json.load(f)
            logger.info(f"Loaded {len(self.checksums)} stored checksums")
        except Exception as e:
            logger.error(f"Failed to load checksums: {str(e)}")
    
    def save_checksums(self):
        """Save checksums to file."""
        try:
            self.integrity_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.integrity_file, 'w') as f:
                json.dump(self.checksums, f, indent=2)
            logger.info(f"Saved {len(self.checksums)} checksums")
        except Exception as e:
            logger.error(f"Failed to save checksums: {str(e)}")
    
    def baseline_system(self):
        """Create baseline checksums for all system components."""
        logger.info("Creating integrity baseline...")
        
        project_root = Path(__file__).parent.parent
        
        # Files to check
        critical_files = [
            # Network components
            "network/vpn_manager.py",
            "network/domain_filter.py",
            "network/kiosk_browser.py",
            # Process management
            "process_manager/allowlist_manager.py",
            "process_manager/process_monitor.py",
            "process_manager/process_enforcer.py",
            # Security
            "security/system_lockdown.py",
            "security/integrity_checker.py",
            "security/profile_templates/exam_apparmor.profile",
            # Config
            "config/system_config.json",
        ]
        
        self.checksums = {}
        
        for file_path in critical_files:
            full_path = project_root / file_path
            if full_path.exists():
                checksum = self.compute_checksum(str(full_path))
                if checksum:
                    self.checksums[file_path] = checksum
                    logger.info(f"  ✓ {file_path}")
            else:
                logger.warning(f"  ✗ {file_path} not found")
        
        self.save_checksums()
        logger.info(f"Baseline created with {len(self.checksums)} files")
        return True
    
    def verify_integrity(self) -> Dict:
        """Verify integrity of all components."""
        logger.info("Verifying system integrity...")
        
        if not self.checksums:
            logger.error("No baseline checksums found. Run baseline_system() first.")
            return {'status': 'error', 'message': 'No baseline'}
        
        project_root = Path(__file__).parent.parent
        results = {
            'verified': [],
            'modified': [],
            'missing': []
        }
        
        for file_path, stored_checksum in self.checksums.items():
            full_path = project_root / file_path
            
            if not full_path.exists():
                results['missing'].append(file_path)
                logger.error(f"✗ MISSING: {file_path}")
                continue
            
            current_checksum = self.compute_checksum(str(full_path))
            
            if current_checksum == stored_checksum:
                results ['verified'].append(file_path)
                logger.info(f"  ✓ {file_path}")
            else:
                results['modified'].append(file_path)
                logger.error(f"  ✗ MODIFIED: {file_path}")
                logger.error(f"     Stored:  {stored_checksum}")
                logger.error(f"     Current: {current_checksum}")
        
        # Summary
        total = len(self.checksums)
        verified = len(results['verified'])
        modified = len(results['modified'])
        missing = len(results['missing'])
        
        logger.info(f"\nIntegrity Check Summary:")
        logger.info(f"  Total files:    {total}")
        logger.info(f"  Verified:       {verified}")
        logger.info(f"  Modified:       {modified}")
        logger.info(f"  Missing:        {missing}")
        
        results['status'] = 'ok' if modified == 0 and missing == 0 else 'compromised'
        results['summary'] = f"{verified}/{total} files verified"
        
        return results
    
    def check_apparmor_profile(self) -> bool:
        """Verify AppArmor profile is active and not modified."""
        try:
            result = subprocess.run(['aa-status'], capture_output=True, text=True)
            
            if 'exam-lockdown' in result.stdout:
                logger.info("✓ AppArmor profile is active")
                return True
            else:
                logger.warning("✗ AppArmor profile is not active")
                return False
        except Exception as e:
            logger.error(f"Failed to check AppArmor status: {str(e)}")
            return False


def main():
    """Test integrity checker."""
    import argparse
    import subprocess
    
    parser = argparse.ArgumentParser(description='Integrity Checker')
    parser.add_argument('action', choices=['baseline', 'verify'],
                       help='Action to perform')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    checker = IntegrityChecker()
    
    print("\n" + "="*60)
    print("INTEGRITY CHECKER")
    print("="*60 + "\n")
    
    if args.action == 'baseline':
        print("Creating integrity baseline...\n")
        checker.baseline_system()
        print("\n✓ Baseline created")
        print(f"Checksums saved to: {checker.integrity_file}")
    
    elif args.action == 'verify':
        print("Verifying system integrity...\n")
        results = checker.verify_integrity()
        
        if results['status'] == 'ok':
            print("\n✓ ALL CHECKS PASSED")
            print("System integrity verified")
        else:
            print("\n✗ INTEGRITY VIOLATION DETECTED!")
            if results['modified']:
                print(f"\nModified files ({len(results['modified'])}):")
                for f in results['modified']:
                    print(f"  - {f}")
            if results['missing']:
                print(f"\nMissing files ({len(results['missing'])}):")
                for f in results['missing']:
                    print(f"  - {f}")
            return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
