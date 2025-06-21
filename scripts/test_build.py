#!/usr/bin/env python3
"""
Test script to verify cursor-chat-monitor functionality before building standalone version
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import cursor_chat_monitor
        print("✅ Main module imports successfully")
    except ImportError as e:
        print(f"❌ Main module import failed: {e}")
        return False
    
    try:
        from core.config import load_config, DEFAULT_CONFIG, validate_config
        print("✅ Config module imports successfully")
    except ImportError as e:
        print(f"❌ Config module import failed: {e}")
        return False
    
    try:
        from core.monitor import CrossPlatformMonitor
        print("✅ Monitor module imports successfully")
    except ImportError as e:
        print(f"❌ Monitor module import failed: {e}")
        return False
    
    try:
        from platforms import get_current_platform, get_platform_implementations
        print(f"✅ Platform module imports successfully (Platform: {get_current_platform()})")
    except ImportError as e:
        print(f"❌ Platform module import failed: {e}")
        return False
    
    return True

def test_platform_support():
    """Test platform-specific implementations"""
    print("\n🖥️  Testing platform support...")
    
    try:
        from platforms import get_platform_implementations, get_current_platform
        
        platform = get_current_platform()
        print(f"📱 Current platform: {platform}")
        
        app_accessor, alert_system = get_platform_implementations()
        print(f"✅ App accessor: {app_accessor.get_platform_name()}")
        print(f"✅ Alert system: {alert_system.get_platform_name()}")
        
        return True
    except Exception as e:
        print(f"❌ Platform support test failed: {e}")
        return False

def test_config_loading():
    """Test configuration loading"""
    print("\n⚙️  Testing configuration...")
    
    try:
        from core.config import load_config, validate_config
        
        # Test default config
        config = load_config(None)
        print(f"✅ Default config loaded: {len(config)} settings")
        
        if validate_config(config):
            print("✅ Config validation passed")
        else:
            print("❌ Config validation failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_monitor_creation():
    """Test monitor creation without running it"""
    print("\n🔍 Testing monitor creation...")
    
    try:
        from core.config import load_config
        from core.monitor import CrossPlatformMonitor
        
        config = load_config(None)
        monitor = CrossPlatformMonitor(
            config=config,
            interval_ms=1000,
            debug=True,
            daemon_mode=False
        )
        
        print("✅ Monitor created successfully")
        print(f"📊 Session ID: {monitor.session_id}")
        print(f"⏱️  Interval: {monitor.interval_ms}ms")
        print(f"🎯 Target texts: {len(monitor.awaiting_user_action_texts)}")
        
        return True
    except Exception as e:
        print(f"❌ Monitor creation failed: {e}")
        return False

def test_command_line():
    """Test command line parsing"""
    print("\n📋 Testing command line interface...")
    
    try:
        # Test help
        print("Testing --help...")
        os.system("python3 cursor_chat_monitor.py --help > /dev/null 2>&1")
        
        # Test platform info
        print("Testing --platform-info...")
        result = os.system("python3 cursor_chat_monitor.py --platform-info > /dev/null 2>&1")
        if result == 0:
            print("✅ Command line interface works")
            return True
        else:
            print("❌ Command line test failed")
            return False
    except Exception as e:
        print(f"❌ Command line test failed: {e}")
        return False

def test_build_dependencies():
    """Test build dependencies"""
    print("\n🔨 Testing build dependencies...")
    
    try:
        import PyInstaller
        print(f"✅ PyInstaller available: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller not found - run: pip3 install pyinstaller")
        return False
    
    # Check if we have macOS-specific dependencies
    try:
        import objc
        print("✅ PyObjC available for macOS support")
    except ImportError:
        print("⚠️  PyObjC not found - may affect macOS functionality")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Testing cursor-chat-monitor before building standalone version")
    print("=" * 70)
    
    tests = [
        ("Import Tests", test_imports),
        ("Platform Support", test_platform_support),
        ("Configuration", test_config_loading),
        ("Monitor Creation", test_monitor_creation),
        ("Command Line", test_command_line),
        ("Build Dependencies", test_build_dependencies),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready to build standalone version.")
        print("\n🏗️  To build: python3 build_standalone.py")
        return 0
    else:
        print("❌ Some tests failed. Fix issues before building.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 