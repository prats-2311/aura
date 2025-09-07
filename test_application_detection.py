#!/usr/bin/env python3
"""
Test script for enhanced application detection with PDF reader support.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.application_detector import ApplicationDetector, ApplicationInfo, ApplicationType, BrowserType

def test_application_detection():
    """Test enhanced application detection functionality."""
    print("Testing enhanced application detection with PDF reader support...")
    
    # Initialize detector
    detector = ApplicationDetector()
    
    # Test PDF reader detection
    print("\nTesting PDF reader detection...")
    
    pdf_test_cases = [
        ("Preview", "com.apple.Preview"),
        ("Adobe Acrobat Reader", "com.adobe.Reader"),
        ("PDF Expert", "com.readdle.PDFExpert-Mac"),
        ("Skim", "net.sourceforge.skim-app.skim"),
        ("PDFpen", "com.smileonmymac.PDFpen"),
    ]
    
    for app_name, bundle_id in pdf_test_cases:
        # Create mock app info
        app_info = ApplicationInfo(
            name=app_name,
            bundle_id=bundle_id,
            process_id=12345,
            app_type=ApplicationType.UNKNOWN
        )
        
        # Classify the application
        app_type, browser_type, confidence = detector._classify_application(app_info)
        
        print(f"  {app_name}: {app_type.value} (confidence: {confidence:.2f})")
        
        # Verify it's detected as PDF reader
        if app_type == ApplicationType.PDF_READER:
            print(f"    ✓ Correctly identified as PDF reader")
        else:
            print(f"    ✗ Incorrectly identified as {app_type.value}")
    
    # Test non-PDF applications to ensure they're not misclassified
    print("\nTesting non-PDF applications...")
    
    non_pdf_test_cases = [
        ("Google Chrome", "com.google.Chrome", ApplicationType.WEB_BROWSER),
        ("Safari", "com.apple.Safari", ApplicationType.WEB_BROWSER),
        ("Visual Studio Code", "com.microsoft.VSCode", ApplicationType.ELECTRON_APP),
        ("Finder", "com.apple.finder", ApplicationType.SYSTEM_APP),
    ]
    
    for app_name, bundle_id, expected_type in non_pdf_test_cases:
        # Create mock app info
        app_info = ApplicationInfo(
            name=app_name,
            bundle_id=bundle_id,
            process_id=12345,
            app_type=ApplicationType.UNKNOWN
        )
        
        # Classify the application
        app_type, browser_type, confidence = detector._classify_application(app_info)
        
        print(f"  {app_name}: {app_type.value} (confidence: {confidence:.2f})")
        
        # Verify it's not misclassified as PDF reader
        if app_type == expected_type:
            print(f"    ✓ Correctly identified as {expected_type.value}")
        else:
            print(f"    ✗ Incorrectly identified as {app_type.value}, expected {expected_type.value}")
    
    print("\nApplication detection test completed.")

if __name__ == "__main__":
    test_application_detection()