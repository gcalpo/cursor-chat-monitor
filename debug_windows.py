#!/usr/bin/env python3
"""
Debug script to test the optimized hybrid Windows window traversal
"""
import win32gui
import win32process
import sys

# Try to import psutil, but make it optional
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

import uiautomation as auto
import logging
import time
from collections import deque

# Disable verbose UI Automation logging
auto.OPERATION_WAIT_TIME = 0
logging.getLogger('uiautomation').setLevel(logging.ERROR)

# Global cache for sidebar paths on a per-window basis
# Key: window_handle, Value: (path_structure, timestamp)
SIDEBAR_PATH_CACHE = {}
CACHE_TIMEOUT = 30  # Cache expires after 30 seconds

def get_cached_sidebar_path(window_handle):
    """Get cached sidebar path for a window if it exists and is not expired."""
    if window_handle in SIDEBAR_PATH_CACHE:
        path_structure, timestamp = SIDEBAR_PATH_CACHE[window_handle]
        if time.time() - timestamp < CACHE_TIMEOUT:
            print(f"    📋 Using cached sidebar path (age: {time.time() - timestamp:.1f}s)")
            return path_structure
        else:
            print(f"    ⏰ Cached sidebar path expired (age: {time.time() - timestamp:.1f}s)")
            del SIDEBAR_PATH_CACHE[window_handle]
    return None

def cache_sidebar_path(window_handle, path_structure):
    """Cache the sidebar path for a window."""
    SIDEBAR_PATH_CACHE[window_handle] = (path_structure, time.time())
    print(f"    💾 Cached sidebar path for window {window_handle}")

def enum_windows_proc(hwnd, windows):
    """Find Cursor windows"""
    if win32gui.IsWindowVisible(hwnd):
        window_text = win32gui.GetWindowText(hwnd)
        if window_text and "cursor" in window_text.lower():
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
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
            except:
                pass
    return True

def trace_path_to_aichat_url(root_element, max_depth=30):
    """Trace the path to the aichat element and output it like a URL."""
    from collections import deque
    
    # Use a queue for BFS: (element, depth, path)
    queue = deque([(root_element, 0, [])])
    element_count = 0
    
    while queue and element_count < 10000:  # Safety limit
        current_element, depth, path = queue.popleft()
        
        if max_depth is not None and depth > max_depth:
            continue
            
        element_count += 1
        
        try:
            automation_id = getattr(current_element, 'AutomationId', '')
            name = getattr(current_element, 'Name', '')
            class_name = getattr(current_element, 'ClassName', '')
            control_type = getattr(current_element, 'ControlTypeName', '') if hasattr(current_element, 'ControlTypeName') else ''
            localized_type = getattr(current_element, 'LocalizedControlType', '') if hasattr(current_element, 'LocalizedControlType') else ''
            
            # Create current element info
            current_info = {
                'depth': depth,
                'automation_id': automation_id,
                'name': name,
                'class_name': class_name,
                'control_type': control_type,
                'localized_type': localized_type,
                'element_count': element_count
            }
            
            # Check if this is the chat sidebar
            is_chat_sidebar = ('aichat' in automation_id.lower() or 
                              'workbench.panel.aichat' in automation_id or
                              'chat' in name.lower() and 'panel' in automation_id.lower())
            
            if is_chat_sidebar:
                # Build the URL-like path
                url_parts = []
                for path_element in path + [current_info]:
                    # Use the most descriptive identifier available
                    identifier = (path_element['automation_id'] or 
                                path_element['name'] or 
                                path_element['class_name'] or 
                                path_element['control_type'] or 
                                path_element['localized_type'] or 
                                'unknown')
                    
                    # Clean up the identifier for URL format
                    identifier = identifier.replace(' ', '_').replace('.', '_').replace('-', '_')
                    url_parts.append(identifier)
                
                # Construct the URL
                url_path = '/'.join(url_parts)
                print(f"🌐 URL Path to aichat: {url_path}")
                print(f"   Depth: {depth}")
                print(f"   Elements processed: {element_count}")
                
                # Also show the detailed path
                print(f"📋 Detailed path:")
                for i, path_element in enumerate(path + [current_info]):
                    print(f"   {i+1}. {path_element['class_name'] or 'unnamed'}")
                    if path_element['automation_id']:
                        print(f"      AutomationId: {path_element['automation_id']}")
                    if path_element['name']:
                        print(f"      Name: {path_element['name']}")
                    if path_element['control_type']:
                        print(f"      Type: {path_element['control_type']}")
                
                return url_path
            
            # Add current element to path
            current_path = path + [current_info]
            
            # Add children to queue for next level (BFS)
            try:
                children = current_element.GetChildren()
                for child in children:
                    queue.append((child, depth + 1, current_path))
            except:
                pass
                
        except Exception as e:
            pass
    
    print("❌ Chat sidebar not found in the element tree")
    return None

def analyze_path_patterns(root_element, max_depth=30):
    """Analyze path patterns to identify exclusion criteria for non-chat paths."""
    from collections import deque, defaultdict
    
    # Track patterns: {pattern: count}
    path_patterns = defaultdict(int)
    chat_paths = []
    non_chat_paths = []
    
    # Use a queue for BFS: (element, depth, path)
    queue = deque([(root_element, 0, [])])
    element_count = 0
    
    while queue and element_count < 5000:  # Limit for analysis
        current_element, depth, path = queue.popleft()
        
        if max_depth is not None and depth > max_depth:
            continue
            
        element_count += 1
        
        try:
            automation_id = getattr(current_element, 'AutomationId', '')
            name = getattr(current_element, 'Name', '')
            class_name = getattr(current_element, 'ClassName', '')
            control_type = getattr(current_element, 'ControlTypeName', '') if hasattr(current_element, 'ControlTypeName') else ''
            localized_type = getattr(current_element, 'LocalizedControlType', '') if hasattr(current_element, 'LocalizedControlType') else ''
            
            # Create current element info
            current_info = {
                'depth': depth,
                'automation_id': automation_id,
                'name': name,
                'class_name': class_name,
                'control_type': control_type,
                'localized_type': localized_type,
                'element_count': element_count
            }
            
            # Check if this is the chat sidebar
            is_chat_sidebar = ('aichat' in automation_id.lower() or 
                              'workbench.panel.aichat' in automation_id or
                              'chat' in name.lower() and 'panel' in automation_id.lower())
            
            current_path = path + [current_info]
            
            if is_chat_sidebar:
                chat_paths.append(current_path)
                # Create pattern for chat path
                pattern = []
                for elem in current_path:
                    pattern.append(f"{elem['class_name']}:{elem['automation_id']}")
                path_patterns['/'.join(pattern)] += 1
            else:
                # Only track non-chat paths that are containers (potential dead ends)
                if (class_name == 'Chrome_RenderWidgetHostHWND' or
                    control_type.lower() in ['groupcontrol', 'panecontrol', 'windowcontrol', 'documentcontrol', 'group', 'pane', 'window', 'document']):
                    non_chat_paths.append(current_path)
                    # Create pattern for non-chat path
                    pattern = []
                    for elem in current_path:
                        pattern.append(f"{elem['class_name']}:{elem['automation_id']}")
                    path_patterns['/'.join(pattern)] += 1
            
            # Add children to queue for next level (BFS)
            try:
                children = current_element.GetChildren()
                for child in children:
                    queue.append((child, depth + 1, current_path))
            except:
                pass
                
        except Exception as e:
            pass
    
    # Analyze patterns to find exclusion criteria
    exclusion_criteria = []
    
    # Look for common patterns in non-chat paths that don't appear in chat paths
    non_chat_patterns = set()
    chat_patterns = set()
    
    for path in non_chat_paths:
        for elem in path:
            if elem['automation_id']:
                non_chat_patterns.add(elem['automation_id'])
            if elem['class_name']:
                non_chat_patterns.add(elem['class_name'])
    
    for path in chat_paths:
        for elem in path:
            if elem['automation_id']:
                chat_patterns.add(elem['automation_id'])
            if elem['class_name']:
                chat_patterns.add(elem['class_name'])
    
    # Find patterns that only appear in non-chat paths
    exclusive_non_chat = non_chat_patterns - chat_patterns
    
    print(f"\n🔍 PATH ANALYSIS RESULTS:")
    print(f"  Elements analyzed: {element_count}")
    print(f"  Chat paths found: {len(chat_paths)}")
    print(f"  Non-chat container paths: {len(non_chat_paths)}")
    print(f"  Unique patterns in non-chat paths: {len(non_chat_patterns)}")
    print(f"  Unique patterns in chat paths: {len(chat_patterns)}")
    print(f"  Exclusive non-chat patterns: {len(exclusive_non_chat)}")
    
    if exclusive_non_chat:
        print(f"\n🚫 POTENTIAL EXCLUSION CRITERIA:")
        for pattern in sorted(list(exclusive_non_chat))[:20]:  # Show first 20
            print(f"    - {pattern}")
    
    # Look for specific exclusion patterns
    specific_exclusions = []
    
    # Common VS Code/Cursor non-chat patterns
    exclusion_keywords = [
    ]
    
    for path in non_chat_paths:
        for elem in path:
            automation_id = elem['automation_id'].lower()
            name = elem['name'].lower()
            for keyword in exclusion_keywords:
                if keyword in automation_id or keyword in name:
                    specific_exclusions.append(f"{keyword} -> {elem['automation_id']} ({elem['class_name']})")
    
    if specific_exclusions:
        print(f"\n🎯 SPECIFIC EXCLUSION PATTERNS:")
        for exclusion in list(set(specific_exclusions))[:15]:  # Show first 15 unique
            print(f"    - {exclusion}")
    
    return exclusive_non_chat, specific_exclusions

def analyze_sidebar_path_structure(root_element, max_depth=30):
    """Analyze the actual path structure to the sidebar and return the optimal traversal sequence."""
    from collections import deque
    
    # Use a queue for BFS: (element, depth, path)
    queue = deque([(root_element, 0, [])])
    element_count = 0
    sidebar_paths = []
    
    while queue and element_count < 10000:  # Safety limit
        current_element, depth, path = queue.popleft()
        
        if max_depth is not None and depth > max_depth:
            continue
            
        element_count += 1
        
        try:
            automation_id = getattr(current_element, 'AutomationId', '')
            name = getattr(current_element, 'Name', '')
            class_name = getattr(current_element, 'ClassName', '')
            control_type = getattr(current_element, 'ControlTypeName', '') if hasattr(current_element, 'ControlTypeName') else ''
            localized_type = getattr(current_element, 'LocalizedControlType', '') if hasattr(current_element, 'LocalizedControlType') else ''
            
            # Create current element info
            current_info = {
                'depth': depth,
                'automation_id': automation_id,
                'name': name,
                'class_name': class_name,
                'control_type': control_type,
                'localized_type': localized_type,
                'element_count': element_count
            }
            
            # Check if this is the chat sidebar
            is_chat_sidebar = ('aichat' in automation_id.lower() or 
                              'workbench.panel.aichat' in automation_id or
                              'chat' in name.lower() and 'panel' in automation_id.lower())
            
            current_path = path + [current_info]
            
            if is_chat_sidebar:
                sidebar_paths.append(current_path)
                print(f"🎯 Found sidebar path #{len(sidebar_paths)}:")
                for i, elem in enumerate(current_path):
                    print(f"   {i+1}. {elem['class_name']} ({elem['control_type']}) - {elem['automation_id']}")
                print()
            
            # Add children to queue for next level (BFS)
            try:
                children = current_element.GetChildren()
                for child in children:
                    queue.append((child, depth + 1, current_path))
            except:
                pass
                
        except Exception as e:
            pass
    
    if not sidebar_paths:
        print("❌ No sidebar paths found")
        return None
    
    # Analyze the common path structure
    print(f"📊 Analyzing {len(sidebar_paths)} sidebar paths...")
    
    # Extract the path structure from each found sidebar
    path_structures = []
    for path in sidebar_paths:
        structure = []
        for elem in path:
            structure.append({
                'class_name': elem['class_name'],
                'control_type': elem['control_type'],
                'automation_id': elem['automation_id'],
                'name': elem['name']
            })
        path_structures.append(structure)
    
    # Find the most common path structure
    if len(path_structures) > 0:
        # Use the first path as the reference (most common pattern)
        reference_path = path_structures[0]
        
        print(f"🎯 Optimal traversal sequence (based on path analysis):")
        for i, elem in enumerate(reference_path):
            print(f"   {i+1}. {elem['class_name']} ({elem['control_type']})")
            if elem['automation_id']:
                print(f"      AutomationId: {elem['automation_id']}")
            if elem['name']:
                print(f"      Name: {elem['name']}")
        
        return reference_path
    
    return None

def extract_uia_text_targeted_traversal(root_element, texts, max_depth=30, sidebar_depth_limit=20, window_handle=None):
    """Targeted traversal based on analyzed sidebar path structure with caching."""
    from collections import deque
    
    # Check cache first if window handle is provided
    path_structure = None
    if window_handle:
        path_structure = get_cached_sidebar_path(window_handle)
    
    # If not in cache, analyze the path structure
    if not path_structure:
        print("🔍 Phase 0: Analyzing sidebar path structure...")
        path_structure = analyze_sidebar_path_structure(root_element, max_depth)
        
        # Cache the result if window handle is provided
        if path_structure and window_handle:
            cache_sidebar_path(window_handle, path_structure)
    
    if not path_structure:
        print("❌ Could not determine sidebar path structure, falling back to hybrid traversal")
        return extract_uia_text_hybrid_with_exclusions(root_element, texts, max_depth, sidebar_depth_limit, window_handle)
    
    # Phase 1: Targeted traversal based on path structure
    phase1_start = time.time()
    excluded_count = 0
    
    def targeted_sidebar_search(element, depth, path_index=0):
        nonlocal excluded_count
        
        if max_depth is not None and depth > max_depth:
            return None
        
        if path_index >= len(path_structure):
            return None
        
        try:
            automation_id = getattr(element, 'AutomationId', '')
            name = getattr(element, 'Name', '')
            class_name = getattr(element, 'ClassName', '')
            control_type = getattr(element, 'ControlTypeName', '') if hasattr(element, 'ControlTypeName') else ''
            
            # Check if this is the chat sidebar
            if ('aichat' in automation_id.lower() or 
                'workbench.panel.aichat' in automation_id or
                'chat' in name.lower() and 'panel' in automation_id.lower()):
                return element
            
            # Get expected element from path structure
            expected_elem = path_structure[path_index]
            
            # Check if current element matches the expected path structure
            matches_structure = (
                (expected_elem['class_name'] and class_name == expected_elem['class_name']) or
                (expected_elem['control_type'] and control_type.lower() == expected_elem['control_type'].lower()) or
                (expected_elem['automation_id'] and automation_id == expected_elem['automation_id'])
            )
            
            if matches_structure:
                # This element matches our expected path, continue to next level
                children = element.GetChildren()
                for child in children:
                    found = targeted_sidebar_search(child, depth + 1, path_index + 1)
                    if found:
                        return found
            else:
                # This element doesn't match our expected path, skip it
                excluded_count += 1
                
                # Still check children but with same path_index (might be alternative path)
                children = element.GetChildren()
                for child in children:
                    found = targeted_sidebar_search(child, depth + 1, path_index)
                    if found:
                        return found
                        
        except Exception:
            pass
        return None

    sidebar_element = targeted_sidebar_search(root_element, 0, 0)
    phase1_time = time.time() - phase1_start
    
    if sidebar_element:
        print(f"    ✅ Phase 1 (Targeted Traversal): {phase1_time:.3f}s - Found chat sidebar (excluded {excluded_count} paths)")
        
        # Phase 2: Content Traversal
        phase2_start = time.time()
        _extract_text_from_sidebar(sidebar_element, texts, sidebar_depth_limit)
        phase2_time = time.time() - phase2_start
        
        print(f"    ✅ Phase 2 (Content): {phase2_time:.3f}s - Extracted {len(texts)} text elements")
        return True, phase1_time, phase2_time

    # Fallback to hybrid traversal if targeted approach fails
    print(f"    ⚠️  Phase 1 (Targeted Traversal): {phase1_time:.3f}s - Chat sidebar not found (excluded {excluded_count} paths), trying hybrid fallback")
    return extract_uia_text_hybrid_with_exclusions(root_element, texts, max_depth, sidebar_depth_limit, window_handle)

def extract_uia_text_hybrid_with_exclusions(root_element, texts, max_depth=30, sidebar_depth_limit=20, window_handle=None):
    """Optimized hybrid traversal with exclusion criteria for non-chat paths."""
    from collections import deque
    
    # Exclusion criteria based on analysis
    exclusion_keywords = [
        'cursor tab'
    ]
    
    # Prefix exclusions (elements starting with these prefixes)
    exclusion_prefixes = [
        'bubble-'
    ]
    
    def should_exclude_path(element):
        """Check if a path should be excluded based on exclusion criteria."""
        try:
            automation_id = getattr(element, 'AutomationId', '').lower()
            name = getattr(element, 'Name', '').lower()
            
            # Check for exclusion keywords
            for keyword in exclusion_keywords:
                if keyword in automation_id or keyword in name:
                    return True
            
            # Check for exclusion prefixes
            for prefix in exclusion_prefixes:
                if automation_id.startswith(prefix) or name.startswith(prefix):
                    return True
            
            # Additional exclusion patterns
            if any(pattern in automation_id for pattern in [
                'workbench.view.', 'workbench.panel.output', 'workbench.panel.problems',
                'workbench.view.explorer', 'workbench.view.search', 'workbench.view.scm'
            ]):
                return True
                
            return False
        except:
            return False

    # Phase 1: Fast Path Search with Exclusions
    phase1_start = time.time()
    excluded_count = 0
    
    def fast_path_sidebar_search_with_exclusions(element, depth):
        nonlocal excluded_count
        if max_depth is not None and depth > max_depth:
            return None
        try:
            automation_id = getattr(element, 'AutomationId', '')
            if 'aichat' in automation_id.lower() or 'workbench.panel.aichat' in automation_id:
                return element
            
            # Check exclusion criteria
            if should_exclude_path(element):
                excluded_count += 1
                return None
            
            # Define all container types that can be in the sidebar path
            container_types = [
                'groupcontrol', 'panecontrol', 'windowcontrol', 'documentcontrol',
                'group', 'pane', 'window', 'document'
            ]
            
            class_name = getattr(element, 'ClassName', '')
            control_type = getattr(element, 'ControlTypeName', '') if hasattr(element, 'ControlTypeName') else ''
            localized_type = getattr(element, 'LocalizedControlType', '') if hasattr(element, 'LocalizedControlType') else ''
            
            # Check if this element is a container type we should descend into
            is_container = (class_name == 'Chrome_RenderWidgetHostHWND' or
                           control_type.lower() in container_types or
                           localized_type.lower() in container_types)
            
            if is_container:
                children = element.GetChildren()
                for child in children:
                    found = fast_path_sidebar_search_with_exclusions(child, depth + 1)
                    if found:
                        return found
        except Exception:
            pass
        return None

    sidebar_element = fast_path_sidebar_search_with_exclusions(root_element, 0)
    phase1_time = time.time() - phase1_start
    
    if sidebar_element:
        print(f"    ✅ Phase 1 (Fast Path with Exclusions): {phase1_time:.3f}s - Found chat sidebar (excluded {excluded_count} paths)")
        
        # Phase 2: Content Traversal
        phase2_start = time.time()
        _extract_text_from_sidebar(sidebar_element, texts, sidebar_depth_limit)
        phase2_time = time.time() - phase2_start
        
        print(f"    ✅ Phase 2 (Content): {phase2_time:.3f}s - Extracted {len(texts)} text elements")
        return True, phase1_time, phase2_time

    # Phase 1b: Fallback Search with Exclusions
    print(f"    ⚠️  Phase 1 (Fast Path with Exclusions): {phase1_time:.3f}s - Chat sidebar not found (excluded {excluded_count} paths), trying fallback")
    
    phase1b_start = time.time()
    queue = deque([(root_element, 0)])
    element_count = 0
    excluded_count_fallback = 0
    
    while queue and element_count < 10000:  # Safety limit
        current_element, depth = queue.popleft()
        if max_depth is not None and depth > max_depth:
            continue
        element_count += 1
        
        try:
            automation_id = getattr(current_element, 'AutomationId', '')
            name = getattr(current_element, 'Name', '')
            class_name = getattr(current_element, 'ClassName', '')
            control_type = getattr(current_element, 'ControlTypeName', '') if hasattr(current_element, 'ControlTypeName') else ''
            localized_type = getattr(current_element, 'LocalizedControlType', '') if hasattr(current_element, 'LocalizedControlType') else ''
            
            is_chat_sidebar = ('aichat' in automation_id.lower() or 
                              'workbench.panel.aichat' in automation_id or
                              'chat' in name.lower() and 'panel' in automation_id.lower())
            
            if is_chat_sidebar:
                phase1b_time = time.time() - phase1b_start
                print(f"    ✅ Phase 1b (Fallback with Exclusions): {phase1b_time:.3f}s - Found chat sidebar after {element_count} elements (excluded {excluded_count_fallback} paths)")
                
                # Phase 2: Content Traversal
                phase2_start = time.time()
                _extract_text_from_sidebar(current_element, texts, sidebar_depth_limit)
                phase2_time = time.time() - phase2_start
                
                print(f"    ✅ Phase 2 (Content): {phase2_time:.3f}s - Extracted {len(texts)} text elements")
                return True, phase1_time + phase1b_time, phase2_time
            
            # Check exclusion criteria before traversing
            if should_exclude_path(current_element):
                excluded_count_fallback += 1
                continue
            
            # Traverse all container types seen in the sidebar path
            should_traverse = False
            container_types = [
                'groupcontrol', 'panecontrol', 'windowcontrol', 'documentcontrol',
                'group', 'pane', 'window', 'document'
            ]
            if (class_name == 'Chrome_RenderWidgetHostHWND' or
                control_type.lower() in container_types or
                localized_type.lower() in container_types or
                ('workbench.panel.aichat' in automation_id.lower())):
                should_traverse = True
            if should_traverse:
                try:
                    children = current_element.GetChildren()
                    for child in children:
                        queue.append((child, depth + 1))
                except:
                    pass
        except Exception:
            pass
    
    phase1b_time = time.time() - phase1b_start
    print(f"    ❌ Phase 1b (Fallback with Exclusions): {phase1b_time:.3f}s - Chat sidebar not found after {element_count} elements (excluded {excluded_count_fallback} paths)")
    return False, phase1_time + phase1b_time, 0.0

def _extract_text_from_sidebar(sidebar_element, texts, max_depth):
    """Extract all text from the sidebar and its descendants with depth limit."""
    from collections import deque
    queue = deque([(sidebar_element, 0)])
    
    while queue:
        current_element, depth = queue.popleft()
        if max_depth is not None and depth > max_depth:
            continue
        
        try:
            # Get various text properties
            for prop_name in ['Name', 'AutomationId', 'ClassName', 'HelpText', 'LocalizedControlType', 'ControlType']:
                try:
                    value = getattr(current_element, prop_name, None)
                    if value and isinstance(value, str) and value.strip():
                        texts.append(value.strip())
                except:
                    pass
            
            # Also try to get the element's text content directly
            try:
                if hasattr(current_element, 'GetText'):
                    text_content = current_element.GetText()
                    if text_content and isinstance(text_content, str) and text_content.strip():
                        texts.append(text_content.strip())
            except:
                pass
            
            # Add children
            children = current_element.GetChildren()
            for child in children:
                queue.append((child, depth + 1))
        except Exception as e:
            pass

def extract_uia_text_hybrid_without_cursor_tab_exclusion(root_element, texts, max_depth=30, sidebar_depth_limit=20):
    """Optimized hybrid traversal WITHOUT "Cursor Tab", "Intermediate D3D Window", and "bubble-" exclusion for comparison."""
    from collections import deque
    
    # Exclusion criteria based on analysis (without "cursor tab", "intermediate d3d window", and "bubble-")
    exclusion_keywords = [
        'explorer', 'outline', 'timeline', 'scm', 'debug', 'extensions', 
        'settings', 'problems', 'output', 'terminal', 'search', 'replace',
        'git', 'source', 'test', 'run', 'debugger', 'breakpoint',
        'callstack', 'variables', 'watch', 'evaluate', 'console',
        'tasks', 'bookmarks', 'snippets', 'references', 'implementations',
        'workbench.view', 'workbench.panel.output', 'workbench.panel.problems',
        'workbench.view.explorer', 'workbench.view.search', 'workbench.view.scm',
        'workbench.view.debug', 'workbench.view.extensions'
        # Note: "cursor tab", "intermediate d3d window", and "bubble-" are intentionally excluded from this list
    ]
    
    # Prefix exclusions (elements starting with these prefixes) - empty for comparison
    exclusion_prefixes = []
    
    def should_exclude_path(element):
        """Check if a path should be excluded based on exclusion criteria."""
        try:
            automation_id = getattr(element, 'AutomationId', '').lower()
            name = getattr(element, 'Name', '').lower()
            
            # Check for exclusion keywords
            for keyword in exclusion_keywords:
                if keyword in automation_id or keyword in name:
                    return True
            
            # Check for exclusion prefixes
            for prefix in exclusion_prefixes:
                if automation_id.startswith(prefix) or name.startswith(prefix):
                    return True
            
            # Additional exclusion patterns
            if any(pattern in automation_id for pattern in [
                'workbench.view.', 'workbench.panel.output', 'workbench.panel.problems',
                'workbench.view.explorer', 'workbench.view.search', 'workbench.view.scm'
            ]):
                return True
                
            return False
        except:
            return False
    
    # Phase 1: Fast Path Search with Exclusions
    phase1_start = time.time()
    excluded_count = 0
    
    def fast_path_sidebar_search_with_exclusions(element, depth):
        nonlocal excluded_count
        if max_depth is not None and depth > max_depth:
            return None
        try:
            automation_id = getattr(element, 'AutomationId', '')
            if 'aichat' in automation_id.lower() or 'workbench.panel.aichat' in automation_id:
                return element
            
            # Check exclusion criteria
            if should_exclude_path(element):
                excluded_count += 1
                return None
            
            # Define all container types that can be in the sidebar path
            container_types = [
                'groupcontrol', 'panecontrol', 'windowcontrol', 'documentcontrol',
                'group', 'pane', 'window', 'document'
            ]
            
            class_name = getattr(element, 'ClassName', '')
            control_type = getattr(element, 'ControlTypeName', '') if hasattr(element, 'ControlTypeName') else ''
            localized_type = getattr(element, 'LocalizedControlType', '') if hasattr(element, 'LocalizedControlType') else ''
            
            # Check if this element is a container type we should descend into
            is_container = (class_name == 'Chrome_RenderWidgetHostHWND' or
                           control_type.lower() in container_types or
                           localized_type.lower() in container_types)
            
            if is_container:
                children = element.GetChildren()
                for child in children:
                    found = fast_path_sidebar_search_with_exclusions(child, depth + 1)
                    if found:
                        return found
        except Exception:
            pass
        return None

    sidebar_element = fast_path_sidebar_search_with_exclusions(root_element, 0)
    phase1_time = time.time() - phase1_start
    
    if sidebar_element:
        print(f"    ✅ Phase 1 (Without Cursor Tab/D3D/bubble- Exclusion): {phase1_time:.3f}s - Found chat sidebar (excluded {excluded_count} paths)")
        
        # Phase 2: Content Traversal
        phase2_start = time.time()
        _extract_text_from_sidebar(sidebar_element, texts, sidebar_depth_limit)
        phase2_time = time.time() - phase2_start
        
        print(f"    ✅ Phase 2 (Content): {phase2_time:.3f}s - Extracted {len(texts)} text elements")
        return True, phase1_time, phase2_time

    # Phase 1b: Fallback Search with Exclusions
    print(f"    ⚠️  Phase 1 (Without Cursor Tab/D3D/bubble- Exclusion): {phase1_time:.3f}s - Chat sidebar not found (excluded {excluded_count} paths), trying fallback")
    
    phase1b_start = time.time()
    queue = deque([(root_element, 0)])
    element_count = 0
    excluded_count_fallback = 0
    
    while queue and element_count < 10000:  # Safety limit
        current_element, depth = queue.popleft()
        if max_depth is not None and depth > max_depth:
            continue
        element_count += 1
        
        try:
            automation_id = getattr(current_element, 'AutomationId', '')
            name = getattr(current_element, 'Name', '')
            class_name = getattr(current_element, 'ClassName', '')
            control_type = getattr(current_element, 'ControlTypeName', '') if hasattr(current_element, 'ControlTypeName') else ''
            localized_type = getattr(current_element, 'LocalizedControlType', '') if hasattr(current_element, 'LocalizedControlType') else ''
            
            is_chat_sidebar = ('aichat' in automation_id.lower() or 
                              'workbench.panel.aichat' in automation_id or
                              'chat' in name.lower() and 'panel' in automation_id.lower())
            
            if is_chat_sidebar:
                phase1b_time = time.time() - phase1b_start
                print(f"    ✅ Phase 1b (Fallback Without Cursor Tab/D3D/bubble- Exclusion): {phase1b_time:.3f}s - Found chat sidebar after {element_count} elements (excluded {excluded_count_fallback} paths)")
                
                # Phase 2: Content Traversal
                phase2_start = time.time()
                _extract_text_from_sidebar(current_element, texts, sidebar_depth_limit)
                phase2_time = time.time() - phase2_start
                
                print(f"    ✅ Phase 2 (Content): {phase2_time:.3f}s - Extracted {len(texts)} text elements")
                return True, phase1_time + phase1b_time, phase2_time
            
            # Check exclusion criteria before traversing
            if should_exclude_path(current_element):
                excluded_count_fallback += 1
                continue
            
            # Traverse all container types seen in the sidebar path
            should_traverse = False
            container_types = [
                'groupcontrol', 'panecontrol', 'windowcontrol', 'documentcontrol',
                'group', 'pane', 'window', 'document'
            ]
            if (class_name == 'Chrome_RenderWidgetHostHWND' or
                control_type.lower() in container_types or
                localized_type.lower() in container_types or
                ('workbench.panel.aichat' in automation_id.lower())):
                should_traverse = True
            if should_traverse:
                try:
                    children = current_element.GetChildren()
                    for child in children:
                        queue.append((child, depth + 1))
                except:
                    pass
        except Exception:
            pass
    
    phase1b_time = time.time() - phase1b_start
    print(f"    ❌ Phase 1b (Fallback Without Cursor Tab/D3D/bubble- Exclusion): {phase1b_time:.3f}s - Chat sidebar not found after {element_count} elements (excluded {excluded_count_fallback} paths)")
    return False, phase1_time + phase1b_time, 0.0

def main():
    print("🔍 Testing optimized hybrid traversal strategy with targeted path analysis and caching...")
    print("=" * 80)
    
    # Phase 0: Window Identification
    phase0_start = time.time()
    found_windows = []
    win32gui.EnumWindows(enum_windows_proc, found_windows)
    phase0_time = time.time() - phase0_start
    
    print(f"\n📊 Summary: Found {len(found_windows)} Cursor windows in {phase0_time:.3f}s")
    print("=" * 80)
    
    total_phase1_time_targeted = 0.0
    total_phase1_time_hybrid = 0.0
    total_phase2_time = 0.0
    successful_windows = 0
    
    # Run multiple iterations to demonstrate caching
    iterations = 3
    print(f"\n🔄 Running {iterations} iterations to demonstrate caching benefits...")
    
    for iteration in range(iterations):
        print(f"\n📋 ITERATION {iteration + 1}/{iterations}")
        print("-" * 40)
        
        iteration_phase1_targeted = 0.0
        iteration_phase1_hybrid = 0.0
        iteration_phase2 = 0.0
        iteration_successful = 0
        
        for i, (hwnd, title, pid) in enumerate(found_windows):
            print(f"Window {i+1}:")
            print(f"  Title: {title}")
            print(f"  PID: {pid}")
            print(f"  HWND: {hwnd}")
            
            try:
                uia_element = auto.ControlFromHandle(hwnd)
                if uia_element:
                    # Test 1: Targeted traversal (path analysis) with caching
                    print("\n  🚀 Test 1: Targeted traversal (path analysis) with caching")
                    texts_targeted = []
                    success1, phase1_time_targeted, phase2_time1 = extract_uia_text_targeted_traversal(uia_element, texts_targeted, 30, 20, hwnd)
                    
                    # Test 2: Hybrid traversal with exclusions
                    print("\n  🚀 Test 2: Hybrid traversal with exclusions")
                    texts_hybrid = []
                    success2, phase1_time_hybrid, phase2_time2 = extract_uia_text_hybrid_with_exclusions(uia_element, texts_hybrid, 30, 20, hwnd)
                    
                    if success1 and success2:
                        iteration_successful += 1
                        iteration_phase1_targeted += phase1_time_targeted
                        iteration_phase1_hybrid += phase1_time_hybrid
                        iteration_phase2 += phase2_time2  # Use the second test's content time
                        
                        # Calculate time savings
                        time_savings = phase1_time_hybrid - phase1_time_targeted
                        savings_percentage = (time_savings / phase1_time_hybrid * 100) if phase1_time_hybrid > 0 else 0
                        
                        print(f"\n  📈 COMPARISON RESULTS:")
                        print(f"    Hybrid traversal:     {phase1_time_hybrid:.3f}s")
                        print(f"    Targeted traversal:   {phase1_time_targeted:.3f}s")
                        print(f"    Time saved:           {time_savings:.3f}s ({savings_percentage:.1f}%)")
                        print(f"    Content extraction:   {phase2_time2:.3f}s")
                        print(f"    Total time saved:     {time_savings:.3f}s")
                    
                    # Only trace URL path on first iteration
                    if iteration == 0:
                        print("\n  🌐 Tracing URL path to aichat...")
                        trace_path_to_aichat_url(uia_element, 30)
                        
                        # Check for target text in both results
                        connection_failed_found_targeted = any("connection failed" in t.lower() for t in texts_targeted)
                        connection_failed_found_hybrid = any("connection failed" in t.lower() for t in texts_hybrid)
                        
                        print(f"  📊 Text Extraction Results:")
                        print(f"    Targeted traversal: {len(texts_targeted)} elements, 'Connection failed' found: {connection_failed_found_targeted}")
                        print(f"    Hybrid traversal:   {len(texts_hybrid)} elements, 'Connection failed' found: {connection_failed_found_hybrid}")
                    
                else:
                    print("    ❌ Could not get UIA element from window handle")
                    
            except Exception as e:
                print(f"    ❌ UIA Error: {e}")
            
            print()
        
        # Accumulate totals
        successful_windows = iteration_successful
        total_phase1_time_targeted += iteration_phase1_targeted
        total_phase1_time_hybrid += iteration_phase1_hybrid
        total_phase2_time += iteration_phase2
        
        # Show iteration summary
        if iteration_successful > 0:
            avg_phase1_targeted = iteration_phase1_targeted / iteration_successful
            avg_phase1_hybrid = iteration_phase1_hybrid / iteration_successful
            avg_phase2 = iteration_phase2 / iteration_successful
            
            time_savings = iteration_phase1_hybrid - iteration_phase1_targeted
            savings_percentage = (time_savings / iteration_phase1_hybrid * 100) if iteration_phase1_hybrid > 0 else 0
            
            print(f"📊 ITERATION {iteration + 1} SUMMARY:")
            print(f"  Phase 1 Hybrid traversal:      {iteration_phase1_hybrid:.3f}s total, {avg_phase1_hybrid:.3f}s avg per window")
            print(f"  Phase 1 Targeted traversal:    {iteration_phase1_targeted:.3f}s total, {avg_phase1_targeted:.3f}s avg per window")
            print(f"  Phase 2 (Content):             {iteration_phase2:.3f}s total, {avg_phase2:.3f}s avg per window")
            print(f"  Time saved this iteration:     {time_savings:.3f}s ({savings_percentage:.1f}%)")
            print(f"  Success Rate: {iteration_successful}/{len(found_windows)} windows ({iteration_successful/len(found_windows)*100:.1f}%)")
    
    # Summary statistics across all iterations
    print("=" * 80)
    print("📈 TIMING COMPARISON SUMMARY (ALL ITERATIONS):")
    print(f"  Phase 0 (Window ID): {phase0_time:.3f}s - Found {len(found_windows)} windows")
    if successful_windows > 0:
        avg_phase1_targeted = total_phase1_time_targeted / iterations
        avg_phase1_hybrid = total_phase1_time_hybrid / iterations
        avg_phase2 = total_phase2_time / iterations
        
        total_time_savings = total_phase1_time_hybrid - total_phase1_time_targeted
        total_savings_percentage = (total_time_savings / total_phase1_time_hybrid * 100) if total_phase1_time_hybrid > 0 else 0
        
        print(f"  Phase 1 Hybrid traversal:      {total_phase1_time_hybrid:.3f}s total, {avg_phase1_hybrid:.3f}s avg per iteration")
        print(f"  Phase 1 Targeted traversal:    {total_phase1_time_targeted:.3f}s total, {avg_phase1_targeted:.3f}s avg per iteration")
        print(f"  Phase 2 (Content):             {total_phase2_time:.3f}s total, {avg_phase2:.3f}s avg per iteration")
        print(f"  Total time saved:              {total_time_savings:.3f}s ({total_savings_percentage:.1f}%)")
        print(f"  Success Rate: {successful_windows}/{len(found_windows)} windows ({successful_windows/len(found_windows)*100:.1f}%)")
        
        # Show cache statistics
        print(f"\n💾 CACHE STATISTICS:")
        print(f"  Cached paths: {len(SIDEBAR_PATH_CACHE)}")
        for hwnd, (path_structure, timestamp) in SIDEBAR_PATH_CACHE.items():
            age = time.time() - timestamp
            print(f"    Window {hwnd}: {len(path_structure)} path elements, age: {age:.1f}s")
    else:
        print("  ❌ No successful window traversals")

if __name__ == "__main__":
    main() 