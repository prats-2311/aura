"""
Unit tests for AccessibilityDebugger class.

Tests tree inspection functionality with mocked accessibility elements.
"""

import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from modules.accessibility_debugger import (
    AccessibilityDebugger,
    AccessibilityTreeDump,
    AccessibilityTreeElement,
    ElementAnalysisResult
)


class TestAccessibilityTreeElement:
    """Test AccessibilityTreeElement data class."""
    
    def test_tree_element_creation(self):
        """Test creating a tree element with all attributes."""
        element = AccessibilityTreeElement(
            role="AXButton",
            title="Click Me",
            description="A test button",
            value="button_value",
            identifier="test_button",
            enabled=True,
            position=(100, 200),
            size=(80, 30),
            children_count=0,
            parent_role="AXWindow",
            depth=2,
            element_id="elem_123",
            all_attributes={"AXRole": "AXButton", "AXTitle": "Click Me"}
        )
        
        assert element.role == "AXButton"
        assert element.title == "Click Me"
        assert element.description == "A test button"
        assert element.position == (100, 200)
        assert element.depth == 2
    
    def test_tree_element_to_dict(self):
        """Test converting tree element to dictionary."""
        element = AccessibilityTreeElement(
            role="AXButton",
            title="Test Button",
            enabled=True
        )
        
        element_dict = element.to_dict()
        
        assert isinstance(element_dict, dict)
        assert element_dict['role'] == "AXButton"
        assert element_dict['title'] == "Test Button"
        assert element_dict['enabled'] is True
    
    def test_get_searchable_text(self):
        """Test extracting searchable text from element."""
        element = AccessibilityTreeElement(
            role="AXButton",
            title="Click Me",
            description="A test button",
            value="button_value",
            identifier="test_button"
        )
        
        searchable_texts = element.get_searchable_text()
        
        assert "Click Me" in searchable_texts
        assert "A test button" in searchable_texts
        assert "button_value" in searchable_texts
        assert "test_button" in searchable_texts
        assert len(searchable_texts) == 4
    
    def test_get_searchable_text_empty(self):
        """Test searchable text with empty/None values."""
        element = AccessibilityTreeElement(
            role="AXButton",
            title=None,
            description="",
            value="   ",  # Whitespace only
            identifier="test_id"
        )
        
        searchable_texts = element.get_searchable_text()
        
        assert "test_id" in searchable_texts
        assert len(searchable_texts) == 1  # Only non-empty, non-whitespace text


class TestAccessibilityTreeDump:
    """Test AccessibilityTreeDump data class."""
    
    def create_sample_tree_dump(self) -> AccessibilityTreeDump:
        """Create a sample tree dump for testing."""
        clickable_elements = [
            {
                'role': 'AXButton',
                'title': 'OK',
                'position': (100, 100),
                'element_id': 'btn_1'
            },
            {
                'role': 'AXButton',
                'title': 'Cancel',
                'position': (200, 100),
                'element_id': 'btn_2'
            }
        ]
        
        searchable_elements = clickable_elements + [
            {
                'role': 'AXTextField',
                'title': 'Username',
                'value': 'test_user',
                'element_id': 'field_1'
            }
        ]
        
        return AccessibilityTreeDump(
            app_name="TestApp",
            app_pid=1234,
            timestamp=datetime.now(),
            root_element={'role': 'AXApplication', 'title': 'TestApp'},
            total_elements=10,
            clickable_elements=clickable_elements,
            searchable_elements=searchable_elements,
            element_roles={'AXButton': 2, 'AXTextField': 1},
            attribute_coverage={'AXTitle': 3, 'AXRole': 3, 'AXValue': 1},
            tree_depth=3,
            generation_time_ms=150.5
        )
    
    def test_find_elements_by_text_exact(self):
        """Test finding elements by exact text match."""
        tree_dump = self.create_sample_tree_dump()
        
        matches = tree_dump.find_elements_by_text("OK", fuzzy=False)
        
        assert len(matches) == 1
        assert matches[0]['title'] == 'OK'
        assert matches[0]['match_score'] == 100.0
    
    @patch('modules.accessibility_debugger.FUZZY_MATCHING_AVAILABLE', True)
    @patch('modules.accessibility_debugger.fuzz')
    def test_find_elements_by_text_fuzzy(self, mock_fuzz):
        """Test finding elements by fuzzy text match."""
        mock_fuzz.ratio.return_value = 85.0
        
        tree_dump = self.create_sample_tree_dump()
        
        matches = tree_dump.find_elements_by_text("Okay", fuzzy=True, threshold=80.0)
        
        assert len(matches) >= 1
        mock_fuzz.ratio.assert_called()
    
    def test_get_elements_by_role(self):
        """Test getting elements by specific role."""
        tree_dump = self.create_sample_tree_dump()
        
        buttons = tree_dump.get_elements_by_role('AXButton')
        
        assert len(buttons) == 2
        assert all(elem['role'] == 'AXButton' for elem in buttons)
    
    def test_to_json(self):
        """Test converting tree dump to JSON."""
        tree_dump = self.create_sample_tree_dump()
        
        json_str = tree_dump.to_json()
        
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed['app_name'] == 'TestApp'
        assert parsed['total_elements'] == 10
    
    def test_get_summary(self):
        """Test getting tree dump summary."""
        tree_dump = self.create_sample_tree_dump()
        
        summary = tree_dump.get_summary()
        
        assert summary['app_name'] == 'TestApp'
        assert summary['total_elements'] == 10
        assert summary['clickable_elements'] == 2
        assert summary['tree_depth'] == 3
        assert 'top_roles' in summary
        assert 'attribute_coverage' in summary


class TestAccessibilityDebugger:
    """Test AccessibilityDebugger class."""
    
    @pytest.fixture
    def debugger(self):
        """Create AccessibilityDebugger instance for testing."""
        config = {
            'debug_level': 'DETAILED',
            'max_tree_depth': 5,
            'max_elements_per_level': 50,
            'cache_ttl_seconds': 30
        }
        return AccessibilityDebugger(config)
    
    @pytest.fixture
    def mock_accessibility_functions(self):
        """Mock accessibility functions for testing."""
        with patch('modules.accessibility_debugger.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True), \
             patch('modules.accessibility_debugger.APPKIT_AVAILABLE', True), \
             patch('modules.accessibility_debugger.AXUIElementCreateSystemWide') as mock_create_system, \
             patch('modules.accessibility_debugger.AXUIElementCopyAttributeValue') as mock_copy_attr, \
             patch('modules.accessibility_debugger.NSWorkspace') as mock_workspace:
            
            # Setup mock returns
            mock_create_system.return_value = Mock()
            mock_copy_attr.return_value = "TestApp"
            
            # Setup workspace mock
            mock_workspace_instance = Mock()
            mock_workspace.sharedWorkspace.return_value = mock_workspace_instance
            
            # Mock running applications
            mock_app = Mock()
            mock_app.localizedName.return_value = "TestApp"
            mock_app.processIdentifier.return_value = 1234
            mock_workspace_instance.runningApplications.return_value = [mock_app]
            
            yield {
                'create_system': mock_create_system,
                'copy_attr': mock_copy_attr,
                'workspace': mock_workspace,
                'workspace_instance': mock_workspace_instance,
                'app': mock_app
            }
    
    def test_debugger_initialization(self, debugger):
        """Test AccessibilityDebugger initialization."""
        assert debugger.debug_level == 'DETAILED'
        assert debugger.max_tree_depth == 5
        assert debugger.max_elements_per_level == 50
        assert debugger.cache_ttl == 30
        assert isinstance(debugger.tree_cache, dict)
    
    def test_debugger_initialization_defaults(self):
        """Test AccessibilityDebugger initialization with defaults."""
        debugger = AccessibilityDebugger()
        
        assert debugger.debug_level == 'BASIC'
        assert debugger.output_format == 'STRUCTURED'
        assert debugger.auto_diagnostics is True
        assert debugger.performance_tracking is True
    
    @patch('modules.accessibility_debugger.ACCESSIBILITY_FUNCTIONS_AVAILABLE', False)
    def test_debugger_initialization_no_accessibility(self, caplog):
        """Test initialization when accessibility functions are not available."""
        debugger = AccessibilityDebugger()
        
        assert "Accessibility functions not available" in caplog.text
    
    def test_get_focused_application_name(self, debugger, mock_accessibility_functions):
        """Test getting focused application name."""
        mocks = mock_accessibility_functions
        mocks['copy_attr'].side_effect = [Mock(), "TestApp"]  # focused_app, app_name
        
        app_name = debugger._get_focused_application_name()
        
        assert app_name == "TestApp"
    
    def test_get_focused_application_name_failure(self, debugger):
        """Test getting focused application name when it fails."""
        with patch('modules.accessibility_debugger.ACCESSIBILITY_FUNCTIONS_AVAILABLE', False):
            app_name = debugger._get_focused_application_name()
            assert app_name is None
    
    def test_get_application_element(self, debugger, mock_accessibility_functions):
        """Test getting application element."""
        mocks = mock_accessibility_functions
        
        # Set up the debugger workspace properly
        debugger.workspace = mocks['workspace_instance']
        
        with patch('modules.accessibility_debugger.AXUIElementCreateApplication') as mock_create_app:
            mock_create_app.return_value = Mock()
            
            element = debugger._get_application_element("TestApp")
            
            assert element is not None
            mock_create_app.assert_called_once_with(1234)
    
    def test_get_application_element_not_found(self, debugger, mock_accessibility_functions):
        """Test getting application element when app is not found."""
        mocks = mock_accessibility_functions
        mocks['workspace_instance'].runningApplications.return_value = []
        
        element = debugger._get_application_element("NonExistentApp")
        
        assert element is None
    
    def test_get_application_pid(self, debugger, mock_accessibility_functions):
        """Test getting application PID."""
        # Set up the debugger workspace properly
        debugger.workspace = mock_accessibility_functions['workspace_instance']
        
        pid = debugger._get_application_pid("TestApp")
        
        assert pid == 1234
    
    def test_get_application_pid_not_found(self, debugger, mock_accessibility_functions):
        """Test getting PID when app is not found."""
        mocks = mock_accessibility_functions
        mocks['workspace_instance'].runningApplications.return_value = []
        
        pid = debugger._get_application_pid("NonExistentApp")
        
        assert pid is None
    
    def test_extract_element_info(self, debugger):
        """Test extracting element information."""
        mock_element = Mock()
        
        with patch('modules.accessibility_debugger.AXUIElementCopyAttributeValue') as mock_copy_attr:
            # Setup attribute returns
            mock_copy_attr.side_effect = lambda elem, attr: {
                'AXRole': 'AXButton',
                'AXTitle': 'Test Button',
                'AXEnabled': True,
                'AXChildren': []
            }.get(attr)
            
            element_info = debugger._extract_element_info(mock_element, depth=1, parent_role='AXWindow')
            
            assert element_info['depth'] == 1
            assert element_info['parent_role'] == 'AXWindow'
            assert element_info['role'] == 'AXButton'
            assert element_info['title'] == 'Test Button'
            assert element_info['enabled'] == 'True'  # Converted to string
            assert 'element_id' in element_info
            assert 'all_attributes' in element_info
    
    def test_extract_element_info_with_exceptions(self, debugger):
        """Test extracting element info when some attributes fail."""
        mock_element = Mock()
        
        def mock_copy_attr(elem, attr):
            if attr == 'AXRole':
                return 'AXButton'
            elif attr == 'AXTitle':
                raise Exception("Attribute access failed")
            else:
                return None
        
        with patch('modules.accessibility_debugger.AXUIElementCopyAttributeValue', side_effect=mock_copy_attr):
            element_info = debugger._extract_element_info(mock_element, depth=0, parent_role=None)
            
            assert element_info['role'] == 'AXButton'
            assert element_info['title'] is None  # Default value
            assert element_info['enabled'] is True  # Default value
    
    def test_has_searchable_content(self, debugger):
        """Test checking if element has searchable content."""
        # Element with searchable content
        element_with_content = {
            'title': 'Button Title',
            'description': None,
            'value': '',
            'identifier': None
        }
        
        assert debugger._has_searchable_content(element_with_content) is True
        
        # Element without searchable content
        element_without_content = {
            'title': None,
            'description': '',
            'value': '   ',  # Whitespace only
            'identifier': None
        }
        
        assert debugger._has_searchable_content(element_without_content) is False
    
    def test_find_exact_matches(self, debugger):
        """Test finding exact text matches."""
        tree_dump = AccessibilityTreeDump(
            app_name="TestApp",
            app_pid=1234,
            timestamp=datetime.now(),
            root_element={},
            total_elements=2,
            clickable_elements=[],
            searchable_elements=[
                {'title': 'OK', 'role': 'AXButton'},
                {'title': 'Cancel', 'role': 'AXButton'},
                {'description': 'OK button', 'role': 'AXButton'}
            ],
            element_roles={},
            attribute_coverage={},
            tree_depth=1,
            generation_time_ms=100
        )
        
        matches = debugger._find_exact_matches(tree_dump, "OK")
        
        assert len(matches) == 1  # Only one from title (description doesn't have 'OK' exactly)
        assert all(match['match_score'] == 100.0 for match in matches)
    
    def test_find_partial_matches(self, debugger):
        """Test finding partial text matches."""
        tree_dump = AccessibilityTreeDump(
            app_name="TestApp",
            app_pid=1234,
            timestamp=datetime.now(),
            root_element={},
            total_elements=1,
            clickable_elements=[],
            searchable_elements=[
                {'title': 'OK Button', 'role': 'AXButton'}
            ],
            element_roles={},
            attribute_coverage={},
            tree_depth=1,
            generation_time_ms=100
        )
        
        matches = debugger._find_partial_matches(tree_dump, "OK")
        
        assert len(matches) == 1
        assert matches[0]['match_score'] < 100.0  # Partial match
        assert matches[0]['matched_text'] == 'OK Button'
    
    def test_find_role_based_matches(self, debugger):
        """Test finding role-based matches."""
        tree_dump = AccessibilityTreeDump(
            app_name="TestApp",
            app_pid=1234,
            timestamp=datetime.now(),
            root_element={},
            total_elements=1,
            clickable_elements=[
                {'title': 'Submit Form', 'role': 'AXButton'}
            ],
            searchable_elements=[
                {'title': 'Submit Form', 'role': 'AXButton'}
            ],
            element_roles={},
            attribute_coverage={},
            tree_depth=1,
            generation_time_ms=100
        )
        
        matches = debugger._find_role_based_matches(tree_dump, "submit")
        
        assert len(matches) == 1
        assert matches[0]['match_score'] == 70.0  # Role-based match score
        assert matches[0]['role'] == 'AXButton'
    
    def test_deduplicate_matches(self, debugger):
        """Test deduplicating matches."""
        matches = [
            {'position': (100, 100), 'title': 'Button', 'role': 'AXButton', 'matched_text': 'Button'},
            {'position': (100, 100), 'title': 'Button', 'role': 'AXButton', 'matched_text': 'Button'},  # Duplicate
            {'position': (200, 100), 'title': 'Other', 'role': 'AXButton', 'matched_text': 'Other'}
        ]
        
        unique_matches = debugger._deduplicate_matches(matches)
        
        assert len(unique_matches) == 2
    
    def test_generate_search_recommendations_no_matches(self, debugger):
        """Test generating recommendations when no matches found."""
        tree_dump = AccessibilityTreeDump(
            app_name="TestApp",
            app_pid=1234,
            timestamp=datetime.now(),
            root_element={},
            total_elements=1,
            clickable_elements=[
                {'title': 'Available Button', 'role': 'AXButton'}
            ],
            searchable_elements=[],
            element_roles={},
            attribute_coverage={},
            tree_depth=1,
            generation_time_ms=100
        )
        
        search_results = {'exact': [], 'fuzzy': [], 'partial': [], 'role_based': []}
        matches = []
        
        recommendations = debugger._generate_search_recommendations(
            "Missing Button", tree_dump, search_results, matches
        )
        
        assert len(recommendations) > 0
        assert any("No elements found" in rec for rec in recommendations)
        assert any("Available clickable elements" in rec for rec in recommendations)
    
    def test_generate_search_recommendations_multiple_matches(self, debugger):
        """Test generating recommendations when multiple matches found."""
        tree_dump = AccessibilityTreeDump(
            app_name="TestApp",
            app_pid=1234,
            timestamp=datetime.now(),
            root_element={},
            total_elements=3,
            clickable_elements=[],
            searchable_elements=[],
            element_roles={},
            attribute_coverage={},
            tree_depth=1,
            generation_time_ms=100
        )
        
        search_results = {'exact': [{}], 'fuzzy': [{}], 'partial': [{}]}
        matches = [
            {'title': 'Button 1', 'role': 'AXButton', 'match_score': 95.0},
            {'title': 'Button 2', 'role': 'AXButton', 'match_score': 85.0}
        ]
        
        recommendations = debugger._generate_search_recommendations(
            "Button", tree_dump, search_results, matches
        )
        
        assert len(recommendations) > 0
        assert any("Multiple matches found" in rec for rec in recommendations)
        assert any("Top matches found" in rec for rec in recommendations)
    
    def test_cleanup_tree_cache(self, debugger):
        """Test cleaning up expired tree cache entries."""
        # Add some cache entries
        old_timestamp = datetime.now() - timedelta(seconds=100)  # Expired
        new_timestamp = datetime.now() - timedelta(seconds=10)   # Not expired
        
        debugger.tree_cache['old_entry'] = AccessibilityTreeDump(
            app_name="OldApp",
            app_pid=1,
            timestamp=old_timestamp,
            root_element={},
            total_elements=0,
            clickable_elements=[],
            searchable_elements=[],
            element_roles={},
            attribute_coverage={},
            tree_depth=0,
            generation_time_ms=0
        )
        
        debugger.tree_cache['new_entry'] = AccessibilityTreeDump(
            app_name="NewApp",
            app_pid=2,
            timestamp=new_timestamp,
            root_element={},
            total_elements=0,
            clickable_elements=[],
            searchable_elements=[],
            element_roles={},
            attribute_coverage={},
            tree_depth=0,
            generation_time_ms=0
        )
        
        debugger._cleanup_tree_cache()
        
        assert 'old_entry' not in debugger.tree_cache
        assert 'new_entry' in debugger.tree_cache
    
    def test_traverse_accessibility_tree_max_depth(self, debugger):
        """Test tree traversal respects max depth."""
        mock_element = Mock()
        
        with patch('modules.accessibility_debugger.AXUIElementCopyAttributeValue') as mock_copy_attr:
            # Setup basic element attributes
            mock_copy_attr.side_effect = lambda elem, attr: {
                'AXRole': 'AXButton',
                'AXTitle': 'Test',
                'AXChildren': []
            }.get(attr)
            
            # Test with max_depth = 0
            root_data, all_elements = debugger._traverse_accessibility_tree(
                mock_element, max_depth=0, current_depth=0
            )
            
            assert root_data['depth'] == 0
            assert len(all_elements) == 1  # Only root element
    
    def test_traverse_accessibility_tree_with_children(self, debugger):
        """Test tree traversal with child elements."""
        mock_parent = Mock()
        mock_child1 = Mock()
        mock_child2 = Mock()
        
        def mock_copy_attr(elem, attr):
            if elem == mock_parent:
                if attr == 'AXRole':
                    return 'AXWindow'
                elif attr == 'AXTitle':
                    return 'Parent Window'
                elif attr == 'AXChildren':
                    return [mock_child1, mock_child2]
            elif elem in [mock_child1, mock_child2]:
                if attr == 'AXRole':
                    return 'AXButton'
                elif attr == 'AXTitle':
                    return f'Child Button {id(elem)}'
                elif attr == 'AXChildren':
                    return []
            return None
        
        with patch('modules.accessibility_debugger.AXUIElementCopyAttributeValue', side_effect=mock_copy_attr):
            root_data, all_elements = debugger._traverse_accessibility_tree(
                mock_parent, max_depth=2, current_depth=0
            )
            
            assert root_data['role'] == 'AXWindow'
            assert len(all_elements) == 3  # Parent + 2 children
            assert 'children' in root_data
            assert len(root_data['children']) == 2
    
    def test_traverse_accessibility_tree_exception_handling(self, debugger):
        """Test tree traversal handles exceptions gracefully."""
        mock_element = Mock()
        
        with patch('modules.accessibility_debugger.AXUIElementCopyAttributeValue', side_effect=Exception("Access denied")):
            root_data, all_elements = debugger._traverse_accessibility_tree(
                mock_element, max_depth=1, current_depth=0
            )
            
            assert root_data['role'] == 'unknown'
            assert 'error' in root_data
            assert len(all_elements) == 1


class TestElementAnalysisResult:
    """Test ElementAnalysisResult data class."""
    
    def test_analysis_result_creation(self):
        """Test creating an analysis result."""
        result = ElementAnalysisResult(
            target_text="Click Me",
            search_strategy="multi_strategy",
            matches_found=2,
            best_match={'title': 'Click Me', 'role': 'AXButton'},
            all_matches=[
                {'title': 'Click Me', 'role': 'AXButton', 'match_score': 100.0},
                {'title': 'Click Here', 'role': 'AXButton', 'match_score': 80.0}
            ],
            similarity_scores={'exact_1': 100.0, 'fuzzy_2': 80.0},
            search_time_ms=25.5,
            recommendations=['Use more specific text']
        )
        
        assert result.target_text == "Click Me"
        assert result.matches_found == 2
        assert result.best_match['title'] == 'Click Me'
        assert len(result.all_matches) == 2
        assert result.search_time_ms == 25.5
    
    def test_analysis_result_to_dict(self):
        """Test converting analysis result to dictionary."""
        result = ElementAnalysisResult(
            target_text="Test",
            search_strategy="exact",
            matches_found=1,
            best_match={'title': 'Test'},
            all_matches=[],
            similarity_scores={},
            search_time_ms=10.0,
            recommendations=[]
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict['target_text'] == "Test"
        assert result_dict['matches_found'] == 1
        assert result_dict['search_time_ms'] == 10.0


# Integration test fixtures and helpers
@pytest.fixture
def sample_accessibility_tree():
    """Create a sample accessibility tree structure for testing."""
    return {
        'role': 'AXApplication',
        'title': 'TestApp',
        'children': [
            {
                'role': 'AXWindow',
                'title': 'Main Window',
                'children': [
                    {
                        'role': 'AXButton',
                        'title': 'OK',
                        'enabled': True,
                        'position': (100, 100),
                        'size': (80, 30)
                    },
                    {
                        'role': 'AXButton',
                        'title': 'Cancel',
                        'enabled': True,
                        'position': (200, 100),
                        'size': (80, 30)
                    },
                    {
                        'role': 'AXTextField',
                        'title': 'Username',
                        'value': 'test_user',
                        'position': (100, 50),
                        'size': (200, 25)
                    }
                ]
            }
        ]
    }


class TestAccessibilityDebuggerIntegration:
    """Integration tests for AccessibilityDebugger."""
    
    def test_full_tree_dump_workflow(self, sample_accessibility_tree):
        """Test the complete tree dump workflow."""
        debugger = AccessibilityDebugger({'debug_level': 'DETAILED'})
        
        # Mock the accessibility API calls to return our sample tree
        with patch.object(debugger, '_get_focused_application_name', return_value='TestApp'), \
             patch.object(debugger, '_get_application_element', return_value=Mock()), \
             patch.object(debugger, '_get_application_pid', return_value=1234), \
             patch.object(debugger, '_traverse_accessibility_tree') as mock_traverse:
            
            # Setup traverse mock to return our sample data
            mock_traverse.return_value = (
                sample_accessibility_tree,
                [
                    {'role': 'AXApplication', 'title': 'TestApp', 'depth': 0},
                    {'role': 'AXWindow', 'title': 'Main Window', 'depth': 1},
                    {'role': 'AXButton', 'title': 'OK', 'depth': 2},
                    {'role': 'AXButton', 'title': 'Cancel', 'depth': 2},
                    {'role': 'AXTextField', 'title': 'Username', 'value': 'test_user', 'depth': 2}
                ]
            )
            
            # Execute tree dump
            tree_dump = debugger.dump_accessibility_tree()
            
            # Verify results
            assert tree_dump.app_name == 'TestApp'
            assert tree_dump.app_pid == 1234
            assert tree_dump.total_elements == 5
            assert isinstance(tree_dump.timestamp, datetime)
            assert tree_dump.generation_time_ms > 0
    
    def test_element_analysis_workflow(self, sample_accessibility_tree):
        """Test the complete element analysis workflow."""
        debugger = AccessibilityDebugger()
        
        # Create a mock tree dump
        tree_dump = AccessibilityTreeDump(
            app_name="TestApp",
            app_pid=1234,
            timestamp=datetime.now(),
            root_element=sample_accessibility_tree,
            total_elements=5,
            clickable_elements=[
                {'role': 'AXButton', 'title': 'OK', 'position': (100, 100)},
                {'role': 'AXButton', 'title': 'Cancel', 'position': (200, 100)}
            ],
            searchable_elements=[
                {'role': 'AXButton', 'title': 'OK', 'position': (100, 100)},
                {'role': 'AXButton', 'title': 'Cancel', 'position': (200, 100)},
                {'role': 'AXTextField', 'title': 'Username', 'value': 'test_user'}
            ],
            element_roles={'AXButton': 2, 'AXTextField': 1},
            attribute_coverage={'AXTitle': 3, 'AXRole': 3},
            tree_depth=2,
            generation_time_ms=100
        )
        
        with patch.object(debugger, 'dump_accessibility_tree', return_value=tree_dump):
            # Test analysis for existing element
            result = debugger.analyze_element_detection_failure("Click OK", "OK")
            
            assert result.target_text == "OK"
            assert result.matches_found > 0
            assert result.search_time_ms > 0
            assert len(result.recommendations) > 0
            
            # Verify best match
            if result.best_match:
                assert result.best_match['title'] == 'OK'
                assert result.best_match['role'] == 'AXButton'