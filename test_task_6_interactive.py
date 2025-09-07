#!/usr/bin/env python3
"""
Interactive Test for Task 6: Text Summarization Integration

This script provides an interactive test for the text summarization integration
with real applications, allowing manual verification of application switching.
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

def check_current_application():
    """Check and display the current active application."""
    try:
        from modules.application_detector import ApplicationDetector
        detector = ApplicationDetector()
        app_info = detector.get_active_application_info()
        
        if app_info:
            print(f"📱 Current active application: {app_info.name} ({app_info.app_type.value})")
            if hasattr(app_info, 'browser_type') and app_info.browser_type:
                print(f"   Browser type: {app_info.browser_type.value}")
            return app_info
        else:
            print("📱 Could not detect current active application")
            return None
    except Exception as e:
        print(f"📱 Application detection error: {e}")
        return None

def test_chrome_with_confirmation():
    """Test Chrome with user confirmation of application switch."""
    
    print("\n" + "=" * 70)
    print("🌐 CHROME BROWSER TEST")
    print("=" * 70)
    
    while True:
        print("\n1. Please switch to Chrome browser now")
        print("2. Make sure a webpage is loaded")
        print("3. Click on the Chrome window to make it active")
        print("⏰ You have 10 seconds to switch to Chrome...")
        
        # Countdown timer for switching to Chrome
        for i in range(10, 0, -1):
            print(f"   Switching to Chrome in {i} seconds...", end='\r')
            time.sleep(1)
        print("   Checking Chrome application now...        ")
        
        # Check current application
        app_info = check_current_application()
        
        if app_info and app_info.app_type.value == 'web_browser':
            print("✅ Chrome browser detected! Proceeding with test...")
            break
        else:
            print("❌ Chrome browser not detected as active application")
            retry = input("Would you like to try again? (y/n): ").lower().strip()
            if retry != 'y':
                return False
    
    # Now run the Chrome test
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create a mock orchestrator
        class MockOrchestrator:
            pass
        
        mock_orchestrator = MockOrchestrator()
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        print("\n🔍 Testing content extraction...")
        
        # Test content extraction
        start_time = time.time()
        content = handler._extract_browser_content()
        extraction_time = time.time() - start_time
        
        if content:
            print(f"✅ Content extracted successfully in {extraction_time:.2f}s")
            print(f"   Content length: {len(content)} characters")
            print(f"   Content preview: {content[:200]}...")
            
            # Test content processing
            print("\n🔧 Testing content processing...")
            processed_content = handler._process_content_for_summarization(content)
            
            if processed_content:
                print(f"✅ Content processed successfully")
                print(f"   Processed length: {len(processed_content)} characters")
                
                # Test summarization
                print("\n🤖 Testing content summarization...")
                start_time = time.time()
                summary = handler._summarize_content(processed_content, "what's on my screen")
                summarization_time = time.time() - start_time
                
                if summary:
                    print(f"✅ Summarization successful in {summarization_time:.2f}s")
                    print(f"   Summary: {summary}")
                    
                    # Test speech output
                    print("\n🔊 Testing speech output...")
                    try:
                        handler._speak_result(summary)
                        print("✅ Speech output completed")
                    except Exception as e:
                        print(f"⚠️ Speech output failed: {e}")
                    
                    return True
                else:
                    print(f"❌ Summarization failed after {summarization_time:.2f}s")
                    
                    # Try fallback
                    print("\n🔄 Testing fallback summary...")
                    fallback = handler._create_fallback_summary(processed_content)
                    if fallback:
                        print(f"✅ Fallback summary: {fallback}")
                        return True
                    else:
                        print("❌ Fallback summary also failed")
                        return False
            else:
                print("❌ Content processing failed")
                return False
        else:
            print(f"❌ Content extraction failed after {extraction_time:.2f}s")
            return False
            
    except Exception as e:
        print(f"❌ Chrome test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_preview_with_confirmation():
    """Test Preview with user confirmation of application switch."""
    
    print("\n" + "=" * 70)
    print("📄 PREVIEW PDF TEST")
    print("=" * 70)
    
    while True:
        print("\n1. Please switch to Preview application")
        print("2. Make sure a PDF document is open")
        print("3. Click on the Preview window to make it active")
        print("⏰ You have 10 seconds to switch to Preview...")
        
        # Countdown timer for switching to Preview
        for i in range(10, 0, -1):
            print(f"   Switching to Preview in {i} seconds...", end='\r')
            time.sleep(1)
        print("   Checking Preview application now...       ")
        
        # Check current application
        app_info = check_current_application()
        
        if app_info and app_info.app_type.value == 'pdf_reader':
            print("✅ Preview PDF reader detected! Proceeding with test...")
            break
        else:
            print("❌ Preview PDF reader not detected as active application")
            print(f"   Detected: {app_info.name if app_info else 'None'} ({app_info.app_type.value if app_info else 'None'})")
            retry = input("Would you like to try again? (y/n): ").lower().strip()
            if retry != 'y':
                return False
    
    # Now run the Preview test
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create a mock orchestrator
        class MockOrchestrator:
            pass
        
        mock_orchestrator = MockOrchestrator()
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        print("\n🔍 Testing PDF content extraction...")
        
        # Test PDF content extraction
        start_time = time.time()
        content = handler._extract_pdf_content()
        extraction_time = time.time() - start_time
        
        if content:
            print(f"✅ PDF content extracted successfully in {extraction_time:.2f}s")
            print(f"   Content length: {len(content)} characters")
            print(f"   Content preview: {content[:200]}...")
            
            # Test content processing
            print("\n🔧 Testing content processing...")
            processed_content = handler._process_content_for_summarization(content)
            
            if processed_content:
                print(f"✅ Content processed successfully")
                print(f"   Processed length: {len(processed_content)} characters")
                
                # Test summarization
                print("\n🤖 Testing content summarization...")
                start_time = time.time()
                summary = handler._summarize_content(processed_content, "what's in this PDF")
                summarization_time = time.time() - start_time
                
                if summary:
                    print(f"✅ Summarization successful in {summarization_time:.2f}s")
                    print(f"   Summary: {summary}")
                    
                    # Test speech output
                    print("\n🔊 Testing speech output...")
                    try:
                        handler._speak_result(summary)
                        print("✅ Speech output completed")
                    except Exception as e:
                        print(f"⚠️ Speech output failed: {e}")
                    
                    return True
                else:
                    print(f"❌ Summarization failed after {summarization_time:.2f}s")
                    
                    # Try fallback
                    print("\n🔄 Testing fallback summary...")
                    fallback = handler._create_fallback_summary(processed_content)
                    if fallback:
                        print(f"✅ Fallback summary: {fallback}")
                        return True
                    else:
                        print("❌ Fallback summary also failed")
                        return False
            else:
                print("❌ Content processing failed")
                return False
        else:
            print(f"❌ PDF content extraction failed after {extraction_time:.2f}s")
            return False
            
    except Exception as e:
        print(f"❌ Preview test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fast_path_integration():
    """Test the complete fast path integration."""
    
    print("\n" + "=" * 70)
    print("🚀 FAST PATH INTEGRATION TEST")
    print("=" * 70)
    
    print("\nThis test will use whichever supported application is currently active.")
    print("Make sure either Chrome (with webpage) or Preview (with PDF) is active.")
    print("⏰ You have 10 seconds to switch to a supported application...")
    
    # Countdown timer for switching to supported app
    for i in range(10, 0, -1):
        print(f"   Switching to supported app in {i} seconds...", end='\r')
        time.sleep(1)
    print("   Checking current application now...            ")
    
    # Check current application
    app_info = check_current_application()
    
    if not app_info:
        print("❌ Could not detect active application")
        return False
    
    if app_info.app_type.value not in ['web_browser', 'pdf_reader']:
        print(f"❌ Active application ({app_info.name}) is not supported for fast path")
        print("   Please switch to Chrome or Preview")
        return False
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create a mock orchestrator
        class MockOrchestrator:
            pass
        
        mock_orchestrator = MockOrchestrator()
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        print(f"\n🔍 Testing fast path with {app_info.name}...")
        
        # Test complete fast path
        test_commands = [
            "what's on my screen",
            "describe what I'm looking at",
            "summarize this content"
        ]
        
        for i, command in enumerate(test_commands, 1):
            print(f"\n  Test {i}: '{command}'")
            
            start_time = time.time()
            result = handler._try_fast_path(command)
            total_time = time.time() - start_time
            
            if result:
                print(f"    ✅ Fast path successful in {total_time:.2f}s")
                print(f"    📝 Result: {result[:100]}...")
                
                if total_time < 5.0:
                    print(f"    ⏱️ Performance target met (<5s)")
                else:
                    print(f"    ⚠️ Performance target exceeded ({total_time:.2f}s)")
                
                # Test speech output
                try:
                    handler._speak_result(result)
                    print(f"    🔊 Speech output completed")
                except Exception as e:
                    print(f"    ⚠️ Speech output failed: {e}")
            else:
                print(f"    ❌ Fast path failed after {total_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Fast path integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main interactive test function."""
    
    print("🚀 Interactive Task 6 Text Summarization Test")
    print("=" * 70)
    
    # Show current application
    print("\n📱 Current application status:")
    check_current_application()
    
    print("\n" + "=" * 70)
    print("TEST OPTIONS:")
    print("1. Test Chrome browser summarization")
    print("2. Test Preview PDF summarization") 
    print("3. Test fast path integration (any supported app)")
    print("4. Run all tests")
    print("=" * 70)
    
    while True:
        choice = input("\nEnter your choice (1-4) or 'q' to quit: ").strip()
        
        if choice == 'q':
            print("👋 Goodbye!")
            return True
        elif choice == '1':
            success = test_chrome_with_confirmation()
            print(f"\n🌐 Chrome test: {'✅ PASSED' if success else '❌ FAILED'}")
        elif choice == '2':
            success = test_preview_with_confirmation()
            print(f"\n📄 Preview test: {'✅ PASSED' if success else '❌ FAILED'}")
        elif choice == '3':
            success = test_fast_path_integration()
            print(f"\n🚀 Fast path test: {'✅ PASSED' if success else '❌ FAILED'}")
        elif choice == '4':
            print("\n🔄 Running all tests...")
            
            chrome_success = test_chrome_with_confirmation()
            preview_success = test_preview_with_confirmation()
            fastpath_success = test_fast_path_integration()
            
            print("\n" + "=" * 70)
            print("📊 FINAL RESULTS:")
            print(f"🌐 Chrome test: {'✅ PASSED' if chrome_success else '❌ FAILED'}")
            print(f"📄 Preview test: {'✅ PASSED' if preview_success else '❌ FAILED'}")
            print(f"🚀 Fast path test: {'✅ PASSED' if fastpath_success else '❌ FAILED'}")
            
            all_passed = chrome_success and preview_success and fastpath_success
            print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
            print("=" * 70)
            
            return all_passed
        else:
            print("❌ Invalid choice. Please enter 1-4 or 'q'.")

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)