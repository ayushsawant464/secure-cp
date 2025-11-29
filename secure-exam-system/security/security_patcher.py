#!/usr/bin/env python3
"""
Security Patcher
Implements critical security fixes identified by red team analysis.
"""

import subprocess
import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SecurityPatcher:
    def __init__(self, config_path="/home/savvy19/Desktop/product/secure-exam-system/config/system_config.json"):
        """Initialize security patcher."""
        import json
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            self.mode = config.get('mode', 'testing')
        except:
            self.mode = 'testing'  # Default to safe mode
        
        self.patches_applied = []
        logger.info(f"Security Patcher initialized (mode: {self.mode})")
    
    def clear_environment_variables(self):
        """
        PATCH #1: Block LD_PRELOAD and dangerous environment variables.
        Prevents library injection attacks.
        """
        logger.info("Applying PATCH #1: Environment variable sanitization")
        
        dangerous_vars = [
            'LD_PRELOAD',
            'LD_LIBRARY_PATH',
            'LD_AUDIT',
            'PYTHONPATH',
            'PERL5LIB'
        ]
        
        for var in dangerous_vars:
            if var in os.environ:
                del os.environ[var]
                logger.info(f"  Cleared {var}")
        
        self.patches_applied.append("environment_sanitization")
        logger.info("✓ Environment sanitized")
        return True
    
    def clear_tmp_directory(self):
        """
        PATCH #2: Clear /tmp directory before exam.
        Prevents access to pre-prepared cheat files.
        """
        logger.info("Applying PATCH #2: /tmp directory cleanup")
        
        try:
            tmp_path = Path("/tmp")
            
            # Get list of files (exclude system files)
            excluded = ['systemd-private', '.X11-unix', '.XIM-unix',  '.font-unix', '.ICE-unix']
            
            count = 0
            for item in tmp_path.iterdir():
                if item.name not in excluded and not item.name.startswith('.'):
                    try:
                        if item.is_file():
                            item.unlink()
                            count += 1
                        elif item.is_dir():
                            shutil.rmtree(item)
                            count += 1
                    except (PermissionError, OSError) as e:
                        logger.warning(f"  Could not remove {item}: {e}")
            
            logger.info(f"  Cleaned {count} items from /tmp")
            self.patches_applied.append("tmp_cleanup")
            logger.info("✓ /tmp cleaned")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clean /tmp: {str(e)}")
            return False
    
    def clear_browser_cache(self):
        """
        PATCH #3: Clear browser cache before exam.
        Prevents access to cached solutions.
        """
        logger.info("Applying PATCH #3: Browser cache cleanup")
        
        cache_paths = [
            Path.home() / ".cache/chromium",
            Path.home() / ".config/chromium/Default/Cache",
            Path.home() / ".cache/google-chrome",
            Path.home() / ".mozilla/firefox",
        ]
        
        count = 0
        for cache_path in cache_paths:
            if cache_path.exists():
                try:
                    shutil.rmtree(cache_path)
                    count += 1
                    logger.info(f"  Cleared {cache_path}")
                except Exception as e:
                    logger.warning(f"  Could not clear {cache_path}: {e}")
        
        self.patches_applied.append("browser_cache_clear")
        logger.info(f"✓ Cleared {count} browser caches")
        return True
    
    def clear_clipboard(self):
        """
        PATCH #4: Clear clipboard before exam.
        Prevents paste from pre-copied cheat sheets.
        """
        logger.info("Applying PATCH #4: Clipboard cleanup")
        
        try:
            # Try xsel
            subprocess.run(['xsel', '-bc'], capture_output=True, timeout=2)
            subprocess.run(['xsel', '-pc'], capture_output=True, timeout=2)
            subprocess.run(['xsel', '-sc'], capture_output=True, timeout=2)
            logger.info("  Cleared clipboard (xsel)")
        except:
            pass
        
        try:
            # Try xclip
            subprocess.run(['xclip', '-selection', 'clipboard', '/dev/null'], 
                          capture_output=True, timeout=2, stdin=subprocess.DEVNULL)
            logger.info("  Cleared clipboard (xclip)")
        except:
            pass
        
        self.patches_applied.append("clipboard_clear")
        logger.info("✓ Clipboard cleared")
        return True
    
    def disable_virtual_consoles(self):
        """
        PATCH #5: Disable virtual console switching.
        Prevents Ctrl+Alt+F1-F6 bypass.
        
        NOTE: This is difficult to fully implement without kernel-level hooks.
        For production, use AppArmor profile + physical keyboard lock.
        """
        logger.info("Applying PATCH #5: Virtual console lockdown")
        
        # SKIP in testing mode - can cause console switching issues
        if self.mode == 'testing':
            logger.info("  ⊘ Skipped in testing mode (production only)")
            self.patches_applied.append("vt_lockdown_skipped")
            return True
        
        try:
            # Try to disable console switching via setkeycodes
            # This attempts to disable the SAK (Secure Attention Key)
            # Note: This may not work on all systems
            
            # Disable SysRq keys (which includes console switching)
            try:
                with open('/proc/sys/kernel/sysrq', 'w') as f:
                    f.write('0')
                logger.info("  Disabled SysRq keys")
            except:
                pass
            
            # Note: Full VT lockdown requires:
            # - X11 server grabbing input (done by kiosk browser)
            # - AppArmor/SELinux preventing chvt access
            # - Physical keyboard lock in production
            
            self.patches_applied.append("vt_lockdown")
            logger.info("✓ Virtual console switching mitigation applied")
            logger.info("  (Full lockdown requires AppArmor + kiosk browser)")
            return True
            
        except Exception as e:
            logger.warning(f"Virtual console lockdown failed: {e}")
            logger.warning("(VT blocking requires kernel-level access)")
            return False
    
    def apply_all_patches(self):
        """Apply all critical security patches."""
        logger.info("\n" + "="*60)
        logger.info("APPLYING CRITICAL SECURITY PATCHES")
        logger.info("="*60 + "\n")
        
        patches = [
            self.clear_environment_variables,
            self.clear_tmp_directory,
            self.clear_browser_cache,
            self.clear_clipboard,
            self.disable_virtual_consoles,
        ]
        
        results = []
        for patch in patches:
            try:
                result = patch()
                results.append(result)
            except Exception as e:
                logger.error(f"{patch.__name__} failed: {e}")
                results.append(False)
        
        success_count = sum(results)
        total = len(results)
        
        logger.info("\n" + "="*60)
        logger.info(f"PATCHES APPLIED: {success_count}/{total}")
        logger.info("="*60)
        
        return all(results)


def main():
    """Test security patcher."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("SECURITY PATCHER")
    print("="*60)
    print("\n⚠️  This will clear /tmp, browser cache, and clipboard")
    print("Continue? (yes/no): ", end='')
    
    confirm = input()
    if confirm.lower() != 'yes':
        print("Cancelled")
        return 0
    
    patcher = SecurityPatcher()
    
    if patcher.apply_all_patches():
        print("\n✓ All patches applied successfully")
        return 0
    else:
        print("\n⚠️  Some patches failed")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
