#!/usr/bin/env python3
"""
Test Gmail Click with Chrome Focus

This script tests the Gmail click functionality specifically with Chrome
and provides instructions for proper setup.
"""

import logging
import sys
import time
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('gmail_chrome_test.log')
        ]
    )
    return logging.getLogger(__name__)

def test_chrome_detection():
    """Test Chrome application detection."""
    logger = logging.getLogger(__name__)
    logger.info("Testing Chrome application detection...")
    
    try:
        from modules.accessibility import AccessibilityModule
        
        # Initialize accessibility module
        accessibility = AccessibilityModule()
        
        # Get all running applications
        if accessibility.workspace:
            running_apps = accessibility.workspace.runningApplications()
            
            logger.info("Running applications:")
            chrome_apps = []
            
            for app in running_apps:
                app_name = app.localizedName()
                logger.info(f"  - {app_name}")
                
                # Check if it's a browser
                if app_name in accessibility.CHROME_APP_NAMES:
                    chrome_apps.append(app_name)
            
            if chrome_apps:
                logger.info(f"✅ Found browser applications: {chrome_apps}")
                return chrome_apps
            else:
                logger.warning("❌ No browser applications found running")
                logger.info("Please open Chrome and navigate to Google homepage")
                return []
        else:
            logger.error("❌ Cannot access workspace - accessibility issue")
            return []
            
    except Exception as e:
        logger.error(f"❌ Error testing Chrome detection: {e}")
        return []

def test_gmail_with_specific_app(app_name):
    """Test Gmail detection with a specific application."""
    logger = logging.getLogger(__name__)
    logger.info(f"Testing Gmail detection with {app_name}...")
    
    try:
        from modules.accessibility import AccessibilityModule
        
        # Initialize accessibility module
        accessibility = AccessibilityModule()
        
        # Test Gmail link detection with the specific app
        logger.info(f"Searching for Gmail in {app_name}...")
        
        # Try Chrome-optimized detection first
        if hasattr(accessibility, 'find_element_enhanced_chrome'):
            result = accessibility.find_element_enhanced_chrome('', 'Gmail', app_name)
            
            if result and result.found:
                element = result.element
                logger.info(f"✅ Gmail found via Chrome-optimized detection:")
                logger.info(f"   Role: {element.get('role')}")
                logger.info(f"   Title: {element.get('title')}")
                logger.info(f"   Coordinates: {element.get('coordinates')}")
                logger.info(f"   Enabled: {element.get('enabled')}")
                return element
        
        # Try standard detection with different roles
        test_roles = ['AXLink', 'AXButton', '']
        
        for role in test_roles:
            logger.info(f"Trying role: {role or 'auto-detect'}")
            
            element = accessibility.find_element(role, 'Gmail', app_name)
            
            if element:
                logger.info(f"✅ Gmail found with role {role}:")
                logger.info(f"   Role: {element.get('role')}")
                logger.info(f"   Title: {element.get('title')}")
                logger.info(f"   Coordinates: {element.get('coordinates')}")
                logger.info(f"   Enabled: {element.get('enabled')}")
                return element
        
        logger.warning(f"❌ Gmail not found in {app_name}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error testing Gmail with {app_name}: {e}")
        return None

def test_full_gmail_click_workflow():
    """Test the complete Gmail click workflow."""
    logger = logging.getLogger(__name__)
    logger.info("Testing complete Gmail click workflow...")
    
    try:
        # First, detect Chrome applications
        chrome_apps = test_chrome_detection()
        
        if not chrome_apps:
            logger.error("No browser applications found. Please:")
            logger.error("1. Open Chrome")
            logger.error("2. Navigate to https://www.google.com")
            logger.error("3. Make sure Gmail link is visible")
            logger.error("4. Run this test again")
            return False
        
        # Test Gmail detection with each browser
        gmail_element = None
        successful_app = None
        
        for app_name in chrome_apps:
            logger.info(f"\n--- Testing with {app_name} ---")
            element = test_gmail_with_specific_app(app_name)
            
            if element:
                gmail_element = element
                successful_app = app_name
                break
        
        if gmail_element:
            logger.info(f"\n✅ Gmail element found in {successful_app}!")
            
            # Test click coordinates
            coords = gmail_element.get('coordinates', [])
            if len(coords) >= 4:
                center_x = coords[0] + coords[2] // 2
                center_y = coords[1] + coords[3] // 2
                
                logger.info(f"Click coordinates: ({center_x}, {center_y})")
                
                # Ask user if they want to perform the actual click
                try:
                    response = input(f"\nWould you like to click Gmail in {successful_app}? (y/n): ")
                    if response.lower().startswith('y'):
                        from modules.automation import AutomationModule
                        
                        automation = AutomationModule()
                        success = automation.click(center_x, center_y)
                        
                        if success:
                            logger.info("✅ Gmail click executed successfully!")
                            return True
                        else:
                            logger.error("❌ Gmail click failed")
                            return False
                    else:
                        logger.info("Click test skipped by user")
                        return True
                        
                except KeyboardInterrupt:
                    logger.info("Test cancelled by user")
                    return False
            else:
                logger.error("❌ Invalid coordinates for Gmail element")
                return False
        else:
            logger.error("❌ Gmail element not found in any browser")
            logger.error("Make sure you're on Google homepage with Gmail link visible")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error in Gmail click workflow: {e}")
        return False

def main():
    """Main test function."""
    logger = setup_logging()
    
    logger.info("Gmail Click Test with Chrome")
    logger.info("=" * 50)
    
    logger.info("\n📋 Prerequisites:")
    logger.info("1. Chrome should be open")
    logger.info("2. Navigate to https://www.google.com")
    logger.info("3. Gmail link should be visible in the top-right")
    logger.info("4. Chrome should be the active/focused application")
    
    input("\nPress Enter when Chrome is ready with Google homepage...")
    
    # Run the test
    success = test_full_gmail_click_workflow()
    
    if success:
        logger.info("\n🎉 Gmail click test completed successfully!")
        logger.info("The Gmail click functionality is working correctly.")
    else:
        logger.info("\n❌ Gmail click test failed.")
        logger.info("Check the logs above for specific issues.")
    
    logger.info(f"\nDetailed logs saved to: gmail_chrome_test.log")

if __name__ == "__main__":
    main()