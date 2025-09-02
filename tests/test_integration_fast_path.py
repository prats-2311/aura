#!/usr/bin/env python3
"""
End-to-End Integration Tests for Fast Path Execution

Tests integration with native macOS applications (Finder, System Preferences),
web browser automation (Safari, Chrome) with accessibility API, and validates
common GUI patterns (menus, buttons, forms) work with fast path.

Requirements: 5.5, 1.4
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, MagicMock, patch, call
import logging
import time
import subprocess
import os
from typing import Dict, Any, List, Optional

# Import the modules under test
from orchestrator import Orchestrator
from modules.accessibility import AccessibilityModule
from modules.automation import AutomationModule


class TestEndToEndFastPath:
    """End-to-end integration tests for fast path execution."""
    
    @pytest.fixture
    def real_accessibility_module(self):
        """Create real AccessibilityModule for integration testing."""
        return AccessibilityModule()
    
    @pytest.fixture
    def real_automation_module(self):
        """Create real AutomationModule for integration testing."""
        return AutomationModule()
    
    @pytest.fixture
    def integration_orchestrator(self, real_accessibility_module, real_automation_module):
        """Create Orchestrator with real modules for integration testing."""
        with patch('orchestrator.VisionModule') as mock_vision, \
             patch('orchestrator.ReasoningModule') as mock_reasoning, \
             patch('orchestrator.AudioModule') as mock_audio, \
             patch('orchestrator.FeedbackModule') as mock_feedback:
            
            # Setup mock modules that won't be used in fast path
            mock_vision.return_value = Mock()
            mock_reasoning.return_value = Mock()
            mock_audio.return_value = Mock()
            mock_feedback.return_value = Mock()
            
            orchestrator = Orchestrator()
            
            # Replace with real modules for fast path testing
            orchestrator.accessibility_module = real_accessibility_module
            orchestrator.automation_module = real_automation_module
            orchestrator.fast_path_enabled = True
            
            return orchestrator
    
    @pytest.fixture
    def finder_app_context(self):
        """Setup context for Finder application testing."""
        return {
            'app_name': 'Finder',
            'bundle_id': 'com.apple.finder',
            'test_elements': [
                {'role': 'AXButton', 'label': 'New Folder', 'action': 'click'},
                {'role': 'AXMenuItem', 'label': 'File', 'action': 'click'},
                {'role': 'AXTextField', 'label': 'Search', 'action': 'type'}
            ]
        }
    
    @pytest.fixture
    def system_preferences_context(self):
        """Setup context for System Preferences testing."""
        return {
            'app_name': 'System Preferences',
            'bundle_id': 'com.apple.systempreferences',
            'test_elements': [
                {'role': 'AXButton', 'label': 'General', 'action': 'click'},
                {'role': 'AXButton', 'label': 'Desktop & Screen Saver', 'action': 'click'},
                {'role': 'AXCheckBox', 'label': 'Dark mode', 'action': 'click'}
            ]
        }
    
    @pytest.fixture
    def safari_context(self):
        """Setup context for Safari browser testing."""
        return {
            'app_name': 'Safari',
            'bundle_id': 'com.apple.Safari',
            'test_elements': [
                {'role': 'AXButton', 'label': 'Reload this page', 'action': 'click'},
                {'role': 'AXTextField', 'label': 'Address and search bar', 'action': 'type'},
                {'role': 'AXButton', 'label': 'Show bookmarks', 'action': 'click'}
            ]
        }


class TestNativeMacOSApplications(TestEndToEndFastPath):
    """Test fast path integration with native macOS applications."""
    
    @pytest.mark.integration
    def test_finder_fast_path_integration(self, integration_orchestrator, finder_app_context, real_accessibility_module):
        """Test fast path execution with Finder application."""
        if not real_accessibility_module.is_accessibility_enabled():
            pytest.skip("Accessibility API not available or permissions not granted")
        
        # Test if Finder is accessible
        app_info = real_accessibility_module.get_active_application()
        if not app_info or app_info.get('name') != 'Finder':
            pytest.skip("Finder not currently active - manual test required")
        
        # Test finding common Finder elements
        test_cases = [
            {'role': 'AXButton', 'label': 'New Folder'},
            {'role': 'AXMenuItem', 'label': 'File'},
            {'role': 'AXTextField', 'label': 'Search'}
        ]
        
        results = []
        for test_case in test_cases:
            start_time = time.time()
            
            # Attempt to find element using fast path
            element = real_accessibility_module.find_element(
                test_case['role'], 
                test_case['label'], 
                'Finder'
            )
            
            execution_time = time.time() - start_time
            
            result = {
                'element_type': f"{test_case['role']}:{test_case['label']}",
                'found': element is not None,
                'execution_time': execution_time,
                'coordinates': element.get('coordinates') if element else None
            }
            results.append(result)
            
            # Verify fast path performance requirement
            if element:
                assert execution_time < 2.0, f"Fast path too slow: {execution_time}s for {test_case}"
        
        # At least some elements should be found in Finder
        found_count = sum(1 for r in results if r['found'])
        assert found_count > 0, f"No Finder elements found via fast path. Results: {results}"
        
        # Log results for analysis
        logging.info(f"Finder fast path test results: {results}")
    
    @pytest.mark.integration
    def test_system_preferences_fast_path_integration(self, integration_orchestrator, system_preferences_context, real_accessibility_module):
        """Test fast path execution with System Preferences."""
        if not real_accessibility_module.is_accessibility_enabled():
            pytest.skip("Accessibility API not available or permissions not granted")
        
        # Test System Preferences accessibility
        app_info = real_accessibility_module.get_active_application()
        if not app_info or 'System Preferences' not in app_info.get('name', ''):
            pytest.skip("System Preferences not currently active - manual test required")
        
        # Test finding System Preferences elements
        test_cases = [
            {'role': 'AXButton', 'label': 'General'},
            {'role': 'AXButton', 'label': 'Desktop'},  # Partial match test
            {'role': 'AXCheckBox', 'label': 'Dark'}    # Partial match test
        ]
        
        results = []
        for test_case in test_cases:
            start_time = time.time()
            
            element = real_accessibility_module.find_element(
                test_case['role'], 
                test_case['label'], 
                'System Preferences'
            )
            
            execution_time = time.time() - start_time
            
            result = {
                'element_type': f"{test_case['role']}:{test_case['label']}",
                'found': element is not None,
                'execution_time': execution_time,
                'actionable': element.get('enabled', False) if element else False
            }
            results.append(result)
            
            # Verify performance
            if element:
                assert execution_time < 2.0, f"Fast path too slow: {execution_time}s"
        
        # Log results
        logging.info(f"System Preferences fast path test results: {results}")
    
    @pytest.mark.integration
    def test_menu_bar_fast_path_integration(self, real_accessibility_module):
        """Test fast path integration with macOS menu bar."""
        if not real_accessibility_module.is_accessibility_enabled():
            pytest.skip("Accessibility API not available")
        
        # Test common menu bar elements
        menu_items = [
            {'role': 'AXMenuBarItem', 'label': 'Apple'},
            {'role': 'AXMenuBarItem', 'label': 'File'},
            {'role': 'AXMenuBarItem', 'label': 'Edit'},
            {'role': 'AXMenuBarItem', 'label': 'View'}
        ]
        
        results = []
        for menu_item in menu_items:
            start_time = time.time()
            
            element = real_accessibility_module.find_element(
                menu_item['role'], 
                menu_item['label']
            )
            
            execution_time = time.time() - start_time
            
            if element:
                # Verify menu bar elements have valid coordinates
                coords = element.get('coordinates', [])
                assert len(coords) == 4, f"Invalid coordinates for {menu_item['label']}: {coords}"
                assert coords[1] < 50, f"Menu bar item not at top of screen: {coords}"  # Menu bar should be near top
            
            results.append({
                'menu_item': menu_item['label'],
                'found': element is not None,
                'execution_time': execution_time
            })
        
        # At least Apple menu should be found
        apple_menu_found = any(r['found'] for r in results if r['menu_item'] == 'Apple')
        if not apple_menu_found:
            logging.warning("Apple menu not found - this may indicate accessibility issues")
        
        logging.info(f"Menu bar fast path test results: {results}")


class TestWebBrowserAutomation(TestEndToEndFastPath):
    """Test fast path integration with web browsers."""
    
    @pytest.mark.integration
    def test_safari_fast_path_integration(self, integration_orchestrator, safari_context, real_accessibility_module):
        """Test fast path execution with Safari browser."""
        if not real_accessibility_module.is_accessibility_enabled():
            pytest.skip("Accessibility API not available")
        
        app_info = real_accessibility_module.get_active_application()
        if not app_info or app_info.get('name') != 'Safari':
            pytest.skip("Safari not currently active - manual test required")
        
        # Test Safari browser elements
        browser_elements = [
            {'role': 'AXButton', 'label': 'Reload'},
            {'role': 'AXTextField', 'label': 'Address'},  # Partial match
            {'role': 'AXButton', 'label': 'Back'},
            {'role': 'AXButton', 'label': 'Forward'}
        ]
        
        results = []
        for element_spec in browser_elements:
            start_time = time.time()
            
            element = real_accessibility_module.find_element(
                element_spec['role'], 
                element_spec['label'], 
                'Safari'
            )
            
            execution_time = time.time() - start_time
            
            result = {
                'element': f"{element_spec['role']}:{element_spec['label']}",
                'found': element is not None,
                'execution_time': execution_time,
                'enabled': element.get('enabled', False) if element else False
            }
            results.append(result)
            
            # Verify fast path performance
            if element:
                assert execution_time < 2.0, f"Safari fast path too slow: {execution_time}s"
        
        logging.info(f"Safari fast path test results: {results}")
    
    @pytest.mark.integration
    def test_chrome_fast_path_integration(self, real_accessibility_module):
        """Test fast path execution with Chrome browser."""
        if not real_accessibility_module.is_accessibility_enabled():
            pytest.skip("Accessibility API not available")
        
        app_info = real_accessibility_module.get_active_application()
        if not app_info or 'Chrome' not in app_info.get('name', ''):
            pytest.skip("Chrome not currently active - manual test required")
        
        # Test Chrome browser elements
        chrome_elements = [
            {'role': 'AXButton', 'label': 'Reload'},
            {'role': 'AXTextField', 'label': 'Address'},
            {'role': 'AXButton', 'label': 'Google Chrome menu'},
            {'role': 'AXButton', 'label': 'Back'}
        ]
        
        results = []
        for element_spec in chrome_elements:
            start_time = time.time()
            
            element = real_accessibility_module.find_element(
                element_spec['role'], 
                element_spec['label'], 
                'Google Chrome'
            )
            
            execution_time = time.time() - start_time
            
            result = {
                'element': f"{element_spec['role']}:{element_spec['label']}",
                'found': element is not None,
                'execution_time': execution_time
            }
            results.append(result)
        
        logging.info(f"Chrome fast path test results: {results}")
    
    @pytest.mark.integration
    def test_web_form_fast_path_integration(self, real_accessibility_module):
        """Test fast path with web form elements."""
        if not real_accessibility_module.is_accessibility_enabled():
            pytest.skip("Accessibility API not available")
        
        # This test requires a web page with form elements to be loaded
        # We'll test common form element patterns
        form_elements = [
            {'role': 'AXTextField', 'label': 'username'},
            {'role': 'AXTextField', 'label': 'email'},
            {'role': 'AXTextField', 'label': 'password'},
            {'role': 'AXButton', 'label': 'submit'},
            {'role': 'AXButton', 'label': 'login'},
            {'role': 'AXCheckBox', 'label': 'remember'},
            {'role': 'AXLink', 'label': 'forgot password'}
        ]
        
        results = []
        for element_spec in form_elements:
            start_time = time.time()
            
            element = real_accessibility_module.find_element(
                element_spec['role'], 
                element_spec['label']
            )
            
            execution_time = time.time() - start_time
            
            result = {
                'form_element': f"{element_spec['role']}:{element_spec['label']}",
                'found': element is not None,
                'execution_time': execution_time,
                'actionable': real_accessibility_module.is_element_actionable(element) if element else False
            }
            results.append(result)
        
        logging.info(f"Web form fast path test results: {results}")


class TestCommonGUIPatterns(TestEndToEndFastPath):
    """Test fast path with common GUI patterns across applications."""
    
    @pytest.mark.integration
    def test_button_patterns_fast_path(self, real_accessibility_module):
        """Test fast path with various button patterns."""
        if not real_accessibility_module.is_accessibility_enabled():
            pytest.skip("Accessibility API not available")
        
        # Common button patterns across applications
        button_patterns = [
            'OK', 'Cancel', 'Apply', 'Save', 'Open', 'Close',
            'Yes', 'No', 'Continue', 'Back', 'Next', 'Finish',
            'Submit', 'Login', 'Sign In', 'Sign Up', 'Register'
        ]
        
        results = []
        for button_text in button_patterns:
            start_time = time.time()
            
            element = real_accessibility_module.find_element('AXButton', button_text)
            
            execution_time = time.time() - start_time
            
            result = {
                'button_text': button_text,
                'found': element is not None,
                'execution_time': execution_time,
                'coordinates_valid': False
            }
            
            if element:
                coords = element.get('coordinates', [])
                result['coordinates_valid'] = len(coords) == 4 and all(c >= 0 for c in coords)
                
                # Verify fast path performance
                assert execution_time < 2.0, f"Button search too slow: {execution_time}s for '{button_text}'"
            
            results.append(result)
        
        # Log pattern matching results
        found_buttons = [r for r in results if r['found']]
        logging.info(f"Found {len(found_buttons)} button patterns via fast path")
        logging.debug(f"Button pattern test results: {results}")
    
    @pytest.mark.integration
    def test_menu_patterns_fast_path(self, real_accessibility_module):
        """Test fast path with menu patterns."""
        if not real_accessibility_module.is_accessibility_enabled():
            pytest.skip("Accessibility API not available")
        
        # Common menu patterns
        menu_patterns = [
            {'role': 'AXMenuBarItem', 'items': ['File', 'Edit', 'View', 'Window', 'Help']},
            {'role': 'AXMenuItem', 'items': ['New', 'Open', 'Save', 'Print', 'Quit']},
            {'role': 'AXMenu', 'items': ['Context Menu', 'Popup Menu']}
        ]
        
        results = []
        for pattern in menu_patterns:
            for item in pattern['items']:
                start_time = time.time()
                
                element = real_accessibility_module.find_element(pattern['role'], item)
                
                execution_time = time.time() - start_time
                
                result = {
                    'menu_type': pattern['role'],
                    'menu_item': item,
                    'found': element is not None,
                    'execution_time': execution_time
                }
                results.append(result)
        
        logging.info(f"Menu pattern test results: {results}")
    
    @pytest.mark.integration
    def test_text_field_patterns_fast_path(self, real_accessibility_module):
        """Test fast path with text field patterns."""
        if not real_accessibility_module.is_accessibility_enabled():
            pytest.skip("Accessibility API not available")
        
        # Common text field patterns
        text_field_patterns = [
            {'role': 'AXTextField', 'labels': ['Search', 'Username', 'Email', 'Name']},
            {'role': 'AXSecureTextField', 'labels': ['Password', 'Confirm Password']},
            {'role': 'AXTextArea', 'labels': ['Message', 'Comment', 'Description']}
        ]
        
        results = []
        for pattern in text_field_patterns:
            for label in pattern['labels']:
                start_time = time.time()
                
                element = real_accessibility_module.find_element(pattern['role'], label)
                
                execution_time = time.time() - start_time
                
                result = {
                    'field_type': pattern['role'],
                    'field_label': label,
                    'found': element is not None,
                    'execution_time': execution_time,
                    'editable': False
                }
                
                if element:
                    # Check if text field is editable
                    result['editable'] = real_accessibility_module.is_element_actionable(element)
                
                results.append(result)
        
        logging.info(f"Text field pattern test results: {results}")
    
    @pytest.mark.integration
    def test_form_element_patterns_fast_path(self, real_accessibility_module):
        """Test fast path with form element patterns."""
        if not real_accessibility_module.is_accessibility_enabled():
            pytest.skip("Accessibility API not available")
        
        # Common form element patterns
        form_patterns = [
            {'role': 'AXCheckBox', 'labels': ['Remember me', 'I agree', 'Subscribe', 'Enable']},
            {'role': 'AXRadioButton', 'labels': ['Yes', 'No', 'Male', 'Female', 'Other']},
            {'role': 'AXPopUpButton', 'labels': ['Country', 'State', 'Language', 'Category']},
            {'role': 'AXSlider', 'labels': ['Volume', 'Brightness', 'Speed', 'Quality']}
        ]
        
        results = []
        for pattern in form_patterns:
            for label in pattern['labels']:
                start_time = time.time()
                
                element = real_accessibility_module.find_element(pattern['role'], label)
                
                execution_time = time.time() - start_time
                
                result = {
                    'element_type': pattern['role'],
                    'element_label': label,
                    'found': element is not None,
                    'execution_time': execution_time,
                    'actionable': False
                }
                
                if element:
                    result['actionable'] = real_accessibility_module.is_element_actionable(element)
                    
                    # Verify performance requirement
                    assert execution_time < 2.0, f"Form element search too slow: {execution_time}s"
                
                results.append(result)
        
        logging.info(f"Form element pattern test results: {results}")


class TestPerformanceBenchmarks(TestEndToEndFastPath):
    """Performance benchmarks for fast path execution."""
    
    @pytest.mark.integration
    @pytest.mark.performance
    def test_fast_path_performance_benchmarks(self, real_accessibility_module):
        """Benchmark fast path performance across different scenarios."""
        if not real_accessibility_module.is_accessibility_enabled():
            pytest.skip("Accessibility API not available")
        
        # Performance test scenarios
        scenarios = [
            {'name': 'Simple Button', 'role': 'AXButton', 'label': 'OK'},
            {'name': 'Menu Item', 'role': 'AXMenuItem', 'label': 'File'},
            {'name': 'Text Field', 'role': 'AXTextField', 'label': 'Search'},
            {'name': 'Complex Label', 'role': 'AXButton', 'label': 'Advanced Settings'},
            {'name': 'Partial Match', 'role': 'AXButton', 'label': 'Sign'}
        ]
        
        benchmark_results = []
        
        for scenario in scenarios:
            times = []
            
            # Run multiple iterations for statistical significance
            for _ in range(10):
                start_time = time.time()
                
                element = real_accessibility_module.find_element(
                    scenario['role'], 
                    scenario['label']
                )
                
                execution_time = time.time() - start_time
                times.append(execution_time)
            
            # Calculate statistics
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            benchmark_result = {
                'scenario': scenario['name'],
                'avg_time': avg_time,
                'min_time': min_time,
                'max_time': max_time,
                'success_rate': sum(1 for t in times if t < 2.0) / len(times)  # Under 2s requirement
            }
            benchmark_results.append(benchmark_result)
            
            # Verify performance requirements
            assert avg_time < 2.0, f"Average time too slow for {scenario['name']}: {avg_time}s"
            assert benchmark_result['success_rate'] >= 0.8, f"Success rate too low for {scenario['name']}: {benchmark_result['success_rate']}"
        
        # Log comprehensive benchmark results
        logging.info("Fast Path Performance Benchmarks:")
        for result in benchmark_results:
            logging.info(f"  {result['scenario']}: avg={result['avg_time']:.3f}s, "
                        f"min={result['min_time']:.3f}s, max={result['max_time']:.3f}s, "
                        f"success_rate={result['success_rate']:.2%}")
    
    @pytest.mark.integration
    @pytest.mark.performance
    def test_accessibility_tree_traversal_performance(self, real_accessibility_module):
        """Test performance of accessibility tree traversal."""
        if not real_accessibility_module.is_accessibility_enabled():
            pytest.skip("Accessibility API not available")
        
        app_info = real_accessibility_module.get_active_application()
        if not app_info:
            pytest.skip("No active application for tree traversal test")
        
        # Test tree traversal at different depths
        depth_tests = [1, 2, 3, 4, 5]
        
        results = []
        for max_depth in depth_tests:
            start_time = time.time()
            
            # Get application element for traversal
            app_element = real_accessibility_module._get_target_application_element(None)
            if app_element:
                elements = real_accessibility_module.traverse_accessibility_tree(
                    app_element, 
                    max_depth=max_depth
                )
                
                execution_time = time.time() - start_time
                
                result = {
                    'max_depth': max_depth,
                    'elements_found': len(elements),
                    'execution_time': execution_time,
                    'elements_per_second': len(elements) / execution_time if execution_time > 0 else 0
                }
                results.append(result)
                
                # Tree traversal should complete in reasonable time
                assert execution_time < 10.0, f"Tree traversal too slow at depth {max_depth}: {execution_time}s"
        
        logging.info(f"Tree traversal performance results: {results}")


if __name__ == '__main__':
    # Configure logging for integration tests
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run integration tests
    pytest.main([
        __file__,
        '-v',
        '-m', 'integration',
        '--tb=short'
    ])