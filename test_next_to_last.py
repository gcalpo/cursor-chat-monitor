#!/usr/bin/env python3
"""Test script for the new 'next to last' window title announcement mode"""

from core.config import get_default_config
from core.monitor import CrossPlatformMonitor

def test_config():
    """Test that the configuration is set correctly for Windows"""
    config = get_default_config()
    print(f"Window title announce mode: {config.get('WINDOW_TITLE_ANNOUNCE_MODE')}")
    print(f"Platform voice: {config.get('PLATFORM_VOICE_CONFIG', {}).get('default_voice', 'unknown')}")

def test_formatting():
    """Test the window title formatting with different modes"""
    config = get_default_config()
    monitor = CrossPlatformMonitor(config)
    
    test_titles = [
        "main.py — Cursor",
        "app.js — MyProject — Cursor", 
        "index.html",
        "README.md — Documentation — Cursor"
    ]
    
    print("\nTesting window title formatting:")
    print("-" * 50)
    
    for title in test_titles:
        formatted = monitor.format_window_title_for_announcement(title)
        print(f"Original: {title}")
        print(f"Formatted: {formatted}")
        print()

def test_all_modes():
    """Test all announcement modes"""
    config = get_default_config()
    monitor = CrossPlatformMonitor(config)
    
    test_title = "main.py — MyProject — Cursor"
    
    print("\nTesting all announcement modes:")
    print("-" * 50)
    
    modes = ["full", "first", "last", "next to last"]
    
    for mode in modes:
        config["WINDOW_TITLE_ANNOUNCE_MODE"] = mode
        formatted = monitor.format_window_title_for_announcement(test_title)
        print(f"{mode:12}: {formatted}")

if __name__ == "__main__":
    test_config()
    test_formatting()
    test_all_modes() 