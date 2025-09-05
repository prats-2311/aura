#!/usr/bin/env python3
"""
Final Gmail Fast Path Test
Comprehensive test of Gmail click command with fast path monitoring.
"""

import sys
import os
import time
import subprocess
import threading
import queue
from typing import Dict, Any, Optional

def setup_chrome_for_gmail():
    """Setup Chrome with Gmail page"""
    print("🚀 Setting up Chrome for Gmail test...")
    
    chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    
    if not os.path.exists(chrome_path):
        print("❌ Chrome not found")
        return False
    
    try:
        cmd = [
            chrome_path,
            '--enable-accessibility',
            '--force-renderer-accessibility',
            '--new-window',
            'https://www.google.com'
        ]
        
        print("Launching Chrome with Google homepage...")
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        time.sleep(4)
        print("✅ Chrome ready for testing")
        return True
        
    except Exception as e:
        print(f"❌ Chrome setup failed: {e}")
        return False

def monitor_accessibility_operations():
    """Monitor accessibility operations in real-time"""
    print("\n📊 Monitoring Accessibility Operations...")
    
    try:
        from modules.accessibility import AccessibilityModule
        
        accessibility = AccessibilityModule()
        accessibility.enable_verbose_logging()
        
        print("✅ Accessibility monitoring enabled")
        
        # Test basic operations
        operations_performed = []
        
        # Test 1: Look for Gmail link
        print("🔍 Testing Gmail link detection...")
        start_time = time.time()
        
        gmail_result = accessibility.find_element("AXLink", "Gmail", "Google Chrome")
        
        detection_time = time.time() - start_time
        operations_performed.append(("Gmail Link Detection", gmail_result is not None, detection_time))
        
        if gmail_result:
            print(f"✅ Gmail link found in {detection_time:.3f}s")
            print(f"   Details: {gmail_result}")
        else:
            print(f"⚠️  Gmail link not found ({detection_time:.3f}s)")
        
        # Test 2: Look for any clickable elements
        print("🔍 Testing general element detection...")
        start_time = time.time()
        
        button_result = accessibility.find_element("AXButton", "", "Google Chrome")
        
        detection_time = time.time() - start_time
        operations_performed.append(("Button Detection", button_result is not None, detection_time))
        
        if button_result:
            print(f"✅ Button found in {detection_time:.3f}s")
        else:
            print(f"⚠️  No buttons found ({detection_time:.3f}s)")
        
        # Test 3: Enhanced search
        print("🔍 Testing enhanced element search...")
        start_time = time.time()
        
        enhanced_result = accessibility.find_element_enhanced("", "Gmail", "Google Chrome")
        
        detection_time = time.time() - start_time
        operations_performed.append(("Enhanced Search", enhanced_result.element is not None if enhanced_result else False, detection_time))
        
        if enhanced_result and enhanced_result.element:
            print(f"✅ Enhanced search found element in {detection_time:.3f}s")
        else:
            print(f"⚠️  Enhanced search found nothing ({detection_time:.3f}s)")
        
        # Get performance summary
        perf_summary = accessibility.get_performance_summary()
        
        return True, operations_performed, perf_summary
        
    except Exception as e:
        print(f"❌ Accessibility monitoring failed: {e}")
        return False, [], {}

def test_orchestrator_gmail_command():
    """Test the Gmail command through the orchestrator"""
    print("\n🎯 Testing Gmail Command via Orchestrator...")
    
    try:
        from orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        print("✅ Orchestrator initialized")
        
        # Test the Gmail click command
        command = "click on Gmail link"
        print(f"🎤 Executing: '{command}'")
        
        start_time = time.time()
        
        # Process the command
        result = orchestrator.process_command(command)
        
        execution_time = time.time() - start_time
        
        print(f"⏱️  Command completed in {execution_time:.2f}s")
        
        if result:
            print(f"✅ Command result: {result}")
            
            # Analyze execution time for fast path indicators
            if execution_time < 2.0:
                print("🚀 Very fast execution - likely used accessibility fast path")
                return True, result, "fast_path"
            elif execution_time < 5.0:
                print("✅ Good execution time - may have used fast path")
                return True, result, "good"
            else:
                print("⚠️  Slower execution - likely used vision fallback")
                return True, result, "fallback"
        else:
            print("❌ No result from command")
            return False, None, "no_result"
            
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None, "error"

def analyze_fast_path_effectiveness():
    """Analyze the effectiveness of the fast path"""
    print("\n📈 Analyzing Fast Path Effectiveness...")
    
    try:
        from modules.accessibility import AccessibilityModule
        
        accessibility = AccessibilityModule()
        
        # Get detailed performance metrics
        perf_summary = accessibility.get_performance_summary()
        
        print("📊 Performance Analysis:")
        
        overall_perf = perf_summary.get('overall_performance', {})
        total_ops = overall_perf.get('total_operations', 0)
        successful_ops = overall_perf.get('successful_operations', 0)
        avg_duration = overall_perf.get('average_duration_ms', 0)
        
        print(f"   Total operations: {total_ops}")
        print(f"   Successful operations: {successful_ops}")
        print(f"   Average duration: {avg_duration:.2f}ms")
        
        if total_ops > 0:
            success_rate = (successful_ops / total_ops) * 100
            print(f"   Success rate: {success_rate:.1f}%")
            
            # Analyze cache performance
            cache_stats = perf_summary.get('cache_statistics', {})
            cache_hits = cache_stats.get('hits', 0)
            cache_misses = cache_stats.get('misses', 0)
            
            if cache_hits + cache_misses > 0:
                cache_hit_rate = (cache_hits / (cache_hits + cache_misses)) * 100
                print(f"   Cache hit rate: {cache_hit_rate:.1f}%")
            
            # Determine fast path effectiveness
            if avg_duration < 50 and success_rate > 80:
                print("🎉 EXCELLENT fast path performance!")
                return "excellent"
            elif avg_duration < 200 and success_rate > 60:
                print("✅ GOOD fast path performance")
                return "good"
            elif success_rate > 40:
                print("⚠️  MODERATE fast path performance")
                return "moderate"
            else:
                print("❌ POOR fast path performance")
                return "poor"
        else:
            print("ℹ️  No operations recorded")
            return "no_data"
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return "error"

def run_comprehensive_gmail_test():
    """Run the comprehensive Gmail fast path test"""
    print("Gmail Fast Path Comprehensive Test")
    print("=" * 40)
    print("Testing Gmail click command with detailed fast path analysis\n")
    
    # Test results tracking
    results = {
        'chrome_setup': False,
        'accessibility_monitoring': False,
        'orchestrator_test': False,
        'fast_path_analysis': 'unknown',
        'overall_performance': 'unknown'
    }
    
    # Step 1: Setup Chrome
    print("=" * 50)
    results['chrome_setup'] = setup_chrome_for_gmail()
    
    if not results['chrome_setup']:
        print("❌ Cannot proceed without Chrome")
        return False
    
    # Wait for Chrome to be ready
    print("\n⏳ Waiting for Chrome to fully load...")
    time.sleep(5)
    
    # Step 2: Monitor accessibility operations
    print("\n" + "=" * 50)
    try:
        success, operations, perf_data = monitor_accessibility_operations()
        results['accessibility_monitoring'] = success
        
        if success and operations:
            print(f"\n📊 Operation Summary:")
            for op_name, success, duration in operations:
                status = "✅" if success else "❌"
                print(f"   {status} {op_name}: {duration:.3f}s")
                
    except Exception as e:
        print(f"❌ Accessibility monitoring error: {e}")
    
    # Step 3: Test orchestrator Gmail command
    print("\n" + "=" * 50)
    try:
        success, result, performance = test_orchestrator_gmail_command()
        results['orchestrator_test'] = success
        results['overall_performance'] = performance
        
    except Exception as e:
        print(f"❌ Orchestrator test error: {e}")
    
    # Step 4: Analyze fast path effectiveness
    print("\n" + "=" * 50)
    try:
        effectiveness = analyze_fast_path_effectiveness()
        results['fast_path_analysis'] = effectiveness
        
    except Exception as e:
        print(f"❌ Fast path analysis error: {e}")
    
    # Final comprehensive summary
    print("\n" + "=" * 50)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 50)
    
    for key, value in results.items():
        if key not in ['fast_path_analysis', 'overall_performance']:
            status = "✅" if value else "❌"
            print(f"{status} {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n🎯 Fast Path Analysis: {results['fast_path_analysis']}")
    print(f"⚡ Overall Performance: {results['overall_performance']}")
    
    # Calculate overall success
    test_success = [results['chrome_setup'], results['accessibility_monitoring'], results['orchestrator_test']]
    passed = sum(test_success)
    total = len(test_success)
    percentage = (passed / total) * 100
    
    print(f"📈 Test Success Rate: {passed}/{total} ({percentage:.0f}%)")
    
    # Provide detailed analysis and recommendations
    print(f"\n🔍 DETAILED ANALYSIS:")
    
    if results['fast_path_analysis'] == 'excellent':
        print("🎉 OUTSTANDING! Your Gmail fast path is working perfectly!")
        print("✅ Accessibility tree extraction: Optimal")
        print("✅ Element detection speed: Excellent")
        print("✅ Chrome integration: Flawless")
        print("✅ Fast path utilization: Maximum")
        
    elif results['fast_path_analysis'] == 'good':
        print("✅ GREAT! Your Gmail fast path is working well!")
        print("✅ Accessibility operations are functional")
        print("✅ Performance is good")
        print("💡 Minor optimizations possible")
        
    elif results['orchestrator_test'] and results['overall_performance'] == 'fast_path':
        print("✅ GOOD! Gmail click command is working with fast path")
        print("✅ Orchestrator successfully processes commands")
        print("✅ Fast execution indicates accessibility usage")
        
    elif results['orchestrator_test']:
        print("⚠️  Gmail click command works but may not be optimized")
        print("✅ Basic functionality is working")
        print("💡 Fast path may need tuning")
        
    else:
        print("❌ Gmail fast path needs attention")
        print("💡 Check Chrome accessibility settings")
        print("💡 Verify accessibility permissions")
    
    print(f"\n📋 RECOMMENDATIONS:")
    
    if not results['accessibility_monitoring']:
        print("• Grant accessibility permissions to Terminal in System Preferences")
        print("• Restart Terminal after granting permissions")
    
    if results['fast_path_analysis'] in ['poor', 'moderate']:
        print("• Restart Chrome completely")
        print("• Re-enable 'Web accessibility' in chrome://accessibility/")
        print("• Check that 'Navigate pages with a text cursor' is enabled")
    
    if results['orchestrator_test'] and results['overall_performance'] == 'fallback':
        print("• Fast path is available but not being used optimally")
        print("• Consider optimizing element detection algorithms")
    
    # Determine overall success
    overall_success = (
        results['chrome_setup'] and 
        (results['accessibility_monitoring'] or results['orchestrator_test']) and
        results['fast_path_analysis'] not in ['poor', 'error']
    )
    
    if overall_success:
        print("\n🎯 CONCLUSION: Gmail fast path is functional and ready for use!")
    else:
        print("\n🔧 CONCLUSION: Gmail fast path needs additional configuration")
    
    return overall_success

if __name__ == "__main__":
    try:
        print("Gmail Fast Path Comprehensive Test")
        print("This will test the complete Gmail click workflow with fast path monitoring\n")
        
        print("Prerequisites:")
        print("1. Chrome accessibility enabled (chrome://accessibility/)")
        print("2. Text cursor navigation enabled (chrome://settings/accessibility)")
        print("3. Accessibility permissions granted to Terminal")
        print("4. Chrome closed before starting\n")
        
        input("Press Enter to begin comprehensive test...")
        
        success = run_comprehensive_gmail_test()
        
        if success:
            print("\n🎉 Gmail fast path is ready for production use!")
        else:
            print("\n🔧 Gmail fast path requires additional setup")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)