#!/usr/bin/env python3
"""
Test script for PDF content extraction functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.pdf_handler import PDFHandler

def test_pdf_extraction():
    """Test PDF content extraction functionality."""
    print("Testing PDF content extraction capabilities...")
    
    # Initialize PDF handler
    handler = PDFHandler()
    
    # Check if pdftotext is available
    print(f"pdftotext available: {handler.pdftotext_available}")
    
    if not handler.pdftotext_available:
        print("Installation instructions:")
        print(handler.get_installation_instructions())
    
    # Test PDF application detection
    print("\nTesting PDF application detection...")
    
    test_apps = [
        ("Preview", "com.apple.preview"),
        ("Adobe Acrobat Reader", "com.adobe.reader"),
        ("PDF Expert", "com.readdle.pdfexpert"),
        ("Chrome", "com.google.chrome"),  # Should return False
        ("Safari", "com.apple.safari")    # Should return False
    ]
    
    for app_name, bundle_id in test_apps:
        is_pdf_app = handler.is_pdf_application(app_name, bundle_id)
        print(f"  {app_name}: {'✓' if is_pdf_app else '✗'} PDF application")
    
    # Test file path detection (will likely fail without open PDF)
    print("\nTesting file path detection...")
    try:
        preview_path = handler.get_pdf_file_path_from_application("Preview")
        if preview_path:
            print(f"✓ Found Preview PDF path: {preview_path}")
        else:
            print("✗ No PDF path found in Preview (expected if no PDF open)")
    except Exception as e:
        print(f"✗ Preview path detection failed: {e}")
    
    print("\nPDF extraction test completed.")

if __name__ == "__main__":
    test_pdf_extraction()