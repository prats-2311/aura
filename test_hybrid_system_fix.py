#!/usr/bin/env python3
"""
Test that the hybrid system now works with the accessibility fix
"""

import logging
import sys

# Set up logging to see what path is being used
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def test_hybrid_system():
    """Test that the hybrid system can use the fast path"""
    
    print("🔍 Testing Hybrid System with Accessibility Fix...")
    
    try:
        # Import the orchestrator which manages the hybrid approach
        from orchestrator import Orchestrator
        
        print("✓ Orchestrator imported successfully")
        
        # Create orchestrator instance
        orchestrator = Orchestrator()
        print("✓ Orchestrator initialized")
        
        # Check accessibility module status
        if hasattr(orchestrator, 'accessibility_module') and orchestrator.accessibility_module:
            status = orchestrator.accessibility_module.get_accessibility_status()
            print(f"\n📊 Accessibility Status:")
            print(f"   API Initialized: {status.get('api_initialized', False)}")
            print(f"   Degraded Mode: {status.get('degraded_mode', True)}")
            print(f"   Frameworks Available: {status.get('frameworks_available', False)}")
            
            if status.get('api_initialized', False) and not status.get('degraded_mode', True):
                print("✅ Accessibility API is working! Hybrid system should use fast path.")
                return True
            else:
                print("⚠ Accessibility API not fully functional, will use vision fallback")
                return False
        else:
            print("✗ No accessibility_module found in orchestrator")
            return False
            
    except Exception as e:
        print(f"✗ Error testing hybrid system: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_accessibility_module_directly():
    """Test the accessibility module directly"""
    
    print("\n🔍 Testing AccessibilityModule directly...")
    
    try:
        from modules.accessibility import AccessibilityModule
        
        accessibility = AccessibilityModule()
        
        # Check if it's working
        if accessibility.is_accessibility_enabled():
            print("✅ AccessibilityModule is enabled and functional!")
            
            # Try to get active application
            app = accessibility.get_active_application()
            if app:
                print(f"✅ Successfully got active application: {app['name']}")
                return True
            else:
                print("⚠ Could not get active application")
                return False
        else:
            print("❌ AccessibilityModule is not enabled")
            return False
            
    except Exception as e:
        print(f"✗ Error testing accessibility module: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing AURA Hybrid System Fix\n")
    
    # Test accessibility module directly first
    accessibility_works = test_accessibility_module_directly()
    
    # Test hybrid system
    hybrid_works = test_hybrid_system()
    
    print(f"\n📋 Summary:")
    print(f"   Accessibility Module: {'✅ Working' if accessibility_works else '❌ Not Working'}")
    print(f"   Hybrid System: {'✅ Working' if hybrid_works else '❌ Not Working'}")
    
    if accessibility_works and hybrid_works:
        print(f"\n🎉 SUCCESS: The hybrid system should now use the fast accessibility path!")
        print(f"   Commands will be processed quickly without needing vision models.")
    elif accessibility_works:
        print(f"\n⚠ PARTIAL: Accessibility works but hybrid system needs checking.")
    else:
        print(f"\n❌ ISSUE: Accessibility module still not working properly.")
    
    sys.exit(0 if (accessibility_works and hybrid_works) else 1)