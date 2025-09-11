#!/usr/bin/env python3
"""
Comprehensive test runner for Explain Selected Text feature

Runs all test suites for the explain selected text feature including unit tests,
integration tests, edge cases, and performance tests with detailed reporting.

Requirements: All requirements from tasks 1-12
"""

import pytest
import sys
import time
import subprocess
from typing import Dict, Any, List
from pathlib import Path


class TestSuiteRunner:
    """Comprehensive test suite runner with detailed reporting."""
    
    def __init__(self):
        self.test_suites = [
            {
                "name": "Unit Tests (Detailed)",
                "file": "tests/test_explain_selected_text_unit_detailed.py",
                "description": "Detailed unit tests for text capture methods and handler components",
                "requirements": ["1.1", "1.3", "1.4", "1.5", "2.1", "2.2", "2.4", "5.5"]
            },
            {
                "name": "Integration Tests",
                "file": "tests/test_explain_selected_text_comprehensive_working.py",
                "description": "Integration tests for complete workflow and system integration",
                "requirements": ["1.1", "1.2", "3.1", "3.2", "3.3", "4.1", "4.2", "4.3", "4.4", "4.5", "5.1", "5.3", "5.4"]
            },
            {
                "name": "Edge Cases (Detailed)",
                "file": "tests/test_explain_selected_text_edge_cases_detailed.py",
                "description": "Detailed edge case tests for various failure scenarios and special content",
                "requirements": ["1.2", "2.3", "2.4", "3.4", "3.5", "5.2", "5.5"]
            },
            {
                "name": "Performance Tests (Detailed)",
                "file": "tests/test_explain_selected_text_performance_detailed.py",
                "description": "Detailed performance tests for timing requirements and scalability",
                "requirements": ["2.3", "3.5", "5.4", "5.5"]
            }
        ]
        
        self.results = {}
        self.total_start_time = None
        self.total_end_time = None

    def run_all_tests(self, verbose: bool = True, stop_on_failure: bool = False) -> bool:
        """
        Run all test suites with comprehensive reporting.
        
        Args:
            verbose: Whether to show detailed output
            stop_on_failure: Whether to stop on first test suite failure
            
        Returns:
            True if all tests passed, False otherwise
        """
        print("=" * 80)
        print("EXPLAIN SELECTED TEXT FEATURE - COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print()
        
        self.total_start_time = time.time()
        
        # Print test suite overview
        self._print_test_overview()
        
        all_passed = True
        
        for i, suite in enumerate(self.test_suites, 1):
            print(f"\n{'='*60}")
            print(f"Running Test Suite {i}/{len(self.test_suites)}: {suite['name']}")
            print(f"{'='*60}")
            print(f"Description: {suite['description']}")
            print(f"Requirements: {', '.join(suite['requirements'])}")
            print(f"File: {suite['file']}")
            print()
            
            # Check if test file exists
            if not Path(suite['file']).exists():
                print(f"❌ ERROR: Test file {suite['file']} not found!")
                self.results[suite['name']] = {
                    'status': 'ERROR',
                    'message': 'Test file not found',
                    'duration': 0,
                    'tests_run': 0,
                    'failures': 0,
                    'errors': 1
                }
                all_passed = False
                if stop_on_failure:
                    break
                continue
            
            # Run the test suite
            suite_start_time = time.time()
            success = self._run_test_suite(suite, verbose)
            suite_end_time = time.time()
            
            # Record results
            duration = suite_end_time - suite_start_time
            self.results[suite['name']]['duration'] = duration
            
            if success:
                print(f"✅ {suite['name']}: PASSED ({duration:.2f}s)")
            else:
                print(f"❌ {suite['name']}: FAILED ({duration:.2f}s)")
                all_passed = False
                if stop_on_failure:
                    break
        
        self.total_end_time = time.time()
        
        # Print comprehensive summary
        self._print_comprehensive_summary()
        
        return all_passed

    def _print_test_overview(self):
        """Print overview of all test suites."""
        print("Test Suite Overview:")
        print("-" * 40)
        
        total_requirements = set()
        for suite in self.test_suites:
            total_requirements.update(suite['requirements'])
        
        print(f"Total Test Suites: {len(self.test_suites)}")
        print(f"Requirements Covered: {len(total_requirements)} ({', '.join(sorted(total_requirements))})")
        print()
        
        for i, suite in enumerate(self.test_suites, 1):
            print(f"{i}. {suite['name']}")
            print(f"   Requirements: {', '.join(suite['requirements'])}")
        print()

    def _run_test_suite(self, suite: Dict[str, Any], verbose: bool) -> bool:
        """
        Run a single test suite.
        
        Args:
            suite: Test suite configuration
            verbose: Whether to show detailed output
            
        Returns:
            True if tests passed, False otherwise
        """
        try:
            # Prepare pytest arguments
            pytest_args = [suite['file']]
            
            if verbose:
                pytest_args.extend(['-v', '-s'])
            else:
                pytest_args.append('-q')
            
            # Add coverage and reporting options
            pytest_args.extend([
                '--tb=short',  # Shorter traceback format
                '--disable-warnings'  # Reduce noise
            ])
            
            # Run pytest
            result = pytest.main(pytest_args)
            
            # Record basic results
            self.results[suite['name']] = {
                'status': 'PASSED' if result == 0 else 'FAILED',
                'message': 'All tests passed' if result == 0 else f'pytest exit code: {result}',
                'tests_run': 0,  # pytest doesn't easily provide this info
                'failures': 0 if result == 0 else 1,
                'errors': 0
            }
            
            return result == 0
            
        except Exception as e:
            print(f"❌ ERROR running {suite['name']}: {e}")
            self.results[suite['name']] = {
                'status': 'ERROR',
                'message': str(e),
                'duration': 0,
                'tests_run': 0,
                'failures': 0,
                'errors': 1
            }
            return False

    def _print_comprehensive_summary(self):
        """Print comprehensive test results summary."""
        total_duration = self.total_end_time - self.total_start_time
        
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        # Overall statistics
        total_suites = len(self.test_suites)
        passed_suites = sum(1 for r in self.results.values() if r['status'] == 'PASSED')
        failed_suites = sum(1 for r in self.results.values() if r['status'] == 'FAILED')
        error_suites = sum(1 for r in self.results.values() if r['status'] == 'ERROR')
        
        print(f"\nOverall Results:")
        print(f"  Total Test Suites: {total_suites}")
        print(f"  Passed: {passed_suites}")
        print(f"  Failed: {failed_suites}")
        print(f"  Errors: {error_suites}")
        print(f"  Success Rate: {passed_suites/total_suites*100:.1f}%")
        print(f"  Total Duration: {total_duration:.2f} seconds")
        
        # Detailed results by suite
        print(f"\nDetailed Results by Test Suite:")
        print("-" * 60)
        
        for suite in self.test_suites:
            name = suite['name']
            if name in self.results:
                result = self.results[name]
                status_icon = "✅" if result['status'] == 'PASSED' else "❌"
                duration = result.get('duration', 0)
                print(f"{status_icon} {name}: {result['status']} ({duration:.2f}s)")
                if result['status'] != 'PASSED':
                    print(f"    Message: {result['message']}")
            else:
                print(f"❓ {name}: NOT RUN")
        
        # Requirements coverage summary
        print(f"\nRequirements Coverage Summary:")
        print("-" * 40)
        
        all_requirements = set()
        covered_requirements = set()
        
        for suite in self.test_suites:
            suite_requirements = set(suite['requirements'])
            all_requirements.update(suite_requirements)
            
            if suite['name'] in self.results and self.results[suite['name']]['status'] == 'PASSED':
                covered_requirements.update(suite_requirements)
        
        coverage_percentage = len(covered_requirements) / len(all_requirements) * 100 if all_requirements else 0
        
        print(f"Total Requirements: {len(all_requirements)}")
        print(f"Covered by Passing Tests: {len(covered_requirements)}")
        print(f"Coverage: {coverage_percentage:.1f}%")
        
        if all_requirements - covered_requirements:
            print(f"Uncovered Requirements: {', '.join(sorted(all_requirements - covered_requirements))}")
        
        # Performance summary
        print(f"\nPerformance Summary:")
        print("-" * 30)
        
        suite_durations = [(name, result.get('duration', 0)) for name, result in self.results.items()]
        suite_durations.sort(key=lambda x: x[1], reverse=True)
        
        for name, duration in suite_durations:
            print(f"  {name}: {duration:.2f}s")
        
        # Final verdict
        print(f"\n{'='*80}")
        if passed_suites == total_suites:
            print("🎉 ALL TESTS PASSED! Explain Selected Text feature is ready for deployment.")
        elif passed_suites > 0:
            print(f"⚠️  PARTIAL SUCCESS: {passed_suites}/{total_suites} test suites passed.")
            print("   Review failed tests before deployment.")
        else:
            print("💥 ALL TESTS FAILED! Feature requires significant fixes.")
        print("=" * 80)

    def run_specific_suite(self, suite_name: str, verbose: bool = True) -> bool:
        """
        Run a specific test suite by name.
        
        Args:
            suite_name: Name of the test suite to run
            verbose: Whether to show detailed output
            
        Returns:
            True if tests passed, False otherwise
        """
        for suite in self.test_suites:
            if suite['name'] == suite_name:
                print(f"Running specific test suite: {suite_name}")
                return self._run_test_suite(suite, verbose)
        
        print(f"❌ Test suite '{suite_name}' not found!")
        print("Available test suites:")
        for suite in self.test_suites:
            print(f"  - {suite['name']}")
        return False

    def list_test_suites(self):
        """List all available test suites."""
        print("Available Test Suites:")
        print("=" * 50)
        
        for i, suite in enumerate(self.test_suites, 1):
            print(f"{i}. {suite['name']}")
            print(f"   File: {suite['file']}")
            print(f"   Description: {suite['description']}")
            print(f"   Requirements: {', '.join(suite['requirements'])}")
            print()


def main():
    """Main entry point for the test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive test runner for Explain Selected Text feature")
    parser.add_argument('--suite', '-s', help='Run specific test suite by name')
    parser.add_argument('--list', '-l', action='store_true', help='List available test suites')
    parser.add_argument('--quiet', '-q', action='store_true', help='Run tests in quiet mode')
    parser.add_argument('--stop-on-failure', action='store_true', help='Stop on first test suite failure')
    
    args = parser.parse_args()
    
    runner = TestSuiteRunner()
    
    if args.list:
        runner.list_test_suites()
        return 0
    
    verbose = not args.quiet
    
    if args.suite:
        success = runner.run_specific_suite(args.suite, verbose)
    else:
        success = runner.run_all_tests(verbose, args.stop_on_failure)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())