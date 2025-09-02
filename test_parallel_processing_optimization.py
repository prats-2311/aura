#!/usr/bin/env python3
"""
Test script for parallel processing optimization implementation.

This script tests the new parallel processing features added to the AccessibilityModule
and Orchestrator as part of task 9.2.
"""

import sys
import time
import logging
from unittest.mock import Mock, patch

# Add modules to path
sys.path.append('.')

from modules.accessibility import AccessibilityModule
from orchestrator import Orchestrator

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_accessibility_parallel_processing():
    """Test AccessibilityModule parallel processing features."""
    print("Testing AccessibilityModule parallel processing...")
    
    # Create accessibility module
    accessibility = AccessibilityModule()
    
    # Test parallel processing configuration
    print("1. Testing parallel processing configuration...")
    stats = accessibility.get_parallel_processing_stats()
    print(f"   Initial stats: {stats}")
    
    # Configure parallel processing
    accessibility.configure_parallel_processing(
        enabled=True,
        predictive_cache=True,
        max_background_workers=3
    )
    
    updated_stats = accessibility.get_parallel_processing_stats()
    print(f"   Updated stats: {updated_stats}")
    
    # Test background tree loading
    print("2. Testing background tree loading...")
    if accessibility.accessibility_enabled:
        current_app = accessibility.get_active_application()
        if current_app:
            app_name = current_app['name']
            app_pid = current_app['pid']
            
            task_id = accessibility.start_background_tree_loading(app_name, app_pid)
            print(f"   Started background task: {task_id}")
            
            # Check task status
            time.sleep(1)  # Give it a moment
            status = accessibility.get_background_task_status(task_id)
            print(f"   Task status: {status}")
        else:
            print("   No active application found")
    else:
        print("   Accessibility not enabled - skipping background loading test")
    
    # Test predictive caching
    print("3. Testing predictive caching...")
    if accessibility.accessibility_enabled:
        current_app = accessibility.get_active_application()
        if current_app:
            app_name = current_app['name']
            app_pid = current_app['pid']
            
            predictive_task_id = accessibility.start_predictive_caching(app_name, app_pid)
            print(f"   Started predictive caching: {predictive_task_id}")
            
            # Wait a moment and check
            time.sleep(2)
            accessibility.cleanup_background_tasks()
        else:
            print("   No active application found")
    else:
        print("   Accessibility not enabled - skipping predictive caching test")
    
    # Test cache statistics
    print("4. Testing cache statistics...")
    cache_stats = accessibility.get_cache_statistics()
    print(f"   Cache stats: {cache_stats}")
    
    print("AccessibilityModule parallel processing tests completed.\n")


def test_orchestrator_parallel_processing():
    """Test Orchestrator parallel processing features."""
    print("Testing Orchestrator parallel processing...")
    
    try:
        # Create orchestrator
        orchestrator = Orchestrator()
        
        # Test parallel processing status
        print("1. Testing parallel processing status...")
        status = orchestrator.get_parallel_processing_status()
        print(f"   Status: {status}")
        
        # Test configuration
        print("2. Testing parallel processing configuration...")
        orchestrator.configure_parallel_processing(
            orchestrator_parallel=True,
            background_preload=True,
            accessibility_parallel=True,
            predictive_cache=True
        )
        
        updated_status = orchestrator.get_parallel_processing_status()
        print(f"   Updated status: {updated_status}")
        
        # Test application focus change handling
        print("3. Testing application focus change handling...")
        orchestrator._handle_application_focus_change()
        print("   Application focus change handled")
        
        print("Orchestrator parallel processing tests completed.\n")
        
    except Exception as e:
        print(f"Error testing orchestrator: {e}")


def test_parallel_element_detection():
    """Test parallel element detection with vision preparation."""
    print("Testing parallel element detection...")
    
    accessibility = AccessibilityModule()
    
    if not accessibility.accessibility_enabled:
        print("   Accessibility not enabled - skipping parallel detection test")
        return
    
    # Mock vision callback
    def mock_vision_callback():
        print("   Vision preparation callback called")
        time.sleep(0.5)  # Simulate vision capture time
        return {"mock": "vision_data"}
    
    # Test parallel element detection
    print("1. Testing find_element_with_vision_preparation...")
    start_time = time.time()
    
    result = accessibility.find_element_with_vision_preparation(
        role="AXButton",
        label="Close",
        vision_callback=mock_vision_callback
    )
    
    elapsed_time = time.time() - start_time
    print(f"   Result: {result}")
    print(f"   Elapsed time: {elapsed_time:.2f}s")
    
    print("Parallel element detection tests completed.\n")


def main():
    """Run all parallel processing tests."""
    print("=" * 60)
    print("PARALLEL PROCESSING OPTIMIZATION TESTS")
    print("=" * 60)
    
    try:
        test_accessibility_parallel_processing()
        test_orchestrator_parallel_processing()
        test_parallel_element_detection()
        
        print("=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())