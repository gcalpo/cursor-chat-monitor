#!/usr/bin/env python3
"""
Test script to demonstrate persistent caching in Windows platform
"""
import sys
import time
import logging
from platforms.windows import WindowsAppAccessor, get_sidebar_path_cache_stats, clear_sidebar_path_cache

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_persistent_caching():
    """Test the persistent caching functionality."""
    print("🔍 Testing persistent caching in Windows platform...")
    print("=" * 60)
    
    # Create app accessor
    app_accessor = WindowsAppAccessor()
    
    # Check prerequisites
    if not app_accessor.check_prerequisites():
        print("❌ Prerequisites not met")
        return
    
    # Find Cursor windows
    print("\n📋 Finding Cursor windows...")
    if not app_accessor.find_target_app("cursor"):
        print("❌ No Cursor windows found")
        return
    
    # Get windows
    windows = app_accessor.get_windows()
    print(f"✅ Found {len(windows)} Cursor windows")
    
    # Show initial cache state
    print(f"\n💾 Initial cache state:")
    cache_stats = app_accessor.get_cache_stats()
    print(f"  Cached PIDs: {cache_stats['cached_pids']}")
    print(f"  Cache size: {cache_stats['cache_size']}")
    
    # Run multiple iterations to demonstrate caching
    iterations = 3
    print(f"\n🔄 Running {iterations} iterations to demonstrate persistent caching...")
    
    for iteration in range(iterations):
        print(f"\n📋 ITERATION {iteration + 1}/{iterations}")
        print("-" * 40)
        
        iteration_start = time.time()
        
        for i, window in enumerate(windows):
            print(f"Window {i+1}: {window.title} (PID: {window.pid})")
            
            # Check if this window is already cached
            if window.pid is not None and app_accessor.is_cached(window.pid):
                print(f"  📋 Using cached path for PID {window.pid}")
            else:
                print(f"  🔍 Analyzing path for PID {window.pid}")
            
            # Extract text content (this will use cache if available)
            start_time = time.time()
            texts = window.get_text_content(max_depth=30, sidebar_depth_limit=20)
            end_time = time.time()
            
            print(f"  ⏱️  Extraction time: {end_time - start_time:.3f}s")
            print(f"  📄 Extracted {len(texts)} text elements")
            
            # Show some sample text
            if texts:
                sample_texts = texts[:3]  # Show first 3 text elements
                for j, text in enumerate(sample_texts):
                    if len(text) > 50:
                        text = text[:50] + "..."
                    print(f"    {j+1}. {text}")
        
        iteration_time = time.time() - iteration_start
        print(f"  ⏱️  Total iteration time: {iteration_time:.3f}s")
        
        # Show cache state after this iteration
        cache_stats = app_accessor.get_cache_stats()
        print(f"  💾 Cache state: {cache_stats['cache_size']} cached PIDs")
        for pid, path_length in cache_stats['cached_paths'].items():
            print(f"    PID {pid}: {path_length} path elements")
    
    # Final cache statistics
    print(f"\n📊 FINAL CACHE STATISTICS:")
    final_cache_stats = app_accessor.get_cache_stats()
    print(f"  Total cached PIDs: {final_cache_stats['cache_size']}")
    print(f"  Cached PIDs: {final_cache_stats['cached_pids']}")
    print(f"  Path details:")
    for pid, path_length in final_cache_stats['cached_paths'].items():
        print(f"    PID {pid}: {path_length} path elements")
    
    # Demonstrate cache clearing
    print(f"\n🧹 Demonstrating cache clearing...")
    if final_cache_stats['cache_size'] > 0:
        # Clear cache for first PID
        first_pid = final_cache_stats['cached_pids'][0]
        print(f"  Clearing cache for PID {first_pid}...")
        app_accessor.clear_cache(first_pid)
        
        # Check cache state
        cache_stats_after_clear = app_accessor.get_cache_stats()
        print(f"  Cache size after clearing PID {first_pid}: {cache_stats_after_clear['cache_size']}")
        
        # Clear all cache
        print(f"  Clearing all cache...")
        app_accessor.clear_cache()
        
        # Check final cache state
        final_cache_stats_after_clear = app_accessor.get_cache_stats()
        print(f"  Final cache size: {final_cache_stats_after_clear['cache_size']}")
    
    print(f"\n✅ Persistent caching test completed!")

if __name__ == "__main__":
    test_persistent_caching() 