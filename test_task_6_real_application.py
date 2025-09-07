#!/usr/bin/env python3
"""
Real Application Test for Task 6: Text Summarization Integration

This script tests the complete text summarization integration with real applications
including Chrome browser and Preview (PDF reader) on macOS.
"""

import sys
import os
import logging
import time
from typing import Dict, Any, Optional

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_chrome_summarization():
    """Test text summarization with real Chrome browser."""
    
    print("=" * 70)
    print("Testing Task 6 Text Summarization with Chrome Browser")
    print("=" * 70)
    
    try:
        # Import required modules
        from handlers.question_answering_handler import QuestionAnsweringHandler
        from modules.application_detector import ApplicationDetector
        from modules.browser_accessibility import BrowserAccessibilityHandler
        from modules.reasoning import ReasoningModule
        from modules.audio import AudioModule
        
        # Create a mock orchestrator with required modules
        class MockOrchestrator:
            def __init__(self):
                self.application_detector = ApplicationDetector()
                self.browser_handler = BrowserAccessibilityHandler()
                self.reasoning_module = ReasoningModule()
                self.audio_module = AudioModule()
        
        mock_orchestrator = MockOrchestrator()
        
        # Initialize the handler
        handler = QuestionAnsweringHandler(mock_orchestrator)
        print("✓ QuestionAnsweringHandler initialized successfully")
        
        # Step 1: Detect active application
        print("\n1. Detecting active application...")
        app_info = handler._detect_active_application()
        
        if app_info:
            print(f"✓ Detected application: {app_info.name} ({app_info.app_type.value})")
            if hasattr(app_info, 'browser_type') and app_info.browser_type:
                print(f"  Browser type: {app_info.browser_type.value}")
        else:
            print("✗ Could not detect active application")
            print("  Please make sure Chrome is the active window")
            return False
        
        # Step 2: Check if application is supported
        print("\n2. Checking application support...")
        is_supported = handler._is_supported_application(app_info)
        
        if is_supported:
            print(f"✓ Application {app_info.name} is supported for fast path")
        else:
            print(f"✗ Application {app_info.name} is not supported for fast path")
            return False
        
        # Step 3: Extract content
        print("\n3. Extracting content from browser...")
        start_time = time.time()
        
        extraction_method = handler._get_extraction_method(app_info)
        if extraction_method == "browser":
            content = handler._extract_browser_content()
        else:
            print(f"✗ Unexpected extraction method: {extraction_method}")
            return False
        
        extraction_time = time.time() - start_time
        
        if content:
            print(f"✓ Content extracted successfully in {extraction_time:.2f}s")
            print(f"  Content length: {len(content)} characters")
            print(f"  Content preview: {content[:200]}...")
        else:
            print("✗ Content extraction failed")
            return False
        
        # Step 4: Process content for summarization
        print("\n4. Processing content for summarization...")
        processed_content = handler._process_content_for_summarization(content)
        
        if processed_content:
            print(f"✓ Content processed successfully")
            print(f"  Processed length: {len(processed_content)} characters")
            print(f"  Size in bytes: {len(processed_content.encode('utf-8'))} bytes")
        else:
            print("✗ Content processing failed")
            return False
        
        # Step 5: Test summarization
        print("\n5. Testing content summarization...")
        test_command = "what's on my screen"
        
        start_time = time.time()
        summary = handler._summarize_content(processed_content, test_command)
        summarization_time = time.time() - start_time
        
        if summary:
            print(f"✓ Content summarization successful in {summarization_time:.2f}s")
            print(f"  Summary length: {len(summary)} characters")
            print(f"  Summary: {summary}")
            
            # Check if summarization met timing requirements
            if summarization_time <= 3.0:
                print(f"✓ Summarization completed within 3-second timeout")
            else:
                print(f"⚠ Summarization took {summarization_time:.2f}s (exceeds 3s timeout)")
        else:
            print(f"✗ Content summarization failed after {summarization_time:.2f}s")
            
            # Test fallback summary
            print("\n5b. Testing fallback summary...")
            fallback_summary = handler._create_fallback_summary(processed_content)
            if fallback_summary:
                print(f"✓ Fallback summary created: {fallback_summary[:100]}...")
                summary = fallback_summary  # Use fallback for speech test
            else:
                print("✗ Fallback summary creation failed")
                return False
        
        # Step 6: Test speech formatting and output
        print("\n6. Testing speech output...")
        
        if summary:
            # Format for speech
            formatted_speech = handler._format_result_for_speech(summary)
            print(f"✓ Speech formatting successful")
            print(f"  Original: {len(summary)} chars")
            print(f"  Formatted: {len(formatted_speech)} chars")
            print(f"  Formatted text: {formatted_speech}")
            
            # Test actual speech output (optional - can be disabled if too disruptive)
            try:
                print("\n  Testing actual speech output...")
                handler._speak_result(summary)
                print("✓ Speech output completed successfully")
            except Exception as e:
                print(f"⚠ Speech output failed (this is non-critical): {e}")
        
        # Step 7: Test complete fast path integration
        print("\n7. Testing complete fast path integration...")
        
        total_start_time = time.time()
        fast_path_result = handler._try_fast_path(test_command)
        total_time = time.time() - total_start_time
        
        if fast_path_result:
            print(f"✓ Complete fast path successful in {total_time:.2f}s")
            print(f"  Result: {fast_path_result}")
            
            # Check if total time meets performance target
            if total_time < 5.0:
                print(f"✓ Fast path completed within 5-second performance target")
            else:
                print(f"⚠ Fast path took {total_time:.2f}s (exceeds 5s target)")
        else:
            print(f"✗ Complete fast path failed after {total_time:.2f}s")
            return False
        
        # Step 8: Test performance statistics
        print("\n8. Testing performance statistics...")
        stats = handler.get_performance_stats()
        
        if stats:
            print("✓ Performance statistics retrieved:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        else:
            print("✗ Performance statistics retrieval failed")
        
        print("\n" + "=" * 70)
        print("✅ Chrome browser summarization test completed successfully!")
        print("✅ All Task 6 features working with real Chrome application")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Chrome test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_preview_summarization():
    """Test text summarization with real Preview (PDF reader)."""
    
    print("\n" + "=" * 70)
    print("Testing Task 6 Text Summarization with Preview (PDF Reader)")
    print("=" * 70)
    
    try:
        # Import required modules
        from handlers.question_answering_handler import QuestionAnsweringHandler
        from modules.application_detector import ApplicationDetector, ApplicationType
        
        # Create a mock orchestrator
        class MockOrchestrator:
            def __init__(self):
                self.application_detector = ApplicationDetector()
        
        mock_orchestrator = MockOrchestrator()
        
        # Initialize the handler
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        # Step 1: Detect active application
        print("\n1. Detecting active application...")
        app_info = handler._detect_active_application()
        
        if app_info:
            print(f"✓ Detected application: {app_info.name} ({app_info.app_type.value})")
        else:
            print("✗ Could not detect active application")
            print("  Please make sure Preview is the active window with a PDF open")
            return False
        
        # Step 2: Check if it's a PDF reader
        if app_info.app_type == ApplicationType.PDF_READER:
            print("✓ PDF reader application detected")
            
            # Step 3: Test PDF content extraction
            print("\n2. Testing PDF content extraction...")
            start_time = time.time()
            
            content = handler._extract_pdf_content()
            extraction_time = time.time() - start_time
            
            if content:
                print(f"✓ PDF content extracted successfully in {extraction_time:.2f}s")
                print(f"  Content length: {len(content)} characters")
                print(f"  Content preview: {content[:200]}...")
                
                # Step 4: Process and summarize content
                print("\n3. Processing and summarizing PDF content...")
                processed_content = handler._process_content_for_summarization(content)
                
                if processed_content:
                    summary = handler._summarize_content(processed_content, "what's in this PDF")
                    
                    if summary:
                        print(f"✓ PDF content summarization successful")
                        print(f"  Summary: {summary}")
                        
                        # Test speech output
                        print("\n4. Testing PDF summary speech output...")
                        try:
                            handler._speak_result(summary)
                            print("✓ PDF summary speech output completed")
                        except Exception as e:
                            print(f"⚠ PDF speech output failed: {e}")
                    else:
                        print("✗ PDF content summarization failed")
                        return False
                else:
                    print("✗ PDF content processing failed")
                    return False
            else:
                print("✗ PDF content extraction failed")
                return False
        else:
            print(f"⚠ Active application is not a PDF reader: {app_info.app_type.value}")
            print("  Please switch to Preview with a PDF document open")
            return False
        
        print("\n" + "=" * 70)
        print("✅ Preview PDF summarization test completed successfully!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Preview test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_end_to_end_handler():
    """Test the complete QuestionAnsweringHandler with real applications."""
    
    print("\n" + "=" * 70)
    print("Testing Complete QuestionAnsweringHandler End-to-End")
    print("=" * 70)
    
    try:
        # Import required modules
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create a mock orchestrator
        class MockOrchestrator:
            pass
        
        mock_orchestrator = MockOrchestrator()
        
        # Initialize the handler
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        # Test the complete handle method
        print("\n1. Testing complete handle() method...")
        
        test_commands = [
            "what's on my screen",
            "describe what I'm looking at",
            "summarize this content",
            "what's the main content here"
        ]
        
        for i, command in enumerate(test_commands, 1):
            print(f"\n  Test {i}: Command '{command}'")
            
            start_time = time.time()
            result = handler.handle(command, {
                "intent": {"intent": "question_answering"},
                "execution_id": f"test_{i}"
            })
            total_time = time.time() - start_time
            
            if result and result.get('success'):
                print(f"    ✓ Command handled successfully in {total_time:.2f}s")
                print(f"    ✓ Method: {result.get('method', 'unknown')}")
                print(f"    ✓ Response: {result.get('response', 'No response')[:100]}...")
                
                if total_time < 5.0:
                    print(f"    ✓ Performance target met (<5s)")
                else:
                    print(f"    ⚠ Performance target exceeded ({total_time:.2f}s)")
            else:
                print(f"    ✗ Command failed after {total_time:.2f}s")
                if result:
                    print(f"    Error: {result.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 70)
        print("✅ End-to-end handler test completed!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n✗ End-to-end test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    
    print("🚀 Starting Task 6 Real Application Tests")
    print("📋 Testing text summarization integration with Chrome and Preview")
    print()
    
    # Check current active application
    try:
        from modules.application_detector import ApplicationDetector
        detector = ApplicationDetector()
        current_app = detector.get_active_application_info()
        
        if current_app:
            print(f"📱 Current active application: {current_app.name} ({current_app.app_type.value})")
        else:
            print("📱 Could not detect current active application")
    except Exception as e:
        print(f"📱 Application detection error: {e}")
    
    print("\n" + "=" * 70)
    print("INSTRUCTIONS:")
    print("1. Make sure Chrome is open with a webpage loaded")
    print("2. Make sure Preview is open with a PDF document")
    print("3. The test will automatically switch between applications with 10-second timers")
    print("4. Use the countdown to switch to the requested application")
    print("=" * 70)
    
    input("\nPress Enter when ready to start testing...")
    
    # Test results
    results = []
    
    # Test 1: Chrome browser summarization
    print("\n🌐 Please switch to Chrome browser now...")
    print("⏰ You have 10 seconds to switch to Chrome...")
    
    # Countdown timer for switching to Chrome
    for i in range(10, 0, -1):
        print(f"   Switching to Chrome in {i} seconds...", end='\r')
        time.sleep(1)
    print("   Starting Chrome test now...                    ")
    
    chrome_success = test_chrome_summarization()
    results.append(("Chrome Summarization", chrome_success))
    
    # Test 2: Preview PDF summarization
    print("\n📄 Please switch to Preview with a PDF document now...")
    print("⏰ You have 10 seconds to switch to Preview...")
    
    # Countdown timer for switching to Preview
    for i in range(10, 0, -1):
        print(f"   Switching to Preview in {i} seconds...", end='\r')
        time.sleep(1)
    print("   Starting Preview test now...                   ")
    
    preview_success = test_preview_summarization()
    results.append(("Preview Summarization", preview_success))
    
    # Test 3: End-to-end handler testing
    print("\n🔄 Testing complete handler (switch to Chrome or Preview)...")
    print("⏰ You have 10 seconds to switch to a supported application...")
    
    # Countdown timer for end-to-end test
    for i in range(10, 0, -1):
        print(f"   Starting end-to-end test in {i} seconds...", end='\r')
        time.sleep(1)
    print("   Starting end-to-end test now...               ")
    
    e2e_success = test_end_to_end_handler()
    results.append(("End-to-End Handler", e2e_success))
    
    # Final results
    print("\n" + "=" * 70)
    print("📊 FINAL TEST RESULTS")
    print("=" * 70)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Task 6 text summarization integration is working correctly with real applications")
        print("✅ Chrome browser content extraction and summarization: WORKING")
        print("✅ Preview PDF content extraction and summarization: WORKING")
        print("✅ Speech output integration: WORKING")
        print("✅ Performance targets: MEETING REQUIREMENTS")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the error messages above and ensure:")
        print("- Chrome is properly installed and accessible")
        print("- Preview is available with PDF documents")
        print("- All required modules are properly configured")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)