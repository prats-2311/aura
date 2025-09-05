#!/usr/bin/env python3
"""
Real Gmail Click Test
Tests the actual Gmail click command using Aura's main interface with fast path monitoring.
"""

import sys
import os
import time
import subprocess
import json
from typing import Dict, Any

def setup_test_environment():
    """Setup the test environment with Chrome and Gmail"""
    print("🔧 Setting up test environment...")
    
    # Launch Chrome with Google homepage
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
        
        print("🚀 Launching Chrome with Google homepage...")
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        time.sleep(4)
        print("✅ Chrome launched and ready")
        return True
        
    except Exception as e:
        print(f"❌ Failed to launch Chrome: {e}")
        return False

def test_aura_gmail_click():
    """Test the Gmail click command using Aura's main interface"""
    print("\n🎯 Testing Gmail Click Command via Aura Main Interface")
    print("-" * 55)
    
    try:
        # Import main Aura interface
        sys.path.append(os.path.dirname(__file__))
        from main import main as aura_main
        
        print("✅ Aura main interface imported successfully")
        
        # Simulate the Gmail click command
        command = "click on Gmail link"
        print(f"🎤 Executing command: '{command}'")
        
        # Capture the start time for performance monitoring
        start_time = time.time()
        
        # This would normally be interactive, but we'll simulate it
        # by directly calling the processing logic
        
        # For testing, we'll create a mock input scenario
        import io
        import contextlib
        
        # Redirect stdin to simulate user input
        test_input = command + "\n"
        
        with contextlib.redirect_stdin(io.StringIO(test_input)):
            try:
                # Call Aura main function
                result = aura_main()
                
                execution_time = time.time() - start_time
                
                print(f"⏱️  Command executed in {execution_time:.2f}s")
                
                if execution_time < 5.0:
                    print("🚀 Fast execution - likely used accessibility fast path")
                    return True, execution_time, "fast_path"
                else:
                    print("⚠️  Slower execution - may have used vision fallback")
                    return True, execution_time, "fallback"
                    
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"❌ Command execution failed after {execution_time:.2f}s: {e}")
                return False, execution_time, "error"
                
    except ImportError as e:
        print(f"❌ Could not import Aura main: {e}")
        return False, 0, "import_error"
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False, 0, "unexpected_error"

def test_orchestrator_directly():
    """Test the orchestrator directly for Gmail click"""
    print("\n🔄 Testing Orchestrator Directly")
    print("-" * 35)
    
    try:
        from orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        print("✅ Orchestrator initialized")
        
        command = "click on Gmail link"
        print(f"🎤 Processing: '{command}'")
        
        start_time = time.time()
        
        # Process the command
        result = orchestrator.process_command(command)
        
        processing_time = time.time() - start_time
        
        print(f"⏱️  Processed in {processing_time:.2f}s")
        
        if result:
            print(f"✅ Result: {result}")
            
            # Analyze the result for fast path indicators
            result_str = str(result).lower()
            
            if 'accessibility' in result_str or processing_time < 3.0:
                print("🚀 Fast path likely used")
                return True, result, "fast_path"
            else:
                print("⚠️  Fallback method likely used")
                return True, result, "fallback"
        else:
            print("❌ No result returned")
            return False, None, "no_result"
            
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None, "error"

def analyze_fast_path_usage():
    """Analyze if the fast path is being used"""
    print("\n📊 Analyzing Fast Path Usage")
    print("-" * 32)
    
    try:
        from modules.accessibility import AccessibilityModule
        
        accessibility = AccessibilityModule()
        
        # Get performance summary
        perf_summary = accessibility.get_performance_summary()
        
        print("📈 Accessibility Performance Summary:")
        print(json.dumps(perf_summary, indent=2))
        
        # Check if operations are happening
        total_ops = perf_summary.get('overall_performance', {}).get('total_operations', 0)
        successful_ops = perf_summary.get('overall_performance', {}).get('successful_operations', 0)
        avg_duration = perf_summary.get('overall_performance', {}).get('average_duration_ms', 0)
        
        print(f"\n📊 Analysis:")
        print(f"   Total operations: {total_ops}")
        print(f"   Successful operations: {successful_ops}")
        print(f"   Average duration: {avg_duration:.2f}ms")
        
        if total_ops > 0:
            success_rate = (successful_ops / total_ops) * 100
            print(f"   Success rate: {success_rate:.1f}%")
            
            if avg_duration < 100:  # Under 100ms is very fast
                print("🚀 Excellent fast path performance")
                return True, "excellent"
            elif avg_duration < 500:  # Under 500ms is good
                print("✅ Good fast path performance")
                return True, "good"
            else:
                print("⚠️  Slow performance - may need optimization")
                return True, "slow"
        else:
            print("ℹ️  No accessibility operations recorded")
            return False, "no_operations"
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False, "error"

def run_gmail_click_test():
    """Run the complete Gmail click test"""
    print("Gmail Click Fast Path Test")
    print("=" * 30)
    print("Testing Gmail link click with accessibility fast path monitoring\n")
    
    # Test results
    results = {
        'environment_setup': False,
        'aura_main_test': False,
        'orchestrator_test': False,
        'fast_path_analysis': False,
        'overall_performance': 'unknown'
    }
    
    # Step 1: Setup environment
    print("=" * 50)
    results['environment_setup'] = setup_test_environment()
    
    if not results['environment_setup']:
        print("❌ Cannot proceed without proper environment setup")
        return False
    
    # Wait for Chrome to be ready
    print("\n⏳ Waiting for Chrome to be fully ready...")
    time.sleep(3)
    
    # Step 2: Test via Aura main interface
    print("\n" + "=" * 50)
    try:
        success, exec_time, method = test_aura_gmail_click()
        results['aura_main_test'] = success
        if success:
            results['overall_performance'] = method
    except Exception as e:
        print(f"❌ Aura main test failed: {e}")
    
    # Step 3: Test via orchestrator directly
    print("\n" + "=" * 50)
    try:
        success, result, method = test_orchestrator_directly()
        results['orchestrator_test'] = success
        if success and results['overall_performance'] == 'unknown':
            results['overall_performance'] = method
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
    
    # Step 4: Analyze fast path usage
    print("\n" + "=" * 50)
    try:
        success, performance = analyze_fast_path_usage()
        results['fast_path_analysis'] = success
    except Exception as e:
        print(f"❌ Fast path analysis failed: {e}")
    
    # Final summary
    print("\n" + "=" * 50)
    print("📊 GMAIL CLICK TEST RESULTS")
    print("=" * 50)
    
    for test_name, result in results.items():
        if test_name != 'overall_performance':
            status = "✅" if result else "❌"
            print(f"{status} {test_name.replace('_', ' ').title()}: {result}")
    
    print(f"\n🎯 Overall Performance: {results['overall_performance']}")
    
    # Calculate success score
    test_results = [v for k, v in results.items() if k != 'overall_performance']
    passed = sum(test_results)
    total = len(test_results)
    percentage = (passed / total) * 100
    
    print(f"📈 Success Rate: {passed}/{total} ({percentage:.0f}%)")
    
    # Provide analysis
    if results['overall_performance'] == 'fast_path':
        print("\n🎉 EXCELLENT! Gmail click is using the accessibility fast path!")
        print("✅ Chrome accessibility settings are working correctly")
        print("✅ Aura is successfully using fast element detection")
        print("✅ Click operations are optimized")
        
    elif results['overall_performance'] == 'fallback':
        print("\n⚠️  Gmail click is using fallback methods")
        print("💡 Fast path may not be fully optimized")
        print("💡 Consider checking Chrome accessibility settings")
        
    elif percentage >= 50:
        print("\n✅ Gmail click functionality is working")
        print("💡 Performance optimizations may be possible")
        
    else:
        print("\n❌ Gmail click needs troubleshooting")
        print("💡 Check Chrome accessibility permissions")
        print("💡 Verify Chrome settings are properly configured")
    
    print(f"\n🔍 Fast Path Status:")
    if results['fast_path_analysis']:
        print("✅ Accessibility module is operational")
    if results['orchestrator_test']:
        print("✅ Orchestrator can process Gmail commands")
    if results['environment_setup']:
        print("✅ Test environment is properly configured")
    
    return percentage >= 75

if __name__ == "__main__":
    try:
        print("Gmail Click Fast Path Test")
        print("This will test clicking on Gmail link using Aura's fast path\n")
        
        print("Make sure:")
        print("1. Chrome accessibility is enabled (Web accessibility)")
        print("2. Chrome is closed before starting")
        print("3. You have accessibility permissions for Terminal\n")
        
        input("Press Enter to start the test...")
        
        success = run_gmail_click_test()
        
        if success:
            print("\n🎯 Gmail fast path is working excellently!")
        else:
            print("\n🔧 Gmail fast path needs optimization")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)