#!/usr/bin/env python3
"""
Test script for Task 6: Text Summarization Integration

This script tests the implementation of text summarization integration
in the QuestionAnsweringHandler.
"""

import sys
import os
import logging
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_summarization_integration():
    """Test the text summarization integration functionality."""
    
    print("=" * 60)
    print("Testing Task 6: Text Summarization Integration")
    print("=" * 60)
    
    try:
        # Import the handler
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create a mock orchestrator
        mock_orchestrator = Mock()
        
        # Initialize the handler
        handler = QuestionAnsweringHandler(mock_orchestrator)
        print("✓ QuestionAnsweringHandler initialized successfully")
        
        # Test 1: Content processing for summarization
        print("\n1. Testing content processing for summarization...")
        
        test_content = """
        This is a sample web page content that contains multiple paragraphs.
        
        The first paragraph discusses the importance of content summarization
        in modern applications. It explains how users often need quick summaries
        of lengthy documents or web pages.
        
        The second paragraph goes into technical details about how summarization
        works using natural language processing techniques. It mentions various
        algorithms and approaches used in the field.
        
        The final paragraph concludes with the benefits of automated summarization
        for improving user experience and productivity.
        """
        
        processed_content = handler._process_content_for_summarization(test_content)
        
        if processed_content:
            print(f"✓ Content processed successfully: {len(processed_content)} characters")
            print(f"  Original: {len(test_content)} chars, Processed: {len(processed_content)} chars")
        else:
            print("✗ Content processing failed")
            return False
        
        # Test 2: Content length management (50KB limit)
        print("\n2. Testing content length management...")
        
        # Create content larger than 50KB
        large_content = "This is a test sentence. " * 3000  # ~75KB
        processed_large = handler._process_content_for_summarization(large_content)
        
        if processed_large:
            processed_size = len(processed_large.encode('utf-8'))
            max_size = 50 * 1024
            if processed_size <= max_size:
                print(f"✓ Large content truncated correctly: {processed_size} bytes (limit: {max_size})")
            else:
                print(f"✗ Content not truncated properly: {processed_size} bytes exceeds limit")
                return False
        else:
            print("✗ Large content processing failed")
            return False
        
        # Test 3: Summarization prompt building
        print("\n3. Testing summarization prompt building...")
        
        test_command = "what's on my screen"
        prompt = handler._create_summarization_prompt(processed_content, test_command)
        
        if prompt and len(prompt) > 0:
            print(f"✓ Summarization prompt created: {len(prompt)} characters")
            print(f"  Prompt preview: {prompt[:100]}...")
        else:
            print("✗ Summarization prompt creation failed")
            return False
        
        # Test 4: Fallback summary creation
        print("\n4. Testing fallback summary creation...")
        
        fallback_summary = handler._create_fallback_summary(processed_content)
        
        if fallback_summary and len(fallback_summary) > 0:
            print(f"✓ Fallback summary created: {len(fallback_summary)} characters")
            print(f"  Summary preview: {fallback_summary[:100]}...")
        else:
            print("✗ Fallback summary creation failed")
            return False
        
        # Test 5: Speech formatting
        print("\n5. Testing speech formatting...")
        
        test_result = "This is a test result with\n\nnewlines and    extra spaces. [Some bracketed content] (parenthetical content)"
        formatted_speech = handler._format_result_for_speech(test_result)
        
        if formatted_speech:
            print(f"✓ Speech formatting successful: {len(formatted_speech)} characters")
            print(f"  Original: '{test_result[:50]}...'")
            print(f"  Formatted: '{formatted_speech[:50]}...'")
        else:
            print("✗ Speech formatting failed")
            return False
        
        # Test 6: Mock summarization with timeout handling
        print("\n6. Testing summarization with mocked ReasoningModule...")
        
        # Mock the ReasoningModule
        with patch('modules.reasoning.ReasoningModule') as mock_reasoning_class:
            mock_reasoning = Mock()
            mock_reasoning.process_query.return_value = "This is a test summary of the content."
            mock_reasoning_class.return_value = mock_reasoning
            
            # Test summarization
            summary = handler._summarize_content(processed_content, test_command)
            
            if summary:
                print(f"✓ Summarization successful: {len(summary)} characters")
                print(f"  Summary: '{summary}'")
            else:
                print("✗ Summarization failed")
                return False
        
        # Test 7: Mock audio output
        print("\n7. Testing audio output with mocked AudioModule...")
        
        with patch('modules.audio.AudioModule') as mock_audio_class:
            mock_audio = Mock()
            mock_audio_class.return_value = mock_audio
            
            # Test speaking result
            handler._speak_result("This is a test result to speak.")
            
            # Verify the audio module was called
            if mock_audio.text_to_speech.called:
                print("✓ Audio output called successfully")
                call_args = mock_audio.text_to_speech.call_args[0][0]
                print(f"  Spoken text: '{call_args}'")
            else:
                print("✗ Audio output not called")
                return False
        
        # Test 8: Performance metrics logging
        print("\n8. Testing performance metrics logging...")
        
        # Create mock application info
        from modules.application_detector import ApplicationType, BrowserType
        
        class MockAppInfo:
            def __init__(self):
                self.name = "Chrome"
                self.app_type = ApplicationType.WEB_BROWSER
                self.browser_type = BrowserType.CHROME
        
        mock_app_info = MockAppInfo()
        
        # Test performance logging
        handler._log_fast_path_performance(
            app_info=mock_app_info,
            extraction_method="browser",
            extraction_time=1.2,
            summarization_time=2.1,
            total_time=3.5,
            content_length=1500,
            summary_length=200
        )
        
        print("✓ Performance metrics logged successfully")
        
        # Test 9: Performance statistics
        print("\n9. Testing performance statistics...")
        
        stats = handler.get_performance_stats()
        
        if stats and isinstance(stats, dict):
            print("✓ Performance statistics retrieved successfully")
            print(f"  Stats: {stats}")
        else:
            print("✗ Performance statistics retrieval failed")
            return False
        
        print("\n" + "=" * 60)
        print("✓ All Task 6 tests passed successfully!")
        print("✓ Text summarization integration is working correctly")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_with_requirements():
    """Test that the implementation meets the specific requirements."""
    
    print("\n" + "=" * 60)
    print("Testing Requirements Compliance")
    print("=" * 60)
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create handler
        mock_orchestrator = Mock()
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        # Requirement 1.2, 1.3: Content length management (50KB limit)
        print("\n1. Testing 50KB content limit (Requirements 1.2, 1.3)...")
        
        # Create content exactly at 50KB
        content_50kb = "A" * (50 * 1024)
        processed = handler._process_content_for_summarization(content_50kb)
        
        if processed and len(processed.encode('utf-8')) <= 50 * 1024:
            print("✓ 50KB content limit enforced correctly")
        else:
            print("✗ 50KB content limit not enforced")
            return False
        
        # Requirement 2.2, 2.3: Timeout handling (3 second limit)
        print("\n2. Testing 3-second timeout handling (Requirements 2.2, 2.3)...")
        
        # Mock a slow ReasoningModule
        with patch('modules.reasoning.ReasoningModule') as mock_reasoning_class:
            mock_reasoning = Mock()
            
            # Simulate timeout by making the method hang
            import time
            def slow_process_query(*args, **kwargs):
                time.sleep(4)  # Longer than 3 second timeout
                return "This should not be returned due to timeout"
            
            mock_reasoning.process_query.side_effect = slow_process_query
            mock_reasoning_class.return_value = mock_reasoning
            
            # Test that timeout is handled
            start_time = time.time()
            result = handler._summarize_content("Test content", "test command")
            end_time = time.time()
            
            # Should return None due to timeout and complete in ~3 seconds
            if result is None and (end_time - start_time) < 4:
                print("✓ 3-second timeout handled correctly")
            else:
                print(f"✗ Timeout not handled correctly: result={result}, time={end_time-start_time:.2f}s")
                return False
        
        # Test fallback to raw text when summarization fails
        print("\n3. Testing fallback to raw text when summarization fails...")
        
        test_content = "This is test content for fallback testing."
        fallback = handler._create_fallback_summary(test_content)
        
        if fallback and len(fallback) > 0:
            print("✓ Fallback to raw text working correctly")
        else:
            print("✗ Fallback to raw text failed")
            return False
        
        # Test response formatting for speech
        print("\n4. Testing response formatting for speech...")
        
        test_response = "This is a test response with formatting issues.\n\nMultiple lines and    spaces."
        formatted = handler._format_result_for_speech(test_response)
        
        # Should clean up formatting issues
        if formatted and '\n' not in formatted and '    ' not in formatted:
            print("✓ Response formatting for speech working correctly")
        else:
            print("✗ Response formatting for speech failed")
            return False
        
        print("\n" + "=" * 60)
        print("✓ All requirements compliance tests passed!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Requirements compliance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Task 6 Implementation Tests...")
    
    # Run basic functionality tests
    success1 = test_summarization_integration()
    
    # Run requirements compliance tests
    success2 = test_integration_with_requirements()
    
    if success1 and success2:
        print("\n🎉 All tests passed! Task 6 implementation is complete and working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)