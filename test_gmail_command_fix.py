#!/usr/bin/env python3
"""
Test script to verify that the "click on the gmail link" command will now work with fast path.
"""

import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)

def test_gmail_command_processing():
    """Test the complete command processing pipeline for Gmail link clicking."""
    
    try:
        from modules.accessibility import AccessibilityModule
        from orchestrator import Orchestrator
        
        print("Testing Gmail command processing pipeline...")
        
        # Test 1: Verify accessibility module can detect links
        print("\n1. Testing AccessibilityModule link detection:")
        accessibility = AccessibilityModule()
        
        # Check that enhanced role detection is available
        enhanced_available = accessibility.is_enhanced_role_detection_available()
        print(f"   Enhanced role detection available: {enhanced_available}")
        
        if not enhanced_available:
            print("   ❌ Enhanced role detection not available!")
            return False
        
        # Check that AXLink is considered clickable
        link_clickable = accessibility.is_clickable_element_role('AXLink')
        print(f"   AXLink is clickable: {link_clickable}")
        
        if not link_clickable:
            print("   ❌ AXLink not considered clickable!")
            return False
        
        print("   ✅ AccessibilityModule can detect links")
        
        # Test 2: Test command validation and normalization
        print("\n2. Testing command validation:")
        orchestrator = Orchestrator()
        
        test_command = "Click on the Gmail link."
        validation_result = orchestrator.validate_command(test_command)
        
        print(f"   Original command: '{test_command}'")
        print(f"   Normalized command: '{validation_result.normalized_command}'")
        print(f"   Command type: {validation_result.command_type}")
        print(f"   Valid: {validation_result.is_valid}")
        
        if not validation_result.is_valid:
            print("   ❌ Command validation failed!")
            return False
        
        if validation_result.command_type != 'click':
            print("   ❌ Command not recognized as click command!")
            return False
        
        print("   ✅ Command validation successful")
        
        # Test 3: Test GUI element extraction
        print("\n3. Testing GUI element extraction:")
        gui_elements = orchestrator._extract_gui_elements_from_command(validation_result.normalized_command)
        
        print(f"   Extracted elements: {gui_elements}")
        
        if not gui_elements:
            print("   ❌ No GUI elements extracted!")
            return False
        
        # Should extract something like {'role': '', 'label': 'gmail link'}
        expected_in_label = 'gmail'
        if isinstance(gui_elements, dict):
            # Single element returned as dict
            label = gui_elements.get('label', '').lower()
            found_gmail = 'gmail' in label
        else:
            # Multiple elements returned as list
            found_gmail = any('gmail' in str(element.get('label', '')).lower() for element in gui_elements)
        
        if not found_gmail:
            print("   ❌ Gmail not found in extracted elements!")
            return False
        
        print("   ✅ GUI element extraction successful")
        
        # Test 4: Verify the fast path would be attempted
        print("\n4. Testing fast path eligibility:")
        
        # Check if the command would trigger fast path
        is_gui_command = any(validation_result.command_type == cmd_type for cmd_type in ['click', 'type', 'scroll'])
        fast_path_enabled = orchestrator.fast_path_enabled
        accessibility_available = orchestrator.module_availability.get('accessibility', False)
        
        print(f"   Is GUI command: {is_gui_command}")
        print(f"   Fast path enabled: {fast_path_enabled}")
        print(f"   Accessibility available: {accessibility_available}")
        
        if not (is_gui_command and fast_path_enabled and accessibility_available):
            print("   ❌ Fast path would not be attempted!")
            return False
        
        print("   ✅ Fast path would be attempted")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("The 'click on the gmail link' command should now work with fast path!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Gmail command processing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_target_extraction():
    """Test that target extraction works correctly for Gmail link commands."""
    
    try:
        from orchestrator import Orchestrator
        
        print("\nTesting target extraction for Gmail commands...")
        
        orchestrator = Orchestrator()
        
        test_commands = [
            "Click on the Gmail link.",
            "click on gmail link",
            "Click the Gmail link",
            "press the gmail link",
            "tap on gmail"
        ]
        
        for command in test_commands:
            print(f"\n   Testing: '{command}'")
            
            # Validate and normalize
            validation = orchestrator.validate_command(command)
            normalized = validation.normalized_command
            print(f"   Normalized: '{normalized}'")
            
            # Extract GUI elements
            elements = orchestrator._extract_gui_elements_from_command(normalized)
            print(f"   Extracted elements: {elements}")
            
            # Check if gmail is in the extracted label
            if elements:
                if isinstance(elements, dict):
                    # Single element returned as dict
                    label = elements.get('label', '').lower()
                else:
                    # Multiple elements returned as list
                    label = elements[0].get('label', '').lower()
                
                if 'gmail' in label:
                    print(f"   ✅ Gmail found in label: '{label}'")
                else:
                    print(f"   ❌ Gmail not found in label: '{label}'")
                    return False
            else:
                print("   ❌ No elements extracted!")
                return False
        
        print("\n✅ Target extraction tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing target extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("GMAIL COMMAND FAST PATH FIX VERIFICATION")
    print("=" * 70)
    
    success = True
    
    # Test the complete command processing pipeline
    if not test_gmail_command_processing():
        success = False
    
    # Test target extraction specifically
    if not test_target_extraction():
        success = False
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("The 'click on the gmail link' command should now work via fast path!")
        print("The accessibility module can now detect AXLink elements.")
        print("Enhanced role detection is working correctly.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("The fix may not be complete or there are other issues.")
    print("=" * 70)
    
    sys.exit(0 if success else 1)