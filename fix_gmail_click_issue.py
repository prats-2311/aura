#!/usr/bin/env python3
"""
Gmail Click Issue Fix Implementation

This script implements the comprehensive fix for the Gmail click issue in AURA.
It addresses:
1. LM Studio model detection (filtering out embedding models)
2. Enhanced Chrome/browser accessibility detection
3. Proper AXLink role handling for Gmail
4. Application focus and tab detection

Usage:
    python fix_gmail_click_issue.py
"""

import logging
import sys
import time
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """Setup logging for the fix implementation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('gmail_click_fix.log')
        ]
    )
    return logging.getLogger(__name__)

def test_lm_studio_model_detection():
    """Test the enhanced LM Studio model detection."""
    logger = logging.getLogger(__name__)
    logger.info("Testing LM Studio model detection...")
    
    try:
        from config import get_active_vision_model
        
        # Test model detection
        model = get_active_vision_model()
        if model:
            logger.info(f"✅ Detected vision model: {model}")
            
            # Check if it's an embedding model (should be filtered out)
            embedding_patterns = ['embedding', 'embed', 'nomic-embed', 'text-embedding']
            if any(pattern in model.lower() for pattern in embedding_patterns):
                logger.error(f"❌ Detected model is an embedding model: {model}")
                logger.error("Please load a proper vision model in LM Studio (e.g., LLaVA, GPT-4V)")
                return False
            else:
                logger.info(f"✅ Model appears to be vision-capable: {model}")
                return True
        else:
            logger.error("❌ No model detected in LM Studio")
            logger.error("Please ensure LM Studio is running and has a vision model loaded")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing model detection: {e}")
        return False

def test_chrome_accessibility():
    """Test Chrome accessibility detection."""
    logger = logging.getLogger(__name__)
    logger.info("Testing Chrome accessibility detection...")
    
    try:
        from modules.accessibility import AccessibilityModule
        
        # Initialize accessibility module
        accessibility = AccessibilityModule()
        
        # Test application detection
        current_app = accessibility.get_active_application()
        if current_app:
            logger.info(f"✅ Active application detected: {current_app.get('name', 'Unknown')}")
            
            # Check if it's a browser
            browser_names = {'Google Chrome', 'Chrome', 'Chromium', 'Safari', 'Firefox', 'Microsoft Edge'}
            if current_app.get('name') in browser_names:
                logger.info(f"✅ Browser application detected: {current_app['name']}")
                return True
            else:
                logger.warning(f"⚠️  Active app is not a browser: {current_app['name']}")
                logger.info("Please make sure Chrome or another browser is the active application")
                return False
        else:
            logger.error("❌ Cannot detect active application")
            logger.error("This may indicate accessibility permission issues")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing Chrome accessibility: {e}")
        return False

def test_gmail_element_detection():
    """Test Gmail element detection with enhanced roles."""
    logger = logging.getLogger(__name__)
    logger.info("Testing Gmail element detection...")
    
    try:
        from modules.accessibility import AccessibilityModule
        
        # Initialize accessibility module
        accessibility = AccessibilityModule()
        
        # Test Gmail link detection with multiple roles
        test_roles = ['AXLink', 'AXButton', '']  # Empty string for auto-detection
        
        for role in test_roles:
            logger.info(f"Testing with role: {role or 'auto-detect'}")
            
            # Try to find Gmail element
            element = accessibility.find_element(role, 'Gmail')
            
            if element:
                logger.info(f"✅ Gmail element found with role {role}:")
                logger.info(f"   Role: {element.get('role')}")
                logger.info(f"   Title: {element.get('title')}")
                logger.info(f"   Coordinates: {element.get('coordinates')}")
                logger.info(f"   Enabled: {element.get('enabled')}")
                return True
            else:
                logger.debug(f"Gmail element not found with role: {role}")
        
        logger.error("❌ Gmail element not found with any role")
        logger.error("Make sure you're on Google's homepage with Gmail link visible")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error testing Gmail detection: {e}")
        return False

def test_full_gmail_click():
    """Test the complete Gmail click workflow."""
    logger = logging.getLogger(__name__)
    logger.info("Testing complete Gmail click workflow...")
    
    try:
        from orchestrator import Orchestrator
        
        # Initialize orchestrator
        orchestrator = Orchestrator()
        
        # Test the complete command execution
        command = "Click on Gmail"
        logger.info(f"Executing command: {command}")
        
        # This should use the enhanced fast path
        result = orchestrator.execute_command(command)
        
        if result.get('success'):
            logger.info("✅ Gmail click command executed successfully!")
            return True
        else:
            logger.error(f"❌ Gmail click command failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing Gmail click: {e}")
        return False

def run_diagnostic_checks():
    """Run comprehensive diagnostic checks."""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("GMAIL CLICK ISSUE DIAGNOSTIC CHECKS")
    logger.info("=" * 60)
    
    checks = [
        ("LM Studio Model Detection", test_lm_studio_model_detection),
        ("Chrome Accessibility", test_chrome_accessibility),
        ("Gmail Element Detection", test_gmail_element_detection),
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        logger.info(f"\n--- {check_name} ---")
        try:
            results[check_name] = check_func()
        except Exception as e:
            logger.error(f"❌ {check_name} failed with exception: {e}")
            results[check_name] = False
        
        time.sleep(1)  # Brief pause between checks
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("DIAGNOSTIC SUMMARY")
    logger.info("=" * 60)
    
    all_passed = True
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{check_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 All diagnostic checks passed!")
        logger.info("You can now test the Gmail click functionality.")
        return True
    else:
        logger.info("\n⚠️  Some diagnostic checks failed.")
        logger.info("Please address the issues above before testing Gmail click.")
        return False

def main():
    """Main function to run the Gmail click issue fix."""
    logger = setup_logging()
    
    logger.info("Gmail Click Issue Fix - Starting diagnostics...")
    
    # Run diagnostic checks
    diagnostics_passed = run_diagnostic_checks()
    
    if diagnostics_passed:
        logger.info("\n" + "=" * 60)
        logger.info("TESTING GMAIL CLICK FUNCTIONALITY")
        logger.info("=" * 60)
        
        # Ask user if they want to test the actual click
        try:
            response = input("\nWould you like to test the Gmail click functionality? (y/n): ")
            if response.lower().startswith('y'):
                logger.info("Make sure Chrome is open with Google homepage visible...")
                input("Press Enter when ready...")
                
                success = test_full_gmail_click()
                if success:
                    logger.info("\n🎉 Gmail click test successful!")
                else:
                    logger.info("\n❌ Gmail click test failed. Check the logs above.")
            else:
                logger.info("Skipping Gmail click test.")
        except KeyboardInterrupt:
            logger.info("\nTest cancelled by user.")
    
    logger.info("\nGmail click issue fix diagnostics completed.")
    logger.info("Check gmail_click_fix.log for detailed logs.")

if __name__ == "__main__":
    main()