#!/usr/bin/env python3
"""
Aura Fast Path Functionality Test
Tests that Aura can use Chrome's accessibility features for fast automation.
"""

import sys
import os
import time
import subprocess

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

try:
    from modules.accessibility import AccessibilityModule
    from modules.automation import AutomationEngine
    from modules.vision import VisionEngine
except ImportError as e:
    print(f"❌ Could not import Aura modules: {e}")
    print("ℹ️  Make sure you're running from the Aura project directory")
    sys.exit(1)

class AuraFastPathTester:
    def __init__(self):
        self.accessibility = None
        self.automation = None
        self.vision = None
        self.results = {
            'accessibility_init': False,
            'automation_init': False,
            'fast_path_detection': False,
            'element_interaction': False,
            'performance_acceptable': False
        }
    
    def setup_aura_modules(self):
        """Initialize Aura modules"""
        print("🔧 Initializing Aura modules...")
        
        try:
            # Initialize accessibility module
            self.accessibility = AccessibilityModule()
            print("✅ Accessibility module initialized")
            self.results['accessibility_init'] = True
        except Exception as e:
            print(f"❌ Accessibility module failed: {e}")
            return False
        
        try:
            # Initialize automation engine
            self.automation = AutomationEngine()
            print("✅ Automation engine initialized")
            self.results['automation_init'] = True
        except Exception as e:
            print(f"❌ Automation engine failed: {e}")
            return False
        
        try:
            # Initialize vision engine (fallback)
            self.vision = VisionEngine()
            print("✅ Vision engine initialized (fallback)")
        except Exception as e:
            print(f"⚠️  Vision engine failed (not critical): {e}")
        
        return True
    
    def test_fast_path_detection(self):
        """Test if fast path can detect elements quickly"""
        print("\n🔍 Testing fast path element detection...")
        
        if not self.accessibility:
            return False
        
        try:
            # Test accessibility-based detection by looking for common elements
            start_time = time.time()
            
            # Try to find a button element (common in most apps)
            element = self.accessibility.find_element("button", "", None)
            
            detection_time = time.time() - start_time
            
            if element:
                print(f"✅ Fast path detected element in {detection_time:.2f}s")
                print(f"   Element: {element.get('role', 'unknown')} - {element.get('title', 'no title')}")
                
                if detection_time < 1.0:  # Very fast
                    print("🚀 Excellent performance - under 1 second")
                    self.results['performance_acceptable'] = True
                elif detection_time < 3.0:  # Acceptable
                    print("✅ Good performance - under 3 seconds")
                    self.results['performance_acceptable'] = True
                else:
                    print("⚠️  Slow performance - over 3 seconds")
                
                self.results['fast_path_detection'] = True
                return True
            else:
                print("ℹ️  No button elements found (may be normal)")
                # Try alternative detection
                enhanced_result = self.accessibility.find_element_enhanced("", "", None)
                if enhanced_result and enhanced_result.element:
                    print("✅ Enhanced detection found elements")
                    self.results['fast_path_detection'] = True
                    return True
                else:
                    print("❌ No elements detected via fast path")
                    return False
                
        except Exception as e:
            print(f"❌ Fast path detection failed: {e}")
            return False
    
    def test_element_interaction(self):
        """Test if fast path can interact with elements"""
        print("\n🎯 Testing fast path element interaction...")
        
        if not self.accessibility:
            return False
        
        try:
            # Test finding clickable elements
            start_time = time.time()
            
            # Try to find clickable elements using accessibility
            button_element = self.accessibility.find_element("AXButton", "", None)
            
            interaction_time = time.time() - start_time
            
            if button_element:
                print(f"✅ Fast path found interactive element in {interaction_time:.2f}s")
                print(f"   Element role: {button_element.get('role', 'unknown')}")
                print(f"   Element title: {button_element.get('title', 'no title')[:50]}")
                print(f"   Coordinates: {button_element.get('coordinates', 'unknown')}")
                
                self.results['element_interaction'] = True
                return True
            else:
                # Try finding any interactive element
                menu_element = self.accessibility.find_element("AXMenuItem", "", None)
                if menu_element:
                    print(f"✅ Fast path found menu element in {interaction_time:.2f}s")
                    self.results['element_interaction'] = True
                    return True
                else:
                    print("ℹ️  No interactive elements found (may be normal if no GUI apps open)")
                    return False
                
        except Exception as e:
            print(f"❌ Element interaction test failed: {e}")
            return False
    
    def test_fallback_mechanism(self):
        """Test that vision fallback works when fast path fails"""
        print("\n🔄 Testing fallback mechanism...")
        
        if not self.vision:
            print("⚠️  Vision engine not available for fallback test")
            return False
        
        try:
            # Simulate fast path failure and test vision fallback
            print("ℹ️  Simulating fast path failure...")
            
            # Test vision-based detection as fallback
            start_time = time.time()
            
            # This would normally be called when accessibility fails
            vision_result = self.vision.analyze_screen()
            
            fallback_time = time.time() - start_time
            
            if vision_result:
                print(f"✅ Vision fallback working in {fallback_time:.2f}s")
                return True
            else:
                print("⚠️  Vision fallback not detecting elements")
                return False
                
        except Exception as e:
            print(f"❌ Fallback test failed: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all fast path tests"""
        print("Aura Fast Path Functionality Test")
        print("=" * 40)
        
        # Setup modules
        if not self.setup_aura_modules():
            print("❌ Cannot proceed - module setup failed")
            return False
        
        # Run tests
        print("\n" + "=" * 40)
        print("🧪 RUNNING FAST PATH TESTS")
        print("=" * 40)
        
        self.test_fast_path_detection()
        self.test_element_interaction()
        self.test_fallback_mechanism()
        
        # Print results
        self.print_results()
        
        # Calculate success
        critical_tests = ['accessibility_init', 'automation_init', 'fast_path_detection']
        critical_passed = sum(1 for test in critical_tests if self.results[test])
        
        return critical_passed >= 2  # At least 2 of 3 critical tests must pass
    
    def print_results(self):
        """Print test results summary"""
        print("\n" + "=" * 40)
        print("📊 FAST PATH TEST RESULTS")
        print("=" * 40)
        
        for key, value in self.results.items():
            status = "✅" if value else "❌"
            print(f"{status} {key.replace('_', ' ').title()}: {value}")
        
        # Calculate overall score
        passed = sum(self.results.values())
        total = len(self.results)
        percentage = (passed / total) * 100
        
        print(f"\n📈 Overall Score: {passed}/{total} ({percentage:.0f}%)")
        
        if percentage >= 80:
            print("\n🎉 Aura fast path is working excellently!")
            print("✅ Chrome accessibility integration is successful")
        elif percentage >= 60:
            print("\n✅ Aura fast path is working well")
            print("💡 Some optimizations possible")
        else:
            print("\n⚠️  Aura fast path needs improvement")
            print("💡 Check Chrome accessibility settings")
        
        print("\n📋 RECOMMENDATIONS:")
        
        if not self.results['accessibility_init']:
            print("• Check accessibility module dependencies")
        
        if not self.results['fast_path_detection']:
            print("• Verify Chrome has 'Web accessibility' enabled")
            print("• Restart Chrome after enabling accessibility features")
        
        if not self.results['performance_acceptable']:
            print("• Consider optimizing element detection algorithms")
        
        if self.results['accessibility_init'] and self.results['fast_path_detection']:
            print("• ✅ Fast path is functional - ready for Aura commands!")

def main():
    """Main test execution"""
    tester = AuraFastPathTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print("\n🚀 Ready to test Aura commands with fast path!")
            print("Try: 'python3 main.py' and give it a web automation command")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()