#!/usr/bin/env python3
"""
Debug script for voice functions
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting debug...")
sys.stdout.flush()

try:
    from core.config import show_platform_voice_info, get_platform_name, get_platform_voice_config
    
    print("Testing voice functions...")
    sys.stdout.flush()
    
    platform = get_platform_name()
    print(f"Platform: {platform}")
    sys.stdout.flush()
    
    config = get_platform_voice_config()
    print(f"Config: {config}")
    sys.stdout.flush()
    
    print("\nCalling show_platform_voice_info():")
    sys.stdout.flush()
    
    result = show_platform_voice_info()
    print(f"Function returned: {result}")
    sys.stdout.flush()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.stdout.flush() 