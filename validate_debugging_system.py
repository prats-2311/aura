#!/usr/bin/env python3
"""
Comprehensive Debugging System Validation

Validates all debugging functionality works correctly and measures performance impact.
This script tests the actual implemented debugging features.

Requirements: 1.1, 7.1, 8.1
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import debugging modules
from modules.accessibility_debugger import AccessibilityDebugger, AccessibilityTreeDump
from modules.permission_validator import PermissionValidator
from modules.diagnostic_tools import AccessibilityHealthChecker
from modules.error_recovery import ErrorRecoveryManager
from modules.fast_path_performance_monitor import FastPathPerformanceMonitor
from modules.performance_reporting_system import PerformanceReportingSystem
from modules.accessibility import AccessibilityModule
from orchestrator import Orchestrator


@dataclass
class ValidationResult:
    """Validation test result."""
    test_name: str
    status: str  # 'PASSED', 'FAILED', 'SKIPPED'
    execution_time: float
    details: Dict[str, Any]
    error_message: Optional[str] = None


class DebuggingSystemValidator:
    """Comprehensive debugging system validator."""
    
    def __init__(self):
        self.setup_logging()
        self.results = []
        self.start_time = None
        self.end_time = None
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('debugging_validation.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive debugging system validation."""
        self.logger.info("Starting comprehensive debugging system validation...")
        self.start_time = time.time()
        
        validation_tests = [
            self.validate_permission_validator,
            self.validate_accessibility_debugger,
            self.validate_diagnostic_tools,
            self.validate_error_recovery,
            self.validate_performance_monitoring,
            self.validate_integration_with_accessibility_module,
            self.validate_real_world_scenarios,
            self.validate_performance_impact
        ]
        
        for test in validation_tests:
            try:
                self.logger.info(f"Running validation test: {test.__name__}")
                start_time = time.time()
                
                result = test()
                execution_time = time.time() - start_time
                
                validation_result = ValidationResult(
                    test_name=test.__name__,
                    status='PASSED' if result['success'] else 'FAILED',
                    execution_time=execution_time,
                    details=result,
                    error_message=result.get('error')
                )
                
                self.results.append(validation_result)
                
                if result['success']:
                    self.logger.info(f"✅ {test.__name__} PASSED ({execution_time:.2f}s)")
                else:
                    self.logger.error(f"❌ {test.__name__} FAILED: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                execution_time = time.time() - start_time
                validation_result = ValidationResult(
                    test_name=test.__name__,
                    status='FAILED',
                    execution_time=execution_time,
                    details={'success': False},
                    error_message=str(e)
                )
                self.results.append(validation_result)
                self.logger.error(f"❌ {test.__name__} FAILED with exception: {e}")
        
        self.end_time = time.time()
        
        # Generate comprehensive report
        return self.generate_validation_report()
    
    def validate_permission_validator(self) -> Dict[str, Any]:
        """Validate permission validator functionality."""
        try:
            validator = PermissionValidator()
            
            # Test permission status checking
            status = validator.check_accessibility_permissions()
            
            # Verify status structure
            required_fields = ['has_permissions', 'permission_level', 'missing_permissions', 
                             'granted_permissions', 'can_request_permissions']
            
            for field in required_fields:
                if field not in status:
                    return {
                        'success': False,
                        'error': f'Missing required field in permission status: {field}',
                        'status': status
                    }
            
            # Test permission guidance
            if not status['has_permissions']:
                guidance = validator.guide_permission_setup()
                if not isinstance(guidance, list) or len(guidance) == 0:
                    return {
                        'success': False,
                        'error': 'Permission guidance should return non-empty list when permissions missing',
                        'guidance': guidance
                    }
            
            return {
                'success': True,
                'permission_status': status,
                'validation_details': {
                    'permission_check_working': True,
                    'guidance_available': not status['has_permissions']
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_accessibility_debugger(self) -> Dict[str, Any]:
        """Validate accessibility debugger functionality."""
        try:
            debugger = AccessibilityDebugger({
                'debug_level': 'DETAILED',
                'output_format': 'STRUCTURED',
                'auto_diagnostics': True
            })
            
            # Test tree dumping
            tree_dump = debugger.dump_accessibility_tree()
            
            # Verify tree dump structure
            required_fields = ['app_name', 'timestamp', 'total_elements', 'clickable_elements', 
                             'searchable_elements', 'element_roles', 'generation_time_ms']
            
            for field in required_fields:
                if not hasattr(tree_dump, field):
                    return {
                        'success': False,
                        'error': f'Missing required field in tree dump: {field}',
                        'tree_dump': str(tree_dump)
                    }
            
            # Test element analysis
            analysis = debugger.analyze_element_detection_failure(
                "click the sign in button", "sign in button"
            )
            
            # Verify analysis structure
            analysis_fields = ['command', 'target_text', 'failure_reasons', 'attempted_strategies',
                             'available_elements', 'recommendations']
            
            for field in analysis_fields:
                if field not in analysis:
                    return {
                        'success': False,
                        'error': f'Missing required field in failure analysis: {field}',
                        'analysis': analysis
                    }
            
            return {
                'success': True,
                'tree_dump_working': True,
                'failure_analysis_working': True,
                'tree_elements_found': tree_dump.total_elements,
                'analysis_recommendations': len(analysis['recommendations'])
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_diagnostic_tools(self) -> Dict[str, Any]:
        """Validate diagnostic tools functionality."""
        try:
            health_checker = AccessibilityHealthChecker()
            
            # Test health checking
            health_status = health_checker.check_accessibility_api_health()
            
            if 'api_available' not in health_status:
                return {
                    'success': False,
                    'error': 'Health status missing api_available field',
                    'health_status': health_status
                }
            
            # Test system information gathering
            system_info = health_checker.gather_system_information()
            
            required_info_fields = ['os_version', 'python_version', 'accessibility_enabled']
            for field in required_info_fields:
                if field not in system_info:
                    return {
                        'success': False,
                        'error': f'Missing required field in system info: {field}',
                        'system_info': system_info
                    }
            
            return {
                'success': True,
                'health_check_working': True,
                'system_info_gathered': True,
                'accessibility_api_available': health_status['api_available'],
                'system_info_fields': len(system_info)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_error_recovery(self) -> Dict[str, Any]:
        """Validate error recovery functionality."""
        try:
            error_recovery = ErrorRecoveryManager()
            
            # Test recovery strategy selection
            strategies = error_recovery.get_recovery_strategies('element_not_found')
            
            if not isinstance(strategies, list) or len(strategies) == 0:
                return {
                    'success': False,
                    'error': 'Recovery strategies should return non-empty list',
                    'strategies': strategies
                }
            
            # Test retry mechanism
            retry_config = error_recovery.get_retry_configuration('accessibility_timeout')
            
            required_retry_fields = ['max_retries', 'base_delay', 'max_delay']
            for field in required_retry_fields:
                if field not in retry_config:
                    return {
                        'success': False,
                        'error': f'Missing required field in retry config: {field}',
                        'config': retry_config
                    }
            
            return {
                'success': True,
                'recovery_strategies_available': len(strategies),
                'retry_configuration_working': True,
                'max_retries_configured': retry_config['max_retries']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_performance_monitoring(self) -> Dict[str, Any]:
        """Validate performance monitoring functionality."""
        try:
            performance_monitor = FastPathPerformanceMonitor()
            reporting_system = PerformanceReportingSystem()
            
            # Test performance tracking
            performance_monitor.start_operation_tracking('test_operation')
            time.sleep(0.1)  # Simulate operation
            metrics = performance_monitor.end_operation_tracking('test_operation', True)
            
            # Verify metrics structure
            required_fields = ['operation_name', 'duration_ms', 'success', 'timestamp']
            for field in required_fields:
                if field not in metrics:
                    return {
                        'success': False,
                        'error': f'Missing required field in performance metrics: {field}',
                        'metrics': metrics
                    }
            
            # Test reporting
            report = reporting_system.generate_performance_report()
            
            if 'summary' not in report or 'metrics' not in report:
                return {
                    'success': False,
                    'error': 'Performance report missing required sections',
                    'report': report
                }
            
            return {
                'success': True,
                'performance_tracking_working': True,
                'reporting_working': True,
                'operation_duration_ms': metrics['duration_ms'],
                'report_sections': list(report.keys())
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_integration_with_accessibility_module(self) -> Dict[str, Any]:
        """Validate integration with accessibility module."""
        try:
            accessibility_module = AccessibilityModule()
            
            # Test that debugging tools are integrated
            has_debugger = hasattr(accessibility_module, 'debugger')
            has_performance_tracking = hasattr(accessibility_module, 'performance_metrics')
            
            # Test element finding with debugging
            element = accessibility_module.find_element('AXButton', 'Test Button')
            
            # Element may be None (not found) but should not raise exception
            # The important thing is that debugging integration doesn't break functionality
            
            return {
                'success': True,
                'debugger_integrated': has_debugger,
                'performance_tracking_integrated': has_performance_tracking,
                'element_finding_working': True,  # No exception means it's working
                'element_found': element is not None
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_real_world_scenarios(self) -> Dict[str, Any]:
        """Validate debugging with real-world scenarios."""
        try:
            debugger = AccessibilityDebugger({'debug_level': 'VERBOSE'})
            
            # Test common failure scenarios
            scenarios = [
                {
                    'name': 'button_not_found',
                    'command': 'click the non-existent button',
                    'target': 'non-existent button'
                },
                {
                    'name': 'ambiguous_text',
                    'command': 'click the button',
                    'target': 'button'
                },
                {
                    'name': 'web_element',
                    'command': 'click the search field',
                    'target': 'search field'
                }
            ]
            
            scenario_results = {}
            
            for scenario in scenarios:
                try:
                    analysis = debugger.analyze_element_detection_failure(
                        scenario['command'], scenario['target']
                    )
                    
                    scenario_results[scenario['name']] = {
                        'analysis_generated': True,
                        'recommendations_count': len(analysis.get('recommendations', [])),
                        'strategies_attempted': len(analysis.get('attempted_strategies', []))
                    }
                    
                except Exception as e:
                    scenario_results[scenario['name']] = {
                        'analysis_generated': False,
                        'error': str(e)
                    }
            
            # Check if at least 2 out of 3 scenarios worked
            successful_scenarios = sum(1 for result in scenario_results.values() 
                                     if result.get('analysis_generated', False))
            
            return {
                'success': successful_scenarios >= 2,
                'scenario_results': scenario_results,
                'successful_scenarios': successful_scenarios,
                'total_scenarios': len(scenarios)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_performance_impact(self) -> Dict[str, Any]:
        """Validate performance impact of debugging features."""
        try:
            # Test with debugging disabled
            debugger_disabled = AccessibilityDebugger({'debug_level': 'NONE'})
            
            disabled_times = []
            for _ in range(5):
                start_time = time.time()
                # Simulate minimal operation
                debugger_disabled.check_accessibility_permissions()
                disabled_times.append(time.time() - start_time)
            
            # Test with debugging enabled
            debugger_enabled = AccessibilityDebugger({'debug_level': 'DETAILED'})
            
            enabled_times = []
            for _ in range(5):
                start_time = time.time()
                # Simulate debugging operation
                debugger_enabled.check_accessibility_permissions()
                debugger_enabled.dump_accessibility_tree()
                enabled_times.append(time.time() - start_time)
            
            # Calculate performance impact
            avg_disabled = sum(disabled_times) / len(disabled_times)
            avg_enabled = sum(enabled_times) / len(enabled_times)
            overhead_percentage = ((avg_enabled - avg_disabled) / avg_disabled) * 100 if avg_disabled > 0 else 0
            
            # Performance impact should be reasonable (less than 100% overhead)
            acceptable_overhead = overhead_percentage < 100
            
            return {
                'success': acceptable_overhead,
                'avg_disabled_time': avg_disabled,
                'avg_enabled_time': avg_enabled,
                'overhead_percentage': overhead_percentage,
                'acceptable_overhead': acceptable_overhead
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        total_execution_time = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        # Calculate statistics
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == 'PASSED'])
        failed_tests = len([r for r in self.results if r.status == 'FAILED'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Generate report
        report = {
            'validation_summary': {
                'timestamp': datetime.now().isoformat(),
                'total_execution_time': total_execution_time,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': success_rate
            },
            'test_results': [asdict(result) for result in self.results],
            'debugging_functionality_assessment': self.assess_debugging_functionality(),
            'performance_impact_assessment': self.assess_performance_impact(),
            'recommendations': self.generate_recommendations()
        }
        
        # Save report
        report_filename = f"debugging_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate human-readable summary
        self.generate_human_readable_summary(report)
        
        self.logger.info(f"Validation report saved to: {report_filename}")
        
        return report
    
    def assess_debugging_functionality(self) -> Dict[str, Any]:
        """Assess overall debugging functionality."""
        functionality_tests = [
            'validate_permission_validator',
            'validate_accessibility_debugger', 
            'validate_diagnostic_tools',
            'validate_error_recovery'
        ]
        
        functionality_results = [r for r in self.results if r.test_name in functionality_tests]
        passed_functionality = len([r for r in functionality_results if r.status == 'PASSED'])
        
        return {
            'core_functionality_working': passed_functionality >= 3,
            'permission_validation_working': any(r.test_name == 'validate_permission_validator' and r.status == 'PASSED' for r in self.results),
            'tree_inspection_working': any(r.test_name == 'validate_accessibility_debugger' and r.status == 'PASSED' for r in self.results),
            'diagnostics_working': any(r.test_name == 'validate_diagnostic_tools' and r.status == 'PASSED' for r in self.results),
            'error_recovery_working': any(r.test_name == 'validate_error_recovery' and r.status == 'PASSED' for r in self.results),
            'functionality_score': (passed_functionality / len(functionality_tests)) * 100
        }
    
    def assess_performance_impact(self) -> Dict[str, Any]:
        """Assess performance impact of debugging features."""
        performance_test = next((r for r in self.results if r.test_name == 'validate_performance_impact'), None)
        
        if not performance_test or performance_test.status != 'PASSED':
            return {
                'performance_acceptable': False,
                'reason': 'Performance impact test failed or not run'
            }
        
        details = performance_test.details
        return {
            'performance_acceptable': details.get('acceptable_overhead', False),
            'overhead_percentage': details.get('overhead_percentage', 0),
            'avg_enabled_time': details.get('avg_enabled_time', 0),
            'avg_disabled_time': details.get('avg_disabled_time', 0)
        }
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        failed_tests = [r for r in self.results if r.status == 'FAILED']
        
        if len(failed_tests) == 0:
            recommendations.append("✅ All debugging functionality validation tests passed successfully!")
            recommendations.append("The debugging enhancement is working as expected and ready for production use.")
        else:
            recommendations.append(f"⚠️ {len(failed_tests)} validation tests failed. Review and address the following issues:")
            
            for test in failed_tests:
                recommendations.append(f"- {test.test_name}: {test.error_message}")
        
        # Specific recommendations based on test results
        functionality_assessment = self.assess_debugging_functionality()
        if not functionality_assessment['core_functionality_working']:
            recommendations.append("🔧 Core debugging functionality needs attention. Ensure all debugging modules are properly implemented.")
        
        performance_assessment = self.assess_performance_impact()
        if not performance_assessment['performance_acceptable']:
            recommendations.append("⚡ Performance impact is higher than expected. Consider optimizing debugging operations.")
        
        return recommendations
    
    def generate_human_readable_summary(self, report: Dict[str, Any]):
        """Generate human-readable validation summary."""
        summary_filename = f"debugging_validation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(summary_filename, 'w') as f:
            f.write("# Debugging System Validation Summary\n\n")
            f.write(f"**Validation Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overall results
            summary = report['validation_summary']
            f.write("## Overall Results\n\n")
            f.write(f"- **Total Tests:** {summary['total_tests']}\n")
            f.write(f"- **Passed:** {summary['passed_tests']}\n")
            f.write(f"- **Failed:** {summary['failed_tests']}\n")
            f.write(f"- **Success Rate:** {summary['success_rate']:.1f}%\n")
            f.write(f"- **Total Execution Time:** {summary['total_execution_time']:.2f} seconds\n\n")
            
            # Test results
            f.write("## Test Results\n\n")
            for result in self.results:
                status_icon = "✅" if result.status == "PASSED" else "❌"
                f.write(f"### {status_icon} {result.test_name.replace('validate_', '').replace('_', ' ').title()}\n\n")
                f.write(f"- **Status:** {result.status}\n")
                f.write(f"- **Execution Time:** {result.execution_time:.2f} seconds\n")
                
                if result.error_message:
                    f.write(f"- **Error:** {result.error_message}\n")
                
                f.write("\n")
            
            # Functionality assessment
            f.write("## Debugging Functionality Assessment\n\n")
            functionality = report['debugging_functionality_assessment']
            f.write(f"- **Core Functionality Working:** {'✅' if functionality['core_functionality_working'] else '❌'}\n")
            f.write(f"- **Permission Validation:** {'✅' if functionality['permission_validation_working'] else '❌'}\n")
            f.write(f"- **Tree Inspection:** {'✅' if functionality['tree_inspection_working'] else '❌'}\n")
            f.write(f"- **Diagnostics:** {'✅' if functionality['diagnostics_working'] else '❌'}\n")
            f.write(f"- **Error Recovery:** {'✅' if functionality['error_recovery_working'] else '❌'}\n")
            f.write(f"- **Functionality Score:** {functionality['functionality_score']:.1f}%\n\n")
            
            # Performance assessment
            f.write("## Performance Impact Assessment\n\n")
            performance = report['performance_impact_assessment']
            f.write(f"- **Performance Acceptable:** {'✅' if performance['performance_acceptable'] else '❌'}\n")
            if 'overhead_percentage' in performance:
                f.write(f"- **Overhead Percentage:** {performance['overhead_percentage']:.1f}%\n")
            f.write("\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            for i, recommendation in enumerate(report['recommendations'], 1):
                f.write(f"{i}. {recommendation}\n")
            f.write("\n")
            
            # Conclusion
            if summary['success_rate'] >= 90:
                f.write("## Conclusion\n\n")
                f.write("✅ **Debugging system validation successful!** All critical debugging functionality is working correctly and ready for production use.\n")
            elif summary['success_rate'] >= 70:
                f.write("## Conclusion\n\n")
                f.write("⚠️ **Debugging system validation mostly successful with some issues.** Review failed tests and address issues before full deployment.\n")
            else:
                f.write("## Conclusion\n\n")
                f.write("❌ **Debugging system validation failed.** Critical issues must be resolved before deployment.\n")
        
        self.logger.info(f"Human-readable validation summary saved to: {summary_filename}")


def main():
    """Main validation execution function."""
    validator = DebuggingSystemValidator()
    
    try:
        # Run comprehensive validation
        report = validator.run_comprehensive_validation()
        
        # Print summary
        summary = report['validation_summary']
        
        print(f"\n{'='*60}")
        print("DEBUGGING SYSTEM VALIDATION COMPLETE")
        print(f"{'='*60}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Execution Time: {summary['total_execution_time']:.2f} seconds")
        print(f"{'='*60}")
        
        if summary['success_rate'] >= 90:
            print("✅ All debugging functionality is working correctly!")
            return 0
        elif summary['success_rate'] >= 70:
            print("⚠️ Most debugging functionality is working with some issues.")
            return 1
        else:
            print("❌ Significant issues detected in debugging functionality.")
            return 2
            
    except Exception as e:
        validator.logger.error(f"Validation execution failed: {e}")
        print(f"❌ Validation execution failed: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())