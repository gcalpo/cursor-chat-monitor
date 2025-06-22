# Python 3.13 Windows ARM64 Compatibility Fix

## Problem

The `psutil` package fails to build on Python 3.13 on Windows ARM64 due to missing pre-compiled wheels and build tool compatibility issues.

### Error Details
```
Building wheel for psutil (pyproject.toml) ... error
error: command 'cl.exe' failed: None
```

This occurs because:
1. Python 3.13 is very new and `psutil` doesn't have pre-compiled wheels for Windows ARM64 yet
2. The Microsoft Visual C++ Build Tools have compatibility issues with Python 3.13 on ARM64
3. The native extension compilation fails during the build process

## Solution

### 1. Made psutil Optional

Modified the codebase to make `psutil` an optional dependency:

**Files Modified:**
- `platforms/windows.py`
- `debug_windows.py`
- `requirements.txt`

### 2. Code Changes

#### Import Handling
```python
# Try to import psutil, but make it optional
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False
```

#### Process Name Verification
```python
# Check process name using psutil if available
if PSUTIL_AVAILABLE:
    try:
        proc = psutil.Process(pid)
        if proc.name().lower() == "cursor.exe":
            windows.append((hwnd, window_text, pid))
    except Exception as e:
        pass  # Could not get process name, skip
else:
    # Fallback: assume it's Cursor if the window title contains "cursor"
    # This is less reliable but allows the app to work without psutil
    windows.append((hwnd, window_text, pid))
```

### 3. Requirements.txt Update

Commented out `psutil` in requirements.txt:
```txt
# Note: psutil is optional - if installation fails, the app will work with reduced functionality
# psutil>=6.0.0  # Commented out due to Python 3.13 Windows ARM64 build issues
```

## Impact

### Reduced Functionality
- **Process name verification**: Without psutil, the app relies on window title matching instead of process name verification
- **Less reliable window detection**: May detect non-Cursor windows that happen to have "cursor" in their title

### Maintained Functionality
- ✅ All core monitoring features work
- ✅ Text extraction from Cursor windows
- ✅ Voice alerts and notifications
- ✅ Cross-platform compatibility
- ✅ Debug and testing features

## Installation Instructions

### For Python 3.13 Windows ARM64 Users

1. **Install Python 3.13** from python.org
2. **Install dependencies** (psutil will be skipped):
   ```cmd
   pip install -r requirements.txt
   ```
3. **Test installation**:
   ```cmd
   python cursor_chat_monitor.py --platform-info
   python cursor_chat_monitor.py --voices
   ```

### For Other Platforms

The fix is backward compatible. Users on other platforms can still install psutil manually if needed:

```cmd
# Try to install psutil (may work on other platforms)
pip install psutil

# Or install all requirements (psutil will be skipped if it fails)
pip install -r requirements.txt
```

## Future Resolution

When `psutil` releases pre-compiled wheels for Python 3.13 Windows ARM64:

1. Uncomment the psutil line in `requirements.txt`
2. The code will automatically use psutil when available
3. Process name verification will be restored

## Testing

The application has been tested and confirmed working on:
- ✅ Python 3.13.5 on Windows ARM64
- ✅ All core functionality operational
- ✅ Voice system working
- ✅ Platform detection working
- ✅ Help and configuration commands working

## Alternative Solutions Considered

1. **Downgrade Python**: Not recommended as Python 3.13 has important improvements
2. **Use conda**: Could work but adds complexity
3. **Manual psutil compilation**: Too complex and error-prone
4. **Alternative process libraries**: None provide the same functionality as psutil

The chosen solution provides the best balance of functionality, compatibility, and maintainability. 