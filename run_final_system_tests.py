#!/usr/bin/env python3
"""
Final System Integration Test Runner

Comprehensive test runner for the hybrid architecture system integration tests.
Executes all tests, generates reports, and validates system performance.

Requirements: 1.3, 2.4, 6.5
"""

import os
import sys
import subprocess
import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class SystemTestRunner:
    """Comprehensive system test runner for hybrid architecture."""
    
    def __init__(self, verbose: bool = False, generate_report: bool = True):
        """Initialize the test runner."""
        self.verbose = verbose
        self.generate_report = generate_report
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
        # Configure logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'system_test_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all system integration tests."""
        self.start_time = time.time()
        self.logger.info("Starting comprehensive system integration tests...")
        
        test_suites = [
            {
                'name': 'Final System Integration Tests',
                'file': 'tests/test_final_system_integration.py',
                'description': 'End-to-end hybrid workflow testing with real applications',
                'timeout': 600  # 10 minutes
            },
            {
                'name': 'Performance Benchmarking Tests',
                'file': 'tests/test_performance_benchmarking.py',
                'description': 'Performance comparison and optimization validation',
                'timeout': 900  # 15 minutes
            },
            {
                'name': 'Hybrid Orchestration Tests',
                'file': 'tests/test_hybrid_orchestration.py',
                'description': 'Fast path routing and fallback mechanism validation',
                'timeout': 300  # 5 minutes
            },
            {
                'name': 'Accessibility Module Tests',
                'file': 'tests/test_accessibility.py',
                'description': 'Accessibility API integration and element detection',
                'timeout': 300  # 5 minutes
            }
        ]
        
        overall_success = True
        
        for suite in test_suites:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Running: {suite['name']}")
            self.logger.info(f"Description: {suite['description']}")
            self.logger.info(f"{'='*60}")
            
            try:
                result = self._run_test_suite(suite)
                self.test_results[suite['name']] = result
                
                if not result['success']:
                    overall_success = False
                    self.logger.error(f"Test suite failed: {suite['name']}")
                else:
                    self.logger.info(f"Test suite passed: {suite['name']}")
                    
            except Exception as e:
                self.logger.error(f"Error running test suite {suite['name']}: {e}")
                self.test_results[suite['name']] = {
                    'success': False,
                    'error': str(e),
                    'execution_time': 0,
                    'tests_run': 0,
                    'tests_passed': 0,
                    'tests_failed': 0
                }
                overall_success = False
        
        self.end_time = time.time()
        
        # Generate comprehensive report
        if self.generate_report:
            self._generate_final_report(overall_success)
        
        return {
            'overall_success': overall_success,
            'total_execution_time': self.end_time - self.start_time,
            'test_results': self.test_results
        }
    
    def _run_test_suite(self, suite: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific test suite."""
        start_time = time.time()
        
        # Check if test file exists
        if not os.path.exists(suite['file']):
            raise FileNotFoundError(f"Test file not found: {suite['file']}")
        
        # Prepare pytest command
        cmd = [
            sys.executable, '-m', 'pytest',
            suite['file'],
            '-v',
            '--tb=short'
        ]
        
        if self.verbose:
            cmd.extend(['--capture=no', '--log-cli-level=DEBUG'])
        
        # Run the test suite
        self.logger.info(f"Executing: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                timeout=suite['timeout'],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            execution_time = time.time() - start_time
            
            # Parse pytest output for basic metrics
            report_data = self._parse_pytest_output(result.stdout)
            
            # Determine success based on return code and report
            success = result.returncode == 0
            
            test_result = {
                'success': success,
                'execution_time': execution_time,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'tests_run': report_data.get('tests_run', 0),
                'tests_passed': report_data.get('tests_passed', 0),
                'tests_failed': report_data.get('tests_failed', 0),
                'tests_skipped': report_data.get('tests_skipped', 0),
                'performance_metrics': report_data.get('performance_metrics', {})
            }
            
            # Log results
            if success:
                self.logger.info(f"✓ Test suite completed successfully in {execution_time:.2f}s")
                self.logger.info(f"  Tests: {test_result['tests_run']} run, "
                               f"{test_result['tests_passed']} passed, "
                               f"{test_result['tests_failed']} failed")
            else:
                self.logger.error(f"✗ Test suite failed in {execution_time:.2f}s")
                self.logger.error(f"  Return code: {result.returncode}")
                if result.stderr:
                    self.logger.error(f"  Error output: {result.stderr[:500]}...")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            self.logger.error(f"Test suite timed out after {suite['timeout']}s")
            
            return {
                'success': False,
                'execution_time': execution_time,
                'error': f"Timeout after {suite['timeout']}s",
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0
            }
    
    def _parse_pytest_output(self, output: str) -> Dict[str, Any]:
        """Parse pytest output for basic metrics."""
        try:
            # Look for test results in output
            lines = output.split('\n')
            
            tests_run = 0
            tests_passed = 0
            tests_failed = 0
            tests_skipped = 0
            
            # Parse the summary line
            for line in lines:
                if 'passed' in line and ('failed' in line or 'error' in line or 'skipped' in line):
                    # Example: "1 failed, 2 passed in 1.23s"
                    import re
                    
                    passed_match = re.search(r'(\d+)\s+passed', line)
                    failed_match = re.search(r'(\d+)\s+failed', line)
                    error_match = re.search(r'(\d+)\s+error', line)
                    skipped_match = re.search(r'(\d+)\s+skipped', line)
                    
                    if passed_match:
                        tests_passed = int(passed_match.group(1))
                    if failed_match:
                        tests_failed = int(failed_match.group(1))
                    if error_match:
                        tests_failed += int(error_match.group(1))
                    if skipped_match:
                        tests_skipped = int(skipped_match.group(1))
                    
                    tests_run = tests_passed + tests_failed + tests_skipped
                    break
                elif 'passed in' in line and 'failed' not in line and 'error' not in line:
                    # Example: "5 passed in 1.23s"
                    import re
                    passed_match = re.search(r'(\d+)\s+passed', line)
                    if passed_match:
                        tests_passed = int(passed_match.group(1))
                        tests_run = tests_passed
                        break
            
            return {
                'tests_run': tests_run,
                'tests_passed': tests_passed,
                'tests_failed': tests_failed,
                'tests_skipped': tests_skipped,
                'performance_metrics': {}
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to parse pytest output: {e}")
            return {
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0,
                'tests_skipped': 0,
                'performance_metrics': {}
            }
    
    def _extract_performance_metrics(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Extract performance metrics from test report."""
        metrics = {}
        
        # Look for performance-related test results
        tests = report.get('tests', [])
        
        for test in tests:
            test_name = test.get('nodeid', '')
            
            # Extract timing information
            if 'performance' in test_name.lower() or 'benchmark' in test_name.lower():
                duration = test.get('duration', 0)
                outcome = test.get('outcome', 'unknown')
                
                metrics[test_name] = {
                    'duration': duration,
                    'outcome': outcome,
                    'passed': outcome == 'passed'
                }
        
        return metrics
    
    def _generate_final_report(self, overall_success: bool):
        """Generate comprehensive final test report."""
        report_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f'final_system_test_report_{report_timestamp}.json'
        
        # Calculate summary statistics
        total_tests = sum(result.get('tests_run', 0) for result in self.test_results.values())
        total_passed = sum(result.get('tests_passed', 0) for result in self.test_results.values())
        total_failed = sum(result.get('tests_failed', 0) for result in self.test_results.values())
        total_execution_time = self.end_time - self.start_time
        
        # Performance analysis
        performance_summary = self._analyze_performance_results()
        
        # System requirements validation
        requirements_validation = self._validate_system_requirements()
        
        # Generate comprehensive report
        final_report = {
            'test_execution_summary': {
                'timestamp': datetime.now().isoformat(),
                'overall_success': overall_success,
                'total_execution_time': total_execution_time,
                'total_test_suites': len(self.test_results),
                'successful_suites': len([r for r in self.test_results.values() if r.get('success', False)]),
                'failed_suites': len([r for r in self.test_results.values() if not r.get('success', False)]),
                'total_tests': total_tests,
                'total_passed': total_passed,
                'total_failed': total_failed,
                'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0
            },
            'test_suite_results': self.test_results,
            'performance_analysis': performance_summary,
            'requirements_validation': requirements_validation,
            'system_health_check': self._perform_system_health_check(),
            'recommendations': self._generate_recommendations()
        }
        
        # Save report
        with open(report_filename, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        # Generate human-readable summary
        self._generate_summary_report(final_report, report_timestamp)
        
        self.logger.info(f"Final test report generated: {report_filename}")
    
    def _analyze_performance_results(self) -> Dict[str, Any]:
        """Analyze performance test results."""
        performance_analysis = {
            'fast_path_performance': {},
            'slow_path_performance': {},
            'performance_improvements': {},
            'regression_detected': False,
            'performance_requirements_met': True
        }
        
        # Extract performance metrics from test results
        for suite_name, result in self.test_results.items():
            if 'Performance' in suite_name or 'performance' in suite_name.lower():
                metrics = result.get('performance_metrics', {})
                
                # Analyze fast path performance
                fast_path_tests = {k: v for k, v in metrics.items() if 'fast_path' in k}
                if fast_path_tests:
                    fast_path_durations = [test['duration'] for test in fast_path_tests.values() if test['passed']]
                    if fast_path_durations:
                        performance_analysis['fast_path_performance'] = {
                            'avg_duration': sum(fast_path_durations) / len(fast_path_durations),
                            'max_duration': max(fast_path_durations),
                            'min_duration': min(fast_path_durations),
                            'tests_count': len(fast_path_durations),
                            'requirement_met': max(fast_path_durations) < 2.0  # 2 second requirement
                        }
                        
                        if max(fast_path_durations) >= 2.0:
                            performance_analysis['performance_requirements_met'] = False
                
                # Analyze slow path performance
                slow_path_tests = {k: v for k, v in metrics.items() if 'slow_path' in k}
                if slow_path_tests:
                    slow_path_durations = [test['duration'] for test in slow_path_tests.values() if test['passed']]
                    if slow_path_durations:
                        performance_analysis['slow_path_performance'] = {
                            'avg_duration': sum(slow_path_durations) / len(slow_path_durations),
                            'max_duration': max(slow_path_durations),
                            'min_duration': min(slow_path_durations),
                            'tests_count': len(slow_path_durations)
                        }
        
        return performance_analysis
    
    def _validate_system_requirements(self) -> Dict[str, Any]:
        """Validate system requirements compliance."""
        validation = {
            'requirement_1_3_fast_path_performance': {
                'description': 'Fast path execution < 2 seconds',
                'status': 'unknown',
                'details': {}
            },
            'requirement_2_4_backward_compatibility': {
                'description': 'Existing AURA functionality preserved',
                'status': 'unknown',
                'details': {}
            },
            'requirement_6_5_system_reliability': {
                'description': 'System maintains reliability and error recovery',
                'status': 'unknown',
                'details': {}
            }
        }
        
        # Check fast path performance requirement
        performance_analysis = self._analyze_performance_results()
        fast_path_perf = performance_analysis.get('fast_path_performance', {})
        
        if fast_path_perf:
            requirement_met = fast_path_perf.get('requirement_met', False)
            validation['requirement_1_3_fast_path_performance']['status'] = 'passed' if requirement_met else 'failed'
            validation['requirement_1_3_fast_path_performance']['details'] = {
                'max_duration': fast_path_perf.get('max_duration', 0),
                'avg_duration': fast_path_perf.get('avg_duration', 0),
                'threshold': 2.0
            }
        
        # Check backward compatibility (based on test results)
        compatibility_tests = [
            result for suite_name, result in self.test_results.items()
            if 'compatibility' in suite_name.lower() or 'backward' in suite_name.lower()
        ]
        
        if compatibility_tests:
            all_passed = all(test.get('success', False) for test in compatibility_tests)
            validation['requirement_2_4_backward_compatibility']['status'] = 'passed' if all_passed else 'failed'
        
        # Check system reliability (based on overall test success)
        overall_success_rate = 0
        total_tests = sum(result.get('tests_run', 0) for result in self.test_results.values())
        total_passed = sum(result.get('tests_passed', 0) for result in self.test_results.values())
        
        if total_tests > 0:
            overall_success_rate = (total_passed / total_tests) * 100
        
        validation['requirement_6_5_system_reliability']['status'] = 'passed' if overall_success_rate >= 95 else 'failed'
        validation['requirement_6_5_system_reliability']['details'] = {
            'success_rate': overall_success_rate,
            'threshold': 95.0
        }
        
        return validation
    
    def _perform_system_health_check(self) -> Dict[str, Any]:
        """Perform system health check."""
        health_check = {
            'timestamp': datetime.now().isoformat(),
            'system_status': 'healthy',
            'checks': {}
        }
        
        # Check Python environment
        health_check['checks']['python_version'] = {
            'status': 'passed',
            'version': sys.version,
            'details': 'Python environment is compatible'
        }
        
        # Check required modules
        required_modules = [
            'pytest', 'psutil', 'concurrent.futures', 
            'threading', 'json', 'logging'
        ]
        
        for module_name in required_modules:
            try:
                __import__(module_name)
                health_check['checks'][f'module_{module_name}'] = {
                    'status': 'passed',
                    'details': f'{module_name} is available'
                }
            except ImportError:
                health_check['checks'][f'module_{module_name}'] = {
                    'status': 'failed',
                    'details': f'{module_name} is not available'
                }
                health_check['system_status'] = 'degraded'
        
        # Check test files
        test_files = [
            'tests/test_final_system_integration.py',
            'tests/test_performance_benchmarking.py',
            'tests/test_hybrid_orchestration.py',
            'tests/test_accessibility.py'
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                health_check['checks'][f'test_file_{os.path.basename(test_file)}'] = {
                    'status': 'passed',
                    'details': f'{test_file} exists'
                }
            else:
                health_check['checks'][f'test_file_{os.path.basename(test_file)}'] = {
                    'status': 'failed',
                    'details': f'{test_file} not found'
                }
                health_check['system_status'] = 'degraded'
        
        return health_check
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Performance recommendations
        performance_analysis = self._analyze_performance_results()
        
        if not performance_analysis.get('performance_requirements_met', True):
            recommendations.append(
                "Fast path performance does not meet <2 second requirement. "
                "Consider optimizing accessibility tree traversal and element caching."
            )
        
        # Test failure recommendations
        failed_suites = [name for name, result in self.test_results.items() if not result.get('success', False)]
        
        if failed_suites:
            recommendations.append(
                f"The following test suites failed: {', '.join(failed_suites)}. "
                "Review test logs and fix underlying issues before deployment."
            )
        
        # Success rate recommendations
        total_tests = sum(result.get('tests_run', 0) for result in self.test_results.values())
        total_passed = sum(result.get('tests_passed', 0) for result in self.test_results.values())
        
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            if success_rate < 95:
                recommendations.append(
                    f"Overall test success rate ({success_rate:.1f}%) is below 95% threshold. "
                    "Investigate and fix failing tests to ensure system reliability."
                )
        
        # System health recommendations
        system_health = self._perform_system_health_check()
        if system_health['system_status'] != 'healthy':
            recommendations.append(
                "System health check detected issues. "
                "Review system health report and resolve any missing dependencies or configuration problems."
            )
        
        if not recommendations:
            recommendations.append(
                "All tests passed successfully! The hybrid architecture implementation "
                "meets all requirements and is ready for deployment."
            )
        
        return recommendations
    
    def _generate_summary_report(self, report: Dict[str, Any], timestamp: str):
        """Generate human-readable summary report."""
        summary_filename = f'test_summary_{timestamp}.txt'
        
        with open(summary_filename, 'w') as f:
            f.write("AURA Hybrid Architecture - Final System Integration Test Report\n")
            f.write("=" * 70 + "\n\n")
            
            # Executive Summary
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 20 + "\n")
            summary = report['test_execution_summary']
            f.write(f"Overall Result: {'PASSED' if summary['overall_success'] else 'FAILED'}\n")
            f.write(f"Total Execution Time: {summary['total_execution_time']:.2f} seconds\n")
            f.write(f"Test Success Rate: {summary['success_rate']:.1f}%\n")
            f.write(f"Tests Run: {summary['total_tests']}\n")
            f.write(f"Tests Passed: {summary['total_passed']}\n")
            f.write(f"Tests Failed: {summary['total_failed']}\n\n")
            
            # Requirements Validation
            f.write("REQUIREMENTS VALIDATION\n")
            f.write("-" * 25 + "\n")
            for req_id, req_data in report['requirements_validation'].items():
                status = req_data['status'].upper()
                f.write(f"{req_id}: {status}\n")
                f.write(f"  Description: {req_data['description']}\n")
                if req_data.get('details'):
                    f.write(f"  Details: {req_data['details']}\n")
                f.write("\n")
            
            # Performance Analysis
            f.write("PERFORMANCE ANALYSIS\n")
            f.write("-" * 22 + "\n")
            perf = report['performance_analysis']
            
            if perf.get('fast_path_performance'):
                fp = perf['fast_path_performance']
                f.write(f"Fast Path Performance:\n")
                f.write(f"  Average Duration: {fp['avg_duration']:.3f}s\n")
                f.write(f"  Maximum Duration: {fp['max_duration']:.3f}s\n")
                f.write(f"  Requirement Met: {'YES' if fp['requirement_met'] else 'NO'}\n\n")
            
            if perf.get('slow_path_performance'):
                sp = perf['slow_path_performance']
                f.write(f"Slow Path Performance:\n")
                f.write(f"  Average Duration: {sp['avg_duration']:.3f}s\n")
                f.write(f"  Maximum Duration: {sp['max_duration']:.3f}s\n\n")
            
            # Recommendations
            f.write("RECOMMENDATIONS\n")
            f.write("-" * 15 + "\n")
            for i, recommendation in enumerate(report['recommendations'], 1):
                f.write(f"{i}. {recommendation}\n\n")
            
            # Test Suite Details
            f.write("TEST SUITE DETAILS\n")
            f.write("-" * 18 + "\n")
            for suite_name, result in report['test_suite_results'].items():
                status = "PASSED" if result.get('success', False) else "FAILED"
                f.write(f"{suite_name}: {status}\n")
                f.write(f"  Execution Time: {result.get('execution_time', 0):.2f}s\n")
                f.write(f"  Tests Run: {result.get('tests_run', 0)}\n")
                f.write(f"  Tests Passed: {result.get('tests_passed', 0)}\n")
                f.write(f"  Tests Failed: {result.get('tests_failed', 0)}\n")
                if result.get('error'):
                    f.write(f"  Error: {result['error']}\n")
                f.write("\n")
        
        self.logger.info(f"Summary report generated: {summary_filename}")


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description='Run AURA Hybrid Architecture System Integration Tests')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--no-report', action='store_true', help='Skip report generation')
    parser.add_argument('--suite', type=str, help='Run specific test suite only')
    
    args = parser.parse_args()
    
    # Create test runner
    runner = SystemTestRunner(
        verbose=args.verbose,
        generate_report=not args.no_report
    )
    
    try:
        # Run all tests
        results = runner.run_all_tests()
        
        # Print final summary
        print("\n" + "=" * 70)
        print("FINAL SYSTEM INTEGRATION TEST RESULTS")
        print("=" * 70)
        
        if results['overall_success']:
            print("🎉 ALL TESTS PASSED! 🎉")
            print("The hybrid architecture implementation is ready for deployment.")
        else:
            print("❌ SOME TESTS FAILED ❌")
            print("Review the test results and fix issues before deployment.")
        
        print(f"\nTotal execution time: {results['total_execution_time']:.2f} seconds")
        print(f"Test suites run: {len(results['test_results'])}")
        
        successful_suites = len([r for r in results['test_results'].values() if r.get('success', False)])
        print(f"Successful suites: {successful_suites}/{len(results['test_results'])}")
        
        # Exit with appropriate code
        sys.exit(0 if results['overall_success'] else 1)
        
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nTest execution failed with error: {e}")
        logging.exception("Test execution error")
        sys.exit(1)


if __name__ == '__main__':
    main()