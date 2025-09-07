#!/usr/bin/env python3
"""
Extract text content from the current Chrome browser tab

This script uses the browser content extraction functionality to get
text content from the currently active Chrome tab.
"""

import sys
import os
import logging
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_chrome_content():
    """Extract content from the current Chrome browser tab."""
    
    print("=" * 60)
    print("Extracting Content from Current Chrome Tab")
    print("=" * 60)
    
    # Start overall timing
    overall_start = time.time()
    
    try:
        # Import required modules
        setup_start = time.time()
        from handlers.question_answering_handler import QuestionAnsweringHandler
        from modules.application_detector import ApplicationDetector
        from unittest.mock import Mock
        
        # Create a mock orchestrator (since we're just testing extraction)
        mock_orchestrator = Mock()
        
        # Create handler instance
        handler = QuestionAnsweringHandler(mock_orchestrator)
        print("✓ QuestionAnsweringHandler created")
        
        # Create application detector to get current Chrome info
        app_detector = ApplicationDetector()
        print("✓ ApplicationDetector created")
        setup_time = time.time() - setup_start
        print(f"⏱️  Setup time: {setup_time:.3f} seconds")
        
        # Get active application info
        print("\n1. Detecting active application...")
        detection_start = time.time()
        app_info = app_detector.get_active_application_info()
        detection_time = time.time() - detection_start
        print(f"⏱️  Application detection time: {detection_time:.3f} seconds")
        
        if not app_info:
            print("❌ Could not detect active application")
            print("Please make sure Chrome is the active (focused) application")
            return False
        
        print(f"✓ Detected application: {app_info.name}")
        print(f"  - Bundle ID: {app_info.bundle_id}")
        print(f"  - Process ID: {app_info.process_id}")
        print(f"  - App Type: {app_info.app_type.value}")
        if app_info.browser_type:
            print(f"  - Browser Type: {app_info.browser_type.value}")
        
        # Check if it's Chrome
        from modules.application_detector import ApplicationType, BrowserType
        if app_info.app_type != ApplicationType.WEB_BROWSER:
            print(f"❌ Active application is not a browser (type: {app_info.app_type.value})")
            print("Please switch to Chrome and make it the active window, then run this script again")
            return False
        
        if app_info.browser_type != BrowserType.CHROME:
            print(f"⚠️  Active browser is {app_info.browser_type.value if app_info.browser_type else 'unknown'}, not Chrome")
            print("This will still work, but the script is designed for Chrome")
        
        # Extract content using the browser content extraction method
        print("\n2. Extracting content from browser...")
        
        # Temporarily override the application detection to use the detected app
        original_detect = handler._detect_active_application
        handler._detect_active_application = lambda: app_info
        
        try:
            extraction_start = time.time()
            content = handler._extract_browser_content()
            extraction_time = time.time() - extraction_start
            print(f"⏱️  Content extraction time: {extraction_time:.3f} seconds")
            
            if content:
                print(f"✓ Successfully extracted {len(content)} characters of content")
                
                # Test content validation timing
                validation_start = time.time()
                is_valid = handler._validate_browser_content(content)
                validation_time = time.time() - validation_start
                print(f"⏱️  Content validation time: {validation_time:.3f} seconds")
                print(f"✓ Content validation: {'PASSED' if is_valid else 'FAILED'}")
                
                # Show timing summary
                overall_time = time.time() - overall_start
                print(f"\n⏱️  TIMING SUMMARY:")
                print(f"  - Setup: {setup_time:.3f}s")
                print(f"  - App Detection: {detection_time:.3f}s")
                print(f"  - Content Extraction: {extraction_time:.3f}s")
                print(f"  - Content Validation: {validation_time:.3f}s")
                print(f"  - Total Time: {overall_time:.3f}s")
                
                # Show some statistics
                word_count = len(content.split())
                char_to_word_ratio = len(content) / word_count if word_count > 0 else 0
                print(f"\n✓ CONTENT STATISTICS:")
                print(f"  - Characters: {len(content)}")
                print(f"  - Words: {word_count}")
                print(f"  - Char/Word ratio: {char_to_word_ratio:.1f}")
                
                print("\n" + "=" * 60)
                print("EXTRACTED CONTENT:")
                print("=" * 60)
                print(content)
                print("=" * 60)
                
                return True
            else:
                extraction_failed_time = time.time() - overall_start
                print(f"⏱️  Time to failure: {extraction_failed_time:.3f} seconds")
                print("❌ Content extraction failed")
                print("This could be due to:")
                print("  - Chrome tab has no content or is loading")
                print("  - Content is too short (<50 characters)")
                print("  - Content failed validation (error page, etc.)")
                print("  - Extraction timeout (>2 seconds)")
                return False
                
        finally:
            # Restore original detection method
            handler._detect_active_application = original_detect
        
    except Exception as e:
        print(f"❌ Error during content extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_browser_accessibility_directly():
    """Test browser accessibility handler directly."""
    
    print("\n" + "=" * 60)
    print("Testing BrowserAccessibilityHandler Directly")
    print("=" * 60)
    
    direct_start = time.time()
    
    try:
        setup_start = time.time()
        from modules.browser_accessibility import BrowserAccessibilityHandler
        from modules.application_detector import ApplicationDetector
        
        # Create instances
        browser_handler = BrowserAccessibilityHandler()
        app_detector = ApplicationDetector()
        setup_time = time.time() - setup_start
        print(f"⏱️  Direct handler setup time: {setup_time:.3f} seconds")
        
        # Get current application
        detection_start = time.time()
        app_info = app_detector.get_active_application_info()
        detection_time = time.time() - detection_start
        print(f"⏱️  App detection time: {detection_time:.3f} seconds")
        
        if not app_info:
            print("❌ Could not detect active application")
            return False
        
        print(f"✓ Testing with {app_info.name}")
        
        # Try direct content extraction
        extraction_start = time.time()
        content = browser_handler.get_page_text_content(app_info)
        extraction_time = time.time() - extraction_start
        total_time = time.time() - direct_start
        
        print(f"⏱️  Direct extraction time: {extraction_time:.3f} seconds")
        print(f"⏱️  Total direct method time: {total_time:.3f} seconds")
        
        if content:
            print(f"✓ Direct extraction successful: {len(content)} characters")
            print("\nFirst 200 characters:")
            print("-" * 40)
            print(content[:200] + "..." if len(content) > 200 else content)
            print("-" * 40)
            return True
        else:
            print("❌ Direct extraction failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in direct extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Make sure Chrome is open with a webpage and is the active (focused) window")
    print("Press Enter to continue...")
    input()
    
    # Try the handler method first
    success1 = extract_chrome_content()
    
    # Also try direct browser handler
    success2 = test_browser_accessibility_directly()
    
    if success1 or success2:
        print("\n🎉 Content extraction working!")
    else:
        print("\n❌ Content extraction failed")
        print("\nTroubleshooting tips:")
        print("1. Make sure Chrome is open and active")
        print("2. Make sure you have a webpage loaded (not a blank tab)")
        print("3. Check that accessibility permissions are granted")
        print("4. Try refreshing the webpage")
    
    sys.exit(0 if (success1 or success2) else 1)