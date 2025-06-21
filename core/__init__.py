"""
Core functionality for cross-platform cursor chat monitoring
"""
from .config import load_config, DEFAULT_CONFIG
from .monitor import CrossPlatformMonitor

__all__ = ['load_config', 'DEFAULT_CONFIG', 'CrossPlatformMonitor'] 