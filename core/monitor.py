"""
Cross-platform monitoring logic for cursor chat monitor
"""
import time
import logging
import sys
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from platforms import get_platform_implementations
from platforms.base import AppAccessor, AlertSystem, WindowElement
from core.config import load_config, validate_config


def get_current_platform() -> str:
    """Get current platform name"""
    if sys.platform == "win32":
        return "Windows"
    elif sys.platform == "darwin":
        return "macOS"
    elif sys.platform.startswith("linux"):
        return "Linux"
    else:
        return "Unknown"


class CrossPlatformMonitor:
    """Cross-platform monitor for cursor chat text detection"""
    
    def __init__(self, config: Dict[str, Any], interval_ms: Optional[int] = None, debug: Optional[bool] = None, daemon_mode: bool = False):
        self.config = config
        self.interval_ms = interval_ms if interval_ms is not None else config.get("DEFAULT_SCAN_INTERVAL_MS", 1500)
        self.debug = debug if debug is not None else config.get("DEFAULT_DEBUG_MODE", False)
        self.daemon_mode = daemon_mode
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.running = True  # Control flag for monitoring loop
        
        # Get platform-specific implementations
        try:
            self.app_accessor, self.alert_system = get_platform_implementations()
        except RuntimeError as e:
            print(f"❌ Platform not supported: {e}")
            sys.exit(1)
        
        # Track counts per window per text: {window_id: {text: count}}
        self.window_text_counts = {}
        self.window_generating_counts = {}
        
        # Debounce tracking: { (window_id, gen_text): last_alert_time }
        self.generating_started_last_alert = {}
        
        # Target texts from config
        self.awaiting_user_action_texts = config.get("AWAITING_USER_ACTION_TEXTS", [])
        self.generating_texts = config.get("GENERATING_TEXTS", [])
        
        # Set up logging
        log_level = logging.DEBUG if self.debug else logging.INFO
        handlers = []
        
        # In daemon mode, don't log to stdout unless debug is on
        if not daemon_mode or self.debug:
            handlers.append(logging.StreamHandler(sys.stdout))
        
        if config.get("LOG_TO_FILE", False) or daemon_mode:
            log_file = config.get("MONITOR_LOG_FILE", "cursor_resume_monitor.log")
            # If daemon mode and no explicit log file path, use home directory
            if daemon_mode and not os.path.isabs(log_file):
                log_file = os.path.expanduser(f"~/.{log_file}")
            handlers.append(logging.FileHandler(log_file))
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(message)s',
            handlers=handlers
        )
        self.logger = logging.getLogger(__name__)
    
    def check_prerequisites(self) -> bool:
        """Check if platform prerequisites are met"""
        return self.app_accessor.check_prerequisites()
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring loop gracefully"""
        self.running = False
        self.logger.info("Monitor stop requested")
    
    def count_texts_in_window(self, window: WindowElement, awaiting_texts: List[str], generating_texts: List[str]) -> tuple[Dict[str, int], Dict[str, int]]:
        """Count occurrences of both awaiting and generating texts in a window with single traversal"""
        awaiting_counts = {text: 0 for text in awaiting_texts}
        generating_counts = {text: 0 for text in generating_texts}
        traversal_time = 0.0
        element_count = 0
        
        try:
            # Start timing the window traversal
            start_time = time.time()
            
            # Get all text from the window (single traversal)
            max_depth = self.config.get("MAX_SEARCH_DEPTH", 30)
            sidebar_depth_limit = self.config.get("SIDEBAR_DEPTH_LIMIT", 20)
            all_text_elements = window.get_text_content(max_depth, sidebar_depth_limit)
            
            # End timing
            end_time = time.time()
            traversal_time = end_time - start_time
            element_count = len(all_text_elements)
            
            # Display timing information (only once per window now)
            window_title = window.get_title()
            if self.debug:
                self.logger.debug(f"Window '{window_title}' traversal: {traversal_time:.3f}s for {element_count} elements")
            else:
                # Show timing info even in non-debug mode for performance monitoring
                print(f"⏱️  Window '{window_title}': {traversal_time:.3f}s ({element_count} elements)")
            
            # Count occurrences for both text sets (case-insensitive)
            for text_element in all_text_elements:
                text_lower = text_element.lower()
                
                # Check awaiting user action texts
                for target_text in awaiting_texts:
                    if target_text.lower() in text_lower:
                        awaiting_counts[target_text] += 1
                
                # Check generating texts
                for target_text in generating_texts:
                    if target_text.lower() in text_lower:
                        generating_counts[target_text] += 1
            
        except Exception as e:
            self.logger.error(f"Error counting texts in window '{window.get_title()}': {e}")
        
        return counts

    def count_texts_in_extracted_content(self, all_text_elements: List[str], target_texts: List[str]) -> Dict[str, int]:
        """Count occurrences of target texts in already extracted text content."""
        counts = {text: 0 for text in target_texts}
        
        # Count occurrences (case-insensitive)
        for text_element in all_text_elements:
            text_lower = text_element.lower()
            for target_text in target_texts:
                if target_text.lower() in text_lower:
                    counts[target_text] += 1
        
        return counts

    def extract_text_from_window(self, window: WindowElement) -> Tuple[List[str], float, int]:
        """Extract all text content from a window with timing information."""
        traversal_time = 0.0
        element_count = 0
        
        try:
            # Start timing the window traversal
            start_time = time.time()
            
            # Get all text from the window
            max_depth = self.config.get("MAX_SEARCH_DEPTH", 30)
            sidebar_depth_limit = self.config.get("SIDEBAR_DEPTH_LIMIT", 20)
            all_text_elements = window.get_text_content(max_depth, sidebar_depth_limit)
            
            # End timing
            end_time = time.time()
            traversal_time = end_time - start_time
            element_count = len(all_text_elements)
            
            # Display timing information
            window_title = window.get_title()
            if self.debug:
                self.logger.debug(f"Window '{window_title}' traversal: {traversal_time:.3f}s for {element_count} elements")
            else:
                # Show timing info even in non-debug mode for performance monitoring
                print(f"⏱️  Window '{window_title}': {traversal_time:.3f}s ({element_count} elements)")
            
        except Exception as e:
            self.logger.error(f"Error extracting text from window '{window.get_title()}': {e}")
            all_text_elements = []
            traversal_time = 0.0
            element_count = 0
        
        return all_text_elements, traversal_time, element_count
    
    def format_window_title_for_announcement(self, window_title: str) -> str:
        """Format window title for audio announcement based on config"""
        mode = self.config.get("WINDOW_TITLE_ANNOUNCE_MODE", "last")
        replace_periods = self.config.get("REPLACE_PERIODS_IN_ANNOUNCEMENT", True)

        formatted_title = window_title

        # Split only on emdash or hyphen with spaces around them
        if " — " in window_title:
            segments = [seg.strip() for seg in window_title.split(" — ")]
        elif " - " in window_title:
            segments = [seg.strip() for seg in window_title.split(" - ")]
        else:
            segments = [window_title.strip()]

        if mode == "first":
            formatted_title = segments[0] if segments else window_title
        elif mode == "last":
            formatted_title = segments[-1] if segments else window_title
        elif mode == "next-to-last":
            if len(segments) >= 2:
                formatted_title = segments[-2]
            elif len(segments) == 1:
                formatted_title = segments[0]
            else:
                formatted_title = window_title
        # "full" mode uses the complete title as-is

        if replace_periods:
            formatted_title = formatted_title.replace(".", " ")

        return formatted_title
    
    def play_alert(self, window_title: str, old_count: int, new_count: int, target_text: Optional[str] = None) -> None:
        """Play audio alert for text count change"""
        announce_title = self.format_window_title_for_announcement(window_title)
        
        if target_text:
            message = f"{target_text} in {announce_title}"
        else:
            message = f"Text change detected in {announce_title}"
        
        voice_config = {
            "VOICE_NAME": self.config.get("VOICE_NAME", "Daniel"),
            "SPEECH_RATE": self.config.get("SPEECH_RATE", 175)
        }
        
        self.alert_system.play_audio_alert(message, voice_config)
    
    def play_generating_complete_alert(self, window_title: str, gen_text: str) -> None:
        """Play audio alert for generation completion"""
        announce_title = self.format_window_title_for_announcement(window_title)
        message = f"{gen_text} complete in {announce_title}"
        
        voice_config = {
            "VOICE_NAME": self.config.get("VOICE_NAME", "Daniel"),
            "SPEECH_RATE": self.config.get("SPEECH_RATE", 175)
        }
        
        self.alert_system.play_audio_alert(message, voice_config)
    
    def play_generating_started_alert(self, window_title: str, gen_text: str) -> None:
        """Play audio alert for generation start"""
        announce_title = self.format_window_title_for_announcement(window_title)
        message = f"{gen_text} started on {announce_title}"
        
        voice_config = {
            "VOICE_NAME": self.config.get("VOICE_NAME", "Daniel"),
            "SPEECH_RATE": self.config.get("SPEECH_RATE", 175)
        }
        
        self.alert_system.play_audio_alert(message, voice_config)
    
    def run_monitoring(self) -> None:
        """Run the main cross-platform monitoring loop"""
        platform_name = get_current_platform()
        
        # Only print startup info if not in daemon mode
        if not self.daemon_mode:
            print(f"🔍 Starting Cursor Multi-Text Monitor")
            print(f"🖥️  Platform: {platform_name}")
            print(f"📊 Session ID: {self.session_id}")
            print(f"🎯 Target texts: {self.awaiting_user_action_texts}")
            print(f"🎯 Generating texts: {self.generating_texts}")
            print(f"⏱️  Scan interval: {self.interval_ms} ms")
            print(f"🔊 Audio alerts: {self.alert_system.get_platform_name()}")
            
            if self.debug:
                print(f"🐛 Debug mode: ON (will show extracted text)")
            
            print(f"🚀 Press Ctrl+C to stop")
            print("=" * 60)
        
        # Log startup in daemon mode
        self.logger.info(f"Starting Cursor Multi-Text Monitor (Platform: {platform_name}, Session: {self.session_id})")
        
        scan_count = 0
        
        try:
            while self.running:
                scan_count += 1
                
                # Find target app
                if not self.app_accessor.find_target_app("cursor"):
                    self.logger.debug("Cursor not found, waiting...")
                    time.sleep(self.interval_ms / 1000.0)
                    continue
                
                # Get windows
                windows = self.app_accessor.get_windows()
                
                if not windows:
                    self.logger.debug("No windows found")
                    time.sleep(self.interval_ms / 1000.0)
                    continue
                
                # Process each window
                current_scan_counts = {}
                current_generating_counts = {}
                alerts_triggered = 0
                
                # Start timing the complete scan
                scan_start_time = time.time()
                
                for window in windows:
                    window_id = window.get_id()
                    
                    # Extract text content once per window (optimization)
                    all_text_elements, traversal_time, element_count = self.extract_text_from_window(window)
                    
                    # Count both types of texts in the extracted content
                    current_counts = self.count_texts_in_extracted_content(all_text_elements, self.awaiting_user_action_texts)
                    gen_counts = self.count_texts_in_extracted_content(all_text_elements, self.generating_texts)
                    
                    current_scan_counts[window_id] = current_counts
                    current_generating_counts[window_id] = gen_counts
                    
                    # Handle generating text special logic
                    prev_gen_counts = self.window_generating_counts.get(window_id, {})
                    for gen_text, new_count in gen_counts.items():
                        prev_count = prev_gen_counts.get(gen_text, None)
                        if prev_count is not None:
                            # Generation completed (count went from >0 to 0)
                            if prev_count > 0 and new_count == 0:
                                self.play_generating_complete_alert(window.get_title(), gen_text)
                                print(f"🚨 ALERT: '{gen_text}' complete!")
                                print(f"   Window: {window.get_title()}")
                                print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                                print("-" * 40)
                                alerts_triggered += 1
                            
                            # Generation started (count went from 0 to >0)
                            elif (self.config.get("ANNOUNCE_GENERATING_STARTED", True) and 
                                  prev_count == 0 and new_count > 0):
                                
                                # Debounce logic
                                debounce_key = (window_id, gen_text)
                                now = time.time()
                                last_alert = self.generating_started_last_alert.get(debounce_key, 0)
                                debounce_seconds = self.config.get("GENERATING_STARTED_DEBOUNCE_SECONDS", 10)
                                
                                if debounce_seconds == 0 or (now - last_alert) >= debounce_seconds:
                                    self.generating_started_last_alert[debounce_key] = now
                                    self.play_generating_started_alert(window.get_title(), gen_text)
                                    print(f"🚨 ALERT: '{gen_text}' started!")
                                    print(f"   Window: {window.get_title()}")
                                    print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                                    print("-" * 40)
                                    alerts_triggered += 1
                    
                    # Handle awaiting user action texts
                    if window_id in self.window_text_counts:
                        old_counts = self.window_text_counts[window_id]
                        for text, old_count in old_counts.items():
                            if text in current_counts and current_counts[text] > old_count:
                                # Count increased - trigger alert!
                                self.play_alert(window.get_title(), old_count, current_counts[text], text)
                                alerts_triggered += 1
                                
                                print(f"🚨 ALERT: '{text}' count increased!")
                                print(f"   Window: {window.get_title()}")
                                print(f"   Count: {old_count} → {current_counts[text]}")
                                print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                                print("-" * 40)
                    else:
                        # First time seeing this window - alert if count > 0
                        for text, count in current_counts.items():
                            if count > 0:
                                self.play_alert(window.get_title(), 0, count, text)
                                alerts_triggered += 1
                                
                                print(f"🚨 ALERT: '{text}' found on startup!")
                                print(f"   Window: {window.get_title()}")
                                print(f"   Count: {count}")
                                print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                                print("-" * 40)
                    
                    # Log current status
                    self.logger.debug(f"Window '{window.get_title()}': {current_counts}, generating: {gen_counts}")
                
                # Update stored counts
                self.window_text_counts.update(current_scan_counts)
                self.window_generating_counts.update(current_generating_counts)
                
                # End timing the complete scan
                scan_end_time = time.time()
                scan_duration = scan_end_time - scan_start_time
                print(f"⏱️  Total scan duration: {scan_duration:.3f}s for {len(windows)} windows")
                
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