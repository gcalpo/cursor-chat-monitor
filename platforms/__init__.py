"""
Platform detection and factory for cross-platform cursor chat monitoring
"""
import sys
from typing import Tuple
from .base import AppAccessor, AlertSystem


def get_platform_implementations() -> Tuple[AppAccessor, AlertSystem]:
    """Factory function to get platform-specific implementations"""
    
    if sys.platform == 'darwin':
        from .macos import MacOSAppAccessor, MacOSAlertSystem
        return MacOSAppAccessor(), MacOSAlertSystem()
    
    elif sys.platform == 'win32':
        from .windows import WindowsAppAccessor, WindowsAlertSystem
        return WindowsAppAccessor(), WindowsAlertSystem()
    
    elif sys.platform.startswith('linux'):
        from .linux import LinuxAppAccessor, LinuxAlertSystem
        return LinuxAppAccessor(), LinuxAlertSystem()
    
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")


def get_supported_platforms():
    """Get list of supported platforms"""
    return ['darwin', 'win32', 'linux']


def get_current_platform():
    """Get current platform identifier"""
    if sys.platform == 'darwin':
        return 'macOS'
    elif sys.platform == 'win32':
        return 'Windows'
    elif sys.platform.startswith('linux'):
        return 'Linux'
    else:
        return f'Unknown ({sys.platform})' 