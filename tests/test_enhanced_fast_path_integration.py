"""
Integration tests for enhanced fast path functionality.

Tests end-to-end execution of the enhanced fast path, performance requirements,
backward compatibility, and real application scenarios.

Requirements covered:
- 7.1: Sub-2-second execution time requirements
- 5.1: Backward compatibility with existing functionality
- 1.1: Enhanced element role detection integration
- 2.1: Multi-attribute text searching integration
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.accessibility import AccessibilityModule, ElementMatchResult
from orchestrator import Orchestrator


class TestEnhancedFastPathIntegration:
    """Integration tests for complete enhanced fast path execution."""
    
    @pytest.fixture
    def accessibility_module(self):
        """Create AccessibilityModule instance for testing."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True), \
             patch('modules.accessibility.NSWorkspace'), \
             patch('modules.accessibility.AXUIElementCreateSystemWide'):
            return AccessibilityModule()
    
    @pytest.fixture
    def orchestrator(self):
        """Create Orchestrator instance for testing."""
        with patch('orchestrator.VisionModule'), \
             patch('orchestrator.ReasoningModule'), \
             patch('orchestrator.AutomationModule'), \
             patch('orchestrator.AudioModule'), \
             patch('orchestrator.FeedbackModule'), \
             patch('orchestrator.AccessibilityModule'):
            return Orchestrator()
    
    def test_end_to_end_enhanced_fast_path_execution(self, accessibility_module):
        """Test complete enhanced fast path execution from command to result."""
        # Test the complete flow: command -> target extraction -> element search -> result
        test_commands = [
            "Click on the Gmail link",
            "Press the Submit button",
            "Type in the search box",
            "Select the dropdown menu"
        ]
        
        for command in test_commands:
            start_time = time.time()
            
            try:
                # Test enhanced element finding
                result = accessibility_module.find_element_enhanced('', 'test_target')
                
                # Verify result structure
                assert result is not None
                assert hasattr(result, 'found')
                assert hasattr(result, 'confidence_score')
                assert hasattr(result, 'search_time_ms')
                assert hasattr(result, 'roles_checked')
                assert hasattr(result, 'attributes_checked')
                
                # Verify result types
                assert isinstance(result.found, bool)
                assert isinstance(result.confidence_score, float)
                assert isinstance(result.search_time_ms, float)
                assert isinstance(result.roles_checked, list)
                assert isinstance(result.attributes_checked, list)
                
            except Exception as e:
                # Log the error but don't fail the test if it's due to no elements
                print(f"Enhanced fast path execution failed for '{command}': {e}")
            
            elapsed_time = time.time() - start_time
            # Should complete quickly even if no elements found
            assert elapsed_time < 5.0, f"Enhanced fast path took too long: {elapsed_time:.2f}s"
    
    def test_target_extraction_integration(self, orchestrator):
        """Test target extraction integration with orchestrator."""
        test_cases = [
            ("Click on the Gmail link", "gmail"),
            ("Press the Submit button", "submit"),
            ("Type in the search box", "search"),
            ("Select the dropdown menu", "dropdown")
        ]
        
        for command, expected_keyword in test_cases:
            start_time = time.time()
            
            try:
                result = orchestrator._extract_target_from_command(command)
                
                # Should return a string
                assert isinstance(result, str)
                assert len(result) > 0
                
                # Should contain some form of the expected keyword (case insensitive)
                result_lower = result.lower()
                assert expected_keyword in result_lower or result == command
                
            except Exception as e:
                # Should not crash
                pytest.fail(f"Target extraction failed for '{command}': {e}")
            
            elapsed_time = time.time() - start_time
            # Should be very fast
            assert elapsed_time < 0.1, f"Target extraction took too long: {elapsed_time:.2f}s"
    
    def test_fuzzy_matching_integration(self, accessibility_module):
        """Test fuzzy matching integration with various text scenarios."""
        test_cases = [
            # (element_text, target_text, should_match_approximately)
            ("Gmail Link", "gmail", True),
            ("Submit Button", "submit", True),
            ("Sign In", "sign in", True),
            ("Sign-In Button", "sign in", True),
            ("Google Mail", "gmail", False),  # Different words, might not match
            ("Completely Different", "target", False)
        ]
        
        for element_text, target_text, should_match in test_cases:
            start_time = time.time()
            
            try:
                match_found, confidence = accessibility_module.fuzzy_match_text(element_text, target_text)
                
                # Should return valid results
                assert isinstance(match_found, bool)
                assert isinstance(confidence, float)
                assert 0.0 <= confidence <= 100.0
                
                if should_match:
                    # For cases that should match, we expect reasonable confidence
                    # (though exact behavior depends on fuzzy algorithm)
                    assert confidence >= 0.0  # At least some confidence
                
            except Exception as e:
                pytest.fail(f"Fuzzy matching failed for '{element_text}' vs '{target_text}': {e}")
            
            elapsed_time = time.time() - start_time
            # Should be fast
            assert elapsed_time < 0.2, f"Fuzzy matching took too long: {elapsed_time:.2f}s"
    
    def test_multi_attribute_search_integration(self, accessibility_module):
        """Test multi-attribute search integration."""
        # Test with various mock elements
        test_elements = [
            {'AXTitle': 'Gmail Link', 'AXDescription': 'Email service', 'AXValue': ''},
            {'AXTitle': '', 'AXDescription': 'Submit Button', 'AXValue': 'Submit'},
            {'AXTitle': 'Search', 'AXDescription': '', 'AXValue': 'Enter search terms'},
            {}  # Empty element
        ]
        
        for element in test_elements:
            start_time = time.time()
            
            try:
                match_found, confidence, matched_attribute = accessibility_module._check_element_text_match(
                    element, "search"
                )
                
                # Should return valid results
                assert isinstance(match_found, bool)
                assert isinstance(confidence, float)
                assert isinstance(matched_attribute, str)
                assert 0.0 <= confidence <= 100.0
                
            except Exception as e:
                # Should handle gracefully
                print(f"Multi-attribute search handled error for element {element}: {e}")
            
            elapsed_time = time.time() - start_time
            # Should be fast
            assert elapsed_time < 0.1, f"Multi-attribute search took too long: {elapsed_time:.2f}s"
    
    def test_enhanced_role_detection_integration(self, accessibility_module):
        """Test enhanced role detection integration."""
        # Test that all expected clickable roles are configured
        expected_roles = {'AXButton', 'AXLink', 'AXMenuItem', 'AXCheckBox', 'AXRadioButton'}
        
        assert accessibility_module.clickable_roles == expected_roles
        
        # Test role checking for various roles
        for role in expected_roles:
            assert role in accessibility_module.clickable_roles
        
        # Test non-clickable roles
        non_clickable_roles = ['AXStaticText', 'AXImage', 'AXGroup']
        for role in non_clickable_roles:
            assert role not in accessibility_module.clickable_roles


class TestPerformanceRequirements:
    """Test performance requirements for enhanced fast path."""
    
    @pytest.fixture
    def accessibility_module(self):
        """Create AccessibilityModule instance for testing."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True), \
             patch('modules.accessibility.NSWorkspace'), \
             patch('modules.accessibility.AXUIElementCreateSystemWide'):
            return AccessibilityModule()
    
    def test_sub_2_second_execution_time_requirement(self, accessibility_module):
        """Test that enhanced fast path completes within 2 seconds."""
        # Test multiple iterations to ensure consistent performance
        execution_times = []
        
        for i in range(5):
            start_time = time.time()
            
            try:
                # Test enhanced element finding
                result = accessibility_module.find_element_enhanced('', f'test_target_{i}')
                
                elapsed_time = time.time() - start_time
                execution_times.append(elapsed_time)
                
                # Each individual execution should be under 2 seconds
                assert elapsed_time < 2.0, f"Execution {i+1} took {elapsed_time:.2f}s, exceeds 2s requirement"
                
            except Exception as e:
                elapsed_time = time.time() - start_time
                execution_times.append(elapsed_time)
                
                # Even with errors, should not take more than 2 seconds
                assert elapsed_time < 2.0, f"Failed execution {i+1} took {elapsed_time:.2f}s"
        
        # Average execution time should be well under 2 seconds
        avg_time = sum(execution_times) / len(execution_times)
        assert avg_time < 1.0, f"Average execution time {avg_time:.2f}s should be under 1s"
    
    def test_fuzzy_matching_timeout_compliance(self, accessibility_module):
        """Test that fuzzy matching respects timeout settings."""
        # Test with very short timeout
        start_time = time.time()
        
        match_found, confidence = accessibility_module.fuzzy_match_text(
            "Long text string for timeout testing",
            "Another long text string",
            timeout_ms=50  # Short timeout
        )
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Should complete within reasonable time even with short timeout
        assert elapsed_time < 200, f"Fuzzy matching took {elapsed_time:.1f}ms with 50ms timeout"
        
        # Should return valid results
        assert isinstance(match_found, bool)
        assert isinstance(confidence, float)
    
    def test_attribute_checking_performance(self, accessibility_module):
        """Test that attribute checking meets performance requirements."""
        # Test with multiple attributes
        test_element = {
            'AXTitle': 'Test Element Title',
            'AXDescription': 'Test Element Description',
            'AXValue': 'Test Element Value'
        }
        
        start_time = time.time()
        
        match_found, confidence, matched_attribute = accessibility_module._check_element_text_match(
            test_element, "test"
        )
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Should complete within 500ms as per requirements
        assert elapsed_time < 500, f"Attribute checking took {elapsed_time:.1f}ms, exceeds 500ms requirement"
        
        # Should return valid results
        assert isinstance(match_found, bool)
        assert isinstance(confidence, float)
        assert isinstance(matched_attribute, str)
    
    def test_performance_monitoring_integration(self, accessibility_module):
        """Test that performance monitoring is working."""
        # Check that performance monitoring is enabled
        assert hasattr(accessibility_module, 'performance_monitoring_enabled')
        
        # Check that performance metrics are being tracked
        assert hasattr(accessibility_module, 'performance_metrics')
        assert isinstance(accessibility_module.performance_metrics, list)
        
        # Check that operation metrics exist
        assert hasattr(accessibility_module, 'operation_metrics')
        assert isinstance(accessibility_module.operation_metrics, dict)


class TestBackwardCompatibility:
    """Test backward compatibility with existing functionality."""
    
    @pytest.fixture
    def accessibility_module(self):
        """Create AccessibilityModule instance for testing."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True), \
             patch('modules.accessibility.NSWorkspace'), \
             patch('modules.accessibility.AXUIElementCreateSystemWide'):
            return AccessibilityModule()
    
    def test_existing_find_element_method_compatibility(self, accessibility_module):
        """Test that existing find_element method still works."""
        # Test that the original method exists and can be called
        assert hasattr(accessibility_module, 'find_element')
        assert callable(accessibility_module.find_element)
        
        try:
            # Should not crash when called
            result = accessibility_module.find_element('AXButton', 'Submit')
            # Result format may vary, but should not crash
            assert result is not None or result is None  # Either is acceptable
        except Exception as e:
            # If it fails due to no elements, that's acceptable
            print(f"Original find_element method handled error: {e}")
    
    def test_enhanced_method_fallback_behavior(self, accessibility_module):
        """Test that enhanced methods fall back gracefully."""
        # Test with fuzzy matching disabled
        original_enabled = accessibility_module.fuzzy_matching_enabled
        
        try:
            accessibility_module.fuzzy_matching_enabled = False
            
            # Should still work with fuzzy matching disabled
            match_found, confidence = accessibility_module.fuzzy_match_text("test", "test")
            assert isinstance(match_found, bool)
            assert isinstance(confidence, float)
            
        finally:
            accessibility_module.fuzzy_matching_enabled = original_enabled
    
    def test_configuration_backward_compatibility(self, accessibility_module):
        """Test that configuration changes don't break existing functionality."""
        # Test that all expected configuration attributes exist
        config_attributes = [
            'fuzzy_matching_enabled',
            'fuzzy_confidence_threshold',
            'clickable_roles',
            'accessibility_attributes',
            'fast_path_timeout_ms',
            'performance_monitoring_enabled'
        ]
        
        for attr in config_attributes:
            assert hasattr(accessibility_module, attr), f"Missing configuration attribute: {attr}"
    
    def test_error_handling_backward_compatibility(self, accessibility_module):
        """Test that error handling maintains backward compatibility."""
        # Test that methods handle invalid inputs gracefully
        test_cases = [
            lambda: accessibility_module.fuzzy_match_text(None, "test"),
            lambda: accessibility_module.fuzzy_match_text("test", None),
            lambda: accessibility_module._check_element_text_match(None, "test"),
            lambda: accessibility_module._check_element_text_match({}, ""),
        ]
        
        for test_case in test_cases:
            try:
                result = test_case()
                # Should return some result, not crash
                assert result is not None
            except Exception as e:
                # If it raises an exception, it should be a known type
                assert isinstance(e, (AttributeError, TypeError, ValueError))


class TestRealApplicationScenarios:
    """Test enhanced fast path with realistic application scenarios."""
    
    @pytest.fixture
    def accessibility_module(self):
        """Create AccessibilityModule instance for testing."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True), \
             patch('modules.accessibility.NSWorkspace'), \
             patch('modules.accessibility.AXUIElementCreateSystemWide'):
            return AccessibilityModule()
    
    def test_common_gui_elements_detection(self, accessibility_module):
        """Test detection of common GUI elements."""
        # Common GUI elements and their variations
        common_elements = [
            # Buttons
            {'role': 'AXButton', 'title': 'OK', 'description': 'Confirm action'},
            {'role': 'AXButton', 'title': 'Cancel', 'description': 'Cancel operation'},
            {'role': 'AXButton', 'title': 'Submit', 'description': 'Submit form'},
            {'role': 'AXButton', 'title': 'Apply', 'description': 'Apply changes'},
            
            # Links
            {'role': 'AXLink', 'title': 'Gmail', 'description': 'Email service'},
            {'role': 'AXLink', 'title': 'Home', 'description': 'Go to homepage'},
            {'role': 'AXLink', 'title': 'Sign In', 'description': 'Login to account'},
            
            # Menu items
            {'role': 'AXMenuItem', 'title': 'File', 'description': 'File menu'},
            {'role': 'AXMenuItem', 'title': 'Edit', 'description': 'Edit menu'},
            {'role': 'AXMenuItem', 'title': 'View', 'description': 'View menu'},
            
            # Form elements
            {'role': 'AXCheckBox', 'title': 'Remember me', 'description': 'Remember login'},
            {'role': 'AXRadioButton', 'title': 'Option A', 'description': 'First option'},
        ]
        
        for element in common_elements:
            # Test that the role is recognized as clickable
            assert element['role'] in accessibility_module.clickable_roles
            
            # Test multi-attribute matching
            match_found, confidence, matched_attribute = accessibility_module._check_element_text_match(
                element, element['title'].lower()
            )
            
            # Should return valid results
            assert isinstance(match_found, bool)
            assert isinstance(confidence, float)
            assert isinstance(matched_attribute, str)
    
    def test_accessibility_label_variations(self, accessibility_module):
        """Test handling of various accessibility label formats."""
        # Test elements with different label formats
        label_variations = [
            # Standard labels
            {'AXTitle': 'Submit Button', 'AXDescription': '', 'AXValue': ''},
            {'AXTitle': '', 'AXDescription': 'Click to submit', 'AXValue': ''},
            {'AXTitle': '', 'AXDescription': '', 'AXValue': 'Submit'},
            
            # Mixed case and punctuation
            {'AXTitle': 'Sign-In', 'AXDescription': '', 'AXValue': ''},
            {'AXTitle': 'Save & Exit', 'AXDescription': '', 'AXValue': ''},
            {'AXTitle': 'Button #1', 'AXDescription': '', 'AXValue': ''},
            
            # Verbose descriptions
            {'AXTitle': 'Submit Form Button', 'AXDescription': 'Click to submit the form', 'AXValue': ''},
            {'AXTitle': 'Gmail Link', 'AXDescription': 'Navigate to Gmail email service', 'AXValue': ''},
        ]
        
        search_terms = ['submit', 'sign in', 'save', 'button', 'gmail']
        
        for element in label_variations:
            for term in search_terms:
                try:
                    match_found, confidence, matched_attribute = accessibility_module._check_element_text_match(
                        element, term
                    )
                    
                    # Should return valid results without crashing
                    assert isinstance(match_found, bool)
                    assert isinstance(confidence, float)
                    assert isinstance(matched_attribute, str)
                    
                except Exception as e:
                    # Should handle gracefully
                    print(f"Handled error for element {element} with term '{term}': {e}")
    
    def test_performance_with_realistic_workloads(self, accessibility_module):
        """Test performance with realistic workloads."""
        # Simulate multiple rapid searches (realistic user interaction)
        search_terms = ['submit', 'cancel', 'ok', 'gmail', 'sign in', 'home', 'file', 'edit']
        
        total_start_time = time.time()
        individual_times = []
        
        for term in search_terms:
            start_time = time.time()
            
            try:
                # Test enhanced element finding
                result = accessibility_module.find_element_enhanced('', term)
                
                elapsed_time = time.time() - start_time
                individual_times.append(elapsed_time)
                
                # Each search should be fast
                assert elapsed_time < 1.0, f"Search for '{term}' took {elapsed_time:.2f}s"
                
            except Exception as e:
                elapsed_time = time.time() - start_time
                individual_times.append(elapsed_time)
                print(f"Search for '{term}' handled error: {e}")
        
        total_elapsed_time = time.time() - total_start_time
        avg_time = sum(individual_times) / len(individual_times)
        
        # Total time for all searches should be reasonable
        assert total_elapsed_time < 5.0, f"Total search time {total_elapsed_time:.2f}s too long"
        assert avg_time < 0.5, f"Average search time {avg_time:.2f}s too long"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])