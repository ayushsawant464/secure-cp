#!/usr/bin/env python3
"""
Process Allowlist Manager
Manages the allowlist of permitted processes during exam mode.
"""

import json
import logging
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Set

logger = logging.getLogger(__name__)


class AllowlistManager:
    def __init__(self, config_path="/home/savvy19/Desktop/product/secure-exam-system/config/system_config.json"):
        """Initialize allowlist manager."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.allowlist_file = Path(__file__).parent.parent / "config" / "process_allowlist.json"
        self.allowlist = {
            'processes': [],  # List of allowed process names
            'paths': [],      # List of allowed executable paths
            'checksums': {}   # Checksums for validation
        }
        
        # Load existing allowlist if available
        if self.allowlist_file.exists():
            self.load()
        
        logger.info("Allowlist Manager initialized")
    
    def load(self):
        """Load allowlist from file."""
        try:
            with open(self.allowlist_file, 'r') as f:
                self.allowlist = json.load(f)
            logger.info(f"Loaded allowlist with {len(self.allowlist['processes'])} processes")
            return True
        except Exception as e:
            logger.error(f"Failed to load allowlist: {str(e)}")
            return False
    
    def save(self):
        """Save allowlist to file."""
        try:
            # Ensure directory exists
            self.allowlist_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.allowlist_file, 'w') as f:
                json.dump(self.allowlist, f, indent=2)
            logger.info(f"Saved allowlist with {len(self.allowlist['processes'])} processes")
            return True
        except Exception as e:
            logger.error(f"Failed to save allowlist: {str(e)}")
            return False
    
    def add_process(self, name: str, path: str = None, compute_checksum: bool = False):
        """Add a process to the allowlist."""
        if name not in self.allowlist['processes']:
            self.allowlist['processes'].append(name)
            logger.info(f"Added process to allowlist: {name}")
        
        if path and path not in self.allowlist['paths']:
            self.allowlist['paths'].append(path)
            logger.info(f"Added path to allowlist: {path}")
            
            if compute_checksum and os.path.exists(path):
                checksum = self._compute_checksum(path)
                if checksum:
                    self.allowlist['checksums'][path] = checksum
                    logger.info(f"Computed checksum for {path}")
        
        return True
    
    def remove_process(self, name: str):
        """Remove a process from the allowlist."""
        if name in self.allowlist['processes']:
            self.allowlist['processes'].remove(name)
            logger.info(f"Removed process from allowlist: {name}")
            return True
        return False
    
    def is_allowed(self, name: str = None, path: str = None) -> bool:
        """Check if a process is in the allowlist."""
        if name and name in self.allowlist['processes']:
            return True
        
        if path:
            # Check exact path
            if path in self.allowlist['paths']:
                return True
            
            # Check if parent directory matches (for interpreters)
            for allowed_path in self.allowlist['paths']:
                if path.startswith(allowed_path):
                    return True
        
        return False
    
    def validate_checksum(self, path: str) -> bool:
        """Validate checksum of an executable."""
        if path not in self.allowlist['checksums']:
            logger.warning(f"No checksum stored for {path}")
            return True  # No checksum to validate
        
        stored_checksum = self.allowlist['checksums'][path]
        current_checksum = self._compute_checksum(path)
        
        if current_checksum == stored_checksum:
            return True
        else:
            logger.warning(f"Checksum mismatch for {path}!")
            logger.warning(f"  Stored:  {stored_checksum}")
            logger.warning(f"  Current: {current_checksum}")
            return False
    
    def _compute_checksum(self, path: str) -> str:
        """Compute SHA256 checksum of a file."""
        try:
            sha256 = hashlib.sha256()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to compute checksum for {path}: {str(e)}")
            return ""
    
    def get_allowlist(self) -> Dict:
        """Get the current allowlist."""
        return self.allowlist.copy()
    
    def get_processes(self) -> List[str]:
        """Get list of allowed process names."""
        return self.allowlist['processes'].copy()
    
    def get_paths(self) -> List[str]:
        """Get list of allowed paths."""
        return self.allowlist['paths'].copy()
    
    def clear(self):
        """Clear the entire allowlist."""
        self.allowlist = {
            'processes': [],
            'paths': [],
            'checksums': {}
        }
        logger.warning("Allowlist cleared")
    
    def import_system_processes(self, process_list: List[str]):
        """Import a list of system processes."""
        count = 0
        for proc in process_list:
            if proc not in self.allowlist['processes']:
                self.allowlist['processes'].append(proc)
                count += 1
        
        logger.info(f"Imported {count} system processes to allowlist")
        return count


def main():
    """Test allowlist manager."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    am = AllowlistManager()
    
    print("Allowlist Manager Test")
    print("=" * 60)
    
    # Add some test processes
    am.add_process("bash", "/bin/bash", compute_checksum=True)
    am.add_process("python3", "/usr/bin/python3")
    am.add_process("systemd")
    
    # Save
    am.save()
    
    # Check if allowed
    print(f"\nbash allowed: {am.is_allowed(name='bash')}")
    print(f"python3 allowed: {am.is_allowed(name='python3')}")
    print(f"firefox allowed: {am.is_allowed(name='firefox')}")
    
    # Show allowlist
    print(f"\nProcesses in allowlist: {len(am.get_processes())}")
    for proc in am.get_processes():
        print(f"  - {proc}")
    
    return 0


if __name__ == '__main__':
    exit(main())
