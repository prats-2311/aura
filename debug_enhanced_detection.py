#!/usr/bin/env python3
"""
Debug script to check why enhanced role detection is failing.
"""

import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def debug_enhanced_detection():
    """Debug the enhanced role detection availability."""
    
    try:
        from modules.accessibility import AccessibilityModule
        
        print("Debugging enhanced role detection...")
        
        # Initialize the module
        accessibility = AccessibilityModule()
        
        # Check class attribute
        print(f"Class CLICKABLE_ROLES: {hasattr(AccessibilityModule, 'CLICKABLE_ROLES')}")
        if hasattr(AccessibilityModule, 'CLICKABLE_ROLES'):
            print(f"  Value: {AccessibilityModule.CLICKABLE_ROLES}")
        
        # Check instance attribute
        print(f"Instance CLICKABLE_ROLES: {hasattr(accessibility, 'CLICKABLE_ROLES')}")
        if hasattr(accessibility, 'CLICKABLE_ROLES'):
            print(f"  Value: {accessibility.CLICKABLE_ROLES}")
        
        # Check clickable_roles (from config)
        print(f"Instance clickable_roles: {hasattr(accessibility, 'clickable_roles')}")
        if hasattr(accessibility, 'clickable_roles'):
            print(f"  Value: {accessibility.clickable_roles}")
        
        # Check method availability
        print(f"is_clickable_element_role method: {hasattr(accessibility, 'is_clickable_element_role')}")
        
        # Test the availability check step by step
        print("\nTesting is_enhanced_role_detection_available() step by step:")
        
        try:
            # Check if clickable_roles instance attribute or class constant is available
            clickable_roles = getattr(accessibility, 'clickable_roles', None)
            print(f"1. getattr(self, 'clickable_roles', None): {clickable_roles}")
            
            if not clickable_roles:
                try:
                    clickable_roles = accessibility.CLICKABLE_ROLES
                    print(f"2. self.CLICKABLE_ROLES: {clickable_roles}")
                except AttributeError as e:
                    print(f"2. self.CLICKABLE_ROLES failed: {e}")
                    return False
            
            if not clickable_roles:
                print("3. No clickable_roles found")
                return False
            else:
                print(f"3. clickable_roles found: {len(clickable_roles)} roles")
            
            # Check if enhanced methods are available
            if not hasattr(accessibility, 'is_clickable_element_role'):
                print("4. is_clickable_element_role method not found")
                return False
            else:
                print("4. is_clickable_element_role method found")
            
            print("5. All checks passed - should return True")
            return True
            
        except Exception as e:
            print(f"Exception in availability check: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Now test the actual method
        actual_result = accessibility.is_enhanced_role_detection_available()
        print(f"\nActual is_enhanced_role_detection_available(): {actual_result}")
        
        if not actual_result:
            print("❌ Method returned False - there's still an issue!")
        else:
            print("✅ Method returned True - should be working!")
        
        # Test role detection
        print(f"\nTesting role detection:")
        print(f"AXButton clickable: {accessibility.is_clickable_element_role('AXButton')}")
        print(f"AXLink clickable: {accessibility.is_clickable_element_role('AXLink')}")
        
        return actual_result
        
    except Exception as e:
        print(f"Error debugging enhanced detection: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_enhanced_detection()