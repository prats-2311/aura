#!/usr/bin/env python3
"""
Comprehensive Debugging System Test Runner

Executes all debugging functionality tests and generates detailed reports
on debugging tool effectiveness and performance impact.

Requirements: 1.1, 7.1, 8.1
"""

import os
import sys
import subprocess
import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@dataclass
class TestResult:
    """Test execution result."""
    test_name: str
    status: str  # 'PASSED', 'FAILED', 'SKIPPED'
    execution_time: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class TestSuiteResult:
    """Test suite execution result."""
    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    execution_time: float
    test_results: List[TestResult]
    success_rate: float


class DebuggingSystemTestRunner:
    """Comprehensive debugging system test runner."""
    
    def __init__(self):
        self.setup_logging()
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('debugging_system_tests.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_all_debugging_tests(self) -> Dict[str, TestSuiteResult]:
        """Run all debugging system tests."""
        self.logger.info("Starting comprehensive debugging system tests...")
        self.start_time = time.time()
        
        test_suites = {
            'debugging_functionality': self.run_debugging_functionality_tests(),
            'debugging_performance': self.run_debugging_performance_tests(),
            'debugging_integration': self.run_debugging_integration_tests(),
            'real_world_scenarios': self.run_real_world_scenario_tests(),
            'existing_system_integration': self.run_existing_system_integration_tests()
        }
        
        self.end_time = time.time()
        
        # Generate comprehensive report
        self.generate_comprehensive_report(test_suites)
        
        return test_suites
    
    def run_debugging_functionality_tests(self) -> TestSuiteResult:
        """Run debugging functionality validation tests."""
        self.logger.info("Running debugging functionality tests...")
        
        test_commands = [
            # Permission validation tests
            "python -m pytest tests/test_debugging_system_integration.py::TestDebuggingFunctionalityValidation::test_permission_validation_comprehensive -v",
            
            # Tree inspection tests
            "python -m pytest tests/test_debugging_system_integration.py::TestDebuggingFunctionalityValidation::test_accessibility_tree_inspection_comprehensive -v",
            
            # Failure analysis tests
            "python -m pytest tests/test_debugging_system_integration.py::TestDebuggingFunctionalityValidation::test_element_detection_failure_analysis -v",
            
            # Comprehensive diagnostics tests
            "python -m pytest tests/test_debugging_system_integration.py::TestDebuggingFunctionalityValidation::test_comprehensive_diagnostics_execution -v"
        ]
        
        return self.execute_test_suite("debugging_functionality", test_commands)
    
    def run_debugging_performance_tests(self) -> TestSuiteResult:
        """Run debugging performance impact tests."""
        self.logger.info("Running debugging performance tests...")
        
        test_commands = [
            # Performance overhead tests
            "python -m pytest tests/test_debugging_system_integration.py::TestDebuggingPerformanceImpact::test_debugging_overhead_measurement -v",
            
            # Debug level scaling tests
            "python -m pytest tests/test_debugging_system_integration.py::TestDebuggingPerformanceImpact::test_debug_level_performance_scaling -v"
        ]
        
        return self.execute_test_suite("debugging_performance", test_commands)
    
    def run_debugging_integration_tests(self) -> TestSuiteResult:
        """Run debugging integration tests."""
        self.logger.info("Running debugging integration tests...")
        
        test_commands = [
            # Orchestrator integration
            "python -m pytest tests/test_debugging_system_integration.py::TestDebuggingIntegrationWithExistingSystem::test_orchestrator_debugging_integration -v",
            
            # Accessibility module integration
            "python -m pytest tests/test_debugging_system_integration.py::TestDebuggingIntegrationWithExistingSystem::test_accessibility_module_debugging_integration -v"
        ]
        
        return self.execute_test_suite("debugging_integration", test_commands)
    
    def run_real_world_scenario_tests(self) -> TestSuiteResult:
        """Run real-world scenario tests."""
        self.logger.info("Running real-world scenario tests...")
        
        test_commands = [
            # Browser debugging scenarios
            "python -m pytest tests/test_debugging_system_integration.py::TestDebuggingRealWorldScenarios::test_browser_debugging_scenarios -v",
            
            # Native app debugging scenarios
            "python -m pytest tests/test_debugging_system_integration.py::TestDebuggingRealWorldScenarios::test_native_app_debugging_scenarios -v"
        ]
        
        return self.execute_test_suite("real_world_scenarios", test_commands)
    
    def run_existing_system_integration_tests(self) -> TestSuiteResult:
        """Run tests to verify integration with existing system."""
        self.logger.info("Running existing system integration tests...")
        
        test_commands = [
            # Existing debugging tests
            "python -m pytest tests/test_debugging_comprehensive_simple.py -v",
            "python -m pytest tests/test_debugging_integration_comprehensive.py -v",
            "python -m pytest tests/test_debugging_unit_comprehensive.py -v",
            
            # Accessibility debugging tests
            "python -m pytest tests/test_accessibility_debugging_integration.py -v",
            "python -m pytest tests/test_accessibility_debugger.py -v",
            
            # Performance monitoring tests
            "python -m pytest tests/test_performance_monitoring_unit.py -v",
            "python -m pytest tests/test_fast_path_performance_monitor.py -v",
            
            # Diagnostic tools tests
            "python -m pytest tests/test_diagnostic_tools.py -v",
            "python -m pytest tests/test_diagnostic_integration.py -v"
        ]
        
        return self.execute_test_suite("existing_system_integration", test_commands)
    
    def execute_test_suite(self, suite_name: str, test_commands: List[str]) -> TestSuiteResult:
        """Execute a test suite and return results."""
        self.logger.info(f"Executing test suite: {suite_name}")
        
        suite_start_time = time.time()
        test_results = []
        
        for command in test_commands:
            test_name = self.extract_test_name(command)
            test_start_time = time.time()
            
            try:
                self.logger.info(f"Running test: {test_name}")
                
                # Execute test command
                result = subprocess.run(
                    command.split(),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout per test
                )
                
                test_execution_time = time.time() - test_start_time
                
                if result.returncode == 0:
                    test_result = TestResult(
                        test_name=test_name,
                        status='PASSED',
                        execution_time=test_execution_time,
                        details={'stdout': result.stdout}
                    )
                    self.logger.info(f"Test PASSED: {test_name} ({test_execution_time:.2f}s)")
                else:
                    test_result = TestResult(
                        test_name=test_name,
                        status='FAILED',
                        execution_time=test_execution_time,
                        error_message=result.stderr,
                        details={'stdout': result.stdout, 'stderr': result.stderr}
                    )
                    self.logger.error(f"Test FAILED: {test_name} - {result.stderr}")
                
            except subprocess.TimeoutExpired:
                test_execution_time = time.time() - test_start_time
                test_result = TestResult(
                    test_name=test_name,
                    status='FAILED',
                    execution_time=test_execution_time,
                    error_message="Test timed out after 5 minutes"
                )
                self.logger.error(f"Test TIMEOUT: {test_name}")
                
            except Exception as e:
                test_execution_time = time.time() - test_start_time
                test_result = TestResult(
                    test_name=test_name,
                    status='FAILED',
                    execution_time=test_execution_time,
                    error_message=str(e)
                )
                self.logger.error(f"Test ERROR: {test_name} - {e}")
            
            test_results.append(test_result)
        
        suite_execution_time = time.time() - suite_start_time
        
        # Calculate suite statistics
        passed_tests = len([r for r in test_results if r.status == 'PASSED'])
        failed_tests = len([r for r in test_results if r.status == 'FAILED'])
        skipped_tests = len([r for r in test_results if r.status == 'SKIPPED'])
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        suite_result = TestSuiteResult(
            suite_name=suite_name,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            execution_time=suite_execution_time,
            test_results=test_results,
            success_rate=success_rate
        )
        
        self.logger.info(f"Test suite {suite_name} completed: "
                        f"{passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
        return suite_result
    
    def extract_test_name(self, command: str) -> str:
        """Extract test name from pytest command."""
        parts = command.split("::")
        if len(parts) >= 3:
            return f"{parts[1]}::{parts[2]}"
        elif len(parts) >= 2:
            return parts[1]
        else:
            return command.split()[-1]
    
    def generate_comprehensive_report(self, test_suites: Dict[str, TestSuiteResult]):
        """Generate comprehensive test report."""
        self.logger.info("Generating comprehensive test report...")
        
        total_execution_time = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        # Calculate overall statistics
        total_tests = sum(suite.total_tests for suite in test_suites.values())
        total_passed = sum(suite.passed_tests for suite in test_suites.values())
        total_failed = sum(suite.failed_tests for suite in test_suites.values())
        total_skipped = sum(suite.skipped_tests for suite in test_suites.values())
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Generate report
        report = {
            'test_execution_summary': {
                'timestamp': datetime.now().isoformat(),
                'total_execution_time': total_execution_time,
                'total_tests': total_tests,
                'passed_tests': total_passed,
                'failed_tests': total_failed,
                'skipped_tests': total_skipped,
                'overall_success_rate': overall_success_rate
            },
            'test_suites': {name: asdict(suite) for name, suite in test_suites.items()},
            'debugging_effectiveness_analysis': self.analyze_debugging_effectiveness(test_suites),
            'performance_impact_analysis': self.analyze_performance_impact(test_suites),
            'recommendations': self.generate_recommendations(test_suites)
        }
        
        # Save report to file
        report_filename = f"debugging_system_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate human-readable summary
        self.generate_human_readable_summary(report, test_suites)
        
        self.logger.info(f"Comprehensive test report saved to: {report_filename}")
    
    def analyze_debugging_effectiveness(self, test_suites: Dict[str, TestSuiteResult]) -> Dict[str, Any]:
        """Analyze debugging tool effectiveness."""
        functionality_suite = test_suites.get('debugging_functionality')
        
        if not functionality_suite:
            return {'analysis': 'No debugging functionality tests executed'}
        
        effectiveness_analysis = {
            'permission_validation_effectiveness': functionality_suite.success_rate >= 90,
            'tree_inspection_effectiveness': functionality_suite.success_rate >= 85,
            'failure_analysis_effectiveness': functionality_suite.success_rate >= 80,
            'overall_debugging_effectiveness': functionality_suite.success_rate,
            'critical_issues_identified': [
                result.test_name for result in functionality_suite.test_results 
                if result.status == 'FAILED'
            ]
        }
        
        return effectiveness_analysis
    
    def analyze_performance_impact(self, test_suites: Dict[str, TestSuiteResult]) -> Dict[str, Any]:
        """Analyze performance impact of debugging features."""
        performance_suite = test_suites.get('debugging_performance')
        
        if not performance_suite:
            return {'analysis': 'No debugging performance tests executed'}
        
        # Extract performance metrics from test results
        performance_analysis = {
            'acceptable_overhead': performance_suite.success_rate >= 90,
            'debug_level_scaling_working': performance_suite.success_rate >= 85,
            'performance_impact_within_limits': performance_suite.success_rate >= 80,
            'average_test_execution_time': sum(
                result.execution_time for result in performance_suite.test_results
            ) / len(performance_suite.test_results) if performance_suite.test_results else 0,
            'performance_issues_identified': [
                result.test_name for result in performance_suite.test_results 
                if result.status == 'FAILED'
            ]
        }
        
        return performance_analysis
    
    def generate_recommendations(self, test_suites: Dict[str, TestSuiteResult]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Overall success rate recommendations
        overall_success_rate = sum(suite.success_rate for suite in test_suites.values()) / len(test_suites)
        
        if overall_success_rate < 80:
            recommendations.append("Overall test success rate is below 80%. Review failed tests and address critical issues.")
        
        # Suite-specific recommendations
        for suite_name, suite in test_suites.items():
            if suite.success_rate < 85:
                recommendations.append(f"Test suite '{suite_name}' has low success rate ({suite.success_rate:.1f}%). "
                                     f"Review and fix failing tests.")
            
            if suite.failed_tests > 0:
                failed_test_names = [r.test_name for r in suite.test_results if r.status == 'FAILED']
                recommendations.append(f"Failed tests in '{suite_name}': {', '.join(failed_test_names)}")
        
        # Performance-specific recommendations
        performance_suite = test_suites.get('debugging_performance')
        if performance_suite and performance_suite.success_rate < 90:
            recommendations.append("Debugging performance tests indicate issues. "
                                 "Review performance impact and optimize debugging overhead.")
        
        # Integration-specific recommendations
        integration_suite = test_suites.get('debugging_integration')
        if integration_suite and integration_suite.success_rate < 90:
            recommendations.append("Debugging integration tests indicate issues. "
                                 "Review integration with existing system components.")
        
        if not recommendations:
            recommendations.append("All debugging system tests passed successfully. "
                                 "Debugging functionality is working as expected.")
        
        return recommendations
    
    def generate_human_readable_summary(self, report: Dict[str, Any], test_suites: Dict[str, TestSuiteResult]):
        """Generate human-readable test summary."""
        summary_filename = f"debugging_system_test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(summary_filename, 'w') as f:
            f.write("# Debugging System Test Summary\n\n")
            f.write(f"**Test Execution Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overall results
            summary = report['test_execution_summary']
            f.write("## Overall Results\n\n")
            f.write(f"- **Total Tests:** {summary['total_tests']}\n")
            f.write(f"- **Passed:** {summary['passed_tests']}\n")
            f.write(f"- **Failed:** {summary['failed_tests']}\n")
            f.write(f"- **Skipped:** {summary['skipped_tests']}\n")
            f.write(f"- **Success Rate:** {summary['overall_success_rate']:.1f}%\n")
            f.write(f"- **Total Execution Time:** {summary['total_execution_time']:.2f} seconds\n\n")
            
            # Test suite results
            f.write("## Test Suite Results\n\n")
            for suite_name, suite in test_suites.items():
                f.write(f"### {suite_name.replace('_', ' ').title()}\n\n")
                f.write(f"- **Tests:** {suite.total_tests}\n")
                f.write(f"- **Passed:** {suite.passed_tests}\n")
                f.write(f"- **Failed:** {suite.failed_tests}\n")
                f.write(f"- **Success Rate:** {suite.success_rate:.1f}%\n")
                f.write(f"- **Execution Time:** {suite.execution_time:.2f} seconds\n\n")
                
                if suite.failed_tests > 0:
                    f.write("**Failed Tests:**\n")
                    for result in suite.test_results:
                        if result.status == 'FAILED':
                            f.write(f"- {result.test_name}: {result.error_message}\n")
                    f.write("\n")
            
            # Analysis results
            f.write("## Debugging Effectiveness Analysis\n\n")
            effectiveness = report['debugging_effectiveness_analysis']
            f.write(f"- **Overall Debugging Effectiveness:** {effectiveness.get('overall_debugging_effectiveness', 0):.1f}%\n")
            f.write(f"- **Permission Validation Working:** {'✅' if effectiveness.get('permission_validation_effectiveness') else '❌'}\n")
            f.write(f"- **Tree Inspection Working:** {'✅' if effectiveness.get('tree_inspection_effectiveness') else '❌'}\n")
            f.write(f"- **Failure Analysis Working:** {'✅' if effectiveness.get('failure_analysis_effectiveness') else '❌'}\n\n")
            
            f.write("## Performance Impact Analysis\n\n")
            performance = report['performance_impact_analysis']
            f.write(f"- **Acceptable Overhead:** {'✅' if performance.get('acceptable_overhead') else '❌'}\n")
            f.write(f"- **Debug Level Scaling:** {'✅' if performance.get('debug_level_scaling_working') else '❌'}\n")
            f.write(f"- **Performance Within Limits:** {'✅' if performance.get('performance_impact_within_limits') else '❌'}\n")
            f.write(f"- **Average Test Time:** {performance.get('average_test_execution_time', 0):.2f} seconds\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            for i, recommendation in enumerate(report['recommendations'], 1):
                f.write(f"{i}. {recommendation}\n")
            f.write("\n")
            
            # Conclusion
            if summary['overall_success_rate'] >= 90:
                f.write("## Conclusion\n\n")
                f.write("✅ **All debugging functionality tests passed successfully.** "
                       "The debugging enhancement is working as expected and ready for deployment.\n")
            elif summary['overall_success_rate'] >= 80:
                f.write("## Conclusion\n\n")
                f.write("⚠️ **Most debugging functionality tests passed with some issues.** "
                       "Review failed tests and address issues before deployment.\n")
            else:
                f.write("## Conclusion\n\n")
                f.write("❌ **Significant issues detected in debugging functionality.** "
                       "Critical issues must be resolved before deployment.\n")
        
        self.logger.info(f"Human-readable test summary saved to: {summary_filename}")


def main():
    """Main test execution function."""
    runner = DebuggingSystemTestRunner()
    
    try:
        # Run all debugging system tests
        test_results = runner.run_all_debugging_tests()
        
        # Print summary
        total_tests = sum(suite.total_tests for suite in test_results.values())
        total_passed = sum(suite.passed_tests for suite in test_results.values())
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*60}")
        print("DEBUGGING SYSTEM TEST EXECUTION COMPLETE")
        print(f"{'='*60}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_tests - total_passed}")
        print(f"Success Rate: {overall_success_rate:.1f}%")
        print(f"{'='*60}")
        
        if overall_success_rate >= 90:
            print("✅ All debugging functionality is working correctly!")
            return 0
        elif overall_success_rate >= 80:
            print("⚠️ Most debugging functionality is working with some issues.")
            return 1
        else:
            print("❌ Significant issues detected in debugging functionality.")
            return 2
            
    except Exception as e:
        runner.logger.error(f"Test execution failed: {e}")
        print(f"❌ Test execution failed: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())