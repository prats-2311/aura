"""
Unit tests for enhanced result data models in AccessibilityModule.

Tests ElementMatchResult and TargetExtractionResult dataclasses including
creation, serialization, and to_dict methods.
"""

import pytest
import time
from typing import Dict, Any, List
from modules.accessibility import ElementMatchResult, TargetExtractionResult


class TestElementMatchResult:
    """Test cases for ElementMatchResult dataclass."""
    
    def test_element_match_result_creation_with_found_element(self):
        """Test creating ElementMatchResult with a found element."""
        element = {
            'role': 'AXButton',
            'title': 'Submit',
            'coordinates': [100, 200, 80, 30],
            'center_point': [140, 215],
            'enabled': True,
            'app_name': 'Safari'
        }
        
        fuzzy_matches = [
            {'text': 'Submit', 'score': 95.0, 'attribute': 'AXTitle'},
            {'text': 'Submit Button', 'score': 87.0, 'attribute': 'AXDescription'}
        ]
        
        result = ElementMatchResult(
            element=element,
            found=True,
            confidence_score=95.0,
            matched_attribute='AXTitle',
            search_time_ms=150.5,
            roles_checked=['AXButton', 'AXLink'],
            attributes_checked=['AXTitle', 'AXDescription'],
            fuzzy_matches=fuzzy_matches,
            fallback_triggered=False
        )
        
        assert result.element == element
        assert result.found is True
        assert result.confidence_score == 95.0
        assert result.matched_attribute == 'AXTitle'
        assert result.search_time_ms == 150.5
        assert result.roles_checked == ['AXButton', 'AXLink']
        assert result.attributes_checked == ['AXTitle', 'AXDescription']
        assert result.fuzzy_matches == fuzzy_matches
        assert result.fallback_triggered is False
    
    def test_element_match_result_creation_with_not_found(self):
        """Test creating ElementMatchResult when element is not found."""
        result = ElementMatchResult(
            element=None,
            found=False,
            confidence_score=0.0,
            matched_attribute='',
            search_time_ms=75.2,
            roles_checked=['AXButton', 'AXLink', 'AXMenuItem'],
            attributes_checked=['AXTitle', 'AXDescription', 'AXValue'],
            fuzzy_matches=[],
            fallback_triggered=True
        )
        
        assert result.element is None
        assert result.found is False
        assert result.confidence_score == 0.0
        assert result.matched_attribute == ''
        assert result.search_time_ms == 75.2
        assert result.roles_checked == ['AXButton', 'AXLink', 'AXMenuItem']
        assert result.attributes_checked == ['AXTitle', 'AXDescription', 'AXValue']
        assert result.fuzzy_matches == []
        assert result.fallback_triggered is True
    
    def test_element_match_result_to_dict_with_element(self):
        """Test to_dict method with found element."""
        element = {
            'role': 'AXLink',
            'title': 'Gmail',
            'coordinates': [50, 100, 60, 20],
            'center_point': [80, 110],
            'enabled': True,
            'app_name': 'Chrome'
        }
        
        fuzzy_matches = [
            {'text': 'Gmail', 'score': 100.0, 'attribute': 'AXTitle'}
        ]
        
        result = ElementMatchResult(
            element=element,
            found=True,
            confidence_score=100.0,
            matched_attribute='AXTitle',
            search_time_ms=45.8,
            roles_checked=['AXLink'],
            attributes_checked=['AXTitle'],
            fuzzy_matches=fuzzy_matches,
            fallback_triggered=False
        )
        
        result_dict = result.to_dict()
        
        expected_dict = {
            'found': True,
            'confidence_score': 100.0,
            'matched_attribute': 'AXTitle',
            'search_time_ms': 45.8,
            'roles_checked': ['AXLink'],
            'attributes_checked': ['AXTitle'],
            'fuzzy_match_count': 1,
            'fallback_triggered': False,
            'element_info': {
                'role': 'AXLink',
                'title': 'Gmail',
                'coordinates': [50, 100, 60, 20]
            }
        }
        
        assert result_dict == expected_dict
    
    def test_element_match_result_to_dict_without_element(self):
        """Test to_dict method when element is not found."""
        result = ElementMatchResult(
            element=None,
            found=False,
            confidence_score=0.0,
            matched_attribute='',
            search_time_ms=120.3,
            roles_checked=['AXButton', 'AXLink'],
            attributes_checked=['AXTitle', 'AXDescription'],
            fuzzy_matches=[],
            fallback_triggered=True
        )
        
        result_dict = result.to_dict()
        
        expected_dict = {
            'found': False,
            'confidence_score': 0.0,
            'matched_attribute': '',
            'search_time_ms': 120.3,
            'roles_checked': ['AXButton', 'AXLink'],
            'attributes_checked': ['AXTitle', 'AXDescription'],
            'fuzzy_match_count': 0,
            'fallback_triggered': True,
            'element_info': None
        }
        
        assert result_dict == expected_dict
    
    def test_element_match_result_default_fallback_triggered(self):
        """Test that fallback_triggered defaults to False."""
        result = ElementMatchResult(
            element=None,
            found=False,
            confidence_score=0.0,
            matched_attribute='',
            search_time_ms=50.0,
            roles_checked=[],
            attributes_checked=[],
            fuzzy_matches=[]
        )
        
        assert result.fallback_triggered is False
    
    def test_element_match_result_with_multiple_fuzzy_matches(self):
        """Test ElementMatchResult with multiple fuzzy matches."""
        fuzzy_matches = [
            {'text': 'Sign In', 'score': 95.0, 'attribute': 'AXTitle'},
            {'text': 'Sign-In Button', 'score': 87.0, 'attribute': 'AXDescription'},
            {'text': 'Login', 'score': 75.0, 'attribute': 'AXValue'}
        ]
        
        result = ElementMatchResult(
            element={'role': 'AXButton', 'title': 'Sign In'},
            found=True,
            confidence_score=95.0,
            matched_attribute='AXTitle',
            search_time_ms=200.1,
            roles_checked=['AXButton'],
            attributes_checked=['AXTitle', 'AXDescription', 'AXValue'],
            fuzzy_matches=fuzzy_matches
        )
        
        result_dict = result.to_dict()
        assert result_dict['fuzzy_match_count'] == 3
        assert result.fuzzy_matches == fuzzy_matches


class TestTargetExtractionResult:
    """Test cases for TargetExtractionResult dataclass."""
    
    def test_target_extraction_result_creation(self):
        """Test creating TargetExtractionResult with typical values."""
        result = TargetExtractionResult(
            original_command="Click on the Gmail link",
            extracted_target="gmail link",
            action_type="click",
            confidence=0.95,
            removed_words=["click", "on", "the"],
            processing_time_ms=12.5
        )
        
        assert result.original_command == "Click on the Gmail link"
        assert result.extracted_target == "gmail link"
        assert result.action_type == "click"
        assert result.confidence == 0.95
        assert result.removed_words == ["click", "on", "the"]
        assert result.processing_time_ms == 12.5
    
    def test_target_extraction_result_to_dict(self):
        """Test to_dict method for TargetExtractionResult."""
        result = TargetExtractionResult(
            original_command="Press the Submit button",
            extracted_target="submit button",
            action_type="press",
            confidence=0.88,
            removed_words=["press", "the"],
            processing_time_ms=8.3
        )
        
        result_dict = result.to_dict()
        
        expected_dict = {
            'original_command': "Press the Submit button",
            'extracted_target': "submit button",
            'action_type': "press",
            'confidence': 0.88,
            'removed_words': ["press", "the"],
            'processing_time_ms': 8.3
        }
        
        assert result_dict == expected_dict
    
    def test_target_extraction_result_with_empty_removed_words(self):
        """Test TargetExtractionResult when no words are removed."""
        result = TargetExtractionResult(
            original_command="Gmail",
            extracted_target="Gmail",
            action_type="click",
            confidence=1.0,
            removed_words=[],
            processing_time_ms=5.1
        )
        
        assert result.removed_words == []
        assert result.confidence == 1.0
        
        result_dict = result.to_dict()
        assert result_dict['removed_words'] == []
    
    def test_target_extraction_result_with_type_action(self):
        """Test TargetExtractionResult with type action."""
        result = TargetExtractionResult(
            original_command="Type in the search box",
            extracted_target="search box",
            action_type="type",
            confidence=0.92,
            removed_words=["type", "in", "the"],
            processing_time_ms=15.7
        )
        
        assert result.action_type == "type"
        assert result.extracted_target == "search box"
        
        result_dict = result.to_dict()
        assert result_dict['action_type'] == "type"
        assert result_dict['extracted_target'] == "search box"
    
    def test_target_extraction_result_with_low_confidence(self):
        """Test TargetExtractionResult with low confidence score."""
        result = TargetExtractionResult(
            original_command="Do something with that thing",
            extracted_target="something with that thing",
            action_type="unknown",
            confidence=0.25,
            removed_words=["do"],
            processing_time_ms=25.0
        )
        
        assert result.confidence == 0.25
        assert result.action_type == "unknown"
        
        result_dict = result.to_dict()
        assert result_dict['confidence'] == 0.25
    
    def test_target_extraction_result_serialization_types(self):
        """Test that to_dict returns proper types for serialization."""
        result = TargetExtractionResult(
            original_command="Click the button",
            extracted_target="button",
            action_type="click",
            confidence=0.95,
            removed_words=["click", "the"],
            processing_time_ms=10.0
        )
        
        result_dict = result.to_dict()
        
        # Verify all values are JSON-serializable types
        assert isinstance(result_dict['original_command'], str)
        assert isinstance(result_dict['extracted_target'], str)
        assert isinstance(result_dict['action_type'], str)
        assert isinstance(result_dict['confidence'], (int, float))
        assert isinstance(result_dict['removed_words'], list)
        assert isinstance(result_dict['processing_time_ms'], (int, float))
        
        # Verify list contains strings
        for word in result_dict['removed_words']:
            assert isinstance(word, str)


class TestDataModelIntegration:
    """Integration tests for both data models."""
    
    def test_data_models_work_together(self):
        """Test that both data models can be used together in a workflow."""
        # Simulate target extraction
        extraction_result = TargetExtractionResult(
            original_command="Click on the Gmail link",
            extracted_target="gmail link",
            action_type="click",
            confidence=0.95,
            removed_words=["click", "on", "the"],
            processing_time_ms=10.0
        )
        
        # Simulate element matching
        element = {
            'role': 'AXLink',
            'title': 'Gmail',
            'coordinates': [100, 200, 50, 20]
        }
        
        match_result = ElementMatchResult(
            element=element,
            found=True,
            confidence_score=87.5,
            matched_attribute='AXTitle',
            search_time_ms=45.0,
            roles_checked=['AXLink'],
            attributes_checked=['AXTitle'],
            fuzzy_matches=[{'text': 'Gmail', 'score': 87.5, 'attribute': 'AXTitle'}]
        )
        
        # Verify both results can be serialized
        extraction_dict = extraction_result.to_dict()
        match_dict = match_result.to_dict()
        
        assert extraction_dict['extracted_target'] == "gmail link"
        assert match_dict['found'] is True
        assert match_dict['element_info']['title'] == 'Gmail'
    
    def test_data_models_handle_edge_cases(self):
        """Test data models with edge case values."""
        # Test with minimal values
        extraction_result = TargetExtractionResult(
            original_command="",
            extracted_target="",
            action_type="",
            confidence=0.0,
            removed_words=[],
            processing_time_ms=0.0
        )
        
        match_result = ElementMatchResult(
            element=None,
            found=False,
            confidence_score=0.0,
            matched_attribute="",
            search_time_ms=0.0,
            roles_checked=[],
            attributes_checked=[],
            fuzzy_matches=[]
        )
        
        # Should not raise exceptions
        extraction_dict = extraction_result.to_dict()
        match_dict = match_result.to_dict()
        
        assert extraction_dict['confidence'] == 0.0
        assert match_dict['found'] is False
        assert match_dict['element_info'] is None