#!/usr/bin/env python3
"""
Test Chrome content extraction with timing measurements

This script will:
1. Try to activate Chrome
2. Wait for it to become active
3. Extract content with detailed timing
"""

import sys
import os
import time
import subprocess
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def activate_chrome():
    """Try to activate Chrome using AppleScript."""
    print("🔄 Attempting to activate Chrome...")
    
    try:
        # AppleScript to activate Chrome
        applescript = '''
        tell application "Google Chrome"
            activate
        end tell
        '''
        
        activation_start = time.time()
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            timeout=5
        )
        activation_time = time.time() - activation_start
        
        print(f"⏱️  Chrome activation time: {activation_time:.3f} seconds")
        
        if result.returncode == 0:
            print("✓ Chrome activation command successful")
            # Give Chrome a moment to become active
            time.sleep(1)
            return True
        else:
            print(f"❌ Chrome activation failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Chrome activation timed out")
        return False
    except Exception as e:
        print(f"❌ Error activating Chrome: {e}")
        return False

def wait_for_chrome_active(max_wait=5):
    """Wait for Chrome to become the active application."""
    print("⏳ Waiting for Chrome to become active...")
    
    from modules.application_detector import ApplicationDetector, ApplicationType, BrowserType
    
    app_detector = ApplicationDetector()
    wait_start = time.time()
    
    while time.time() - wait_start < max_wait:
        app_info = app_detector.get_active_application_info()
        
        if (app_info and 
            app_info.app_type == ApplicationType.WEB_BROWSER and 
            app_info.browser_type == BrowserType.CHROME):
            wait_time = time.time() - wait_start
            print(f"✓ Chrome is now active (waited {wait_time:.3f} seconds)")
            return app_info
        
        time.sleep(0.1)  # Check every 100ms
    
    wait_time = time.time() - wait_start
    print(f"❌ Chrome did not become active within {wait_time:.3f} seconds")
    return None

def test_chrome_extraction_with_timing():
    """Test Chrome content extraction with detailed timing."""
    
    print("=" * 70)
    print("Chrome Content Extraction Timing Test")
    print("=" * 70)
    
    overall_start = time.time()
    
    try:
        # Step 1: Try to activate Chrome
        if not activate_chrome():
            print("❌ Could not activate Chrome. Make sure Chrome is installed.")
            return False
        
        # Step 2: Wait for Chrome to become active
        app_info = wait_for_chrome_active()
        if not app_info:
            print("❌ Chrome did not become active. Please manually switch to Chrome.")
            return False
        
        # Step 3: Set up extraction components
        setup_start = time.time()
        from handlers.question_answering_handler import QuestionAnsweringHandler
        from unittest.mock import Mock
        
        mock_orchestrator = Mock()
        handler = QuestionAnsweringHandler(mock_orchestrator)
        setup_time = time.time() - setup_start
        print(f"⏱️  Handler setup time: {setup_time:.3f} seconds")
        
        # Step 4: Extract content
        print(f"\n📄 Extracting content from Chrome...")
        print(f"   - App: {app_info.name}")
        print(f"   - Bundle: {app_info.bundle_id}")
        print(f"   - Browser: {app_info.browser_type.value}")
        
        # Override detection to use our Chrome app info
        original_detect = handler._detect_active_application
        handler._detect_active_application = lambda: app_info
        
        try:
            extraction_start = time.time()
            content = handler._extract_browser_content()
            extraction_time = time.time() - extraction_start
            
            print(f"⏱️  Content extraction time: {extraction_time:.3f} seconds")
            
            if content:
                # Test validation timing
                validation_start = time.time()
                is_valid = handler._validate_browser_content(content)
                validation_time = time.time() - validation_start
                
                # Calculate total time
                total_time = time.time() - overall_start
                
                print(f"✅ SUCCESS! Extracted {len(content)} characters")
                print(f"✅ Content validation: {'PASSED' if is_valid else 'FAILED'}")
                
                # Timing summary
                print(f"\n⏱️  DETAILED TIMING BREAKDOWN:")
                print(f"   - Chrome activation: ~1.0s (estimated)")
                print(f"   - Wait for active: varies")
                print(f"   - Handler setup: {setup_time:.3f}s")
                print(f"   - Content extraction: {extraction_time:.3f}s")
                print(f"   - Content validation: {validation_time:.3f}s")
                print(f"   - TOTAL TIME: {total_time:.3f}s")
                
                # Content stats
                word_count = len(content.split())
                print(f"\n📊 CONTENT STATISTICS:")
                print(f"   - Characters: {len(content):,}")
                print(f"   - Words: {word_count:,}")
                print(f"   - Avg chars/word: {len(content)/word_count:.1f}")
                
                # Show first part of content
                print(f"\n📄 CONTENT PREVIEW (first 300 chars):")
                print("-" * 50)
                preview = content[:300].replace('\n', ' ').replace('\r', ' ')
                print(preview + "..." if len(content) > 300 else preview)
                print("-" * 50)
                
                # Performance assessment
                print(f"\n🎯 PERFORMANCE ASSESSMENT:")
                if extraction_time < 1.0:
                    print(f"   ✅ Extraction time ({extraction_time:.3f}s) is EXCELLENT (< 1s)")
                elif extraction_time < 2.0:
                    print(f"   ✅ Extraction time ({extraction_time:.3f}s) is GOOD (< 2s)")
                elif extraction_time < 3.0:
                    print(f"   ⚠️  Extraction time ({extraction_time:.3f}s) is ACCEPTABLE (< 3s)")
                else:
                    print(f"   ❌ Extraction time ({extraction_time:.3f}s) is TOO SLOW (> 3s)")
                
                if total_time < 5.0:
                    print(f"   ✅ Total time ({total_time:.3f}s) meets 5s requirement")
                else:
                    print(f"   ❌ Total time ({total_time:.3f}s) exceeds 5s requirement")
                
                return True
                
            else:
                total_time = time.time() - overall_start
                print(f"❌ Content extraction failed after {total_time:.3f} seconds")
                print("   Possible reasons:")
                print("   - Chrome tab is blank or loading")
                print("   - Content is too short")
                print("   - Content failed validation")
                print("   - Extraction timed out")
                return False
                
        finally:
            handler._detect_active_application = original_detect
        
    except Exception as e:
        total_time = time.time() - overall_start
        print(f"❌ Error after {total_time:.3f} seconds: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_browser_handler():
    """Test the browser handler directly for comparison."""
    
    print("\n" + "=" * 70)
    print("Direct BrowserAccessibilityHandler Test")
    print("=" * 70)
    
    try:
        from modules.browser_accessibility import BrowserAccessibilityHandler
        from modules.application_detector import ApplicationDetector
        
        # Get current app (should still be Chrome)
        app_detector = ApplicationDetector()
        app_info = app_detector.get_active_application_info()
        
        if not app_info:
            print("❌ No active application detected")
            return False
        
        print(f"📱 Testing with: {app_info.name}")
        
        # Test direct extraction
        browser_handler = BrowserAccessibilityHandler()
        
        direct_start = time.time()
        content = browser_handler.get_page_text_content(app_info)
        direct_time = time.time() - direct_start
        
        print(f"⏱️  Direct extraction time: {direct_time:.3f} seconds")
        
        if content:
            print(f"✅ Direct extraction successful: {len(content)} characters")
            return True
        else:
            print("❌ Direct extraction failed")
            return False
            
    except Exception as e:
        print(f"❌ Direct extraction error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Chrome content extraction timing test...")
    print("📝 This test will:")
    print("   1. Try to activate Chrome")
    print("   2. Wait for Chrome to become active")
    print("   3. Extract content with detailed timing")
    print("   4. Test direct browser handler for comparison")
    print()
    
    # Run the main test
    success1 = test_chrome_extraction_with_timing()
    
    # Run direct handler test for comparison
    success2 = test_direct_browser_handler()
    
    print("\n" + "=" * 70)
    if success1 or success2:
        print("🎉 TIMING TEST COMPLETED SUCCESSFULLY!")
        print("📊 Check the timing measurements above to see performance")
    else:
        print("❌ TIMING TEST FAILED")
        print("💡 Make sure Chrome is installed and has a webpage loaded")
    print("=" * 70)
    
    sys.exit(0 if (success1 or success2) else 1)