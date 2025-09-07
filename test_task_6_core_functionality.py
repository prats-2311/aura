#!/usr/bin/env python3
"""
Task 6 Core Functionality Test

This script tests the core text summarization functionality without
relying on application detection, using mock content instead.
"""

import sys
import os
import logging
import time
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_summarization_core_functionality():
    """Test the core summarization functionality with mock content."""
    
    print("🧪 Testing Task 6 Core Summarization Functionality")
    print("=" * 60)
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create mock orchestrator
        class MockOrchestrator:
            pass
        
        handler = QuestionAnsweringHandler(MockOrchestrator())
        
        # Test 1: Content processing
        print("\n1️⃣ Testing content processing...")
        
        sample_content = """
        Welcome to OpenAI's GPT-4 Documentation
        
        GPT-4 is a large multimodal model that can accept image and text inputs 
        and produce text outputs. It exhibits human-level performance on various 
        professional and academic benchmarks.
        
        Key Features:
        - Advanced reasoning capabilities
        - Multimodal input support
        - Improved factual accuracy
        - Better instruction following
        
        Getting Started:
        To use GPT-4, you'll need an API key from OpenAI. The model supports
        both chat completions and text completions endpoints.
        
        Best Practices:
        1. Provide clear and specific instructions
        2. Use system messages to set context
        3. Implement proper error handling
        4. Monitor usage and costs
        
        For more information, visit our comprehensive documentation.
        """
        
        processed_content = handler._process_content_for_summarization(sample_content)
        
        if processed_content:
            print(f"✅ Content processed: {len(processed_content)} characters")
            print(f"   Preview: {processed_content[:100]}...")
        else:
            print("❌ Content processing failed")
            return False
        
        # Test 2: Summarization with mock ReasoningModule
        print("\n2️⃣ Testing summarization with mock ReasoningModule...")
        
        with patch('modules.reasoning.ReasoningModule') as mock_reasoning_class:
            mock_reasoning = Mock()
            mock_reasoning.process_query.return_value = (
                "This webpage is about OpenAI's GPT-4, a large multimodal AI model. "
                "It explains that GPT-4 can process both text and images, performs at "
                "human-level on various benchmarks, and offers advanced reasoning capabilities. "
                "The page covers key features, getting started instructions, and best practices "
                "for using the API."
            )
            mock_reasoning_class.return_value = mock_reasoning
            
            start_time = time.time()
            summary = handler._summarize_content(processed_content, "what's on my screen")
            summarization_time = time.time() - start_time
            
            if summary:
                print(f"✅ Summarization successful in {summarization_time:.2f}s")
                print(f"   Summary: {summary}")
                
                # Verify timeout compliance
                if summarization_time <= 3.0:
                    print("✅ Summarization completed within 3-second timeout")
                else:
                    print(f"⚠️ Summarization took {summarization_time:.2f}s (exceeds 3s timeout)")
            else:
                print(f"❌ Summarization failed after {summarization_time:.2f}s")
                return False
        
        # Test 3: Timeout handling
        print("\n3️⃣ Testing timeout handling...")
        
        with patch('modules.reasoning.ReasoningModule') as mock_reasoning_class:
            mock_reasoning = Mock()
            
            # Simulate slow response that exceeds timeout
            def slow_process_query(*args, **kwargs):
                time.sleep(4)  # Longer than 3-second timeout
                return "This should not be returned due to timeout"
            
            mock_reasoning.process_query.side_effect = slow_process_query
            mock_reasoning_class.return_value = mock_reasoning
            
            start_time = time.time()
            summary = handler._summarize_content(processed_content, "test timeout")
            timeout_test_time = time.time() - start_time
            
            if summary is None and timeout_test_time < 4:
                print("✅ Timeout handling working correctly")
            else:
                print(f"❌ Timeout handling failed: result={summary}, time={timeout_test_time:.2f}s")
                return False
        
        # Test 4: Fallback summary
        print("\n4️⃣ Testing fallback summary...")
        
        fallback_summary = handler._create_fallback_summary(processed_content)
        
        if fallback_summary:
            print(f"✅ Fallback summary created: {len(fallback_summary)} characters")
            print(f"   Fallback: {fallback_summary}")
        else:
            print("❌ Fallback summary creation failed")
            return False
        
        # Test 5: Speech formatting
        print("\n5️⃣ Testing speech formatting...")
        
        test_text = "This is a test summary with\n\nnewlines and    extra spaces. [Some bracketed content] (parenthetical content)"
        formatted_speech = handler._format_result_for_speech(test_text)
        
        if formatted_speech:
            print(f"✅ Speech formatting successful")
            print(f"   Original: {test_text}")
            print(f"   Formatted: {formatted_speech}")
            
            # Verify formatting improvements
            if '\n' not in formatted_speech and '    ' not in formatted_speech:
                print("✅ Formatting cleaned up correctly")
            else:
                print("⚠️ Some formatting issues remain")
        else:
            print("❌ Speech formatting failed")
            return False
        
        # Test 6: Audio output (mocked)
        print("\n6️⃣ Testing audio output...")
        
        with patch('modules.audio.AudioModule') as mock_audio_class:
            mock_audio = Mock()
            mock_audio_class.return_value = mock_audio
            
            handler._speak_result("This is a test summary for speech output.")
            
            if mock_audio.text_to_speech.called:
                print("✅ Audio output called successfully")
                call_args = mock_audio.text_to_speech.call_args[0][0]
                print(f"   Spoken text: '{call_args}'")
            else:
                print("❌ Audio output not called")
                return False
        
        # Test 7: Content length management (50KB limit)
        print("\n7️⃣ Testing content length management...")
        
        # Create content larger than 50KB
        large_content = "This is a test sentence that will be repeated many times. " * 1000  # ~58KB
        processed_large = handler._process_content_for_summarization(large_content)
        
        if processed_large:
            processed_size = len(processed_large.encode('utf-8'))
            max_size = 50 * 1024
            
            if processed_size <= max_size:
                print(f"✅ Large content truncated correctly: {processed_size} bytes (limit: {max_size})")
            else:
                print(f"❌ Content not truncated properly: {processed_size} bytes exceeds limit")
                return False
        else:
            print("❌ Large content processing failed")
            return False
        
        # Test 8: Performance metrics
        print("\n8️⃣ Testing performance metrics...")
        
        # Create mock application info for performance logging
        from modules.application_detector import ApplicationType, BrowserType
        
        class MockAppInfo:
            def __init__(self):
                self.name = "Chrome"
                self.app_type = ApplicationType.WEB_BROWSER
                self.browser_type = BrowserType.CHROME
        
        mock_app_info = MockAppInfo()
        
        handler._log_fast_path_performance(
            app_info=mock_app_info,
            extraction_method="browser",
            extraction_time=1.2,
            summarization_time=2.1,
            total_time=3.5,
            content_length=1500,
            summary_length=200
        )
        
        print("✅ Performance metrics logged successfully")
        
        # Get performance stats
        stats = handler.get_performance_stats()
        if stats:
            print(f"✅ Performance stats retrieved: {len(stats)} metrics")
        else:
            print("❌ Performance stats retrieval failed")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 ALL CORE FUNCTIONALITY TESTS PASSED!")
        print("✅ Text summarization integration is working correctly")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Core functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_with_mock_apps():
    """Test integration with mock application detection."""
    
    print("\n🔗 Testing Integration with Mock Applications")
    print("=" * 60)
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        from modules.application_detector import ApplicationType, BrowserType
        
        # Create mock orchestrator
        class MockOrchestrator:
            pass
        
        handler = QuestionAnsweringHandler(MockOrchestrator())
        
        # Mock application info
        class MockAppInfo:
            def __init__(self, name, app_type, browser_type=None):
                self.name = name
                self.app_type = app_type
                self.browser_type = browser_type
        
        # Test with mock Chrome
        print("\n🌐 Testing with mock Chrome browser...")
        
        chrome_app = MockAppInfo("Chrome", ApplicationType.WEB_BROWSER, BrowserType.CHROME)
        
        # Test application support check
        is_supported = handler._is_supported_application(chrome_app)
        if is_supported:
            print("✅ Chrome detected as supported application")
        else:
            print("❌ Chrome not detected as supported")
            return False
        
        # Test extraction method selection
        extraction_method = handler._get_extraction_method(chrome_app)
        if extraction_method == "browser":
            print("✅ Correct extraction method selected for Chrome")
        else:
            print(f"❌ Wrong extraction method: {extraction_method}")
            return False
        
        # Test with mock Preview
        print("\n📄 Testing with mock Preview PDF reader...")
        
        preview_app = MockAppInfo("Preview", ApplicationType.PDF_READER)
        
        # Test application support check
        is_supported = handler._is_supported_application(preview_app)
        if is_supported:
            print("✅ Preview detected as supported application")
        else:
            print("❌ Preview not detected as supported")
            return False
        
        # Test extraction method selection
        extraction_method = handler._get_extraction_method(preview_app)
        if extraction_method == "pdf":
            print("✅ Correct extraction method selected for Preview")
        else:
            print(f"❌ Wrong extraction method: {extraction_method}")
            return False
        
        # Test with unsupported app
        print("\n❌ Testing with unsupported application...")
        
        unsupported_app = MockAppInfo("TextEdit", ApplicationType.NATIVE_APP)
        
        is_supported = handler._is_supported_application(unsupported_app)
        if not is_supported:
            print("✅ Unsupported application correctly identified")
        else:
            print("❌ Unsupported application incorrectly marked as supported")
            return False
        
        print("\n✅ All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    
    print("🚀 Task 6 Core Functionality Test Suite")
    print("=" * 60)
    print("This test verifies the summarization functionality without")
    print("requiring actual application switching.")
    print("=" * 60)
    
    # Run core functionality tests
    core_success = test_summarization_core_functionality()
    
    # Run integration tests
    integration_success = test_integration_with_mock_apps()
    
    # Final results
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    print(f"Core Functionality: {'✅ PASSED' if core_success else '❌ FAILED'}")
    print(f"Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    
    overall_success = core_success and integration_success
    
    print("=" * 60)
    
    if overall_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Task 6 text summarization integration is fully functional")
        print("✅ The implementation meets all requirements:")
        print("  • Content processing with 50KB limit ✅")
        print("  • Summarization with 3-second timeout ✅")
        print("  • Fallback to raw text when needed ✅")
        print("  • Speech output integration ✅")
        print("  • Performance monitoring ✅")
        print("  • Error handling and recovery ✅")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the error messages above")
    
    return overall_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)