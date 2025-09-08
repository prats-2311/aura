#!/usr/bin/env python3
"""
Test AURA application switching with real "what's on my screen" commands
"""

import sys
import os
import time
import threading
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from handlers.question_answering_handler import QuestionAnsweringHandler
from orchestrator import Orchestrator

def test_aura_app_switching():
    """Test AURA with real application switching scenario"""
    
    print("🎯 AURA Application Switching Test")
    print("=" * 60)
    print("This test simulates the real AURA workflow:")
    print("1. Chrome detection and content extraction")
    print("2. Preview detection and PDF content extraction")
    print("3. Voice summaries for both")
    print()
    
    # Initialize AURA components
    print("🔧 Initializing AURA components...")
    try:
        orchestrator = Orchestrator()
        handler = QuestionAnsweringHandler(orchestrator)
        print("✅ AURA components initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize AURA: {e}")
        return
    
    print("\n" + "=" * 60)
    print("📋 TEST PHASE 1: CHROME DETECTION")
    print("=" * 60)
    print("Instructions:")
    print("1. Open Chrome with a content-rich webpage (news, documentation, etc.)")
    print("2. Make sure Chrome is the ACTIVE/FOCUSED window")
    print("3. Test will start automatically in 10 seconds...")
    print()
    
    # Countdown for Chrome setup
    for i in range(10, 0, -1):
        print(f"⏰ Starting Chrome test in {i} seconds... (Make sure Chrome is active!)")
        time.sleep(1)
    
    print("\n🚀 EXECUTING: 'What's on my screen?' with Chrome")
    print("-" * 40)
    
    # Test Chrome detection and extraction
    start_time = time.time()
    try:
        result = handler.handle("What's on my screen?", {
            "intent": {"intent": "question_answering"},
            "execution_id": "chrome_test_001"
        })
        
        execution_time = time.time() - start_time
        
        print(f"⏱️  Execution time: {execution_time:.2f} seconds")
        print(f"📊 Status: {result.get('status', 'unknown')}")
        print(f"🔧 Method: {result.get('method', 'unknown')}")
        
        if result.get('method') == 'fast_path':
            print(f"⚡ Fast path used: {result.get('extraction_method', 'unknown')}")
            print(f"📝 Content length: {result.get('content_length', 'unknown')} chars")
            print(f"📄 Summary length: {result.get('summary_length', 'unknown')} chars")
        elif result.get('method') == 'vision_fallback':
            print(f"👁️  Vision fallback used: {result.get('fallback_reason', 'unknown')}")
        
        print(f"💬 Response: {result.get('message', 'No message')[:100]}...")
        
        if result.get('status') == 'success':
            print("✅ Chrome test PASSED")
        else:
            print("❌ Chrome test FAILED")
            
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"❌ Chrome test ERROR after {execution_time:.2f}s: {e}")
    
    print("\n" + "=" * 60)
    print("📋 TEST PHASE 2: PREVIEW DETECTION")
    print("=" * 60)
    print("Instructions:")
    print("1. Open Preview with a PDF document")
    print("2. Make sure Preview is the ACTIVE/FOCUSED window")
    print("3. Click on Preview window to ensure it has focus")
    print("4. Test will start automatically in 15 seconds...")
    print()
    
    # Countdown for Preview setup
    for i in range(15, 0, -1):
        print(f"⏰ Starting Preview test in {i} seconds... (Switch to Preview now!)")
        time.sleep(1)
    
    print("\n🚀 EXECUTING: 'What's on my screen?' with Preview")
    print("-" * 40)
    
    # Test Preview detection and extraction
    start_time = time.time()
    try:
        result = handler.handle("What's on my screen?", {
            "intent": {"intent": "question_answering"},
            "execution_id": "preview_test_001"
        })
        
        execution_time = time.time() - start_time
        
        print(f"⏱️  Execution time: {execution_time:.2f} seconds")
        print(f"📊 Status: {result.get('status', 'unknown')}")
        print(f"🔧 Method: {result.get('method', 'unknown')}")
        
        if result.get('method') == 'fast_path':
            print(f"⚡ Fast path used: {result.get('extraction_method', 'unknown')}")
            print(f"📝 Content length: {result.get('content_length', 'unknown')} chars")
            print(f"📄 Summary length: {result.get('summary_length', 'unknown')} chars")
        elif result.get('method') == 'vision_fallback':
            print(f"👁️  Vision fallback used: {result.get('fallback_reason', 'unknown')}")
        
        print(f"💬 Response: {result.get('message', 'No message')[:100]}...")
        
        if result.get('status') == 'success':
            print("✅ Preview test PASSED")
        else:
            print("❌ Preview test FAILED")
            
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"❌ Preview test ERROR after {execution_time:.2f}s: {e}")
    
    print("\n" + "=" * 60)
    print("📋 TEST PHASE 3: RAPID SWITCHING TEST")
    print("=" * 60)
    print("Instructions:")
    print("1. Switch between Chrome and Preview every few seconds")
    print("2. Test will run 5 iterations with 8-second intervals")
    print("3. This tests application detection accuracy")
    print()
    
    # Rapid switching test
    for i in range(5):
        app_suggestion = "Chrome" if i % 2 == 0 else "Preview"
        print(f"\n🔄 Iteration {i+1}/5 - Switch to {app_suggestion} now!")
        
        # Countdown for switching
        for j in range(8, 0, -1):
            print(f"⏰ Testing in {j} seconds... (Make sure {app_suggestion} is active!)")
            time.sleep(1)
        
        print(f"🚀 EXECUTING: 'What's on my screen?' (expecting {app_suggestion})")
        
        start_time = time.time()
        try:
            result = handler.handle("What's on my screen?", {
                "intent": {"intent": "question_answering"},
                "execution_id": f"switching_test_{i+1:03d}"
            })
            
            execution_time = time.time() - start_time
            
            # Determine detected app type
            method = result.get('method', 'unknown')
            if method == 'fast_path':
                extraction_method = result.get('extraction_method', 'unknown')
                if extraction_method == 'text_based':
                    # Could be browser or PDF, need to check further
                    detected_app = "Browser or PDF"
                else:
                    detected_app = "Unknown"
            elif method == 'vision_fallback':
                detected_app = "Vision fallback"
            else:
                detected_app = "Unknown"
            
            print(f"  ⏱️  Time: {execution_time:.2f}s | Method: {method} | App: {detected_app}")
            print(f"  💬 Response: {result.get('message', 'No message')[:80]}...")
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"  ❌ ERROR after {execution_time:.2f}s: {e}")
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print("✅ Test completed successfully!")
    print()
    print("Key things to verify from the test:")
    print("1. Chrome content was extracted and summarized correctly")
    print("2. Preview PDF content was extracted and summarized correctly") 
    print("3. Application switching was detected properly")
    print("4. Response times were under 5 seconds for fast path")
    print("5. Voice summaries were provided for both applications")
    print()
    print("If any issues were found, check the logs above for details.")

def test_application_detection_only():
    """Quick test of just application detection"""
    
    print("🔍 Quick Application Detection Test")
    print("=" * 40)
    
    try:
        orchestrator = Orchestrator()
        handler = QuestionAnsweringHandler(orchestrator)
        
        for i in range(3):
            print(f"\nDetection #{i+1}:")
            app_info = handler._detect_active_application()
            if app_info:
                print(f"  Detected: {app_info.name} ({app_info.app_type.value})")
                print(f"  Bundle: {app_info.bundle_id}")
                print(f"  Confidence: {app_info.detection_confidence}")
            else:
                print("  No application detected")
            
            if i < 2:  # Don't sleep after last iteration
                time.sleep(3)
                
    except Exception as e:
        print(f"❌ Detection test failed: {e}")

if __name__ == "__main__":
    print("🎯 AURA Application Switching Test Suite")
    print("=" * 60)
    print("Choose test mode:")
    print("1. Full AURA workflow test (recommended)")
    print("2. Quick application detection test only")
    print()
    
    # Auto-start full test after 5 seconds
    print("Starting full workflow test in 5 seconds...")
    print("(Press Ctrl+C to cancel)")
    
    try:
        for i in range(5, 0, -1):
            print(f"Starting in {i}...")
            time.sleep(1)
        
        test_aura_app_switching()
        
    except KeyboardInterrupt:
        print("\n\n🔍 Running quick detection test instead...")
        test_application_detection_only()