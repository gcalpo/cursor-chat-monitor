#!/usr/bin/env python3
"""
Universal build script for cursor-chat-monitor

Detects the current platform and runs the appropriate platform-specific build script.
"""

import os
import sys
import subprocess
from pathlib import Path

def get_platform_info():
    """Get detailed platform information"""
    platform = sys.platform
    
    if platform == 'darwin':
        return 'macOS', 'build_macos.py'
    elif platform == 'win32':
        return 'Windows', 'build_windows.py'
    elif platform.startswith('linux'):
        return 'Linux', 'build_linux.py'
    else:
        return f'Unknown ({platform})', None

def check_build_script_exists(script_path):
    """Check if platform-specific build script exists"""
    return Path(script_path).exists()

def run_platform_build(script_path):
    """Run the platform-specific build script"""
    try:
        result = subprocess.run([sys.executable, script_path], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with exit code: {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Build script not found: {script_path}")
        return False

def show_platform_help():
    """Show help for manual platform-specific builds"""
    print("🛠️  Manual build options:")
    print("")
    print("macOS:")
    print("   python3 build_macos.py")
    print("")
    print("Windows:")
    print("   python build_windows.py")
    print("")
    print("Linux:")
    print("   python3 build_linux.py")
    print("")
    
def main():
    """Main build dispatcher"""
    print("🏗️  Universal cursor-chat-monitor build script")
    print("=" * 60)
    
    # Get platform information
    platform_name, build_script = get_platform_info()
    print(f"🔍 Detected platform: {platform_name}")
    
    if build_script is None:
        print(f"❌ Unsupported platform: {platform_name}")
        print("")
        print("Supported platforms:")
        print("  - macOS (darwin)")
        print("  - Windows (win32)")
        print("  - Linux (linux)")
        show_platform_help()
        sys.exit(1)
    
    # Check if platform-specific build script exists
    if not check_build_script_exists(build_script):
        print(f"❌ Platform build script not found: {build_script}")
        print("")
        print("Please ensure all platform build scripts are present:")
        print("  - build_macos.py")
        print("  - build_windows.py") 
        print("  - build_linux.py")
        sys.exit(1)
    
    print(f"🚀 Running platform-specific build: {build_script}")
    print("-" * 60)
    
    # Run platform-specific build
    success = run_platform_build(build_script)
    
    print("-" * 60)
    
    if success:
        print("🎉 Build completed successfully!")
        print("")
        print("📁 Check the ./dist/ directory for your platform-specific distribution")
        print("📖 See the README.md in ./dist/ for installation instructions")
    else:
        print("❌ Build failed!")
        print("")
        print("💡 Try running the platform-specific build script directly:")
        print(f"   python3 {build_script}")
        sys.exit(1)

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            print("Universal cursor-chat-monitor build script")
            print("")
            print("Usage:")
            print("  python3 build.py           # Auto-detect platform and build")
            print("  python3 build.py --help    # Show this help")
            print("")
            show_platform_help()
            sys.exit(0)
        elif sys.argv[1] == '--platform':
            platform_name, _ = get_platform_info()
            print(platform_name)
            sys.exit(0)
    
    main() 