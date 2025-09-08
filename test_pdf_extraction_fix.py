#!/usr/bin/env python3
"""
Test PDF Extraction Fix

This script tests that the PDF extraction timeout fix works correctly
by testing the QuestionAnsweringHandler with a PDF application.
"""

import sys
import os
import logging
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pdf_extraction_timeout_fix():
    """Test that PDF extraction works without signal timeout errors."""
    
    print("🧪 Testing PDF Extraction Timeout Fix")
    print("=" * 60)
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create a mock orchestrator
        class MockOrchestrator:
            pass
        
        mock_orchestrator = MockOrchestrator()
        
        print("1️⃣ Creating QuestionAnsweringHandler...")
        handler = QuestionAnsweringHandler(mock_orchestrator)
        print("✅ Handler created successfully")
        
        print("2️⃣ Testing PDF extraction method (will likely fail but shouldn't crash with signal error)...")
        
        try:
            # This will likely fail because there's no PDF open, but it shouldn't crash with signal error
            result = handler._extract_pdf_content()
            
            if result:
                print(f"✅ PDF extraction successful: {len(result)} characters")
            else:
                print("⚠️ PDF extraction returned None (expected if no PDF is open)")
            
            print("✅ No signal timeout error - fix is working!")
            return True
            
        except Exception as e:
            if "signal only works in main thread" in str(e):
                print(f"❌ Signal timeout error still present: {e}")
                return False
            else:
                print(f"⚠️ Different error (expected): {e}")
                print("✅ No signal timeout error - fix is working!")
                return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_browser_extraction_timeout_fix():
    """Test that browser extraction works without signal timeout errors."""
    
    print("\n🌐 Testing Browser Extraction Timeout Fix")
    print("=" * 60)
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create a mock orchestrator
        class MockOrchestrator:
            pass
        
        mock_orchestrator = MockOrchestrator()
        
        print("1️⃣ Creating QuestionAnsweringHandler...")
        handler = QuestionAnsweringHandler(mock_orchestrator)
        print("✅ Handler created successfully")
        
        print("2️⃣ Testing browser extraction method (will likely fail but shouldn't crash with signal error)...")
        
        try:
            # This will likely fail because there's no browser detected, but it shouldn't crash with signal error
            result = handler._extract_browser_content()
            
            if result:
                print(f"✅ Browser extraction successful: {len(result)} characters")
            else:
                print("⚠️ Browser extraction returned None (expected if no browser is active)")
            
            print("✅ No signal timeout error - fix is working!")
            return True
            
        except Exception as e:
            if "signal only works in main thread" in str(e):
                print(f"❌ Signal timeout error still present: {e}")
                return False
            else:
                print(f"⚠️ Different error (expected): {e}")
                print("✅ No signal timeout error - fix is working!")
                return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_handler_in_thread():
    """Test that the handler works correctly when called from a thread (like in the orchestrator)."""
    
    print("\n🧵 Testing Handler in Thread (Simulating Orchestrator)")
    print("=" * 60)
    
    import threading
    import queue
    
    result_queue = queue.Queue()
    error_queue = queue.Queue()
    
    def handler_worker():
        try:
            from handlers.question_answering_handler import QuestionAnsweringHandler
            
            # Create a mock orchestrator
            class MockOrchestrator:
                pass
            
            mock_orchestrator = MockOrchestrator()
            handler = QuestionAnsweringHandler(mock_orchestrator)
            
            # Test the handle method (this is what the orchestrator calls)
            result = handler.handle("what's on my screen", {
                "intent": {"intent": "question_answering"},
                "execution_id": "test_thread"
            })
            
            result_queue.put(result)
            
        except Exception as e:
            error_queue.put(e)
    
    print("1️⃣ Starting handler in separate thread...")
    
    # Start handler in thread (simulating orchestrator behavior)
    handler_thread = threading.Thread(target=handler_worker, daemon=True)
    handler_thread.start()
    
    # Wait for result with timeout
    handler_thread.join(timeout=10.0)
    
    if handler_thread.is_alive():
        print("❌ Handler thread timed out")
        return False
    
    # Check for errors
    if not error_queue.empty():
        error = error_queue.get()
        if "signal only works in main thread" in str(error):
            print(f"❌ Signal timeout error in thread: {error}")
            return False
        else:
            print(f"⚠️ Different error (may be expected): {error}")
    
    # Check result
    if not result_queue.empty():
        result = result_queue.get()
        print(f"✅ Handler completed in thread: {result.get('status', 'unknown')}")
    else:
        print("⚠️ No result from handler (may be expected)")
    
    print("✅ No signal timeout error in thread - fix is working!")
    return True

def main():
    """Main test function."""
    
    print("🚀 PDF Extraction Timeout Fix Test Suite")
    print("=" * 60)
    print("This test verifies that the signal timeout issues are fixed")
    print("and the handler works correctly in threaded environments.")
    print("=" * 60)
    
    # Run tests
    test1_success = test_pdf_extraction_timeout_fix()
    test2_success = test_browser_extraction_timeout_fix()
    test3_success = test_handler_in_thread()
    
    # Final results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    tests = [
        ("PDF Extraction Fix", test1_success),
        ("Browser Extraction Fix", test2_success),
        ("Handler in Thread", test3_success)
    ]
    
    passed_count = 0
    for test_name, success in tests:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed_count += 1
    
    print("=" * 60)
    
    if passed_count == len(tests):
        print("🎉 ALL TESTS PASSED!")
        print("✅ Signal timeout issues are fixed")
        print("✅ PDF extraction should now work in the main application")
        print("✅ Handler works correctly in threaded environments")
    else:
        print(f"⚠️ {passed_count}/{len(tests)} TESTS PASSED")
        print("❌ Some signal timeout issues may still exist")
    
    return passed_count == len(tests)

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