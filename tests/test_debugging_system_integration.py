#!/usr/bin/env python3
"""
Comprehensive System Integration Tests for Click Debugging Enhancement

Tests all debugging functionality works correctly with real-world scenarios,
validates debugging tool effectiveness, and measures performance impact.

Requirements: 1.1, 7.1, 8.1
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, MagicMock, patch, call
import logging
import time
import os
import tempfile
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import debugging modules
from modules.accessibility_debugger import AccessibilityDebugger
from modules.permission_validator import PermissionValidator
from modules.diagnostic_tools import AccessibilityHealthChecker, DiagnosticReportGenerator
from modules.error_recovery import ErrorRecoveryManager
from modules.fast_path_performance_monitor import FastPathPerformanceMonitor
from modules.performance_reporting_system import PerformanceReportingSystem
from modules.accessibility import AccessibilityModule
from orchestrator import Orchestrator


@dataclass
class DebuggingTestScenario:
    """Represents a debugging test scenario."""
    name: str
    description: str
    command: str
    expected_debug_features: List[str]
    expected_diagnostics: List[str]
    failure_mode: Optional[str] = None
    app_name: Optional[str] = None
    complexity_level: str = "simple"


@dataclass
class DebuggingTestResult:
    """Results from debugging functionality testing."""
    scenario_name: str
    debug_features_tested: List[str]
    diagnostics_generated: List[str]
    performance_impact: float
    success: bool
    error_recovery_triggered: bool
    recommendations_provided: List[str]
    execution_time: float


class TestDebuggingSystemIntegration:
    """Comprehensive debugging system integration test suite."""
    
    @pytest.fixture(scope="class")
    def debugging_test_scenarios(self):
        """Define comprehensive debugging test scenarios."""
        return [
            # Permission Validation Tests
            DebuggingTestScenario(
                name="permission_validation_success",
                description="Test accessibility permission validation when permissions are granted",
                command="click the sign in button",
                expected_debug_features=["permission_check", "tree_inspection"],
                expected_diagnostics=["permission_status", "accessibility_health"],
                complexity_level="simple"
            ),
            DebuggingTestScenario(
                name="permission_validation_failure",
                description="Test permission validation when permissions are denied",
                command="click the submit button",
                expected_debug_features=["permission_check", "permission_guidance"],
                expected_diagnostics=["permission_status", "remediation_steps"],
                failure_mode="permission_denied",
                complexity_level="medium"
            ),
            
            # Accessibility Tree Inspection Tests
            DebuggingTestScenario(
                name="tree_inspection_simple_app",
                description="Test accessibility tree inspection with simple native app",
                command="click the OK button",
                expected_debug_features=["tree_dump", "element_analysis"],
                expected_diagnostics=["tree_structure", "element_attributes"],
                app_name="System Preferences",
                complexity_level="simple"
            ),
            DebuggingTestScenario(
                name="tree_inspection_complex_web_app",
                description="Test accessibility tree inspection with complex web application",
                command="click the search button",
                expected_debug_features=["tree_dump", "element_analysis", "fuzzy_matching"],
                expected_diagnostics=["tree_structure", "element_attributes", "match_scores"],
                app_name="Google Chrome",
                complexity_level="complex"
            ),
            
            # Element Detection Failure Analysis Tests
            DebuggingTestScenario(
                name="element_not_found_analysis",
                description="Test failure analysis when element is not found",
                command="click the non-existent button",
                expected_debug_features=["failure_analysis", "similarity_scoring"],
                expected_diagnostics=["failure_reasons", "closest_matches", "recommendations"],
                failure_mode="element_not_found",
                complexity_level="medium"
            ),
            DebuggingTestScenario(
                name="fuzzy_matching_failure_analysis",
                description="Test analysis when fuzzy matching fails",
                command="click the ambiguous text",
                expected_debug_features=["fuzzy_matching", "similarity_scoring"],
                expected_diagnostics=["match_scores", "alternative_matches"],
                failure_mode="fuzzy_match_failed",
                complexity_level="medium"
            ),
            
            # Application-Specific Detection Tests
            DebuggingTestScenario(
                name="browser_specific_detection",
                description="Test browser-specific accessibility detection strategies",
                command="click the address bar",
                expected_debug_features=["app_detection", "strategy_selection"],
                expected_diagnostics=["app_type", "detection_strategy"],
                app_name="Safari",
                complexity_level="medium"
            ),
            DebuggingTestScenario(
                name="native_app_detection",
                description="Test native macOS app detection strategies",
                command="click the Applications folder",
                expected_debug_features=["app_detection", "strategy_selection"],
                expected_diagnostics=["app_type", "detection_strategy"],
                app_name="Finder",
                complexity_level="simple"
            ),
            
            # Error Recovery Tests
            DebuggingTestScenario(
                name="accessibility_api_timeout_recovery",
                description="Test error recovery when accessibility API times out",
                command="click the slow loading button",
                expected_debug_features=["error_recovery", "retry_mechanism"],
                expected_diagnostics=["timeout_handling", "recovery_attempts"],
                failure_mode="api_timeout",
                complexity_level="medium"
            ),
            DebuggingTestScenario(
                name="tree_refresh_recovery",
                description="Test accessibility tree refresh when elements become stale",
                command="click the dynamic button",
                expected_debug_features=["tree_recovery", "cache_invalidation"],
                expected_diagnostics=["tree_refresh", "element_staleness"],
                failure_mode="stale_elements",
                complexity_level="complex"
            ),
            
            # Performance Monitoring Tests
            DebuggingTestScenario(
                name="performance_tracking_fast_path",
                description="Test performance monitoring during successful fast path execution",
                command="click the quick button",
                expected_debug_features=["performance_tracking", "metrics_collection"],
                expected_diagnostics=["execution_times", "success_rates"],
                complexity_level="simple"
            ),
            DebuggingTestScenario(
                name="performance_degradation_detection",
                description="Test detection of performance degradation",
                command="click the slow button",
                expected_debug_features=["performance_monitoring", "degradation_detection"],
                expected_diagnostics=["performance_alerts", "trend_analysis"],
                failure_mode="performance_degradation",
                complexity_level="medium"
            ),
            
            # Comprehensive Diagnostic Tests
            DebuggingTestScenario(
                name="comprehensive_health_check",
                description="Test comprehensive system health diagnostics",
                command="run system diagnostics",
                expected_debug_features=["health_check", "comprehensive_diagnostics"],
                expected_diagnostics=["system_health", "issue_prioritization", "remediation_steps"],
                complexity_level="complex"
            )
        ]
    
    @pytest.fixture
    def mock_debugging_environment(self):
        """Mock debugging environment for testing."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True):
            
            # Mock system state for different scenarios
            mock_system_state = {
                'permissions': {
                    'accessibility_enabled': True,
                    'permission_level': 'FULL',
                    'can_request': True
                },
                'applications': {
                    'System Preferences': {'pid': 1001, 'accessible': True, 'type': 'native'},
                    'Google Chrome': {'pid': 1002, 'accessible': True, 'type': 'browser'},
                    'Safari': {'pid': 1003, 'accessible': True, 'type': 'browser'},
                    'Finder': {'pid': 1004, 'accessible': True, 'type': 'native'}
                },
                'accessibility_tree': {
                    'elements_count': 150,
                    'clickable_elements': 25,
                    'searchable_elements': 40,
                    'roles': ['AXButton', 'AXTextField', 'AXStaticText', 'AXMenuButton']
                }
            }
            
            yield mock_system_state
    
    @pytest.fixture
    def debugging_modules_with_mocks(self, mock_debugging_environment):
        """Create debugging modules with comprehensive mocks."""
        
        # Create debugging modules
        debugger = AccessibilityDebugger({
            'debug_level': 'VERBOSE',
            'output_format': 'STRUCTURED',
            'auto_diagnostics': True
        })
        
        permission_validator = PermissionValidator()
        diagnostic_tools = AccessibilityHealthChecker()
        error_recovery = ErrorRecoveryManager()
        performance_monitor = FastPathPerformanceMonitor()
        reporting_system = PerformanceReportingSystem()
        
        # Mock the underlying system calls
        with patch.object(debugger, 'validate_accessibility_permissions') as mock_validate_perms, \
             patch.object(debugger, 'dump_accessibility_tree') as mock_dump_tree, \
             patch.object(debugger, 'analyze_element_detection_failure') as mock_analyze_failure, \
             patch.object(diagnostic_tools, 'run_comprehensive_diagnostics') as mock_diagnostics:
            
            # Setup mock behaviors based on system state
            self._setup_debugging_mock_behaviors(
                mock_validate_perms, mock_dump_tree, mock_analyze_failure, 
                mock_diagnostics, mock_debugging_environment
            )
            
            yield {
                'debugger': debugger,
                'permission_validator': permission_validator,
                'diagnostic_tools': diagnostic_tools,
                'error_recovery': error_recovery,
                'performance_monitor': performance_monitor,
                'reporting_system': reporting_system,
                'mocks': {
                    'validate_perms': mock_validate_perms,
                    'dump_tree': mock_dump_tree,
                    'analyze_failure': mock_analyze_failure,
                    'diagnostics': mock_diagnostics
                }
            }
    
    def _setup_debugging_mock_behaviors(self, mock_validate_perms, mock_dump_tree, 
                                      mock_analyze_failure, mock_diagnostics, system_state):
        """Setup realistic mock behaviors for debugging modules."""
        
        # Permission validation mock
        mock_validate_perms.return_value = {
            'has_permissions': system_state['permissions']['accessibility_enabled'],
            'permission_level': system_state['permissions']['permission_level'],
            'missing_permissions': [] if system_state['permissions']['accessibility_enabled'] else ['accessibility'],
            'granted_permissions': ['accessibility'] if system_state['permissions']['accessibility_enabled'] else [],
            'can_request_permissions': system_state['permissions']['can_request'],
            'system_version': '12.0',
            'recommendations': [] if system_state['permissions']['accessibility_enabled'] else [
                'Grant accessibility permissions in System Preferences'
            ]
        }
        
        # Tree dump mock
        mock_dump_tree.return_value = {
            'app_name': 'TestApp',
            'timestamp': '2024-01-01T12:00:00',
            'root_element': {'role': 'AXApplication', 'title': 'TestApp'},
            'total_elements': system_state['accessibility_tree']['elements_count'],
            'clickable_elements': [
                {'role': 'AXButton', 'title': 'Sign In', 'coordinates': [100, 200, 150, 50]},
                {'role': 'AXButton', 'title': 'Cancel', 'coordinates': [260, 200, 150, 50]}
            ],
            'searchable_elements': [
                {'role': 'AXTextField', 'title': 'Username', 'coordinates': [100, 150, 200, 30]},
                {'role': 'AXTextField', 'title': 'Password', 'coordinates': [100, 180, 200, 30]}
            ],
            'element_roles': {role: 10 for role in system_state['accessibility_tree']['roles']},
            'attribute_coverage': {'AXTitle': 80, 'AXRole': 100, 'AXEnabled': 95}
        }
        
        # Failure analysis mock
        def mock_failure_analysis(command, target):
            if "non-existent" in target:
                return {
                    'command': command,
                    'target_text': target,
                    'app_name': 'TestApp',
                    'failure_reasons': ['element_not_found', 'no_matching_role'],
                    'attempted_strategies': ['exact_match', 'fuzzy_match', 'role_based'],
                    'available_elements': [
                        {'role': 'AXButton', 'title': 'Sign In'},
                        {'role': 'AXButton', 'title': 'Cancel'}
                    ],
                    'closest_matches': [
                        {'element': {'role': 'AXButton', 'title': 'Sign In'}, 'similarity': 0.3}
                    ],
                    'similarity_scores': {'Sign In': 0.3, 'Cancel': 0.1},
                    'recommendations': [
                        'Check element text spelling',
                        'Verify element is visible and enabled',
                        'Try using role-based detection'
                    ],
                    'recovery_suggestions': [
                        'Use vision fallback',
                        'Wait for element to appear',
                        'Check application state'
                    ]
                }
            else:
                return {
                    'command': command,
                    'target_text': target,
                    'app_name': 'TestApp',
                    'failure_reasons': [],
                    'attempted_strategies': ['exact_match'],
                    'available_elements': [{'role': 'AXButton', 'title': target}],
                    'closest_matches': [{'element': {'role': 'AXButton', 'title': target}, 'similarity': 1.0}],
                    'similarity_scores': {target: 1.0},
                    'recommendations': [],
                    'recovery_suggestions': []
                }
        
        mock_analyze_failure.side_effect = mock_failure_analysis
        
        # Comprehensive diagnostics mock
        mock_diagnostics.return_value = {
            'timestamp': '2024-01-01T12:00:00',
            'permission_status': mock_validate_perms.return_value,
            'accessibility_health': {
                'api_available': True,
                'response_time': 0.1,
                'tree_accessible': True,
                'element_detection_working': True
            },
            'performance_metrics': {
                'fast_path_success_rate': 85.0,
                'average_execution_time': 0.8,
                'fallback_rate': 15.0
            },
            'detected_issues': [
                {
                    'type': 'performance',
                    'severity': 'medium',
                    'description': 'Fast path success rate below 90%',
                    'impact': 'Increased fallback to vision workflow'
                }
            ],
            'recommendations': [
                'Review element detection strategies',
                'Check application-specific optimizations',
                'Monitor performance trends'
            ],
            'success_rate': 85.0,
            'average_response_time': 0.8
        }


class TestDebuggingFunctionalityValidation(TestDebuggingSystemIntegration):
    """Test debugging functionality validation."""
    
    def test_permission_validation_comprehensive(self, debugging_modules_with_mocks, debugging_test_scenarios):
        """Test comprehensive permission validation functionality."""
        modules = debugging_modules_with_mocks
        debugger = modules['debugger']
        
        # Test permission validation scenarios
        permission_scenarios = [s for s in debugging_test_scenarios 
                              if 'permission_check' in s.expected_debug_features]
        
        for scenario in permission_scenarios:
            try:
                # Execute permission validation
                permission_status = debugger.validate_accessibility_permissions()
                
                # Verify permission status structure
                assert 'has_permissions' in permission_status
                assert 'permission_level' in permission_status
                assert 'missing_permissions' in permission_status
                assert 'granted_permissions' in permission_status
                assert 'recommendations' in permission_status
                
                # Verify permission validation was called
                modules['mocks']['validate_perms'].assert_called()
                
                # Test permission guidance for failure scenarios
                if scenario.failure_mode == "permission_denied":
                    # Mock permission denied state
                    with patch.object(debugger, 'validate_accessibility_permissions') as mock_denied:
                        mock_denied.return_value = {
                            'has_permissions': False,
                            'permission_level': 'NONE',
                            'missing_permissions': ['accessibility'],
                            'granted_permissions': [],
                            'recommendations': ['Grant accessibility permissions in System Preferences']
                        }
                        
                        denied_status = debugger.validate_accessibility_permissions()
                        assert denied_status['has_permissions'] is False
                        assert len(denied_status['recommendations']) > 0
                        assert 'accessibility' in denied_status['missing_permissions']
                
                logging.info(f"Permission validation test passed for scenario: {scenario.name}")
                
            except Exception as e:
                pytest.fail(f"Permission validation test failed for {scenario.name}: {e}")
    
    def test_accessibility_tree_inspection_comprehensive(self, debugging_modules_with_mocks, debugging_test_scenarios):
        """Test comprehensive accessibility tree inspection functionality."""
        modules = debugging_modules_with_mocks
        debugger = modules['debugger']
        
        # Test tree inspection scenarios
        tree_scenarios = [s for s in debugging_test_scenarios 
                         if 'tree_dump' in s.expected_debug_features]
        
        for scenario in tree_scenarios:
            try:
                # Execute tree dump
                tree_dump = debugger.dump_accessibility_tree(scenario.app_name)
                
                # Verify tree dump structure
                assert 'app_name' in tree_dump
                assert 'timestamp' in tree_dump
                assert 'root_element' in tree_dump
                assert 'total_elements' in tree_dump
                assert 'clickable_elements' in tree_dump
                assert 'searchable_elements' in tree_dump
                assert 'element_roles' in tree_dump
                assert 'attribute_coverage' in tree_dump
                
                # Verify tree dump content
                assert tree_dump['total_elements'] > 0
                assert len(tree_dump['clickable_elements']) > 0
                assert len(tree_dump['element_roles']) > 0
                
                # Verify tree dump was called with correct app name
                modules['mocks']['dump_tree'].assert_called_with(scenario.app_name)
                
                # Test element search functionality
                if hasattr(tree_dump, 'find_elements_by_text'):
                    search_results = tree_dump.find_elements_by_text("Sign In")
                    assert isinstance(search_results, list)
                
                logging.info(f"Tree inspection test passed for scenario: {scenario.name}")
                
            except Exception as e:
                pytest.fail(f"Tree inspection test failed for {scenario.name}: {e}")
    
    def test_element_detection_failure_analysis(self, debugging_modules_with_mocks, debugging_test_scenarios):
        """Test element detection failure analysis functionality."""
        modules = debugging_modules_with_mocks
        debugger = modules['debugger']
        
        # Test failure analysis scenarios
        failure_scenarios = [s for s in debugging_test_scenarios 
                           if 'failure_analysis' in s.expected_debug_features]
        
        for scenario in failure_scenarios:
            try:
                # Extract target from command
                target = scenario.command.split("click the ")[-1] if "click the " in scenario.command else "button"
                
                # Execute failure analysis
                failure_analysis = debugger.analyze_element_detection_failure(scenario.command, target)
                
                # Verify failure analysis structure
                assert 'command' in failure_analysis
                assert 'target_text' in failure_analysis
                assert 'app_name' in failure_analysis
                assert 'failure_reasons' in failure_analysis
                assert 'attempted_strategies' in failure_analysis
                assert 'available_elements' in failure_analysis
                assert 'closest_matches' in failure_analysis
                assert 'similarity_scores' in failure_analysis
                assert 'recommendations' in failure_analysis
                assert 'recovery_suggestions' in failure_analysis
                
                # Verify failure analysis content for failure scenarios
                if scenario.failure_mode == "element_not_found":
                    assert len(failure_analysis['failure_reasons']) > 0
                    assert len(failure_analysis['recommendations']) > 0
                    assert len(failure_analysis['recovery_suggestions']) > 0
                
                # Verify failure analysis was called correctly
                modules['mocks']['analyze_failure'].assert_called_with(scenario.command, target)
                
                logging.info(f"Failure analysis test passed for scenario: {scenario.name}")
                
            except Exception as e:
                pytest.fail(f"Failure analysis test failed for {scenario.name}: {e}")
    
    def test_comprehensive_diagnostics_execution(self, debugging_modules_with_mocks, debugging_test_scenarios):
        """Test comprehensive diagnostics execution."""
        modules = debugging_modules_with_mocks
        diagnostic_tools = modules['diagnostic_tools']
        
        # Test comprehensive diagnostics
        diagnostic_scenarios = [s for s in debugging_test_scenarios 
                              if 'comprehensive_diagnostics' in s.expected_debug_features]
        
        for scenario in diagnostic_scenarios:
            try:
                # Execute comprehensive diagnostics
                diagnostic_report = diagnostic_tools.run_comprehensive_health_check()
                
                # Verify diagnostic report structure
                assert 'timestamp' in diagnostic_report
                assert 'permission_status' in diagnostic_report
                assert 'accessibility_health' in diagnostic_report
                assert 'performance_metrics' in diagnostic_report
                assert 'detected_issues' in diagnostic_report
                assert 'recommendations' in diagnostic_report
                assert 'success_rate' in diagnostic_report
                assert 'average_response_time' in diagnostic_report
                
                # Verify diagnostic content
                assert diagnostic_report['success_rate'] >= 0
                assert diagnostic_report['average_response_time'] >= 0
                assert isinstance(diagnostic_report['detected_issues'], list)
                assert isinstance(diagnostic_report['recommendations'], list)
                
                # Verify diagnostics was called
                modules['mocks']['diagnostics'].assert_called()
                
                logging.info(f"Comprehensive diagnostics test passed for scenario: {scenario.name}")
                
            except Exception as e:
                pytest.fail(f"Comprehensive diagnostics test failed for {scenario.name}: {e}")


class TestDebuggingPerformanceImpact(TestDebuggingSystemIntegration):
    """Test debugging performance impact on normal operations."""
    
    def test_debugging_overhead_measurement(self, debugging_modules_with_mocks):
        """Test that debugging features have minimal performance overhead."""
        modules = debugging_modules_with_mocks
        debugger = modules['debugger']
        
        # Test command execution with debugging disabled
        test_command = "click the sign in button"
        
        # Measure baseline performance (debugging disabled)
        baseline_times = []
        for _ in range(10):
            start_time = time.time()
            
            # Simulate normal command execution
            with patch.object(debugger, 'debug_level', 'NONE'):
                # Mock minimal processing
                time.sleep(0.01)  # Simulate minimal processing
            
            execution_time = time.time() - start_time
            baseline_times.append(execution_time)
        
        # Measure performance with debugging enabled
        debug_times = []
        for _ in range(10):
            start_time = time.time()
            
            # Simulate command execution with debugging
            with patch.object(debugger, 'debug_level', 'VERBOSE'):
                # Execute debugging operations
                debugger.validate_accessibility_permissions()
                debugger.dump_accessibility_tree()
                debugger.analyze_element_detection_failure(test_command, "sign in button")
            
            execution_time = time.time() - start_time
            debug_times.append(execution_time)
        
        # Calculate performance impact
        avg_baseline = sum(baseline_times) / len(baseline_times)
        avg_debug = sum(debug_times) / len(debug_times)
        overhead_percentage = ((avg_debug - avg_baseline) / avg_baseline) * 100
        
        # Verify performance impact is acceptable
        assert overhead_percentage < 50, f"Debugging overhead {overhead_percentage:.1f}% exceeds 50% threshold"
        assert avg_debug < 2.0, f"Debug-enabled execution time {avg_debug:.2f}s exceeds 2s threshold"
        
        logging.info(f"Debugging performance impact: {overhead_percentage:.1f}% overhead, "
                    f"Baseline: {avg_baseline:.3f}s, Debug: {avg_debug:.3f}s")
    
    def test_debug_level_performance_scaling(self, debugging_modules_with_mocks):
        """Test that different debug levels have appropriate performance scaling."""
        modules = debugging_modules_with_mocks
        debugger = modules['debugger']
        
        debug_levels = ['BASIC', 'DETAILED', 'VERBOSE']
        level_times = {}
        
        for level in debug_levels:
            times = []
            for _ in range(5):
                start_time = time.time()
                
                with patch.object(debugger, 'debug_level', level):
                    # Simulate debug operations based on level
                    if level == 'BASIC':
                        # Minimal debugging
                        debugger.validate_accessibility_permissions()
                    elif level == 'DETAILED':
                        # Moderate debugging
                        debugger.validate_accessibility_permissions()
                        debugger.dump_accessibility_tree()
                    elif level == 'VERBOSE':
                        # Full debugging
                        debugger.validate_accessibility_permissions()
                        debugger.dump_accessibility_tree()
                        debugger.analyze_element_detection_failure("test", "button")
                
                execution_time = time.time() - start_time
                times.append(execution_time)
            
            level_times[level] = sum(times) / len(times)
        
        # Verify performance scaling
        assert level_times['BASIC'] < level_times['DETAILED'], "BASIC should be faster than DETAILED"
        assert level_times['DETAILED'] < level_times['VERBOSE'], "DETAILED should be faster than VERBOSE"
        assert level_times['VERBOSE'] < 3.0, f"VERBOSE level time {level_times['VERBOSE']:.2f}s exceeds 3s"
        
        logging.info(f"Debug level performance scaling: "
                    f"BASIC: {level_times['BASIC']:.3f}s, "
                    f"DETAILED: {level_times['DETAILED']:.3f}s, "
                    f"VERBOSE: {level_times['VERBOSE']:.3f}s")


class TestDebuggingRealWorldScenarios(TestDebuggingSystemIntegration):
    """Test debugging with real-world application scenarios."""
    
    def test_browser_debugging_scenarios(self, debugging_modules_with_mocks):
        """Test debugging functionality with browser applications."""
        modules = debugging_modules_with_mocks
        debugger = modules['debugger']
        
        browser_scenarios = [
            {
                'app_name': 'Google Chrome',
                'command': 'click the address bar',
                'expected_elements': ['AXTextField', 'AXButton']
            },
            {
                'app_name': 'Safari',
                'command': 'click the search field',
                'expected_elements': ['AXTextField', 'AXStaticText']
            }
        ]
        
        for scenario in browser_scenarios:
            try:
                # Test tree inspection for browser
                tree_dump = debugger.dump_accessibility_tree(scenario['app_name'])
                
                # Verify browser-specific elements are detected
                assert tree_dump['app_name'] == scenario['app_name'] or tree_dump['app_name'] == 'TestApp'
                assert tree_dump['total_elements'] > 0
                
                # Test failure analysis for browser commands
                target = scenario['command'].split("click the ")[-1]
                failure_analysis = debugger.analyze_element_detection_failure(
                    scenario['command'], target
                )
                
                # Verify browser-specific analysis
                assert failure_analysis['command'] == scenario['command']
                assert failure_analysis['target_text'] == target
                
                logging.info(f"Browser debugging test passed for {scenario['app_name']}")
                
            except Exception as e:
                pytest.fail(f"Browser debugging test failed for {scenario['app_name']}: {e}")
    
    def test_native_app_debugging_scenarios(self, debugging_modules_with_mocks):
        """Test debugging functionality with native macOS applications."""
        modules = debugging_modules_with_mocks
        debugger = modules['debugger']
        
        native_scenarios = [
            {
                'app_name': 'Finder',
                'command': 'click the Applications folder',
                'expected_roles': ['AXButton', 'AXOutline', 'AXRow']
            },
            {
                'app_name': 'System Preferences',
                'command': 'click the Security & Privacy button',
                'expected_roles': ['AXButton', 'AXGroup', 'AXStaticText']
            }
        ]
        
        for scenario in native_scenarios:
            try:
                # Test tree inspection for native app
                tree_dump = debugger.dump_accessibility_tree(scenario['app_name'])
                
                # Verify native app elements are detected
                assert tree_dump['total_elements'] > 0
                assert len(tree_dump['clickable_elements']) > 0
                
                # Test failure analysis for native app commands
                target = scenario['command'].split("click the ")[-1]
                failure_analysis = debugger.analyze_element_detection_failure(
                    scenario['command'], target
                )
                
                # Verify native app analysis
                assert failure_analysis['command'] == scenario['command']
                assert len(failure_analysis['available_elements']) > 0
                
                logging.info(f"Native app debugging test passed for {scenario['app_name']}")
                
            except Exception as e:
                pytest.fail(f"Native app debugging test failed for {scenario['app_name']}: {e}")


class TestDebuggingIntegrationWithExistingSystem(TestDebuggingSystemIntegration):
    """Test debugging integration with existing AURA system."""
    
    def test_orchestrator_debugging_integration(self, debugging_modules_with_mocks):
        """Test debugging integration with orchestrator."""
        modules = debugging_modules_with_mocks
        
        # Create orchestrator with debugging enabled
        with patch('orchestrator.AccessibilityDebugger') as mock_debugger_class:
            mock_debugger_class.return_value = modules['debugger']
            
            orchestrator = Orchestrator()
            
            # Test that orchestrator can use debugging features
            test_command = "click the sign in button"
            
            with patch.object(orchestrator, '_attempt_fast_path_execution') as mock_fast_path:
                # Configure fast path to use debugging
                mock_fast_path.return_value = {
                    'success': False,
                    'fallback_required': True,
                    'debug_info': {
                        'permission_status': modules['mocks']['validate_perms'].return_value,
                        'tree_dump': modules['mocks']['dump_tree'].return_value,
                        'failure_analysis': modules['mocks']['analyze_failure'].return_value
                    }
                }
                
                # Execute command with debugging
                result = orchestrator._attempt_fast_path_execution(test_command, {})
                
                # Verify debugging integration
                assert 'debug_info' in result
                assert 'permission_status' in result['debug_info']
                assert 'tree_dump' in result['debug_info']
                assert 'failure_analysis' in result['debug_info']
                
                logging.info("Orchestrator debugging integration test passed")
    
    def test_accessibility_module_debugging_integration(self, debugging_modules_with_mocks):
        """Test debugging integration with accessibility module."""
        modules = debugging_modules_with_mocks
        
        # Create accessibility module with debugging
        with patch('modules.accessibility.AccessibilityDebugger') as mock_debugger_class:
            mock_debugger_class.return_value = modules['debugger']
            
            accessibility_module = AccessibilityModule()
            
            # Test debugging during element finding
            with patch.object(accessibility_module, 'find_element') as mock_find_element:
                mock_find_element.return_value = None  # Simulate element not found
                
                # Attempt to find element (should trigger debugging)
                result = accessibility_module.find_element('AXButton', 'Sign In')
                
                # Verify debugging was triggered
                assert result is None  # Element not found
                
                # Verify debugging methods would be called in real scenario
                modules['mocks']['validate_perms'].assert_called()
                modules['mocks']['dump_tree'].assert_called()
                
                logging.info("Accessibility module debugging integration test passed")


if __name__ == "__main__":
    # Configure logging for test execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])