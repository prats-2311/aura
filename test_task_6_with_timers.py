#!/usr/bin/env python3
"""
Task 6 Test with Proper Timers

This script tests the text summarization integration with proper timing
to allow for application switching between Kiro, Chrome, and Preview.
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

def countdown_timer(seconds: int, message: str):
    """Display a countdown timer."""
    print(f"⏰ {message}")
    for i in range(seconds, 0, -1):
        print(f"   {i} seconds remaining...", end='\r')
        time.sleep(1)
    print("   Starting test now...                    ")

def check_and_display_app():
    """Check and display current application."""
    try:
        from modules.application_detector import ApplicationDetector
        detector = ApplicationDetector()
        app_info = detector.get_active_application_info()
        
        if app_info:
            print(f"📱 Current app: {app_info.name} ({app_info.app_type.value})")
            return app_info
        else:
            print("📱 No application detected")
            return None
    except Exception as e:
        print(f"📱 Detection error: {e}")
        return None

def test_chrome_summarization():
    """Test Chrome browser summarization with timer."""
    
    print("\n" + "=" * 60)
    print("🌐 TESTING CHROME BROWSER SUMMARIZATION")
    print("=" * 60)
    
    print("\n📋 Instructions:")
    print("1. Open Chrome browser")
    print("2. Navigate to any webpage with content")
    print("3. Make sure Chrome window is visible")
    
    countdown_timer(10, "You have 10 seconds to switch to Chrome...")
    
    # Check if Chrome is active
    app_info = check_and_display_app()
    
    if not app_info or app_info.app_type.value != 'web_browser':
        print("❌ Chrome browser not detected. Skipping Chrome test.")
        return False
    
    print("✅ Browser detected! Testing summarization...")
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create mock orchestrator
        class MockOrchestrator:
            pass
        
        handler = QuestionAnsweringHandler(MockOrchestrator())
        
        # Test the complete fast path
        print("\n🔍 Testing complete fast path...")
        start_time = time.time()
        
        result = handler._try_fast_path("what's on my screen")
        
        total_time = time.time() - start_time
        
        if result:
            print(f"✅ Fast path successful in {total_time:.2f}s")
            print(f"📝 Summary: {result}")
            
            # Test speech output
            print("\n🔊 Testing speech output...")
            try:
                handler._speak_result(result)
                print("✅ Speech output completed")
            except Exception as e:
                print(f"⚠️ Speech failed: {e}")
            
            return True
        else:
            print(f"❌ Fast path failed after {total_time:.2f}s")
            return False
            
    except Exception as e:
        print(f"❌ Chrome test error: {e}")
        return False

def test_preview_summarization():
    """Test Preview PDF summarization with timer."""
    
    print("\n" + "=" * 60)
    print("📄 TESTING PREVIEW PDF SUMMARIZATION")
    print("=" * 60)
    
    print("\n📋 Instructions:")
    print("1. Open Preview application")
    print("2. Open any PDF document")
    print("3. Make sure Preview window is visible")
    
    countdown_timer(10, "You have 10 seconds to switch to Preview...")
    
    # Check if Preview is active
    app_info = check_and_display_app()
    
    if not app_info or app_info.app_type.value != 'pdf_reader':
        print("❌ Preview PDF reader not detected. Skipping Preview test.")
        return False
    
    print("✅ PDF reader detected! Testing summarization...")
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create mock orchestrator
        class MockOrchestrator:
            pass
        
        handler = QuestionAnsweringHandler(MockOrchestrator())
        
        # Test the complete fast path
        print("\n🔍 Testing complete fast path...")
        start_time = time.time()
        
        result = handler._try_fast_path("what's in this PDF")
        
        total_time = time.time() - start_time
        
        if result:
            print(f"✅ Fast path successful in {total_time:.2f}s")
            print(f"📝 Summary: {result}")
            
            # Test speech output
            print("\n🔊 Testing speech output...")
            try:
                handler._speak_result(result)
                print("✅ Speech output completed")
            except Exception as e:
                print(f"⚠️ Speech failed: {e}")
            
            return True
        else:
            print(f"❌ Fast path failed after {total_time:.2f}s")
            return False
            
    except Exception as e:
        print(f"❌ Preview test error: {e}")
        return False

def test_handler_integration():
    """Test complete handler integration with timer."""
    
    print("\n" + "=" * 60)
    print("🔄 TESTING COMPLETE HANDLER INTEGRATION")
    print("=" * 60)
    
    print("\n📋 Instructions:")
    print("Switch to either Chrome (with webpage) or Preview (with PDF)")
    
    countdown_timer(10, "You have 10 seconds to switch to a supported app...")
    
    # Check current app
    app_info = check_and_display_app()
    
    if not app_info:
        print("❌ No application detected")
        return False
    
    if app_info.app_type.value not in ['web_browser', 'pdf_reader']:
        print(f"❌ App {app_info.name} not supported for fast path")
        return False
    
    print(f"✅ Supported app detected: {app_info.name}")
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create mock orchestrator
        class MockOrchestrator:
            pass
        
        handler = QuestionAnsweringHandler(MockOrchestrator())
        
        # Test multiple commands
        commands = [
            "what's on my screen",
            "describe what I'm looking at",
            "summarize this content"
        ]
        
        success_count = 0
        
        for i, command in enumerate(commands, 1):
            print(f"\n🧪 Test {i}: '{command}'")
            
            start_time = time.time()
            
            # Test the complete handle method
            try:
                result = handler.handle(command, {
                    "intent": {"intent": "question_answering"},
                    "execution_id": f"test_{i}"
                })
                
                total_time = time.time() - start_time
                
                if result and result.get('success'):
                    print(f"    ✅ Success in {total_time:.2f}s")
                    print(f"    📝 Method: {result.get('method', 'unknown')}")
                    
                    response = result.get('response', '')
                    if response:
                        print(f"    📄 Response: {response[:100]}...")
                    
                    success_count += 1
                else:
                    print(f"    ❌ Failed in {total_time:.2f}s")
                    if result:
                        print(f"    ❌ Error: {result.get('error', 'Unknown')}")
                        
            except Exception as e:
                total_time = time.time() - start_time
                print(f"    ❌ Exception in {total_time:.2f}s: {e}")
        
        print(f"\n📊 Results: {success_count}/{len(commands)} tests passed")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Handler integration test error: {e}")
        return False

def main():
    """Main test function with proper timing."""
    
    print("🚀 Task 6 Text Summarization Test with Timers")
    print("=" * 60)
    
    # Show initial state
    print("\n📱 Initial application state:")
    check_and_display_app()
    
    print("\n" + "=" * 60)
    print("🎯 TEST PLAN:")
    print("1. Chrome browser summarization test")
    print("2. Preview PDF summarization test") 
    print("3. Complete handler integration test")
    print("=" * 60)
    
    input("\nPress Enter to start testing...")
    
    # Run tests with results tracking
    results = []
    
    # Test 1: Chrome
    chrome_result = test_chrome_summarization()
    results.append(("Chrome Browser", chrome_result))
    
    # Small pause between tests
    print("\n⏸️ Pausing 3 seconds before next test...")
    time.sleep(3)
    
    # Test 2: Preview
    preview_result = test_preview_summarization()
    results.append(("Preview PDF", preview_result))
    
    # Small pause between tests
    print("\n⏸️ Pausing 3 seconds before next test...")
    time.sleep(3)
    
    # Test 3: Handler integration
    handler_result = test_handler_integration()
    results.append(("Handler Integration", handler_result))
    
    # Final results
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    passed_count = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed_count += 1
    
    print("=" * 60)
    print(f"📈 Overall: {passed_count}/{len(results)} tests passed")
    
    if passed_count == len(results):
        print("🎉 ALL TESTS PASSED!")
        print("✅ Task 6 text summarization integration is working correctly!")
    elif passed_count > 0:
        print("⚠️ PARTIAL SUCCESS")
        print("✅ Some features are working correctly")
    else:
        print("❌ ALL TESTS FAILED")
        print("❌ Please check application setup and try again")
    
    return passed_count > 0

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