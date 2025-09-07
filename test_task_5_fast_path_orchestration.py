#!/usr/bin/env python3
"""
Test script for Task 5: Fast Path Orchestration Logic

This script tests the implementation of the fast path orchestration logic
in the QuestionAnsweringHandler, including content processing pipeline,
performance monitoring, and error handling.
"""

import sys
import os
import logging
import time
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """Set up logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_fast_path_orchestration():
    """Test the fast path orchestration logic implementation."""
    print("=" * 60)
    print("Testing Fast Path Orchestration Logic (Task 5)")
    print("=" * 60)
    
    try:
        # Import required modules
        from handlers.question_answering_handler import QuestionAnsweringHandler
        from modules.application_detector import ApplicationInfo, ApplicationType, BrowserType
        
        # Create mock orchestrator
        mock_orchestrator = Mock()
        
        # Create handler instance
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        print("✓ QuestionAnsweringHandler initialized successfully")
        
        # Test 1: Content processing for summarization
        print("\n1. Testing content processing for summarization...")
        
        test_content = "This is a test content with multiple sentences. It should be processed correctly for summarization. The content has enough words to pass validation."
        processed = handler._process_content_for_summarization(test_content)
        
        if processed and len(processed) > 0:
            print(f"✓ Content processing successful: {len(processed)} characters")
        else:
            print("✗ Content processing failed")
            return False
        
        # Test 2: Content processing with oversized content
        print("\n2. Testing content processing with oversized content...")
        
        large_content = "Test content. " * 5000  # Create large content
        processed_large = handler._process_content_for_summarization(large_content)
        
        if processed_large and len(processed_large) < len(large_content):  # Should be truncated
            print(f"✓ Large content processing successful: {len(processed_large)} characters (truncated from {len(large_content)})")
        else:
            print(f"✗ Large content processing failed: processed={len(processed_large) if processed_large else 0}, original={len(large_content)}")
            return False
        
        # Test 3: Fallback summary creation
        print("\n3. Testing fallback summary creation...")
        
        test_content_for_summary = "This is the first sentence. This is the second sentence. This is the third sentence. This is the fourth sentence."
        fallback_summary = handler._create_fallback_summary(test_content_for_summary)
        
        if fallback_summary and len(fallback_summary) > 0:
            print(f"✓ Fallback summary created: {len(fallback_summary)} characters")
            print(f"   Summary: {fallback_summary[:100]}...")
        else:
            print("✗ Fallback summary creation failed")
            return False
        
        # Test 4: Summarization prompt creation
        print("\n4. Testing summarization prompt creation...")
        
        test_commands = [
            "what's on my screen",
            "summarize this page",
            "tell me the key points",
            "describe what I'm looking at"
        ]
        
        for command in test_commands:
            prompt = handler._create_summarization_prompt(test_content, command)
            if prompt and len(prompt) > len(test_content):  # Should include prompt text + content
                print(f"✓ Prompt created for '{command}': {len(prompt)} characters")
            else:
                print(f"✗ Prompt creation failed for '{command}'")
                return False
        
        # Test 5: Performance logging
        print("\n5. Testing performance logging...")
        
        # Create mock application info
        mock_app_info = Mock()
        mock_app_info.name = "Google Chrome"
        mock_app_info.app_type = ApplicationType.WEB_BROWSER
        mock_app_info.browser_type = BrowserType.CHROME
        
        # Test performance logging
        handler._log_fast_path_performance(
            mock_app_info, 
            "browser", 
            1.5,  # extraction_time
            2.0,  # summarization_time
            3.5,  # total_time
            1000, # content_length
            200   # summary_length
        )
        
        print("✓ Performance logging completed")
        
        # Test 6: Performance statistics
        print("\n6. Testing performance statistics...")
        
        # Simulate some fast path attempts
        handler._fast_path_attempts = 10
        handler._fast_path_successes = 8
        handler._fallback_count = 2
        
        stats = handler.get_performance_stats()
        
        if stats and 'fast_path_success_rate' in stats:
            print(f"✓ Performance stats generated:")
            print(f"   Success rate: {stats['fast_path_success_rate']}%")
            print(f"   Attempts: {stats['fast_path_attempts']}")
            print(f"   Successes: {stats['fast_path_successes']}")
            print(f"   Fallbacks: {stats['fallback_count']}")
        else:
            print("✗ Performance statistics generation failed")
            return False
        
        # Test 7: Mock fast path orchestration flow
        print("\n7. Testing fast path orchestration flow (mocked)...")
        
        with patch.object(handler, '_detect_active_application') as mock_detect, \
             patch.object(handler, '_is_supported_application') as mock_supported, \
             patch.object(handler, '_get_extraction_method') as mock_method, \
             patch.object(handler, '_extract_browser_content') as mock_extract, \
             patch.object(handler, '_process_content_for_summarization') as mock_process, \
             patch.object(handler, '_summarize_content') as mock_summarize:
            
            # Set up mocks
            mock_detect.return_value = mock_app_info
            mock_supported.return_value = True
            mock_method.return_value = "browser"
            mock_extract.return_value = "Test extracted content from browser"
            mock_process.return_value = "Processed test content"
            mock_summarize.return_value = "Summarized test content"
            
            # Test the orchestration
            result = handler._try_fast_path("what's on my screen")
            
            if result == "Summarized test content":
                print("✓ Fast path orchestration flow successful")
                print(f"   Result: {result}")
            else:
                print(f"✗ Fast path orchestration flow failed: {result}")
                return False
        
        # Test 8: Error handling in orchestration
        print("\n8. Testing error handling in orchestration...")
        
        with patch.object(handler, '_detect_active_application') as mock_detect:
            # Simulate application detection failure
            mock_detect.return_value = None
            
            result = handler._try_fast_path("what's on my screen")
            
            if result is None:
                print("✓ Error handling successful - returned None for failed detection")
            else:
                print(f"✗ Error handling failed - should return None but got: {result}")
                return False
        
        print("\n" + "=" * 60)
        print("✓ All Fast Path Orchestration Logic tests passed!")
        print("✓ Task 5 implementation is working correctly")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Make sure all required modules are available")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test execution."""
    setup_logging()
    
    print("Fast Path Orchestration Logic Test")
    print("Testing Task 5 implementation...")
    
    success = test_fast_path_orchestration()
    
    if success:
        print("\n🎉 Task 5 implementation test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Task 5 implementation test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()