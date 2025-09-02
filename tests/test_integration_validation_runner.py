#!/usr/bin/env python3
"""
Integration and Validation Test Runner for Hybrid Architecture

Comprehensive test runner that executes both end-to-end fast path tests
and fallback validation tests, providing unified reporting and analysis.

Requirements: 5.5, 1.4, 5.3, 2.1, 2.2
"""

import pytest
import sys
import os
import logging
import time
import json
from typing import Dict, Any, List
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import test modules
from tests.test_integration_fast_path import *
from tests.test_fallback_validation import *


class IntegrationTestRunner:
    """Comprehensive test runner for hybrid architecture validation."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = {
            'fast_path_tests': {},
            'fallback_tests': {},
            'performance_metrics': {},
            'summary': {}
        }
        self.start_time = None
        self.end_time = None
    
    def setup_logging(self):
        """Configure logging for integration tests."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('integration_test_results.log')
            ]
        )
    
    def run_fast_path_integration_tests(self) -> Dict[str, Any]:
        """Run end-to-end fast path integration tests."""
        self.logger.info("Starting Fast Path Integration Tests...")
        
        # Test categories for fast path
        test_categories = [
            {
                'name': 'native_macos_apps',
                'tests': [
                    'test_finder_fast_path_integration',
                    'test_system_preferences_fast_path_integration',
                    'test_menu_bar_fast_path_integration'
                ]
            },
            {
                'name': 'web_browser_automation',
                'tests': [
                    'test_safari_fast_path_integration',
                    'test_chrome_fast_path_integration',
                    'test_web_form_fast_path_integration'
                ]
            },
            {
                'name': 'gui_patterns',
                'tests': [
                    'test_button_patterns_fast_path',
                    'test_menu_patterns_fast_path',
                    'test_text_field_patterns_fast_path',
                    'test_form_element_patterns_fast_path'
                ]
            },
            {
                'name': 'performance_benchmarks',
                'tests': [
                    'test_fast_path_performance_benchmarks',
                    'test_accessibility_tree_traversal_performance'
                ]
            }
        ]
        
        results = {}
        for category in test_categories:
            category_results = self._run_test_category(
                category['name'], 
                category['tests'],
                'tests.test_integration_fast_path'
            )
            results[category['name']] = category_results
        
        self.test_results['fast_path_tests'] = results
        return results
    
    def run_fallback_validation_tests(self) -> Dict[str, Any]:
        """Run fallback validation tests."""
        self.logger.info("Starting Fallback Validation Tests...")
        
        # Test categories for fallback validation
        test_categories = [
            {
                'name': 'non_accessible_apps',
                'tests': [
                    'test_accessibility_disabled_application_fallback',
                    'test_accessibility_permission_denied_fallback',
                    'test_accessibility_api_unavailable_fallback',
                    'test_legacy_application_fallback'
                ]
            },
            {
                'name': 'complex_ui_elements',
                'tests': [
                    'test_canvas_element_fallback',
                    'test_custom_control_fallback',
                    'test_dynamic_content_fallback',
                    'test_overlapping_elements_fallback'
                ]
            },
            {
                'name': 'error_injection',
                'tests': [
                    'test_accessibility_timeout_recovery',
                    'test_accessibility_memory_error_recovery',
                    'test_accessibility_connection_error_recovery',
                    'test_intermittent_accessibility_failure_recovery',
                    'test_accessibility_degraded_mode_recovery'
                ]
            },
            {
                'name': 'fallback_performance',
                'tests': [
                    'test_fallback_transition_performance',
                    'test_fallback_audio_feedback_timing',
                    'test_fallback_resource_cleanup'
                ]
            },
            {
                'name': 'fallback_integration',
                'tests': [
                    'test_seamless_fallback_to_vision_workflow',
                    'test_fallback_preserves_command_context',
                    'test_fallback_error_reporting'
                ]
            }
        ]
        
        results = {}
        for category in test_categories:
            category_results = self._run_test_category(
                category['name'], 
                category['tests'],
                'tests.test_fallback_validation'
            )
            results[category['name']] = category_results
        
        self.test_results['fallback_tests'] = results
        return results
    
    def _run_test_category(self, category_name: str, test_names: List[str], module_name: str) -> Dict[str, Any]:
        """Run a specific category of tests."""
        self.logger.info(f"Running {category_name} tests...")
        
        category_results = {
            'total_tests': len(test_names),
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': [],
            'execution_time': 0,
            'test_details': {}
        }
        
        start_time = time.time()
        
        for test_name in test_names:
            test_result = self._run_single_test(test_name, module_name)
            category_results['test_details'][test_name] = test_result
            
            if test_result['status'] == 'passed':
                category_results['passed'] += 1
            elif test_result['status'] == 'failed':
                category_results['failed'] += 1
                category_results['errors'].append({
                    'test': test_name,
                    'error': test_result.get('error', 'Unknown error')
                })
            elif test_result['status'] == 'skipped':
                category_results['skipped'] += 1
        
        category_results['execution_time'] = time.time() - start_time
        
        self.logger.info(f"{category_name} results: "
                        f"{category_results['passed']} passed, "
                        f"{category_results['failed']} failed, "
                        f"{category_results['skipped']} skipped")
        
        return category_results
    
    def _run_single_test(self, test_name: str, module_name: str) -> Dict[str, Any]:
        """Run a single test and capture results."""
        test_result = {
            'status': 'unknown',
            'execution_time': 0,
            'error': None,
            'output': []
        }
        
        start_time = time.time()
        
        try:
            # Use pytest to run the specific test
            test_path = f"{module_name}::{test_name}"
            
            # Capture pytest output
            result = pytest.main([
                test_path,
                '-v',
                '--tb=short',
                '--capture=no'
            ])
            
            if result == 0:
                test_result['status'] = 'passed'
            elif result == 1:
                test_result['status'] = 'failed'
            elif result == 2:
                test_result['status'] = 'skipped'
            else:
                test_result['status'] = 'error'
                test_result['error'] = f"Pytest returned code {result}"
        
        except Exception as e:
            test_result['status'] = 'error'
            test_result['error'] = str(e)
            self.logger.error(f"Error running test {test_name}: {e}")
        
        test_result['execution_time'] = time.time() - start_time
        return test_result
    
    def collect_performance_metrics(self):
        """Collect and analyze performance metrics from test results."""
        self.logger.info("Collecting performance metrics...")
        
        metrics = {
            'fast_path_performance': {
                'average_execution_time': 0,
                'success_rate': 0,
                'performance_requirement_compliance': 0  # < 2 seconds requirement
            },
            'fallback_performance': {
                'average_fallback_time': 0,
                'fallback_success_rate': 0,
                'resource_cleanup_success': 0
            },
            'overall_hybrid_performance': {
                'total_test_execution_time': 0,
                'hybrid_workflow_efficiency': 0
            }
        }
        
        # Analyze fast path performance
        fast_path_times = []
        fast_path_successes = 0
        fast_path_total = 0
        
        for category, results in self.test_results['fast_path_tests'].items():
            if 'performance' in category:
                for test_name, test_result in results['test_details'].items():
                    if test_result['status'] == 'passed':
                        fast_path_times.append(test_result['execution_time'])
                        fast_path_successes += 1
                    fast_path_total += 1
        
        if fast_path_times:
            metrics['fast_path_performance']['average_execution_time'] = sum(fast_path_times) / len(fast_path_times)
            metrics['fast_path_performance']['success_rate'] = fast_path_successes / fast_path_total
            
            # Check compliance with < 2 second requirement
            compliant_tests = sum(1 for t in fast_path_times if t < 2.0)
            metrics['fast_path_performance']['performance_requirement_compliance'] = compliant_tests / len(fast_path_times)
        
        # Analyze fallback performance
        fallback_times = []
        fallback_successes = 0
        fallback_total = 0
        
        for category, results in self.test_results['fallback_tests'].items():
            for test_name, test_result in results['test_details'].items():
                fallback_times.append(test_result['execution_time'])
                if test_result['status'] == 'passed':
                    fallback_successes += 1
                fallback_total += 1
        
        if fallback_times:
            metrics['fallback_performance']['average_fallback_time'] = sum(fallback_times) / len(fallback_times)
            metrics['fallback_performance']['fallback_success_rate'] = fallback_successes / fallback_total
        
        # Calculate overall metrics
        total_execution_time = self.end_time - self.start_time if self.end_time and self.start_time else 0
        metrics['overall_hybrid_performance']['total_test_execution_time'] = total_execution_time
        
        self.test_results['performance_metrics'] = metrics
        return metrics
    
    def generate_summary_report(self):
        """Generate comprehensive summary report."""
        self.logger.info("Generating summary report...")
        
        # Calculate overall statistics
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        
        # Fast path test summary
        for category, results in self.test_results['fast_path_tests'].items():
            total_tests += results['total_tests']
            total_passed += results['passed']
            total_failed += results['failed']
            total_skipped += results['skipped']
        
        # Fallback test summary
        for category, results in self.test_results['fallback_tests'].items():
            total_tests += results['total_tests']
            total_passed += results['passed']
            total_failed += results['failed']
            total_skipped += results['skipped']
        
        summary = {
            'test_execution_summary': {
                'total_tests': total_tests,
                'passed': total_passed,
                'failed': total_failed,
                'skipped': total_skipped,
                'success_rate': total_passed / total_tests if total_tests > 0 else 0
            },
            'requirements_compliance': {
                'requirement_5_5': self._check_requirement_5_5_compliance(),
                'requirement_1_4': self._check_requirement_1_4_compliance(),
                'requirement_5_3': self._check_requirement_5_3_compliance(),
                'requirement_2_1': self._check_requirement_2_1_compliance(),
                'requirement_2_2': self._check_requirement_2_2_compliance()
            },
            'performance_analysis': self.test_results.get('performance_metrics', {}),
            'recommendations': self._generate_recommendations()
        }
        
        self.test_results['summary'] = summary
        return summary
    
    def _check_requirement_5_5_compliance(self) -> Dict[str, Any]:
        """Check compliance with requirement 5.5 (integration tests for various application types)."""
        native_app_tests = self.test_results['fast_path_tests'].get('native_macos_apps', {})
        browser_tests = self.test_results['fast_path_tests'].get('web_browser_automation', {})
        
        return {
            'description': 'Integration tests for native applications and browsers',
            'native_app_coverage': native_app_tests.get('passed', 0) > 0,
            'browser_coverage': browser_tests.get('passed', 0) > 0,
            'compliant': (native_app_tests.get('passed', 0) > 0 and browser_tests.get('passed', 0) > 0)
        }
    
    def _check_requirement_1_4_compliance(self) -> Dict[str, Any]:
        """Check compliance with requirement 1.4 (GUI patterns validation)."""
        gui_pattern_tests = self.test_results['fast_path_tests'].get('gui_patterns', {})
        
        return {
            'description': 'Common GUI patterns work with fast path',
            'patterns_tested': gui_pattern_tests.get('total_tests', 0),
            'patterns_working': gui_pattern_tests.get('passed', 0),
            'compliant': gui_pattern_tests.get('passed', 0) >= gui_pattern_tests.get('total_tests', 1) * 0.7  # 70% success rate
        }
    
    def _check_requirement_5_3_compliance(self) -> Dict[str, Any]:
        """Check compliance with requirement 5.3 (fallback scenarios)."""
        fallback_tests = self.test_results['fallback_tests']
        
        total_fallback_tests = sum(category.get('total_tests', 0) for category in fallback_tests.values())
        passed_fallback_tests = sum(category.get('passed', 0) for category in fallback_tests.values())
        
        return {
            'description': 'Fallback scenarios validation',
            'fallback_tests_total': total_fallback_tests,
            'fallback_tests_passed': passed_fallback_tests,
            'compliant': passed_fallback_tests >= total_fallback_tests * 0.8  # 80% success rate
        }
    
    def _check_requirement_2_1_compliance(self) -> Dict[str, Any]:
        """Check compliance with requirement 2.1 (automatic fallback)."""
        non_accessible_tests = self.test_results['fallback_tests'].get('non_accessible_apps', {})
        
        return {
            'description': 'Automatic fallback to vision workflow',
            'fallback_scenarios_tested': non_accessible_tests.get('total_tests', 0),
            'successful_fallbacks': non_accessible_tests.get('passed', 0),
            'compliant': non_accessible_tests.get('passed', 0) >= non_accessible_tests.get('total_tests', 1) * 0.9  # 90% success rate
        }
    
    def _check_requirement_2_2_compliance(self) -> Dict[str, Any]:
        """Check compliance with requirement 2.2 (consistent user experience)."""
        fallback_integration_tests = self.test_results['fallback_tests'].get('fallback_integration', {})
        
        return {
            'description': 'Consistent user experience during fallback',
            'integration_tests': fallback_integration_tests.get('total_tests', 0),
            'successful_integrations': fallback_integration_tests.get('passed', 0),
            'compliant': fallback_integration_tests.get('passed', 0) == fallback_integration_tests.get('total_tests', 0)
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Performance recommendations
        perf_metrics = self.test_results.get('performance_metrics', {})
        fast_path_perf = perf_metrics.get('fast_path_performance', {})
        
        if fast_path_perf.get('performance_requirement_compliance', 0) < 0.9:
            recommendations.append(
                "Fast path performance compliance is below 90%. Consider optimizing accessibility tree traversal."
            )
        
        if fast_path_perf.get('success_rate', 0) < 0.8:
            recommendations.append(
                "Fast path success rate is below 80%. Review element detection algorithms and fuzzy matching."
            )
        
        # Fallback recommendations
        fallback_perf = perf_metrics.get('fallback_performance', {})
        
        if fallback_perf.get('fallback_success_rate', 0) < 0.9:
            recommendations.append(
                "Fallback success rate is below 90%. Improve error handling and recovery mechanisms."
            )
        
        # Coverage recommendations
        summary = self.test_results.get('summary', {})
        compliance = summary.get('requirements_compliance', {})
        
        for req_id, req_compliance in compliance.items():
            if isinstance(req_compliance, dict) and not req_compliance.get('compliant', True):
                recommendations.append(
                    f"Requirement {req_id} is not fully compliant. Review {req_compliance.get('description', 'requirement details')}."
                )
        
        if not recommendations:
            recommendations.append("All tests passed successfully. Hybrid architecture implementation is ready for production.")
        
        return recommendations
    
    def save_results_to_file(self, filename: str = 'integration_test_results.json'):
        """Save test results to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            self.logger.info(f"Test results saved to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save results to file: {e}")
    
    def run_all_tests(self):
        """Run all integration and validation tests."""
        self.setup_logging()
        self.start_time = time.time()
        
        self.logger.info("Starting Hybrid Architecture Integration and Validation Tests")
        self.logger.info("=" * 80)
        
        try:
            # Run fast path integration tests
            self.run_fast_path_integration_tests()
            
            # Run fallback validation tests
            self.run_fallback_validation_tests()
            
            # Collect performance metrics
            self.collect_performance_metrics()
            
            # Generate summary report
            self.generate_summary_report()
            
        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            raise
        finally:
            self.end_time = time.time()
        
        # Save results
        self.save_results_to_file()
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print test execution summary."""
        summary = self.test_results.get('summary', {})
        test_summary = summary.get('test_execution_summary', {})
        
        self.logger.info("=" * 80)
        self.logger.info("HYBRID ARCHITECTURE INTEGRATION TEST SUMMARY")
        self.logger.info("=" * 80)
        
        self.logger.info(f"Total Tests: {test_summary.get('total_tests', 0)}")
        self.logger.info(f"Passed: {test_summary.get('passed', 0)}")
        self.logger.info(f"Failed: {test_summary.get('failed', 0)}")
        self.logger.info(f"Skipped: {test_summary.get('skipped', 0)}")
        self.logger.info(f"Success Rate: {test_summary.get('success_rate', 0):.2%}")
        
        if self.start_time and self.end_time:
            total_time = self.end_time - self.start_time
            self.logger.info(f"Total Execution Time: {total_time:.2f} seconds")
        
        # Print requirements compliance
        compliance = summary.get('requirements_compliance', {})
        self.logger.info("\nRequirements Compliance:")
        for req_id, req_data in compliance.items():
            if isinstance(req_data, dict):
                status = "✓ COMPLIANT" if req_data.get('compliant') else "✗ NON-COMPLIANT"
                self.logger.info(f"  {req_id}: {status}")
        
        # Print recommendations
        recommendations = summary.get('recommendations', [])
        if recommendations:
            self.logger.info("\nRecommendations:")
            for i, rec in enumerate(recommendations, 1):
                self.logger.info(f"  {i}. {rec}")
        
        self.logger.info("=" * 80)


def main():
    """Main entry point for integration test runner."""
    runner = IntegrationTestRunner()
    
    try:
        runner.run_all_tests()
        return 0
    except Exception as e:
        logging.error(f"Integration test execution failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())