#!/usr/bin/env python3
"""
Debug script to test Windows window detection with both Win32 and UI Automation
"""
import win32gui
import win32process
import sys
import psutil
import uiautomation as auto
import logging

# Disable verbose UI Automation logging
auto.OPERATION_WAIT_TIME = 0
logging.getLogger('uiautomation').setLevel(logging.ERROR)

# Recursive text extraction using Win32 APIs
def extract_text_recursive(hwnd, texts, visited, current_depth, max_depth=None):
    if max_depth is not None and current_depth > max_depth:
        return
    if hwnd in visited:
        return
    visited.add(hwnd)
    try:
        window_text = win32gui.GetWindowText(hwnd)
        if window_text:  # Remove length filter to see all text
            texts.append(f"[Win32] {window_text} (depth: {current_depth})")
    except Exception as e:
        pass
    # Recurse into child windows
    try:
        def enum_child_proc(child_hwnd, _):
            extract_text_recursive(child_hwnd, texts, visited, current_depth + 1, max_depth)
            return True
        win32gui.EnumChildWindows(hwnd, enum_child_proc, None)
    except Exception as e:
        pass

# Recursive text extraction using UI Automation
def extract_uia_text(element, texts, current_depth, max_depth=None):
    if max_depth is not None and current_depth > max_depth:
        return
    
    try:
        # Get various text properties - expanded list
        for prop_name in ['Name', 'AutomationId', 'ClassName', 'HelpText', 'LocalizedControlType', 'ControlType']:
            try:
                value = getattr(element, prop_name, None)
                if value and isinstance(value, str) and value.strip():
                    texts.append(f"[UIA] {value.strip()} (depth: {current_depth})")
            except:
                pass
        
        # Also try to get the element's text content directly
        try:
            if hasattr(element, 'GetText'):
                text_content = element.GetText()
                if text_content and isinstance(text_content, str) and text_content.strip():
                    texts.append(f"[UIA Text] {text_content.strip()} (depth: {current_depth})")
        except:
            pass
        
        # Get children and recurse
        try:
            children = element.GetChildren()
            for child in children:
                extract_uia_text(child, texts, current_depth + 1, max_depth)
        except:
            pass
            
    except Exception as e:
        pass

def enum_windows_proc(hwnd, windows):
    if win32gui.IsWindowVisible(hwnd):
        window_text = win32gui.GetWindowText(hwnd)
        if window_text and "cursor" in window_text.lower():
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc = psutil.Process(pid)
                    if proc.name().lower() == "cursor.exe":
                        windows.append((hwnd, window_text, pid))
                        print(f"Found Cursor window: '{window_text}' (PID: {pid}, HWND: {hwnd})")
                except Exception as e:
                    print(f"Skipping window '{window_text}' (PID: {pid}): {e}")
            except Exception as e:
                print(f"Error getting process info for window '{window_text}': {e}")
    return True

def main():
    print("🔍 Searching for Cursor windows with Win32 + UI Automation...")
    print("=" * 60)
    
    found_windows = []
    win32gui.EnumWindows(enum_windows_proc, found_windows)
    
    print(f"\n📊 Summary: Found {len(found_windows)} Cursor windows")
    print("=" * 60)
    
    for i, (hwnd, title, pid) in enumerate(found_windows):
        print(f"Window {i+1}:")
        print(f"  Title: {title}")
        print(f"  PID: {pid}")
        print(f"  HWND: {hwnd}")
        
        # Extract all text using both methods
        texts = []
        visited = set()
        
        # Method 1: Win32 API extraction
        extract_text_recursive(hwnd, texts, visited, 0, 30)
        
        # Method 2: UI Automation extraction
        try:
            uia_element = auto.ControlFromHandle(hwnd)
            if uia_element:
                extract_uia_text(uia_element, texts, 0, 30)
        except Exception as e:
            print(f"  UIA Error: {e}")
        
        print(f"  Extracted {len(texts)} text elements:")
        found_agent = False
        for t in texts:
            print(f"    - '{t}'")
            if "agent" in t.lower():
                found_agent = True
        if found_agent:
            print("  🚩 Found element containing 'agent'!")
        else:
            print("  ❌ No 'agent' element found")
        print()

if __name__ == "__main__":
    main() 