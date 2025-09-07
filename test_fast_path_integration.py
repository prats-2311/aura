#!/usr/bin/env python3
"""
Test script for integrated fast path content extraction with question answering.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.browser_accessibility import BrowserAccessibilityHandler
from modules.pdf_handler import PDFHandler
from modules.application_detector import ApplicationDetector, ApplicationInfo, ApplicationType, BrowserType

def test_fast_path_integration():
    """Test the integrated fast path content extraction functionality."""
    print("Testing integrated fast path content extraction...")
    
    # Test 1: Browser content extraction
    print("\n=== Test 1: Browser Content Extraction ===")
    browser_handler = BrowserAccessibilityHandler()
    
    # Create mock Chrome app info
    chrome_app_info = ApplicationInfo(
        name="Google Chrome",
        bundle_id="com.google.Chrome",
        process_id=12345,
        app_type=ApplicationType.WEB_BROWSER,
        browser_type=BrowserType.CHROME
    )
    
    try:
        content = browser_handler.get_page_text_content(chrome_app_info)
        if content:
            print(f"✓ Browser content extraction successful: {len(content)} characters")
            print(f"  Sample content: {content[:150]}...")
        else:
            print("✗ Browser content extraction returned None (expected if no browser window open)")
    except Exception as e:
        print(f"✗ Browser content extraction failed: {e}")
    
    # Test 2: PDF content extraction
    print("\n=== Test 2: PDF Content Extraction ===")
    pdf_handler = PDFHandler()
    
    print(f"pdftotext available: {pdf_handler.pdftotext_available}")
    
    try:
        # Test with Preview (most common PDF reader on macOS)
        pdf_content = pdf_handler.extract_text_from_open_document("Preview")
        if pdf_content:
            print(f"✓ PDF content extraction successful: {len(pdf_content)} characters")
            print(f"  Sample content: {pdf_content[:150]}...")
        else:
            print("✗ PDF content extraction returned None (expected if no PDF open)")
    except Exception as e:
        print(f"✗ PDF content extraction failed: {e}")
    
    # Test 3: Application detection integration
    print("\n=== Test 3: Application Detection Integration ===")
    detector = ApplicationDetector()
    
    # Test PDF reader detection
    pdf_test_cases = [
        ("Preview", "com.apple.Preview"),
        ("Adobe Acrobat Reader", "com.adobe.Reader"),
        ("Google Chrome", "com.google.Chrome"),  # Should be web browser
    ]
    
    for app_name, bundle_id in pdf_test_cases:
        app_info = ApplicationInfo(
            name=app_name,
            bundle_id=bundle_id,
            process_id=12345,
            app_type=ApplicationType.UNKNOWN
        )
        
        app_type, browser_type, confidence = detector._classify_application(app_info)
        print(f"  {app_name}: {app_type.value} (confidence: {confidence:.2f})")
        
        # Test content extraction strategy selection
        if app_type == ApplicationType.WEB_BROWSER:
            print(f"    → Would use browser content extraction")
        elif app_type == ApplicationType.PDF_READER:
            print(f"    → Would use PDF content extraction")
        else:
            print(f"    → Would fall back to vision analysis")
    
    # Test 4: Performance comparison simulation
    print("\n=== Test 4: Performance Comparison Simulation ===")
    
    import time
    
    # Simulate fast path timing
    fast_path_start = time.time()
    time.sleep(0.1)  # Simulate fast extraction
    fast_path_time = time.time() - fast_path_start
    
    # Simulate vision analysis timing
    vision_start = time.time()
    time.sleep(2.0)  # Simulate slower vision analysis
    vision_time = time.time() - vision_start
    
    print(f"  Simulated fast path time: {fast_path_time:.2f}s")
    print(f"  Simulated vision analysis time: {vision_time:.2f}s")
    print(f"  Fast path speedup: {vision_time / fast_path_time:.1f}x faster")
    
    print("\nFast path integration test completed.")

if __name__ == "__main__":
    test_fast_path_integration()