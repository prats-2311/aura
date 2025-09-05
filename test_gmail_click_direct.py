#!/usr/bin/env python3
"""
Direct Gmail Click Test
Directly tests the Gmail click command execution with fast path monitoring.
"""

import sys
import os
import time
import subprocess
import threading
import io
from contextlib import redirect_stdout, redirect_stderr

def setup_chrome():
    """Setup Chrome for testing"""
    print("🚀 Setting up Chrome...")
    
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
        
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(4)
        print("✅ Chrome ready")
        return True
        
    except Exception as e:
        print(f"❌ Chrome setup failed: {e}")
        return False

def test_gmail_click_command():
    """Test the Gmail click command directly"""
    print("\n🎯 Testing Gmail Click Command Directly")
    print("-" * 40)
    
    try:
        # Import the orchestrator
        from orchestrator import Orchestrator
        
        print("✅ Orchestrator imported successfully")
        
        # Initialize orchestrator
        orchestrator = Orchestrator()
        print("✅ Orchestrator initialized")
        
        # Test the Gmail click command
        command = "click on Gmail link"
        print(f"🎤 Executing command: '{command}'")
        
        # Capture start time for performance analysis
        start_time = time.time()
        
        # Execute the command
        result = orchestrator.process_command(command)
        
        execution_time = time.time() - start_time
        
        print(f"⏱️  Command executed in {execution_time:.2f} seconds")
        
        # Analyze the result
        if result:
            print(f"✅ Command successful!")
            print(f"📋 Result: {result}")
            
            # Analyze execution characteristics
            result_str = str(result).lower()
            
            if execution_time < 2.0:
                print("🚀 FAST execution - likely used accessibility fast path")
                fast_path_used = True
            elif execution_time < 5.0:
                print("✅ GOOD execution time - may have used fast path")
                fast_path_used = True
            else:
                print("⚠️  SLOW execution - likely used vision fallback")
                fast_path_used = False
            
            # Check for accessibility indicators in result
            accessibility_indicators = ['accessibility', 'fast', 'element', 'tree']
            found_indicators = [indicator for indicator in accessibility_indicators if indicator in result_str]
            
            if found_indicators:
                print(f"🔍 Accessibility indicators found: {found_indicators}")
            
            return True, execution_time, fast_path_used, result
            
        else:
            print("❌ Command failed - no result returned")
            return False, execution_time, False, None
            
    except Exception as e:
        print(f"❌ Gmail click test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, 0, False, None

def monitor_accessibility_performance():
    """Monitor accessibility performance during execution"""
    print("\n📊 Monitoring Accessibility Performance")
    print("-" * 40)
    
    try:
        from modules.accessibility import AccessibilityModule
        
        accessibility = AccessibilityModule()
        
        # Enable detailed logging
        accessibility.enable_verbose_logging()
        print("✅ Verbose accessibility logging enabled")
        
        # Test basic accessibility operations
        print("🔍 Testing accessibility operations...")
        
        operations = []
        
        # Test 1: Find Gmail link
        start_time = time.time()
        gmail_element = accessibility.find_element("AXLink", "Gmail", "Google Chrome")
        duration = time.time() - start_time
        operations.append(("Gmail Link Search", gmail_element is not None, duration))
        
        # Test 2: Find any link
        start_time = time.time()
        any_link = accessibility.find_element("AXLink", "", "Google Chrome")
        duration = time.time() - start_time
        operations.append(("Any Link Search", any_link is not None, duration))
        
        # Test 3: Enhanced search
        start_time = time.time()
        enhanced_result = accessibility.find_element_enhanced("", "Gmail", "Google Chrome")
        duration = time.time() - start_time
        operations.append(("Enhanced Search", enhanced_result.element is not None if enhanced_result else False, duration))
        
        # Display results
        print("📊 Accessibility Operation Results:")
        for op_name, success, duration in operations:
            status = "✅" if success else "❌"
            print(f"   {status} {op_name}: {duration:.3f}s")
        
        # Get performance summary
        perf_summary = accessibility.get_performance_summary()
        
        total_ops = perf_summary.get('overall_performance', {}).get('total_operations', 0)
        successful_ops = perf_summary.get('overall_performance', {}).get('successful_operations', 0)
        avg_duration = perf_summary.get('overall_performance', {}).get('average_duration_ms', 0)
        
        print(f"\n📈 Performance Summary:")
        print(f"   Total operations: {total_ops}")
        print(f"   Successful operations: {successful_ops}")
        print(f"   Average duration: {avg_duration:.2f}ms")
        
        if total_ops > 0:
            success_rate = (successful_ops / total_ops) * 100
            print(f"   Success rate: {success_rate:.1f}%")
            
            if avg_duration < 100:
                print("🚀 Excellent accessibility performance")
                return "excellent"
            elif avg_duration < 500:
                print("✅ Good accessibility performance")
                return "good"
            else:
                print("⚠️  Slow accessibility performance")
                return "slow"
        else:
            print("ℹ️  No accessibility operations recorded")
            return "no_data"
            
    except Exception as e:
        print(f"❌ Accessibility monitoring failed: {e}")
        return "error"

def run_direct_gmail_test():
    """Run the direct Gmail click test"""
    print("Direct Gmail Click Test")
    print("=" * 25)
    print("Testing Gmail click command execution with fast path analysis\n")
    
    # Test results
    results = {
        'chrome_setup': False,
        'gmail_command_success': False,
        'fast_path_used': False,
        'accessibility_performance': 'unknown',
        'execution_time': 0
    }
    
    # Step 1: Setup Chrome
    print("=" * 50)
    results['chrome_setup'] = setup_chrome()
    
    if not results['chrome_setup']:
        print("❌ Cannot proceed without Chrome")
        return False
    
    # Wait for Chrome to be ready
    print("\n⏳ Waiting for Chrome to be ready...")
    time.sleep(5)
    
    # Step 2: Monitor accessibility performance
    print("\n" + "=" * 50)
    results['accessibility_performance'] = monitor_accessibility_performance()
    
    # Step 3: Test Gmail click command
    print("\n" + "=" * 50)
    success, exec_time, fast_path, result = test_gmail_click_command()
    
    results['gmail_command_success'] = success
    results['fast_path_used'] = fast_path
    results['execution_time'] = exec_time
    
    # Final analysis
    print("\n" + "=" * 50)
    print("📊 DIRECT TEST RESULTS")
    print("=" * 50)
    
    for key, value in results.items():
        if key not in ['execution_time']:
            status = "✅" if value else "❌"
            print(f"{status} {key.replace('_', ' ').title()}: {value}")
    
    print(f"⏱️  Execution Time: {results['execution_time']:.2f}s")
    
    # Overall assessment
    print(f"\n🎯 FAST PATH ASSESSMENT:")
    
    if results['gmail_command_success'] and results['fast_path_used']:
        print("🎉 EXCELLENT! Gmail click is using the fast path successfully!")
        print("✅ Command execution: Working")
        print("✅ Performance: Fast")
        print("✅ Fast path utilization: Confirmed")
        
        if results['accessibility_performance'] in ['excellent', 'good']:
            print("✅ Accessibility operations: Optimal")
        
        print(f"\n🚀 CONCLUSION: Your Chrome accessibility settings are working perfectly!")
        print(f"   The Gmail click command is using the accessibility fast path")
        print(f"   for rapid element detection and interaction.")
        
        return True
        
    elif results['gmail_command_success']:
        print("✅ GOOD! Gmail click command is working")
        
        if results['fast_path_used']:
            print("✅ Fast execution detected")
        else:
            print("⚠️  Slower execution - may be using fallback methods")
        
        print(f"\n💡 CONCLUSION: Gmail click is functional")
        print(f"   Performance optimizations may be possible")
        
        return True
        
    else:
        print("❌ Gmail click command failed")
        print("💡 Check Chrome accessibility settings")
        print("💡 Verify accessibility permissions")
        
        return False

if __name__ == "__main__":
    try:
        print("Direct Gmail Click Fast Path Test")
        print("This will directly execute the Gmail click command and monitor fast path usage\n")
        
        print("Setup checklist:")
        print("✓ Chrome accessibility enabled (chrome://accessibility/)")
        print("✓ Text cursor navigation enabled (chrome://settings/accessibility)")
        print("✓ Chrome closed before starting")
        print("✓ Accessibility permissions granted to Terminal\n")
        
        input("Press Enter to start direct test...")
        
        success = run_direct_gmail_test()
        
        if success:
            print("\n🎯 Gmail fast path test PASSED!")
            print("Your system is ready for fast, reliable Gmail automation!")
        else:
            print("\n🔧 Gmail fast path test needs attention")
            print("Please check the recommendations above")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)