"""
Abstract base classes for cross-platform cursor chat monitoring
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any


class WindowElement(ABC):
    """Abstract representation of a UI window element"""
    
    def __init__(self, window_id: str, title: str):
        self.window_id = window_id
        self.title = title
    
    @abstractmethod
    def get_text_content(self, max_depth: int = 30, sidebar_depth_limit: int = 20) -> List[str]:
        """Extract all text content from this window element"""
        pass
    
    def get_title(self) -> str:
        """Get window title"""
        return self.title
    
    def get_id(self) -> str:
        """Get unique window identifier"""
        return self.window_id


class AppAccessor(ABC):
    """Abstract interface for accessing application UI elements"""
    
    def __init__(self):
        self.target_app = None
        self.target_pid = None
    
    @abstractmethod
    def check_prerequisites(self) -> bool:
        """Check if platform-specific requirements are met"""
        pass
    
    @abstractmethod
    def find_target_app(self, app_name: str = "cursor") -> bool:
        """Find and connect to target application"""
        pass
    
    @abstractmethod
    def get_windows(self) -> List[WindowElement]:
        """Get all accessible windows from target app"""
        pass
    
    def get_platform_name(self) -> str:
        """Get platform name for logging/debugging"""
        return self.__class__.__name__.replace('AppAccessor', '')


class AlertSystem(ABC):
    """Abstract interface for system notifications/alerts"""
    
    @abstractmethod
    def play_audio_alert(self, message: str, voice_config: Dict[str, Any]) -> None:
        """Play audio alert with platform-specific TTS"""
        pass
    
    @abstractmethod
    def show_notification(self, title: str, message: str) -> None:
        """Show system notification (optional, can be no-op)"""
        pass
    
    def get_platform_name(self) -> str:
        """Get platform name for logging/debugging"""
        return self.__class__.__name__.replace('AlertSystem', '')


class PlatformConfig:
    """Platform-specific configuration and capabilities"""
    
    def __init__(self):
        self.supports_accessibility = False
        self.supports_tts = False
        self.supports_notifications = False
        self.required_permissions = []
        self.optional_dependencies = []
    
    def validate_environment(self) -> Dict[str, bool]:
        """Validate that platform environment meets requirements"""
        return {
            "accessibility": self.supports_accessibility,
            "tts": self.supports_tts,
            "notifications": self.supports_notifications
        } 