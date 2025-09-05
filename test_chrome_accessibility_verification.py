#!/usr/bin/env python3
"""
Chrome Accessibility Verification Test
Tests that Chrome's accessibility features are properly enabled for Aura fast path functionality.
"""

import subprocess
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import os

class ChromeAccessibilityTester:
    def __init__(self):
        self.driver = None
        self.results = {
            'accessibility_api_enabled': False,
            'web_accessibility_mode': False,
            'fast_path_compatible': False,
            'element_detection_speed': None,
            'accessibility_tree_available': False
        }
    
    def setup_chrome_with_accessibility(self):
        """Setup Chrome with accessibility features enabled"""
        chrome_options = Options()
        
        # Enable accessibility features
        chrome_options.add_argument('--enable-accessibility')
        chrome_options.add_argument('--force-renderer-accessibility')
        chrome_options.add_argument('--enable-automation')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        
        # Enable remote debugging for accessibility inspection
        chrome_options.add_argument('--remote-debugging-port=9222')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome driver initialized with accessibility features")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            return False
    
    def test_accessibility_api_connection(self):
        """Test if we can connect to Chrome's accessibility API"""
        try:
            # Try to connect to Chrome DevTools Protocol
            response = requests.get('http://localhost:9222/json', timeout=5)
            if response.status_code == 200:
                tabs = response.json()
                print(f"✅ Chrome DevTools accessible - {len(tabs)} tabs found")
                self.results['accessibility_api_enabled'] = True
                return True
        except Exception as e:
            print(f"❌ Chrome DevTools not accessible: {e}")
        
        self.results['accessibility_api_enabled'] = False
        return False
    
    def test_web_accessibility_mode(self):
        """Test if web accessibility mode is enabled"""
        if not self.driver:
            return False
        
        try:
            # Navigate to chrome://accessibility/
            self.driver.get('chrome://accessibility/')
            time.sleep(2)
            
            # Check if accessibility internals page loads
            page_source = self.driver.page_source.lower()
            
            if 'accessibility internals' in page_source:
                print("✅ Chrome accessibility internals page accessible")
                
                # Look for web accessibility indicators
                if 'web accessibility' in page_source or 'accessibility tree' in page_source:
                    print("✅ Web accessibility mode appears to be enabled")
                    self.results['web_accessibility_mode'] = True
                    return True
                else:
                    print("⚠️  Web accessibility mode may not be fully enabled")
            
        except Exception as e:
            print(f"❌ Error checking web accessibility mode: {e}")
        
        self.results['web_accessibility_mode'] = False
        return False
    
    def test_element_detection_speed(self):
        """Test fast element detection capabilities"""
        if not self.driver:
            return False
        
        try:
            # Navigate to a test page
            self.driver.get('https://www.google.com')
            
            # Measure time to detect search box
            start_time = time.time()
            
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            detection_time = time.time() - start_time
            self.results['element_detection_speed'] = detection_time
            
            if detection_time < 2.0:  # Fast detection under 2 seconds
                print(f"✅ Fast element detection: {detection_time:.2f}s")
                return True
            else:
                print(f"⚠️  Slow element detection: {detection_time:.2f}s")
                return False
                
        except Exception as e:
            print(f"❌ Element detection test failed: {e}")
            return False
    
    def test_accessibility_tree_access(self):
        """Test if accessibility tree is available"""
        if not self.driver:
            return False
        
        try:
            # Try to execute accessibility-related JavaScript
            script = """
            return {
                hasAccessibilityAPI: typeof window.getComputedAccessibleNode !== 'undefined',
                hasAriaSupport: document.querySelector('[aria-label]') !== null || 
                               document.querySelector('[role]') !== null,
                accessibilityTreeAvailable: !!document.querySelector('*[aria-*], *[role]')
            };
            """
            
            result = self.driver.execute_script(script)
            
            if result.get('hasAriaSupport') or result.get('accessibilityTreeAvailable'):
                print("✅ Accessibility tree elements detected")
                self.results['accessibility_tree_available'] = True
                return True
            else:
                print("⚠️  Limited accessibility tree access")
                
        except Exception as e:
            print(f"❌ Accessibility tree test failed: {e}")
        
        self.results['accessibility_tree_available'] = False
        return False
    
    def test_fast_path_compatibility(self):
        """Test overall fast path compatibility"""
        compatibility_score = 0
        total_tests = 4
        
        if self.results['accessibility_api_enabled']:
            compatibility_score += 1
        if self.results['web_accessibility_mode']:
            compatibility_score += 1
        if self.results['element_detection_speed'] and self.results['element_detection_speed'] < 2.0:
            compatibility_score += 1
        if self.results['accessibility_tree_available']:
            compatibility_score += 1
        
        compatibility_percentage = (compatibility_score / total_tests) * 100
        
        if compatibility_percentage >= 75:
            print(f"✅ Fast path compatibility: {compatibility_percentage:.0f}%")
            self.results['fast_path_compatible'] = True
            return True
        else:
            print(f"❌ Fast path compatibility: {compatibility_percentage:.0f}% (needs improvement)")
            self.results['fast_path_compatible'] = False
            return False
    
    def run_comprehensive_test(self):
        """Run all accessibility tests"""
        print("🔍 Starting Chrome Accessibility Verification Tests...")
        print("=" * 60)
        
        # Setup Chrome
        if not self.setup_chrome_with_accessibility():
            print("❌ Cannot proceed - Chrome setup failed")
            return False
        
        try:
            # Run individual tests
            print("\n1. Testing Accessibility API Connection...")
            self.test_accessibility_api_connection()
            
            print("\n2. Testing Web Accessibility Mode...")
            self.test_web_accessibility_mode()
            
            print("\n3. Testing Element Detection Speed...")
            self.test_element_detection_speed()
            
            print("\n4. Testing Accessibility Tree Access...")
            self.test_accessibility_tree_access()
            
            print("\n5. Evaluating Fast Path Compatibility...")
            self.test_fast_path_compatibility()
            
            # Print summary
            self.print_summary()
            
            return self.results['fast_path_compatible']
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 ACCESSIBILITY TEST RESULTS SUMMARY")
        print("=" * 60)
        
        for key, value in self.results.items():
            status = "✅" if value else "❌"
            if key == 'element_detection_speed' and value:
                print(f"{status} {key.replace('_', ' ').title()}: {value:.2f}s")
            else:
                print(f"{status} {key.replace('_', ' ').title()}: {value}")
        
        print("\n📋 RECOMMENDATIONS:")
        
        if not self.results['accessibility_api_enabled']:
            print("• Ensure Chrome is running with --remote-debugging-port=9222")
        
        if not self.results['web_accessibility_mode']:
            print("• Go to chrome://accessibility/ and enable 'Web accessibility'")
            print("• Restart Chrome after enabling")
        
        if not self.results['accessibility_tree_available']:
            print("• Test on pages with proper ARIA attributes")
            print("• Ensure accessibility features are not blocked by extensions")
        
        if self.results['fast_path_compatible']:
            print("\n🎉 Chrome is properly configured for Aura fast path functionality!")
        else:
            print("\n⚠️  Chrome needs additional configuration for optimal Aura performance")

def main():
    """Main test execution"""
    tester = ChromeAccessibilityTester()
    
    try:
        success = tester.run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()