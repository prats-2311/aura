"""
Integration tests for AURA interactive debugging features.

Tests the interactive debugging mode, step-by-step execution, and session
recording/playback functionality.
"""

import unittest
import tempfile
import os
import sys
import json
import time
from unittest.mock import patch, MagicMock
from io import StringIO
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from debug_interactive import InteractiveDebugger, DebugSession
    from debug_step_by_step import StepByStepDebugger, ExecutionStep
    INTERACTIVE_MODULES_AVAILABLE = True
except ImportError:
    INTERACTIVE_MODULES_AVAILABLE = False


class TestInteractiveDebuggingIntegration(unittest.TestCase):
    """Integration tests for interactive debugging features."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
    
    def tearDown(self):
        """Clean up test files."""
        for file_path in self.test_files:
            try:
                os.remove(file_path)
            except FileNotFoundError:
                pass
        
        try:
            os.rmdir(self.temp_dir)
        except OSError:
            pass
    
    def _create_temp_file(self, suffix='.json'):
        """Create a temporary file for testing."""
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self.temp_dir)
        os.close(fd)
        self.test_files.append(path)
        return path
    
    @unittest.skipUnless(INTERACTIVE_MODULES_AVAILABLE, "Interactive modules not available")
    def test_interactive_debugger_tree_command(self):
        """Test tree command in interactive debugger."""
        debugger = InteractiveDebugger()
        debugger.recording = True  # Enable recording for test
        
        # Mock the accessibility debugger
        with patch.object(debugger.debugger, 'dump_accessibility_tree') as mock_dump:
            mock_tree_dump = MagicMock()
            mock_tree_dump.app_name = 'TestApp'
            mock_tree_dump.total_elements = 150
            mock_tree_dump.clickable_elements = [
                {'title': 'Button1', 'role': 'AXButton'},
                {'title': 'Link1', 'role': 'AXLink'}
            ]
            mock_tree_dump.tree_depth = 6
            mock_tree_dump.element_roles = {'AXButton': 5, 'AXStaticText': 100}
            
            mock_dump.return_value = mock_tree_dump
            
            # Capture output
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                debugger.do_tree('TestApp')
                output = mock_stdout.getvalue()
            
            # Verify output contains expected information
            self.assertIn('TestApp', output)
            self.assertIn('150', output)  # total elements
            self.assertIn('✅', output)   # success indicator
            
            # Verify session recording
            self.assertEqual(len(debugger.session.commands), 1)
            recorded_cmd = debugger.session.commands[0]
            self.assertEqual(recorded_cmd['command'], 'tree')
            self.assertTrue(recorded_cmd['result']['success'])
    
    @unittest.skipUnless(INTERACTIVE_MODULES_AVAILABLE, "Interactive modules not available")
    def test_interactive_debugger_element_command(self):
        """Test element analysis command in interactive debugger."""
        debugger = InteractiveDebugger()
        debugger.recording = True  # Enable recording for test
        
        with patch.object(debugger.debugger, 'analyze_element_detection_failure') as mock_analyze:
            mock_analysis = MagicMock()
            mock_analysis.target_text = 'Sign In'
            mock_analysis.search_strategy = 'multi_strategy'
            mock_analysis.matches_found = 1
            mock_analysis.search_time_ms = 35.0
            mock_analysis.best_match = {
                'role': 'AXButton',
                'title': 'Sign In',
                'match_score': 98.0,
                'matched_text': 'Sign In'
            }
            mock_analysis.recommendations = ['Element found with high confidence']
            
            mock_analyze.return_value = mock_analysis
            
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                debugger.do_element('Sign In TestApp')
                output = mock_stdout.getvalue()
            
            self.assertIn('Sign In', output)
            self.assertIn('98.0%', output)
            self.assertIn('✅', output)
            
            # Verify session recording
            self.assertEqual(len(debugger.session.commands), 1)
            recorded_cmd = debugger.session.commands[0]
            self.assertEqual(recorded_cmd['command'], 'element')
            self.assertEqual(recorded_cmd['args'], ['Sign', 'In', 'TestApp'])
    
    @unittest.skipUnless(INTERACTIVE_MODULES_AVAILABLE, "Interactive modules not available")
    def test_interactive_debugger_health_command(self):
        """Test health check command in interactive debugger."""
        debugger = InteractiveDebugger()
        debugger.recording = True  # Enable recording for test
        
        with patch.object(debugger.health_checker, 'run_comprehensive_health_check') as mock_health:
            mock_report = MagicMock()
            mock_report.overall_health_score = 92.0
            mock_report.detected_issues = []
            mock_report.generation_time_ms = 800.0
            mock_report.generate_summary.return_value = 'System health is excellent'
            
            mock_health.return_value = mock_report
            
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                debugger.do_health('')
                output = mock_stdout.getvalue()
            
            self.assertIn('92.0/100', output)
            self.assertIn('✅', output)
            self.assertIn('excellent', output)
            
            # Verify session recording
            self.assertEqual(len(debugger.session.commands), 1)
            recorded_cmd = debugger.session.commands[0]
            self.assertEqual(recorded_cmd['command'], 'health')
            self.assertTrue(recorded_cmd['result']['success'])
    
    @unittest.skipUnless(INTERACTIVE_MODULES_AVAILABLE, "Interactive modules not available")
    def test_interactive_debugger_session_recording(self):
        """Test session recording functionality."""
        session_file = self._create_temp_file('.json')
        debugger = InteractiveDebugger(record_file=session_file)
        debugger.recording = True
        
        # Execute multiple commands
        with patch.object(debugger.debugger, 'dump_accessibility_tree') as mock_dump:
            mock_tree_dump = MagicMock()
            mock_tree_dump.app_name = 'TestApp'
            mock_tree_dump.total_elements = 100
            mock_tree_dump.clickable_elements = []
            mock_tree_dump.tree_depth = 5
            mock_tree_dump.element_roles = {}
            mock_dump.return_value = mock_tree_dump
            
            with patch('sys.stdout', new_callable=StringIO):
                debugger.do_tree('TestApp')
        
        with patch.object(debugger.permission_validator, 'check_accessibility_permissions') as mock_perms:
            mock_status = MagicMock()
            mock_status.has_permissions = True
            mock_status.permission_level = 'FULL'
            mock_status.get_summary.return_value = 'Permissions OK'
            mock_perms.return_value = mock_status
            
            with patch('sys.stdout', new_callable=StringIO):
                debugger.do_permissions('')
        
        # Save session
        with patch('sys.stdout', new_callable=StringIO):
            debugger.do_save(session_file)
        
        # Verify session file
        self.assertTrue(os.path.exists(session_file))
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        self.assertIn('metadata', session_data)
        self.assertIn('commands', session_data)
        self.assertGreaterEqual(len(session_data['commands']), 2)  # At least tree and permissions
        
        # Verify command types
        command_names = [cmd['command'] for cmd in session_data['commands']]
        self.assertIn('tree', command_names)
        self.assertIn('permissions', command_names)
    
    @unittest.skipUnless(INTERACTIVE_MODULES_AVAILABLE, "Interactive modules not available")
    def test_interactive_debugger_session_playback(self):
        """Test session playback functionality."""
        # Create a test session file
        session_file = self._create_temp_file('.json')
        session_data = {
            'metadata': {
                'session_id': 'test_playback_session',
                'start_time': datetime.now().isoformat(),
                'platform': 'test',
                'python_version': '3.11.0'
            },
            'commands': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'command': 'tree',
                    'args': ['TestApp'],
                    'result': {'success': True, 'app_name': 'TestApp'},
                    'execution_time_ms': 100.0
                },
                {
                    'timestamp': datetime.now().isoformat(),
                    'command': 'health',
                    'args': [],
                    'result': {'success': True, 'health_score': 85.0},
                    'execution_time_ms': 500.0
                }
            ],
            'end_time': datetime.now().isoformat(),
            'total_commands': 2
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        # Test playback
        debugger = InteractiveDebugger()
        
        # Mock user input to skip command execution
        with patch('builtins.input', side_effect=['N', 'N']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                debugger.do_playback(session_file)
                output = mock_stdout.getvalue()
        
        self.assertIn('test_playback_session', output)
        self.assertIn('2 commands', output)
        self.assertIn('✅', output)
    
    @unittest.skipUnless(INTERACTIVE_MODULES_AVAILABLE, "Interactive modules not available")
    def test_interactive_debugger_cache_command(self):
        """Test cache status command."""
        debugger = InteractiveDebugger()
        
        # Add some mock cache data
        debugger.debugger.tree_cache = {
            'TestApp_DETAILED': MagicMock(app_name='TestApp', timestamp=datetime.now())
        }
        debugger.permission_validator.permission_cache = {'status': 'cached'}
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            debugger.do_cache('')
            output = mock_stdout.getvalue()
        
        self.assertIn('Cache Status', output)
        self.assertIn('Tree cache entries: 1', output)
        self.assertIn('Permission cache entries: 1', output)
        self.assertIn('Session commands:', output)


class TestStepByStepDebuggingIntegration(unittest.TestCase):
    """Integration tests for step-by-step debugging."""
    
    @unittest.skipUnless(INTERACTIVE_MODULES_AVAILABLE, "Interactive modules not available")
    def test_execution_step_creation(self):
        """Test creation and execution of execution steps."""
        def test_function(arg1, arg2, kwarg1=None):
            return {'arg1': arg1, 'arg2': arg2, 'kwarg1': kwarg1}
        
        step = ExecutionStep(
            step_id='test_step',
            name='Test Step',
            description='A test step',
            function=test_function,
            args=('value1', 'value2'),
            kwargs={'kwarg1': 'kwarg_value'}
        )
        
        # Execute step
        result = step.execute(debug_mode=False)
        
        self.assertTrue(step.executed)
        self.assertTrue(step.success)
        self.assertIsNotNone(step.result)
        self.assertEqual(step.result['arg1'], 'value1')
        self.assertEqual(step.result['arg2'], 'value2')
        self.assertEqual(step.result['kwarg1'], 'kwarg_value')
        self.assertGreater(step.execution_time_ms, 0)
        
        # Verify result dictionary
        self.assertIn('step_id', result)
        self.assertIn('success', result)
        self.assertIn('execution_time_ms', result)
    
    @unittest.skipUnless(INTERACTIVE_MODULES_AVAILABLE, "Interactive modules not available")
    def test_execution_step_failure(self):
        """Test execution step failure handling."""
        def failing_function():
            raise ValueError("Test error")
        
        step = ExecutionStep(
            step_id='failing_step',
            name='Failing Step',
            description='A step that fails',
            function=failing_function
        )
        
        result = step.execute(debug_mode=False)
        
        self.assertTrue(step.executed)
        self.assertFalse(step.success)
        self.assertIsNotNone(step.error)
        self.assertIn('Test error', step.error)
        self.assertGreater(step.execution_time_ms, 0)
    
    @unittest.skipUnless(INTERACTIVE_MODULES_AVAILABLE, "Interactive modules not available")
    def test_step_by_step_debugger_initialization(self):
        """Test step-by-step debugger initialization."""
        debugger = StepByStepDebugger()
        
        self.assertIsNotNone(debugger.debugger)
        self.assertIsNotNone(debugger.reasoning)
        self.assertIsNotNone(debugger.accessibility)
        self.assertIsNotNone(debugger.orchestrator)
        self.assertEqual(len(debugger.steps), 0)
        self.assertEqual(debugger.current_step_index, 0)
        self.assertIsInstance(debugger.execution_context, dict)
    
    @unittest.skipUnless(INTERACTIVE_MODULES_AVAILABLE, "Interactive modules not available")
    def test_command_execution_steps_creation(self):
        """Test creation of command execution steps."""
        debugger = StepByStepDebugger()
        
        command = "Click on Sign In button"
        steps = debugger.create_command_execution_steps(command)
        
        self.assertGreater(len(steps), 0)
        self.assertEqual(len(steps), 8)  # Expected number of steps
        
        # Verify step IDs
        expected_step_ids = [
            'parse_command', 'check_permissions', 'get_accessibility_tree',
            'extract_target', 'find_element', 'validate_element',
            'execute_action', 'verify_result'
        ]
        
        actual_step_ids = [step.step_id for step in steps]
        self.assertEqual(actual_step_ids, expected_step_ids)
        
        # Verify all steps have required attributes
        for step in steps:
            self.assertIsNotNone(step.step_id)
            self.assertIsNotNone(step.name)
            self.assertIsNotNone(step.description)
            self.assertIsNotNone(step.function)
    
    @unittest.skipUnless(INTERACTIVE_MODULES_AVAILABLE, "Interactive modules not available")
    def test_step_by_step_execution_with_mocks(self):
        """Test step-by-step execution with mocked components."""
        debugger = StepByStepDebugger()
        debugger.interactive_mode = False  # Disable interactive prompts
        
        # Mock all the component methods
        with patch.object(debugger.reasoning, 'get_action_plan') as mock_parse:
            mock_parse.return_value = {
                'actions': [{'action': 'click', 'target': 'Sign In'}],
                'metadata': {'confidence': 0.95}
            }
            
            with patch.object(debugger, 'permission_validator') as mock_pv:
                mock_status = MagicMock()
                mock_status.has_permissions = True
                mock_status.permission_level = 'FULL'
                mock_status.get_summary.return_value = 'OK'
                mock_pv.check_accessibility_permissions.return_value = mock_status
                
                with patch.object(debugger.debugger, '_get_focused_application_name') as mock_app:
                    mock_app.return_value = 'TestApp'
                    
                    with patch.object(debugger.debugger, 'dump_accessibility_tree') as mock_tree:
                        mock_tree_dump = MagicMock()
                        mock_tree_dump.total_elements = 100
                        mock_tree_dump.clickable_elements = []
                        mock_tree_dump.tree_depth = 5
                        mock_tree_dump.generation_time_ms = 100.0
                        mock_tree.return_value = mock_tree_dump
                        
                        with patch.object(debugger.debugger, 'analyze_element_detection_failure') as mock_analyze:
                            mock_analysis = MagicMock()
                            mock_analysis.matches_found = 1
                            mock_analysis.best_match = {
                                'role': 'AXButton',
                                'title': 'Sign In',
                                'enabled': True,
                                'position': (100, 200)
                            }
                            mock_analysis.search_time_ms = 50.0
                            mock_analysis.recommendations = []
                            mock_analyze.return_value = mock_analysis
                            
                            # Execute command step by step
                            with patch('sys.stdout', new_callable=StringIO):
                                results = debugger.execute_command_step_by_step("Click on Sign In")
            
            # Verify execution results
            self.assertIsInstance(results, dict)
            self.assertIn('command', results)
            self.assertIn('overall_success', results)
            self.assertIn('steps', results)
            self.assertIn('total_execution_time_ms', results)
            
            # Should have executed all steps successfully
            self.assertTrue(results['overall_success'])
            self.assertEqual(len(results['steps']), 8)
            
            # Verify all steps succeeded
            for step_result in results['steps']:
                self.assertTrue(step_result['success'], f"Step {step_result['name']} failed")
    
    @unittest.skipUnless(INTERACTIVE_MODULES_AVAILABLE, "Interactive modules not available")
    def test_step_by_step_execution_with_failure(self):
        """Test step-by-step execution with step failure."""
        debugger = StepByStepDebugger()
        debugger.interactive_mode = False
        
        # Mock parse command to succeed
        with patch.object(debugger.reasoning, 'get_action_plan') as mock_parse:
            mock_parse.return_value = {
                'actions': [{'action': 'click', 'target': 'Sign In'}],
                'metadata': {'confidence': 0.95}
            }
            
            # Mock permission check to fail
            with patch.object(debugger, 'permission_validator') as mock_pv:
                mock_pv.check_accessibility_permissions.side_effect = Exception("Permission check failed")
                
                with patch('sys.stdout', new_callable=StringIO):
                    results = debugger.execute_command_step_by_step("Click on Sign In")
        
        # Verify execution failed
        self.assertFalse(results['overall_success'])
        self.assertEqual(results['failed_step'], 'check_permissions')
        
        # Should have executed parse_command but failed at check_permissions
        self.assertGreaterEqual(len(results['steps']), 1)
        self.assertTrue(results['steps'][0]['success'])  # parse_command should succeed
        
        if len(results['steps']) > 1:
            self.assertFalse(results['steps'][1]['success'])  # check_permissions should fail
    
    @unittest.skipUnless(INTERACTIVE_MODULES_AVAILABLE, "Interactive modules not available")
    def test_breakpoint_functionality(self):
        """Test breakpoint setting and listing."""
        debugger = StepByStepDebugger()
        
        # Set breakpoints
        debugger.set_breakpoint('parse_command')
        debugger.set_breakpoint('find_element')
        
        self.assertIn('parse_command', debugger.breakpoints)
        self.assertIn('find_element', debugger.breakpoints)
        
        # Remove breakpoint
        debugger.remove_breakpoint('parse_command')
        self.assertNotIn('parse_command', debugger.breakpoints)
        self.assertIn('find_element', debugger.breakpoints)
        
        # List breakpoints
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            debugger.list_breakpoints()
            output = mock_stdout.getvalue()
        
        self.assertIn('find_element', output)
        self.assertNotIn('parse_command', output)


class TestDebuggingToolsIntegration(unittest.TestCase):
    """Integration tests for debugging tools working together."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
    
    def tearDown(self):
        """Clean up test files."""
        for file_path in self.test_files:
            try:
                os.remove(file_path)
            except FileNotFoundError:
                pass
        
        try:
            os.rmdir(self.temp_dir)
        except OSError:
            pass
    
    def _create_temp_file(self, suffix='.json'):
        """Create a temporary file for testing."""
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self.temp_dir)
        os.close(fd)
        self.test_files.append(path)
        return path
    
    @unittest.skipUnless(INTERACTIVE_MODULES_AVAILABLE, "Interactive modules not available")
    def test_debugging_workflow_integration(self):
        """Test complete debugging workflow integration."""
        # Create interactive debugger
        debugger = InteractiveDebugger()
        debugger.recording = True  # Enable recording for test
        
        # Mock components for consistent testing
        with patch.object(debugger.debugger, 'dump_accessibility_tree') as mock_tree:
            mock_tree_dump = MagicMock()
            mock_tree_dump.app_name = 'TestApp'
            mock_tree_dump.total_elements = 200
            mock_tree_dump.clickable_elements = [
                {'title': 'Sign In', 'role': 'AXButton'},
                {'title': 'Register', 'role': 'AXLink'}
            ]
            mock_tree_dump.tree_depth = 7
            mock_tree_dump.element_roles = {'AXButton': 15, 'AXStaticText': 150}
            mock_tree.return_value = mock_tree_dump
            
            with patch.object(debugger.debugger, 'analyze_element_detection_failure') as mock_analyze:
                mock_analysis = MagicMock()
                mock_analysis.target_text = 'Sign In'
                mock_analysis.matches_found = 1
                mock_analysis.best_match = {
                    'role': 'AXButton',
                    'title': 'Sign In',
                    'match_score': 100.0
                }
                mock_analysis.recommendations = ['Perfect match found']
                mock_analyze.return_value = mock_analysis
                
                with patch.object(debugger.health_checker, 'run_comprehensive_health_check') as mock_health:
                    mock_report = MagicMock()
                    mock_report.overall_health_score = 95.0
                    mock_report.detected_issues = []
                    mock_report.generate_summary.return_value = 'System is healthy'
                    mock_health.return_value = mock_report
                    
                    # Execute debugging workflow
                    with patch('sys.stdout', new_callable=StringIO):
                        # 1. Check system health
                        debugger.do_health('')
                        
                        # 2. Dump accessibility tree
                        debugger.do_tree('TestApp')
                        
                        # 3. Analyze specific element
                        debugger.do_element('Sign In TestApp')
                        
                        # 4. Check cache status
                        debugger.do_cache('')
        
        # Verify all commands were recorded
        self.assertEqual(len(debugger.session.commands), 4)
        
        command_names = [cmd['command'] for cmd in debugger.session.commands]
        expected_commands = ['health', 'tree', 'element', 'cache']
        self.assertEqual(command_names, expected_commands)
        
        # Verify all commands succeeded
        for cmd in debugger.session.commands:
            self.assertTrue(cmd['result']['success'], f"Command {cmd['command']} failed")
    
    @unittest.skipUnless(INTERACTIVE_MODULES_AVAILABLE, "Interactive modules not available")
    def test_session_persistence_integration(self):
        """Test session persistence across debugging sessions."""
        session_file = self._create_temp_file('.json')
        
        # First debugging session
        debugger1 = InteractiveDebugger(record_file=session_file)
        debugger1.recording = True
        
        with patch.object(debugger1.debugger, 'dump_accessibility_tree') as mock_tree:
            mock_tree_dump = MagicMock()
            mock_tree_dump.app_name = 'App1'
            mock_tree_dump.total_elements = 50
            mock_tree_dump.clickable_elements = []
            mock_tree_dump.tree_depth = 3
            mock_tree_dump.element_roles = {}
            mock_tree.return_value = mock_tree_dump
            
            with patch('sys.stdout', new_callable=StringIO):
                debugger1.do_tree('App1')
                debugger1.do_save(session_file)
        
        # Verify session file was created
        self.assertTrue(os.path.exists(session_file))
        
        # Second debugging session - load previous session
        debugger2 = InteractiveDebugger()
        debugger2.recording = True  # Enable recording for second session
        
        with patch('builtins.input', return_value='N'):  # Don't replay commands
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                debugger2.do_playback(session_file)
                output = mock_stdout.getvalue()
        
        self.assertIn('1 commands', output)  # Only tree command was saved initially
        self.assertIn('✅', output)
        
        # Add more commands to second session
        with patch.object(debugger2.permission_validator, 'check_accessibility_permissions') as mock_perms:
            mock_status = MagicMock()
            mock_status.has_permissions = True
            mock_status.get_summary.return_value = 'OK'
            mock_perms.return_value = mock_status
            
            with patch('sys.stdout', new_callable=StringIO):
                debugger2.do_permissions('')
        
        # Save combined session
        combined_file = self._create_temp_file('.json')
        with patch('sys.stdout', new_callable=StringIO):
            debugger2.do_save(combined_file)
        
        # Verify combined session
        with open(combined_file, 'r') as f:
            combined_data = json.load(f)
        
        # Should have commands from second session (playback + permissions + save)
        self.assertGreaterEqual(len(combined_data['commands']), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)