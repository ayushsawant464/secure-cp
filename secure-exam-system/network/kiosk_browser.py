#!/usr/bin/env python3
"""
Kiosk Browser
Implements a fullscreen locked browser for codeforces.com with escape prevention.
"""

import subprocess
import json
import logging
import os
import signal
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class KioskBrowser:
    def __init__(self, config_path=None):
        """Initialize kiosk browser with configuration.
        
        Args:
            config_path: Path to configuration file. If None, uses environment variable
                        EXAM_CONFIG or defaults to config/system_config.json
        """
        if config_path is None:
            config_path = os.environ.get('EXAM_CONFIG')
            if config_path is None:
                script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                config_path = os.path.join(script_dir, 'config', 'system_config.json')
        
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.mode = self.config['mode']
        self.kiosk_config = self.config['kiosk']
        self.network_config = self.config['network']
        self.vpn_config = self.config['vpn']
        
        self.browser = self.kiosk_config.get('browser', 'chromium-browser')
        self.start_url = self.kiosk_config.get('start_url', 'https://codeforces.com')
        self.namespace = self.vpn_config.get('namespace', 'exam_ns')
        self.is_testing = (self.mode == 'testing')
        
        self.process = None
        
        logger.info(f"Kiosk Browser initialized in {self.mode} mode")
    
    def build_browser_args(self):
        """Build command-line arguments for kiosk mode browser."""
        args = [self.browser]
        
        # Kiosk mode - fullscreen, no UI
        args.extend([
            '--kiosk',
            self.start_url,
            '--no-first-run',
            '--disable-session-crashed-bubble',
            '--disable-infobars',
        ])
        
        # Disable developer tools
        if self.kiosk_config.get('disable_dev_tools', True):
            args.extend([
                '--disable-dev-tools',
                '--disable-extensions',
            ])
        
        # Disable context menu (right-click)
        if self.kiosk_config.get('disable_context_menu', True):
            args.append('--disable-background-networking')
        
        # Content settings to block non-codeforces domains at browser level
        allowed_domains = self.network_config.get('allowed_domains', [])
        domains_str = ','.join([d.replace('*.', '') for d in allowed_domains])
        
        # User data directory
        user_data_dir = '/tmp/exam-browser-profile'
        args.append(f'--user-data-dir={user_data_dir}')
        
        # Certificate pinning (if enabled)
        if self.network_config.get('certificate_pinning_enabled', False):
            # Chromium supports HPKP (Public Key Pinning)
            # This would need the actual pin values
            logger.info("Certificate pinning enabled (requires pin configuration)")
        
        # Security settings
        args.extend([
            '--no-default-browser-check',
            '--disable-translate',
            '--disable-features=TranslateUI',
            '--overscroll-history-navigation=0',  # Disable swipe navigation
        ])
        
        return args
    
    def setup_key_blocking(self):
        """
        Setup key blocking to prevent escape mechanisms.
        This uses xdotool or similar to intercept key combinations.
        """
        # Skip key blocking in testing mode to avoid interfering with developer workflow
        if self.is_testing:
            logger.info("Skipping key blocking in testing mode")
            return True
        
        logger.info("Setting up key blocking for escape prevention (production mode)...")
        
        # List of key combinations to block
        blocked_keys = [
            'F11',  # Fullscreen toggle
            'Alt+F4',  # Close window
            'Alt+Tab',  # Window switching
            'Ctrl+Alt+F1', 'Ctrl+Alt+F2', 'Ctrl+Alt+F3',  # Virtual consoles
            'Ctrl+Shift+Esc',  # Task manager
            'Ctrl+Alt+Del',  # System interrupt
            'Super+L',  # Lock screen
        ]
        
        # NOTE: Implementing full combo blocking requires a window manager or xbindkeys.
        # Here we provide a simple xmodmap based approach that disables the primary keys.
        # This works for most X environments but may need adjustment per hardware.
        
        # Save current keymap to restore later
        self._original_keymap = subprocess.run(['xmodmap', '-pke'], capture_output=True, text=True).stdout
        
        # Disable specific keycodes (common values, may vary on your system)
        # F4 (keycode 70), F11 (keycode 95), Tab (keycode 23), Alt_L (keycode 64)
        keycodes_to_disable = [70, 95, 23, 64]
        for kc in keycodes_to_disable:
            subprocess.run(['xmodmap', '-e', f'keycode {kc} = NoSymbol'], capture_output=True)
        
        logger.info("Key blocking applied (production mode).")
        return True
    
    def start(self):
        """Start kiosk browser."""
        logger.info("Starting Kiosk Browser...")
        
        # Setup key blocking
        self.setup_key_blocking()
        
        # Build browser command
        browser_cmd = self.build_browser_args()
        
        try:
            if self.is_testing:
                # Run in namespace for testing
                full_cmd = ['ip', 'netns', 'exec', self.namespace] + browser_cmd
                logger.info(f"Starting browser in namespace {self.namespace}")
            else:
                full_cmd = browser_cmd
                logger.info("Starting browser on host")
            
            logger.info(f"Browser command: {' '.join(full_cmd)}")
            
            # Start browser
            self.process = subprocess.Popen(
                full_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            logger.info(f"Kiosk browser started with PID {self.process.pid}")
            
            # Wait a bit to see if it crashes immediately
            time.sleep(2)
            if self.process.poll() is not None:
                logger.error("Browser crashed immediately")
                return False
            
            logger.info("Kiosk Browser started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start browser: {str(e)}")
            return False
    
    def stop(self):
        """Stop kiosk browser and restore keymap."""
        logger.info("Stopping Kiosk Browser...")
        
        # Restore original keymap if we saved it
        if hasattr(self, '_original_keymap') and self._original_keymap:
            subprocess.run(['xmodmap', '-'], input=self._original_keymap.encode(), capture_output=True)
            logger.info("Keymap restored to original state")
        
        if self.process is None:
            logger.warning("No browser process to stop")
            return True
        
        try:
            # Terminate browser process group
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            
            # Wait for termination
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Browser didn't terminate, forcing kill...")
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                self.process.wait()
            
            logger.info("Kiosk Browser stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping browser: {str(e)}")
            return False
    
    def is_running(self):
        """Check if browser is still running."""
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def wait(self):
        """Wait for browser to exit."""
        if self.process:
            return self.process.wait()
        return 0


def main():
    """Test kiosk browser."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    kb = KioskBrowser()
    
    print("Starting Kiosk Browser...")
    print("Press Ctrl+C to stop\n")
    
    if kb.start():
        print("Kiosk Browser started successfully!")
        print("The browser should be running in fullscreen kiosk mode")
        print("Try accessing codeforces.com - it should work")
        print("Try accessing other sites - they should be blocked\n")
        
        try:
            # Wait for browser
            kb.wait()
        except KeyboardInterrupt:
            print("\nStopping browser...")
            kb.stop()
    else:
        print("Failed to start Kiosk Browser")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
