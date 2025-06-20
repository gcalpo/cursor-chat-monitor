#!/usr/bin/env python3
"""
Cursor Multi-Text Monitor
Monitors all Cursor IDE windows for multiple target texts
and plays audio alert when count increases in any window.
Usage: python3 cursor_chat_monitor.py [--interval=5] [--config=config.json]
       
Config file priority:
1. --config argument (if provided)
2. ~/.cursor_chat_monitor (if exists)
3. Default configuration
"""

import sys
import time
import argparse
import subprocess
import json
import os
from typing import Dict, List
import logging
from datetime import datetime
import re

# ============================================================================
# DEFAULT CONFIGURATION SETTINGS
# ============================================================================

# Default configuration - can be overridden by external config file
DEFAULT_CONFIG = {
    # Texts to monitor for (case-insensitive)
    "AWAITING_USER_ACTION_TEXTS": [
        "resume the conversation",
        "Connection failed",
        "trouble connecting to the model provider",
        "File is being edited by another chat",
    ],
    
    # Texts to monitor for completion (case-insensitive, special handling: alert when count goes from >0 to 0)
    "GENERATING_TEXTS": [
        "generating"
    ],
    
    # Default scan interval in milliseconds
    "DEFAULT_SCAN_INTERVAL_MS": 1500,
    
    # Maximum depth to search in accessibility tree
    "MAX_SEARCH_DEPTH": 30,
    
    # Voice alert settings
    "VOICE_NAME": "Daniel",
    "SPEECH_RATE": 175,        # Words per minute (100-300 recommended)
    
    # Window title announcement mode: 'full', 'first', or 'last'
    "WINDOW_TITLE_ANNOUNCE_MODE": "last",  # Options: 'full', 'first', 'last'
    
    # Replace periods with spaces in announcement (default: True)
    "REPLACE_PERIODS_IN_ANNOUNCEMENT": True,
    
    # Announce when generating starts (count goes from 0 to >0)
    "ANNOUNCE_GENERATING_STARTED": True,
    
    # Debounce time for 'generating started' alert (seconds). 0 disables debouncing.
    "GENERATING_STARTED_DEBOUNCE_SECONDS": 10,
    
    # Log file names
    "MONITOR_LOG_FILE": "cursor_resume_monitor.log",
    
    # Enable logging to file (default: False)
    "LOG_TO_FILE": False,
    
    # Debug mode default
    "DEFAULT_DEBUG_MODE": False
}

def load_config(config_file_path: str = None) -> dict:
    """Load configuration from file if provided, otherwise look for ~/.cursor_chat_monitor, or use defaults"""
    config = DEFAULT_CONFIG.copy()
    
    # If no config file specified, look for default config in user's home directory
    if not config_file_path:
        default_config_path = os.path.expanduser("~/.cursor_chat_monitor")
        if os.path.exists(default_config_path):
            config_file_path = default_config_path
            print(f"📁 Found default config file: {config_file_path}")
    
    if config_file_path:
        if not os.path.exists(config_file_path):
            print(f"⚠️  Config file not found: {config_file_path}")
            print("📝 Using default configuration")
            return config
        
        try:
            with open(config_file_path, 'r') as f:
                external_config = json.load(f)
            
            # Merge external config with defaults
            config.update(external_config)
            print(f"✅ Configuration loaded from: {config_file_path}")
            
            # Validate critical configuration values
            if not isinstance(config.get("AWAITING_USER_ACTION_TEXTS"), list):
                print("⚠️  AWAITING_USER_ACTION_TEXTS must be a list, using default")
                config["AWAITING_USER_ACTION_TEXTS"] = DEFAULT_CONFIG["AWAITING_USER_ACTION_TEXTS"]
            
            if not isinstance(config.get("GENERATING_TEXTS"), list):
                print("⚠️  GENERATING_TEXTS must be a list, using default")
                config["GENERATING_TEXTS"] = DEFAULT_CONFIG["GENERATING_TEXTS"]
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in config file: {e}")
            print("📝 Using default configuration")
        except Exception as e:
            print(f"❌ Error loading config file: {e}")
            print("📝 Using default configuration")
    else:
        print("📝 No config file found, using default configuration")
    
    return config

# Global configuration - will be set by load_config()
CONFIG = {}

# ============================================================================
# END CONFIGURATION
# ============================================================================

# macOS-specific imports (PyObjC)
try:
    from AppKit import NSWorkspace
    from ApplicationServices import (
        AXUIElementCreateApplication, 
        AXUIElementCopyAttributeValue,
        kAXErrorSuccess,
        kAXTitleAttribute,
        kAXValueAttribute,
        kAXRoleAttribute,
        kAXChildrenAttribute,
        kAXDescriptionAttribute,
        AXIsProcessTrusted
    )
    ACCESSIBILITY_AVAILABLE = True
except ImportError as e:
    print(f"❌ Accessibility APIs not available: {e}")
    ACCESSIBILITY_AVAILABLE = False

class CursorMultiTextMonitor:
    """Monitor for multiple target texts in Cursor IDE windows"""
    
    def __init__(self, interval_ms: int = None, debug: bool = None):
        # Use config values with fallbacks
        self.interval_ms = interval_ms if interval_ms is not None else CONFIG.get("DEFAULT_SCAN_INTERVAL_MS", 1500)
        self.debug = debug if debug is not None else CONFIG.get("DEFAULT_DEBUG_MODE", False)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Track counts per window per text: {window_id: {text: count}}
        self.window_text_counts = {}  
        self.cursor_app = None
        self.cursor_pid = None
        self.awaiting_user_action_texts = CONFIG.get("AWAITING_USER_ACTION_TEXTS", DEFAULT_CONFIG["AWAITING_USER_ACTION_TEXTS"])
        self.generating_texts = CONFIG.get("GENERATING_TEXTS", DEFAULT_CONFIG["GENERATING_TEXTS"])
        # Track generating-like counts per window: {window_id: {text: count}}
        self.window_generating_counts = {}  # {window_id: {text: count}}
        # Debounce: { (window_id, gen_text): last_alert_time }
        self.generating_started_last_alert = {}
        
        # Set up logging
        log_level = logging.DEBUG if self.debug else logging.INFO
        handlers = [logging.StreamHandler(sys.stdout)]
        if CONFIG.get("LOG_TO_FILE", False):
            log_file = CONFIG.get("MONITOR_LOG_FILE", "cursor_resume_monitor.log")
            handlers.insert(0, logging.FileHandler(log_file))
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(message)s',
            handlers=handlers
        )
        self.logger = logging.getLogger(__name__)
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        if not ACCESSIBILITY_AVAILABLE:
            print("❌ Accessibility APIs not available")
            return False
        
        if sys.platform != 'darwin':
            print("❌ This script is designed for macOS only")
            return False
        
        if not AXIsProcessTrusted():
            print("❌ No accessibility permissions granted")
            print("💡 Go to System Preferences > Security & Privacy > Accessibility")
            print("   and add Terminal (or your Python interpreter) to the list")
            return False
        
        return True
    
    def find_cursor_app(self) -> bool:
        """Find and connect to Cursor application"""
        try:
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()
            
            # Target main Cursor process (ignore helpers)
            for app in running_apps:
                if app.localizedName() == 'Cursor' and 'helper' not in app.localizedName().lower():
                    self.cursor_pid = app.processIdentifier()
                    self.cursor_app = AXUIElementCreateApplication(self.cursor_pid)
                    self.logger.debug(f"Connected to main Cursor process (PID: {self.cursor_pid})")
                    return True
            
            self.logger.debug("Main Cursor process not found")
            return False
            
        except Exception as e:
            self.logger.error(f"Error finding Cursor: {e}")
            return False
    
    def get_windows(self) -> List[Dict]:
        """Get all accessible Cursor windows"""
        windows = []
        
        try:
            error_code, ax_windows = AXUIElementCopyAttributeValue(self.cursor_app, "AXWindows", None)
            
            if error_code == kAXErrorSuccess and ax_windows:
                self.logger.debug(f"Found {len(ax_windows)} windows")
                
                for i, ax_window in enumerate(ax_windows):
                    # Get window title
                    error_code, title = AXUIElementCopyAttributeValue(ax_window, kAXTitleAttribute, None)
                    window_title = title if error_code == kAXErrorSuccess else f"Untitled Window {i+1}"
                    
                    # Create unique window ID
                    window_id = f"window_{i}_{window_title}"
                    
                    windows.append({
                        'id': window_id,
                        'title': window_title,
                        'element': ax_window,
                        'index': i
                    })
                    
                    self.logger.debug(f"  Window {i+1}: {window_title}")
            else:
                self.logger.debug(f"No windows found (error: {error_code})")
            
        except Exception as e:
            self.logger.error(f"Error getting windows: {e}")
        
        return windows
    
    def count_awaiting_user_action_texts_in_window(self, window: Dict) -> Dict[str, int]:
        """Count occurrences of all target texts in a window"""
        text_counts = {text: 0 for text in self.awaiting_user_action_texts}
        
        try:
            elements = self._get_all_text_elements(window['element'])
            
            # Debug: Show extracted text for troubleshooting
            if self.debug and elements:
                print(f"\n🔍 DEBUG - Window: {window['title']}")
                print(f"   Extracted {len(elements)} text elements:")
                for i, text in enumerate(elements[:10]):  # Show first 10
                    if text and isinstance(text, str) and len(text.strip()) > 0:
                        preview = text.strip()[:100].replace('\n', '\\n')
                        print(f"   [{i+1}] {preview}")
                        
                        # Highlight if contains any target text
                        for target_text in self.awaiting_user_action_texts:
                            if target_text.lower() in text.lower():
                                print(f"       ✅ CONTAINS TARGET TEXT: '{target_text}'")
                
                if len(elements) > 10:
                    print(f"   ... and {len(elements) - 10} more elements")
                print()
            
            # Count all target text occurrences
            for text in elements:
                if text and isinstance(text, str):
                    for target_text in self.awaiting_user_action_texts:
                        # Case-insensitive search
                        count = text.lower().count(target_text.lower())
                        text_counts[target_text] += count
                        
                        # Debug: Show matches
                        if count > 0 and self.debug:
                            print(f"🎯 MATCH FOUND in '{window['title']}': {count} occurrences of '{target_text}'")
                            print(f"   Text snippet: {text[:200]}...")
            
        except Exception as e:
            self.logger.debug(f"Error scanning window {window['title']}: {e}")
        
        return text_counts
    
    def _get_all_text_elements(self, element, max_depth: int = None, current_depth: int = 0) -> List[str]:
        """Recursively extract all text content from UI elements"""
        if max_depth is None:
            max_depth = CONFIG.get("MAX_SEARCH_DEPTH", 30)
            
        texts = []
        
        if current_depth > max_depth:
            return texts
        
        try:
            # Get text from current element - try all possible attributes
            text_attrs = [kAXValueAttribute, kAXTitleAttribute, kAXDescriptionAttribute]
            
            # Also try some additional attributes that might contain text
            try:
                # Get role first to understand element type
                error_code, role = AXUIElementCopyAttributeValue(element, kAXRoleAttribute, None)
                element_role = role if error_code == kAXErrorSuccess else "Unknown"
                
                for attr in text_attrs:
                    error_code, value = AXUIElementCopyAttributeValue(element, attr, None)
                    if error_code == kAXErrorSuccess and value:
                        if isinstance(value, str) and len(value.strip()) > 0:
                            texts.append(value)
                        # Sometimes text might be in other formats, try to convert
                        elif hasattr(value, '__str__'):
                            str_value = str(value)
                            if len(str_value.strip()) > 0:
                                texts.append(str_value)
                
                # For web content or complex elements, try additional approaches
                if element_role in ['AXWebArea', 'AXGroup', 'AXScrollArea']:
                    # Try to get more attributes that might contain text
                    try:
                        # Try AXHelp attribute
                        error_code, help_text = AXUIElementCopyAttributeValue(element, "AXHelp", None)
                        if error_code == kAXErrorSuccess and help_text and isinstance(help_text, str):
                            texts.append(help_text)
                    except:
                        pass
                        
            except Exception as e:
                if self.debug:
                    self.logger.debug(f"Error getting element attributes at depth {current_depth}: {e}")
            
            # Get children and recurse
            error_code, children = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute, None)
            if error_code == kAXErrorSuccess and children:
                for child in children:
                    child_texts = self._get_all_text_elements(child, max_depth, current_depth + 1)
                    texts.extend(child_texts)
            
        except Exception as e:
            if self.debug:
                self.logger.debug(f"Error extracting text at depth {current_depth}: {e}")
        
        return texts
    
    def count_generating_texts_in_window(self, window: Dict) -> dict:
        """Count occurrences of all generating-like texts in a window (case-insensitive)"""
        counts = {text: 0 for text in self.generating_texts}
        try:
            elements = self._get_all_text_elements(window['element'])
            for text_content in elements:
                if text_content and isinstance(text_content, str):
                    for gen_text in self.generating_texts:
                        counts[gen_text] += text_content.lower().count(gen_text.lower())
        except Exception as e:
            self.logger.debug(f"Error scanning window {window['title']} for generating texts: {e}")
        return counts
    
    def _format_window_title_for_announcement(self, window_title: str) -> str:
        """Format the window title according to the announce mode setting and replace periods if configured. Now splits on em dash only."""
        mode = CONFIG.get("WINDOW_TITLE_ANNOUNCE_MODE", "last").lower()
        # Split on em dash only
        hyphen_split = re.split(r"\s*—\s*", window_title)
        if mode == 'first':
            result = hyphen_split[0].strip() if hyphen_split else window_title
        elif mode == 'last':
            result = hyphen_split[-1].strip() if hyphen_split else window_title
        else:
            result = window_title
        if CONFIG.get("REPLACE_PERIODS_IN_ANNOUNCEMENT", True):
            result = result.replace('.', ' ')
        return result
    
    def play_alert(self, window_title: str, old_count: int, new_count: int, target_text: str = None) -> None:
        """Play audio alert using macOS say command"""
        try:
            announce_title = self._format_window_title_for_announcement(window_title)
            if target_text:
                message = f"{target_text} in {announce_title}"
            else:
                message = f"Text change detected in {announce_title}"
            subprocess.run([
                'say', 
                '-v', CONFIG.get("VOICE_NAME", "Daniel"),     # Voice name from config
                '-r', str(CONFIG.get("SPEECH_RATE", 175)),  # Speech rate from config
                message
            ], check=False)
            self.logger.info(f"🔊 Audio alert played: {message}")
        except Exception as e:
            self.logger.error(f"Error playing audio alert: {e}")
    
    def play_generating_complete_alert(self, window_title: str, gen_text: str) -> None:
        """Play audio alert for '[gen_text] complete' using macOS say command"""
        try:
            announce_title = self._format_window_title_for_announcement(window_title)
            message = f"{gen_text} complete in {announce_title}"
            subprocess.run([
                'say',
                '-v', CONFIG.get("VOICE_NAME", "Daniel"),
                '-r', str(CONFIG.get("SPEECH_RATE", 175)),
                message
            ], check=False)
            self.logger.info(f"🔊 Audio alert played: {message}")
        except Exception as e:
            self.logger.error(f"Error playing '{gen_text} complete' alert: {e}")
    
    def play_generating_started_alert(self, window_title: str, gen_text: str) -> None:
        """Play audio alert for '[gen_text] started on ...' using macOS say command"""
        try:
            announce_title = self._format_window_title_for_announcement(window_title)
            message = f"{gen_text} started on {announce_title}"
            subprocess.run([
                'say',
                '-v', CONFIG.get("VOICE_NAME", "Daniel"),
                '-r', str(CONFIG.get("SPEECH_RATE", 175)),
                message
            ], check=False)
            self.logger.info(f"🔊 Audio alert played: {message}")
        except Exception as e:
            self.logger.error(f"Error playing '{gen_text} started' alert: {e}")
    
    def run_monitoring(self) -> None:
        """Run the main monitoring loop"""
        print(f"🔍 Starting Cursor Multi-Text Monitor")
        print(f"📊 Session ID: {self.session_id}")
        print(f"🎯 Target texts: {self.awaiting_user_action_texts}")
        print(f"🎯 Generating texts: {self.generating_texts}")
        print(f"⏱️  Scan interval: {self.interval_ms} ms")
        print(f"🔊 Audio alerts: macOS 'say' command")
        if self.debug:
            print(f"🐛 Debug mode: ON (will show extracted text)")
        print(f"🚀 Press Ctrl+C to stop")
        print("=" * 60)
        
        scan_count = 0
        
        try:
            while True:
                scan_count += 1
                
                # Find Cursor app
                if not self.find_cursor_app():
                    self.logger.debug("Cursor not found, waiting...")
                    time.sleep(self.interval_ms / 1000.0)
                    continue
                
                # Get windows
                windows = self.get_windows()
                
                if not windows:
                    self.logger.debug("No windows found")
                    time.sleep(self.interval_ms / 1000.0)
                    continue
                
                # Check each window for target texts
                current_scan_counts = {}
                alerts_triggered = 0
                # Track current generating-like counts
                current_generating_counts = {}
                
                for window in windows:
                    window_id = window['id']
                    current_counts = self.count_awaiting_user_action_texts_in_window(window)
                    current_scan_counts[window_id] = current_counts
                    
                    # --- GENERATING SPECIAL HANDLING ---
                    gen_counts = self.count_generating_texts_in_window(window)
                    current_generating_counts[window_id] = gen_counts
                    prev_gen_counts = self.window_generating_counts.get(window_id, {})
                    for gen_text, new_count in gen_counts.items():
                        prev_count = prev_gen_counts.get(gen_text, None)
                        if prev_count is not None:
                            if prev_count > 0 and new_count == 0:
                                # Play special alert for completion
                                self.play_generating_complete_alert(window['title'], gen_text)
                                print(f"🚨 ALERT: '{gen_text}' complete!")
                                print(f"   Window: {window['title']}")
                                print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                                print("-" * 40)
                                alerts_triggered += 1
                            elif CONFIG.get("ANNOUNCE_GENERATING_STARTED", True) and prev_count == 0 and new_count > 0:
                                if self.debug:
                                    print(f"[DEBUG] Generating started check: window_id={window_id}, gen_text='{gen_text}', prev_count={prev_count}, new_count={new_count}")
                                    self.logger.debug(f"[DEBUG] Generating started check: window_id={window_id}, gen_text='{gen_text}', prev_count={prev_count}, new_count={new_count}")
                                # Debounce logic
                                debounce_key = (window_id, gen_text)
                                now = time.time()
                                last_alert = self.generating_started_last_alert.get(debounce_key, 0)
                                debounce_seconds = CONFIG.get("GENERATING_STARTED_DEBOUNCE_SECONDS", 10)
                                if debounce_seconds > 0 and (now - last_alert) < debounce_seconds:
                                    if self.debug:
                                        print(f"[DEBUG] Debounced 'generating started' for {debounce_key}: last_alert={last_alert}, now={now}, debounce_seconds={debounce_seconds}")
                                        self.logger.debug(f"[DEBUG] Debounced 'generating started' for {debounce_key}: last_alert={last_alert}, now={now}, debounce_seconds={debounce_seconds}")
                                    continue
                                self.generating_started_last_alert[debounce_key] = now
                                # Play special alert for started
                                self.play_generating_started_alert(window['title'], gen_text)
                                print(f"🚨 ALERT: '{gen_text}' started!")
                                print(f"   Window: {window['title']}")
                                print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                                print("-" * 40)
                                alerts_triggered += 1
                    # --- END GENERATING SPECIAL HANDLING ---
                    
                    # Check if count increased OR if this is first time seeing window with count > 0
                    if window_id in self.window_text_counts:
                        old_counts = self.window_text_counts[window_id]
                        for text, old_count in old_counts.items():
                            if text in current_counts and current_counts[text] > old_count:
                                # Count increased - trigger alert!
                                self.play_alert(window['title'], old_count, current_counts[text], text)
                                alerts_triggered += 1
                                
                                print(f"🚨 ALERT: '{text}' count increased!")
                                print(f"   Window: {window['title']}")
                                print(f"   Count: {old_count} → {current_counts[text]}")
                                print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                                print("-" * 40)
                    else:
                        # First time seeing this window - alert if count > 0
                        for text, count in current_counts.items():
                            if count > 0:
                                self.play_alert(window['title'], 0, count, text)
                                alerts_triggered += 1
                                
                                print(f"🚨 ALERT: '{text}' found on startup!")
                                print(f"   Window: {window['title']}")
                                print(f"   Count: {count}")
                                print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                                print("-" * 40)
                    
                    # Log current status
                    self.logger.debug(f"Window '{window['title']}': {current_counts}, generating: {gen_counts}")
                
                # Update stored counts
                self.window_text_counts.update(current_scan_counts)
                self.window_generating_counts.update(current_generating_counts)
                
                if alerts_triggered > 0:
                    print(f"🔔 {alerts_triggered} alerts triggered this scan")
                
                time.sleep(self.interval_ms / 1000.0)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Monitoring stopped by user")
            print(f"📊 Total scans: {scan_count}")
            
            # Final summary
            if self.window_text_counts:
                print(f"📈 Final counts by window:")
                for window_id, counts in self.window_text_counts.items():
                    window_title = window_id.split('_', 2)[-1] if '_' in window_id else window_id
                    print(f"   • {window_title}:")
                    for text, count in counts.items():
                        print(f"     • {text}: {count}")

def main():
    parser = argparse.ArgumentParser(description="Monitor Cursor IDE for multiple target texts")
    parser.add_argument("--interval-ms", type=int, help=f"Scan interval in milliseconds (default: from config or {DEFAULT_CONFIG['DEFAULT_SCAN_INTERVAL_MS']})")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode to show extracted text")
    parser.add_argument("--config", type=str, help="Path to JSON configuration file (default: looks for ~/.cursor_chat_monitor)")
    
    args = parser.parse_args()
    
    # Load configuration
    global CONFIG
    CONFIG = load_config(args.config)
    
    monitor = CursorMultiTextMonitor(interval_ms=args.interval_ms, debug=args.debug)
    
    if not monitor.check_prerequisites():
        return 1
    
    monitor.run_monitoring()
    return 0

if __name__ == "__main__":
    sys.exit(main()) 