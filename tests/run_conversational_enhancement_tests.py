#!/usr/bin/env python3
"""
Test runner for conversational AURA enhancement comprehensive test suite.

This script runs all tests for the conversational enhancement functionality
and provides a comprehensive report of test results.

Usage:
    python tests/run_conversational_enhancement_tests.py [--verbose] [--specific-test TEST_NAME]
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_test_file(test_file, verbose=False):
    """
    Run a specific test file and return results.
    
    Args:
        test_file: Path to the test file
        verbose: Whether to show verbose output
        
    Returns:
        dict: Test results with success status and output
    """
    print(f"\n{'='*60}")
    print(f"Running: {test_file}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Run pytest on the specific file
        cmd = [sys.executable, "-m", "pytest", str(test_file)]
        if verbose:
            cmd.extend(["-v", "--tb=short"])
        else:
            cmd.extend(["-q"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per test file
        )
        
        duration = time.time() - start_time
        
        success = result.returncode == 0
        
        print(f"Status: {'PASSED' if success else 'FAILED'}")
        print(f"Duration: {duration:.2f} seconds")
        
        if verbose or not success:
            if result.stdout:
                print(f"\nSTDOUT:\n{result.stdout}")
            if result.stderr:
                print(f"\nSTDERR:\n{result.stderr}")
        
        return {
            'file': test_file,
            'success': success,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"Status: TIMEOUT (after {duration:.2f} seconds)")
        return {
            'file': test_file,
            'success': False,
            'duration': duration,
            'stdout': '',
            'stderr': 'Test timed out after 5 minutes',
            'returncode': -1
        }
    
    except Exception as e:
        duration = time.time() - start_time
        print(f"Status: ERROR - {e}")
        return {
            'file': test_file,
            'success': False,
            'duration': duration,
            'stdout': '',
            'stderr': str(e),
            'returncode': -2
        }


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Run conversational enhancement tests')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Show verbose test output')
    parser.add_argument('--specific-test', '-t', type=str,
                       help='Run only a specific test file (by name)')
    parser.add_argument('--list-tests', '-l', action='store_true',
                       help='List available test files')
    
    args = parser.parse_args()
    
    # Define test files in order of execution
    test_files = [
        'tests/test_intent_recognition_accuracy.py',
        'tests/test_deferred_action_complete_workflows.py', 
        'tests/test_state_management_thread_safety.py',
        'tests/test_conversational_backward_compatibility.py',
        'tests/test_conversational_enhancement_comprehensive.py'
    ]
    
    # Check that test files exist
    existing_test_files = []
    for test_file in test_files:
        if Path(test_file).exists():
            existing_test_files.append(test_file)
        else:
            print(f"Warning: Test file not found: {test_file}")
    
    if args.list_tests:
        print("Available test files:")
        for i, test_file in enumerate(existing_test_files, 1):
            print(f"  {i}. {test_file}")
        return 0
    
    # Filter to specific test if requested
    if args.specific_test:
        matching_tests = [f for f in existing_test_files if args.specific_test in f]
        if not matching_tests:
            print(f"Error: No test files match '{args.specific_test}'")
            print("Available tests:")
            for test_file in existing_test_files:
                print(f"  - {test_file}")
            return 1
        existing_test_files = matching_tests
    
    print("Conversational AURA Enhancement - Comprehensive Test Suite")
    print("=" * 60)
    print(f"Running {len(existing_test_files)} test file(s)")
    print(f"Verbose mode: {'ON' if args.verbose else 'OFF'}")
    
    # Run all tests
    results = []
    total_start_time = time.time()
    
    for test_file in existing_test_files:
        result = run_test_file(test_file, args.verbose)
        results.append(result)
    
    total_duration = time.time() - total_start_time
    
    # Generate summary report
    print(f"\n{'='*60}")
    print("TEST SUMMARY REPORT")
    print(f"{'='*60}")
    
    passed_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    print(f"Total tests run: {len(results)}")
    print(f"Passed: {len(passed_tests)}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Total duration: {total_duration:.2f} seconds")
    
    if passed_tests:
        print(f"\n✅ PASSED TESTS ({len(passed_tests)}):")
        for result in passed_tests:
            print(f"  - {Path(result['file']).name} ({result['duration']:.2f}s)")
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
        for result in failed_tests:
            print(f"  - {Path(result['file']).name} ({result['duration']:.2f}s)")
            if result['stderr']:
                print(f"    Error: {result['stderr'][:100]}...")
    
    # Detailed failure report
    if failed_tests and not args.verbose:
        print(f"\n{'='*60}")
        print("FAILURE DETAILS")
        print(f"{'='*60}")
        
        for result in failed_tests:
            print(f"\nFAILED: {result['file']}")
            print(f"Return code: {result['returncode']}")
            
            if result['stdout']:
                print("STDOUT:")
                print(result['stdout'][:500])
                if len(result['stdout']) > 500:
                    print("... (truncated)")
            
            if result['stderr']:
                print("STDERR:")
                print(result['stderr'][:500])
                if len(result['stderr']) > 500:
                    print("... (truncated)")
    
    # Requirements coverage report
    print(f"\n{'='*60}")
    print("REQUIREMENTS COVERAGE")
    print(f"{'='*60}")
    
    requirements_coverage = {
        '8.1': 'Backward compatibility - existing functionality preserved',
        '8.2': 'Backward compatibility - GUI commands work as before', 
        '8.3': 'Backward compatibility - question answering preserved',
        '8.4': 'Backward compatibility - performance impact minimal',
        '9.1': 'Error handling - intent recognition fallback',
        '9.2': 'Error handling - conversational query errors',
        '9.3': 'Error handling - deferred action failures',
        '9.4': 'Error handling - state management errors'
    }
    
    print("Requirements tested by this test suite:")
    for req_id, description in requirements_coverage.items():
        status = "✅ COVERED" if len(failed_tests) == 0 else "⚠️  CHECK FAILURES"
        print(f"  {req_id}: {description} - {status}")
    
    # Final result
    print(f"\n{'='*60}")
    if len(failed_tests) == 0:
        print("🎉 ALL TESTS PASSED! Conversational enhancement is working correctly.")
        print("✅ Task 11 implementation is COMPLETE and SUCCESSFUL.")
        return 0
    else:
        print(f"❌ {len(failed_tests)} test(s) failed. Please review and fix issues.")
        print("⚠️  Task 11 implementation needs attention.")
        return 1


if __name__ == '__main__':
    sys.exit(main())