"""
Integration tests for AccessibilityDebugger interactive element analysis and search tools.

Tests the interactive functionality with real application scenarios.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

from modules.accessibility_debugger import (
    AccessibilityDebugger,
    AccessibilityTreeDump,
    ElementAnalysisResult
)


class TestInteractiveElementSearch:
    """Test interactive element search functionality."""
    
    @pytest.fixture
    def debugger(self):
        """Create AccessibilityDebugger instance for testing."""
        config = {
            'debug_level': 'DETAILED',
            'max_tree_depth': 3,
            'cache_ttl_seconds': 30
        }
        return AccessibilityDebugger(config)
    
    @pytest.fixture
    def sample_tree_dump(self):
        """Create a sample tree dump with various elements."""
        clickable_elements = [
            {
                'role': 'AXButton',
                'title': 'OK',
                'position': (100, 100),
                'enabled': True,
                'element_id': 'btn_ok'
            },
            {
                'role': 'AXButton', 
                'title': 'Cancel',
                'position': (200, 100),
                'enabled': True,
                'element_id': 'btn_cancel'
            },
            {
                'role': 'AXButton',
                'title': 'Submit Form',
                'position': (150, 200),
                'enabled': True,
                'element_id': 'btn_submit'
            }
        ]
        
        searchable_elements = clickable_elements + [
            {
                'role': 'AXTextField',
                'title': 'Username',
                'value': 'test_user',
                'position': (100, 50),
                'element_id': 'field_username'
            },
            {
                'role': 'AXStaticText',
                'title': 'OK to proceed?',
                'position': (100, 150),
                'element_id': 'text_confirm'
            }
        ]
        
        return AccessibilityTreeDump(
            app_name="TestApp",
            app_pid=1234,
            timestamp=datetime.now(),
            root_element={'role': 'AXApplication', 'title': 'TestApp'},
            total_elements=len(searchable_elements),
            clickable_elements=clickable_elements,
            searchable_elements=searchable_elements,
            element_roles={'AXButton': 3, 'AXTextField': 1, 'AXStaticText': 1},
            attribute_coverage={'AXTitle': 5, 'AXRole': 5, 'AXValue': 1},
            tree_depth=2,
            generation_time_ms=100.0
        )
    
    def test_interactive_element_search_exact_match(self, debugger, sample_tree_dump):
        """Test interactive search with exact match."""
        with patch.object(debugger, 'dump_accessibility_tree', return_value=sample_tree_dump):
            result = debugger.interactive_element_search("OK")
            
            assert result['target_text'] == "OK"
            assert result['app_name'] == "TestApp"
            assert result['total_unique_matches'] > 0
            assert result['best_match'] is not None
            assert result['best_match']['title'] == 'OK'
            assert 'exact' in result['strategy_results']
            assert result['strategy_results']['exact']['count'] > 0
    
    def test_interactive_element_search_multiple_strategies(self, debugger, sample_tree_dump):
        """Test interactive search using multiple strategies."""
        with patch.object(debugger, 'dump_accessibility_tree', return_value=sample_tree_dump):
            result = debugger.interactive_element_search(
                "submit", 
                search_strategies=['exact', 'partial', 'role_based']
            )
            
            assert len(result['search_strategies_used']) == 3
            assert 'exact' in result['strategy_results']
            assert 'partial' in result['strategy_results']
            assert 'role_based' in result['strategy_results']
            
            # Should find the "Submit Form" button through partial matching
            assert result['total_unique_matches'] > 0
            if result['best_match']:
                assert 'submit' in result['best_match']['title'].lower()
    
    @patch('modules.accessibility_debugger.FUZZY_MATCHING_AVAILABLE', True)
    @patch('modules.accessibility_debugger.fuzz')
    def test_interactive_element_search_fuzzy_matching(self, mock_fuzz, debugger, sample_tree_dump):
        """Test interactive search with fuzzy matching."""
        # Mock fuzzy matching to return high scores for similar text
        mock_fuzz.ratio.side_effect = lambda x, y: 85.0 if 'ok' in x.lower() and 'ok' in y.lower() else 30.0
        
        with patch.object(debugger, 'dump_accessibility_tree', return_value=sample_tree_dump):
            result = debugger.interactive_element_search(
                "Okay",  # Similar to "OK"
                search_strategies=['fuzzy']
            )
            
            assert 'fuzzy' in result['strategy_results']
            assert result['strategy_results']['fuzzy']['count'] > 0
            mock_fuzz.ratio.assert_called()
    
    def test_interactive_element_search_no_matches(self, debugger, sample_tree_dump):
        """Test interactive search when no matches are found."""
        with patch.object(debugger, 'dump_accessibility_tree', return_value=sample_tree_dump):
            result = debugger.interactive_element_search("NonExistentElement")
            
            assert result['total_unique_matches'] == 0
            assert result['best_match'] is None
            assert result['analysis']['match_quality'] == 'no_matches'
            assert len(result['analysis']['issues_found']) > 0
            assert len(result['analysis']['recommendations']) > 0
    
    def test_interactive_element_search_performance_tracking(self, debugger, sample_tree_dump):
        """Test that search tracks performance metrics."""
        with patch.object(debugger, 'dump_accessibility_tree', return_value=sample_tree_dump):
            result = debugger.interactive_element_search("OK")
            
            assert 'total_search_time_ms' in result
            assert result['total_search_time_ms'] > 0
            
            # Check that individual strategy times are tracked
            for strategy_result in result['strategy_results'].values():
                assert 'time_ms' in strategy_result
                assert strategy_result['time_ms'] >= 0


class TestElementComparison:
    """Test element comparison functionality."""
    
    @pytest.fixture
    def debugger(self):
        """Create AccessibilityDebugger instance for testing."""
        return AccessibilityDebugger()
    
    def test_compare_identical_elements(self, debugger):
        """Test comparing identical elements."""
        element1 = {
            'role': 'AXButton',
            'title': 'OK',
            'description': 'Confirm action',
            'enabled': True,
            'position': (100, 100)
        }
        element2 = element1.copy()
        
        comparison = debugger.compare_elements(element1, element2)
        
        assert comparison['match_potential'] == 100.0
        assert len(comparison['similarities']) > 0
        assert len(comparison['differences']) == 0
        assert any('very similar' in rec.lower() for rec in comparison['recommendations'])
    
    def test_compare_similar_elements(self, debugger):
        """Test comparing similar but not identical elements."""
        element1 = {
            'role': 'AXButton',
            'title': 'OK',
            'enabled': True,
            'position': (100, 100)
        }
        element2 = {
            'role': 'AXButton',
            'title': 'Cancel',
            'enabled': True,
            'position': (120, 100)  # Slightly different position
        }
        
        comparison = debugger.compare_elements(element1, element2)
        
        assert 0 < comparison['match_potential'] < 100
        assert 'role' in comparison['similarities']  # Same role
        assert 'title' in comparison['differences']  # Different titles
        assert 'position_distance' in comparison
    
    def test_compare_different_elements(self, debugger):
        """Test comparing very different elements."""
        element1 = {
            'role': 'AXButton',
            'title': 'OK',
            'enabled': True
        }
        element2 = {
            'role': 'AXTextField',
            'title': 'Username',
            'value': 'test_user',
            'enabled': True
        }
        
        comparison = debugger.compare_elements(element1, element2)
        
        assert comparison['match_potential'] < 70  # Should be low
        assert 'role' in comparison['differences']
        assert 'title' in comparison['differences']
        assert any('different' in rec.lower() for rec in comparison['recommendations'])
    
    @patch('modules.accessibility_debugger.FUZZY_MATCHING_AVAILABLE', True)
    @patch('modules.accessibility_debugger.fuzz')
    def test_compare_elements_text_similarity(self, mock_fuzz, debugger):
        """Test element comparison with text similarity analysis."""
        mock_fuzz.ratio.return_value = 75.0
        
        element1 = {'role': 'AXButton', 'title': 'Submit'}
        element2 = {'role': 'AXButton', 'title': 'Submit Form'}
        
        comparison = debugger.compare_elements(element1, element2)
        
        assert 'text_similarity_score' in comparison
        assert comparison['text_similarity_score'] == 75.0
        assert 'text_content' in comparison
        mock_fuzz.ratio.assert_called_once()


class TestFuzzyMatchingAnalysis:
    """Test fuzzy matching score analysis."""
    
    @pytest.fixture
    def debugger(self):
        """Create AccessibilityDebugger instance for testing."""
        return AccessibilityDebugger()
    
    @pytest.fixture
    def sample_elements(self):
        """Create sample elements for fuzzy matching analysis."""
        return [
            {'title': 'OK', 'role': 'AXButton'},
            {'title': 'Okay', 'role': 'AXButton'},
            {'title': 'Cancel', 'role': 'AXButton'},
            {'title': 'Submit', 'role': 'AXButton'},
            {'description': 'OK to proceed', 'role': 'AXStaticText'},
            {'value': 'OK_VALUE', 'role': 'AXTextField'}
        ]
    
    @patch('modules.accessibility_debugger.FUZZY_MATCHING_AVAILABLE', False)
    def test_fuzzy_analysis_not_available(self, debugger, sample_elements):
        """Test fuzzy analysis when fuzzy matching is not available."""
        result = debugger.analyze_fuzzy_matching_scores("OK", sample_elements)
        
        assert 'error' in result
        assert 'not available' in result['error']
        assert 'recommendation' in result
    
    @patch('modules.accessibility_debugger.FUZZY_MATCHING_AVAILABLE', True)
    @patch('modules.accessibility_debugger.fuzz')
    def test_fuzzy_analysis_with_good_matches(self, mock_fuzz, debugger, sample_elements):
        """Test fuzzy analysis with good matching scores."""
        # Mock different scores for different text comparisons
        def mock_ratio(text1, text2):
            text1, text2 = text1.lower(), text2.lower()
            if text1 == text2:
                return 100.0
            elif 'ok' in text1 and 'ok' in text2:
                return 85.0
            else:
                return 30.0
        
        mock_fuzz.ratio.side_effect = mock_ratio
        
        result = debugger.analyze_fuzzy_matching_scores("OK", sample_elements)
        
        assert result['target_text'] == "OK"
        assert result['total_elements'] == len(sample_elements)
        assert len(result['best_matches']) > 0
        assert 'threshold_analysis' in result
        assert 'score_distribution' in result
        assert len(result['recommendations']) > 0
        
        # Should find the exact "OK" match with score 100
        best_match = result['best_matches'][0]
        assert best_match['fuzzy_score'] == 100.0
    
    @patch('modules.accessibility_debugger.FUZZY_MATCHING_AVAILABLE', True)
    @patch('modules.accessibility_debugger.fuzz')
    def test_fuzzy_analysis_threshold_effectiveness(self, mock_fuzz, debugger, sample_elements):
        """Test analysis of different threshold effectiveness."""
        # Mock scores: one perfect match, one good match, rest poor
        scores = [100.0, 75.0, 30.0, 25.0, 20.0, 15.0]
        mock_fuzz.ratio.side_effect = scores
        
        result = debugger.analyze_fuzzy_matching_scores("test", sample_elements)
        
        threshold_analysis = result['threshold_analysis']
        
        # At threshold 90, should have 1 match (score 100)
        if 90.0 in threshold_analysis:
            assert threshold_analysis[90.0]['matches'] == 1
        
        # At threshold 70, should have 2 matches (scores 100, 75)
        if 70.0 in threshold_analysis:
            assert threshold_analysis[70.0]['matches'] == 2
        
        # At threshold 50, should still have 2 matches
        if 50.0 in threshold_analysis:
            assert threshold_analysis[50.0]['matches'] == 2


class TestElementContext:
    """Test element context analysis."""
    
    @pytest.fixture
    def debugger(self):
        """Create AccessibilityDebugger instance for testing."""
        return AccessibilityDebugger()
    
    @pytest.fixture
    def hierarchical_tree_dump(self):
        """Create a tree dump with hierarchical structure."""
        searchable_elements = [
            # Parent window
            {'role': 'AXWindow', 'title': 'Main Window', 'depth': 1, 'element_id': 'win_1', 'position': (0, 0)},
            
            # Child buttons at same level
            {'role': 'AXButton', 'title': 'OK', 'depth': 2, 'element_id': 'btn_ok', 'position': (100, 100)},
            {'role': 'AXButton', 'title': 'Cancel', 'depth': 2, 'element_id': 'btn_cancel', 'position': (200, 100)},
            {'role': 'AXButton', 'title': 'Help', 'depth': 2, 'element_id': 'btn_help', 'position': (150, 100)},
            
            # Child elements of buttons
            {'role': 'AXStaticText', 'title': 'OK', 'depth': 3, 'element_id': 'text_ok', 'position': (105, 105)},
            {'role': 'AXStaticText', 'title': 'Cancel', 'depth': 3, 'element_id': 'text_cancel', 'position': (205, 105)},
        ]
        
        return AccessibilityTreeDump(
            app_name="TestApp",
            app_pid=1234,
            timestamp=datetime.now(),
            root_element={'role': 'AXApplication'},
            total_elements=len(searchable_elements),
            clickable_elements=[e for e in searchable_elements if e['role'] == 'AXButton'],
            searchable_elements=searchable_elements,
            element_roles={'AXWindow': 1, 'AXButton': 3, 'AXStaticText': 2},
            attribute_coverage={},
            tree_depth=3,
            generation_time_ms=50.0
        )
    
    def test_get_element_context_with_hierarchy(self, debugger, hierarchical_tree_dump):
        """Test getting context for an element with clear hierarchy."""
        # Get context for the OK button
        ok_button = next(e for e in hierarchical_tree_dump.searchable_elements 
                        if e['element_id'] == 'btn_ok')
        
        context = debugger.get_element_context(ok_button, hierarchical_tree_dump)
        
        assert context['target_element']['element_id'] == 'btn_ok'
        
        # Should find parent window
        assert len(context['parent_elements']) > 0
        parent_roles = [p['role'] for p in context['parent_elements']]
        assert 'AXWindow' in parent_roles
        
        # Should find sibling buttons
        assert len(context['sibling_elements']) > 0
        sibling_titles = [s['title'] for s in context['sibling_elements']]
        assert 'Cancel' in sibling_titles
        assert 'Help' in sibling_titles
        
        # Should find child text element
        assert len(context['child_elements']) > 0
        child_roles = [c['role'] for c in context['child_elements']]
        assert 'AXStaticText' in child_roles
        
        # Check context summary
        summary = context['context_summary']
        assert summary['element_depth'] == 2
        assert summary['parent_count'] > 0
        assert summary['sibling_count'] > 0
        assert summary['child_count'] > 0
    
    def test_get_element_context_position_based_siblings(self, debugger, hierarchical_tree_dump):
        """Test that sibling detection works based on position proximity."""
        ok_button = next(e for e in hierarchical_tree_dump.searchable_elements 
                        if e['element_id'] == 'btn_ok')
        
        context = debugger.get_element_context(ok_button, hierarchical_tree_dump, context_radius=1)
        
        # Should find nearby buttons as siblings
        sibling_positions = [s.get('position') for s in context['sibling_elements']]
        ok_position = ok_button['position']
        
        for pos in sibling_positions:
            if pos:
                # Calculate distance
                distance = ((ok_position[0] - pos[0]) ** 2 + (ok_position[1] - pos[1]) ** 2) ** 0.5
                assert distance < 200  # Should be within proximity threshold
    
    def test_get_element_context_no_position_info(self, debugger):
        """Test context analysis when elements don't have position information."""
        # Create elements without position info
        elements_no_pos = [
            {'role': 'AXWindow', 'title': 'Window', 'depth': 1, 'element_id': 'win'},
            {'role': 'AXButton', 'title': 'Button1', 'depth': 2, 'element_id': 'btn1'},
            {'role': 'AXButton', 'title': 'Button2', 'depth': 2, 'element_id': 'btn2'},
        ]
        
        tree_dump = AccessibilityTreeDump(
            app_name="TestApp",
            app_pid=1234,
            timestamp=datetime.now(),
            root_element={},
            total_elements=3,
            clickable_elements=[],
            searchable_elements=elements_no_pos,
            element_roles={},
            attribute_coverage={},
            tree_depth=2,
            generation_time_ms=10.0
        )
        
        target_element = elements_no_pos[1]  # Button1
        context = debugger.get_element_context(target_element, tree_dump)
        
        # Should still find siblings based on depth
        assert len(context['sibling_elements']) > 0
        assert context['context_summary']['has_position_info'] is False


class TestMatchRanking:
    """Test match ranking and relevance scoring."""
    
    @pytest.fixture
    def debugger(self):
        """Create AccessibilityDebugger instance for testing."""
        return AccessibilityDebugger()
    
    def test_rank_matches_by_relevance(self, debugger):
        """Test ranking matches by relevance score."""
        matches = [
            {
                'title': 'OK Button',
                'role': 'AXButton',
                'enabled': True,
                'match_score': 70.0,
                'search_strategy': 'partial',
                'matched_text': 'OK Button'
            },
            {
                'title': 'OK',
                'role': 'AXButton', 
                'enabled': True,
                'match_score': 100.0,
                'search_strategy': 'exact',
                'matched_text': 'OK'
            },
            {
                'title': 'Okay',
                'role': 'AXStaticText',  # Not clickable
                'enabled': True,
                'match_score': 80.0,
                'search_strategy': 'fuzzy',
                'matched_text': 'Okay'
            }
        ]
        
        ranked = debugger._rank_matches_by_relevance(matches, "OK")
        
        # Exact match with clickable role should rank highest
        assert ranked[0]['title'] == 'OK'
        assert ranked[0]['search_strategy'] == 'exact'
        
        # All matches should have relevance scores
        for match in ranked:
            assert 'relevance_score' in match
            assert match['relevance_score'] >= 0
        
        # Should be sorted by relevance score (highest first)
        scores = [m['relevance_score'] for m in ranked]
        assert scores == sorted(scores, reverse=True)
    
    def test_relevance_scoring_factors(self, debugger):
        """Test that relevance scoring considers multiple factors."""
        # Test exact match bonus
        exact_match = {
            'title': 'Test',
            'matched_text': 'Test',
            'role': 'AXButton',
            'enabled': True,
            'match_score': 80.0,
            'search_strategy': 'exact'
        }
        
        partial_match = {
            'title': 'Test Button',
            'matched_text': 'Test Button', 
            'role': 'AXButton',
            'enabled': True,
            'match_score': 80.0,
            'search_strategy': 'partial'
        }
        
        ranked = debugger._rank_matches_by_relevance([partial_match, exact_match], "Test")
        
        # Exact match should rank higher despite same base score
        assert ranked[0]['search_strategy'] == 'exact'
        assert ranked[0]['relevance_score'] > ranked[1]['relevance_score']


class TestDetailedMatchAnalysis:
    """Test detailed match analysis generation."""
    
    @pytest.fixture
    def debugger(self):
        """Create AccessibilityDebugger instance for testing."""
        return AccessibilityDebugger()
    
    @pytest.fixture
    def sample_tree_dump(self):
        """Create sample tree dump for analysis."""
        return AccessibilityTreeDump(
            app_name="TestApp",
            app_pid=1234,
            timestamp=datetime.now(),
            root_element={},
            total_elements=5,
            clickable_elements=[
                {'role': 'AXButton', 'title': 'OK', 'enabled': True}
            ],
            searchable_elements=[],
            element_roles={'AXButton': 1},
            attribute_coverage={},
            tree_depth=1,
            generation_time_ms=10.0
        )
    
    def test_analysis_no_matches(self, debugger, sample_tree_dump):
        """Test analysis when no matches are found."""
        analysis = debugger._generate_detailed_match_analysis("NonExistent", [], sample_tree_dump)
        
        assert analysis['match_quality'] == 'no_matches'
        assert analysis['confidence_level'] == 'low'
        assert len(analysis['issues_found']) > 0
        assert len(analysis['recommendations']) > 0
        assert 'No elements found' in analysis['issues_found'][0]
    
    def test_analysis_excellent_match(self, debugger, sample_tree_dump):
        """Test analysis with excellent match quality."""
        matches = [
            {
                'title': 'OK',
                'role': 'AXButton',
                'enabled': True,
                'relevance_score': 95.0,
                'search_strategy': 'exact'
            }
        ]
        
        analysis = debugger._generate_detailed_match_analysis("OK", matches, sample_tree_dump)
        
        assert analysis['match_quality'] == 'excellent'
        assert analysis['confidence_level'] == 'high'
        assert analysis['statistics']['total_matches'] == 1
        assert analysis['statistics']['clickable_matches'] == 1
    
    def test_analysis_multiple_high_score_matches(self, debugger, sample_tree_dump):
        """Test analysis with multiple high-scoring matches."""
        matches = [
            {'title': 'OK', 'role': 'AXButton', 'relevance_score': 85.0},
            {'title': 'OK Button', 'role': 'AXButton', 'relevance_score': 80.0},
            {'title': 'Okay', 'role': 'AXButton', 'relevance_score': 75.0}
        ]
        
        analysis = debugger._generate_detailed_match_analysis("OK", matches, sample_tree_dump)
        
        assert 'Multiple high-scoring matches' in ' '.join(analysis['issues_found'])
        assert 'more specific text' in ' '.join(analysis['recommendations']).lower()
        assert analysis['statistics']['total_matches'] == 3
    
    def test_analysis_no_clickable_elements(self, debugger, sample_tree_dump):
        """Test analysis when no clickable elements are found."""
        matches = [
            {'title': 'OK', 'role': 'AXStaticText', 'relevance_score': 70.0}  # Not clickable
        ]
        
        analysis = debugger._generate_detailed_match_analysis("OK", matches, sample_tree_dump)
        
        assert 'No clickable elements' in ' '.join(analysis['issues_found'])
        assert 'not be a clickable element' in ' '.join(analysis['recommendations'])
        assert analysis['statistics']['clickable_matches'] == 0