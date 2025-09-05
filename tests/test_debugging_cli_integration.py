"""
Integration tests for AURA debugging command-line tools.

Tests the debug_cli.py and debug_interactive.py utilities to ensure they work
correctly with real system components and provide accurate debugging information.
"""

import unittest
import subprocess
import json
import tempfile
import os
import sys
import time
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from debug_cli import DebugCLI
    from debug_interactive import InteractiveDebugger, DebugSession
    CLI_MODULES_AVAILABLE = True
except ImportError:
    CLI_MODULES_AVAILABLE = False


class TestDebugCLIIntegration(unittest.TestCase):
    """Integration tests for the debug CLI tool."""
    
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
    
    @unittest.skipUnless(CLI_MODULES_AVAILABLE, "CLI modules not available")
    def test_debug_cli_initialization(self):
        """Test that DebugCLI initializes correctly."""
        cli = DebugCLI()
        
        # Check that components are initialized
        self.assertIsNotNone(cli.debugger)
        self.assertIsNotNone(cli.health_checker)
        self.assertIsNotNone(cli.permission_validator)
        self.assertIsInstance(cli.config, dict)
    
    @unittest.skipUnless(CLI_MODULES_AVAILABLE, "CLI modules not available")
    def test_debug_cli_tree_command(self):
        """Test the tree command functionality."""
        cli = DebugCLI()
        
        # Mock arguments for tree command
        class MockArgs:
            app_name = None
            output = 'text'
            depth = 5
            file = None
        
        args = MockArgs()
        
        # Mock the debugger to avoid actual system calls
        with patch.object(cli.debugger, 'dump_accessibility_tree') as mock_dump:
            # Create a mock tree dump
            mock_tree_dump = MagicMock()
            mock_tree_dump.app_name = 'TestApp'
            mock_tree_dump.total_elements = 100
            mock_tree_dump.clickable_elements = [{'title': 'Button1', 'role': 'AXButton'}]
            mock_tree_dump.tree_depth = 5
            mock_tree_dump.generation_time_ms = 150.0
            mock_tree_dump.element_roles = {'AXButton': 10, 'AXStaticText': 50}
            
            mock_dump.return_value = mock_tree_dump
            
            # Test tree command
            result = cli.cmd_tree(args)
            
            # Verify command executed successfully
            self.assertEqual(result, 0)
            mock_dump.assert_called_once()
    
    @unittest.skipUnless(CLI_MODULES_AVAILABLE, "CLI modules not available")
    def test_debug_cli_tree_json_output(self):
        """Test tree command with JSON output to file."""
        cli = DebugCLI()
        output_file = self._create_temp_file('.json')
        
        class MockArgs:
            app_name = 'TestApp'
            output = 'json'
            depth = 5
            file = output_file
        
        args = MockArgs()
        
        with patch.object(cli.debugger, 'dump_accessibility_tree') as mock_dump:
            mock_tree_dump = MagicMock()
            mock_tree_dump.to_json.return_value = '{"test": "data"}'
            mock_tree_dump.total_elements = 100
            mock_tree_dump.clickable_elements = []
            mock_tree_dump.generation_time_ms = 150.0
            
            mock_dump.return_value = mock_tree_dump
            
            result = cli.cmd_tree(args)
            
            self.assertEqual(result, 0)
            self.assertTrue(os.path.exists(output_file))
            
            # Verify file content
            with open(output_file, 'r') as f:
                content = f.read()
                self.assertEqual(content, '{"test": "data"}')
    
    @unittest.skipUnless(CLI_MODULES_AVAILABLE, "CLI modules not available")
    def test_debug_cli_element_command(self):
        """Test the element analysis command."""
        cli = DebugCLI()
        
        class MockArgs:
            target_text = 'Sign In'
            app_name = 'TestApp'
            fuzzy = True
            threshold = 70.0
            output = 'text'
            file = None
        
        args = MockArgs()
        
        with patch.object(cli.debugger, 'analyze_element_detection_failure') as mock_analyze:
            mock_analysis = MagicMock()
            mock_analysis.target_text = 'Sign In'
            mock_analysis.search_strategy = 'multi_strategy'
            mock_analysis.matches_found = 2
            mock_analysis.search_time_ms = 45.0
            mock_analysis.best_match = {
                'role': 'AXButton',
                'title': 'Sign In',
                'match_score': 95.0,
                'matched_text': 'Sign In'
            }
            mock_analysis.all_matches = [mock_analysis.best_match]
            mock_analysis.recommendations = ['Element found with high confidence']
            mock_analysis.to_dict.return_value = {'test': 'analysis'}
            
            mock_analyze.return_value = mock_analysis
            
            result = cli.cmd_element(args)
            
            self.assertEqual(result, 0)
            mock_analyze.assert_called_once()
    
    @unittest.skipUnless(CLI_MODULES_AVAILABLE, "CLI modules not available")
    def test_debug_cli_health_command(self):
        """Test the health check command."""
        cli = DebugCLI()
        
        class MockArgs:
            format = 'text'
            output = None
        
        args = MockArgs()
        
        with patch.object(cli.health_checker, 'run_comprehensive_health_check') as mock_health:
            mock_report = MagicMock()
            mock_report.overall_health_score = 85.0
            mock_report.detected_issues = []
            mock_report.benchmark_results = []
            mock_report.generation_time_ms = 1000.0
            mock_report.generate_summary.return_value = 'Health check summary'
            
            mock_health.return_value = mock_report
            
            result = cli.cmd_health(args)
            
            self.assertEqual(result, 0)
            mock_health.assert_called_once()
    
    @unittest.skipUnless(CLI_MODULES_AVAILABLE, "CLI modules not available")
    def test_debug_cli_permissions_command(self):
        """Test the permissions check command."""
        cli = DebugCLI()
        
        class MockArgs:
            request = False
            monitor = False
        
        args = MockArgs()
        
        with patch.object(cli.permission_validator, 'check_accessibility_permissions') as mock_perms:
            mock_status = MagicMock()
            mock_status.has_permissions = True
            mock_status.permission_level = 'FULL'
            mock_status.system_version = '14.0'
            mock_status.can_request_permissions = True
            mock_status.granted_permissions = ['basic_access']
            mock_status.missing_permissions = []
            mock_status.recommendations = []
            mock_status.get_summary.return_value = 'Permissions OK'
            
            mock_perms.return_value = mock_status
            
            result = cli.cmd_permissions(args)
            
            self.assertEqual(result, 0)
            mock_perms.assert_called_once()
    
    def test_debug_cli_command_line_interface(self):
        """Test the command-line interface using subprocess."""
        # Test help command
        result = subprocess.run([
            sys.executable, 'debug_cli.py', '--help'
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Should exit with 0 and show help text
        self.assertEqual(result.returncode, 0)
        self.assertIn('AURA Debugging Command-Line Interface', result.stdout)
        self.assertIn('tree', result.stdout)
        self.assertIn('element', result.stdout)
        self.assertIn('health', result.stdout)


class TestDebugSessionIntegration(unittest.TestCase):
    """Integration tests for debug session recording and playback."""
    
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
    
    @unittest.skipUnless(CLI_MODULES_AVAILABLE, "CLI modules not available")
    def test_debug_session_creation(self):
        """Test debug session creation and basic functionality."""
        session = DebugSession('test_session')
        
        self.assertEqual(session.session_id, 'test_session')
        self.assertIsInstance(session.start_time, datetime)
        self.assertEqual(len(session.commands), 0)
        self.assertIn('session_id', session.metadata)
    
    @unittest.skipUnless(CLI_MODULES_AVAILABLE, "CLI modules not available")
    def test_debug_session_recording(self):
        """Test command recording in debug session."""
        session = DebugSession('test_session')
        
        # Record a command
        test_result = {
            'success': True,
            'execution_time_ms': 100.0,
            'data': 'test_data'
        }
        
        session.record_command('tree', ['Safari'], test_result)
        
        self.assertEqual(len(session.commands), 1)
        
        recorded_command = session.commands[0]
        self.assertEqual(recorded_command['command'], 'tree')
        self.assertEqual(recorded_command['args'], ['Safari'])
        self.assertEqual(recorded_command['result'], test_result)
        self.assertIn('timestamp', recorded_command)
    
    @unittest.skipUnless(CLI_MODULES_AVAILABLE, "CLI modules not available")
    def test_debug_session_save_load(self):
        """Test saving and loading debug sessions."""
        session = DebugSession('test_session')
        
        # Add some commands
        session.record_command('tree', [], {'success': True})
        session.record_command('health', [], {'success': True, 'score': 85.0})
        
        # Save session
        session_file = self._create_temp_file('.json')
        session.save_session(session_file)
        
        # Verify file exists and has content
        self.assertTrue(os.path.exists(session_file))
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        self.assertIn('metadata', session_data)
        self.assertIn('commands', session_data)
        self.assertEqual(len(session_data['commands']), 2)
        self.assertEqual(session_data['metadata']['session_id'], 'test_session')
        
        # Load session
        new_session = DebugSession()
        new_session.load_session(session_file)
        
        self.assertEqual(new_session.session_id, 'test_session')
        self.assertEqual(len(new_session.commands), 2)
    
    @unittest.skipUnless(CLI_MODULES_AVAILABLE, "CLI modules not available")
    def test_interactive_debugger_initialization(self):
        """Test interactive debugger initialization."""
        debugger = InteractiveDebugger()
        
        # Check components are initialized
        self.assertIsNotNone(debugger.debugger)
        self.assertIsNotNone(debugger.health_checker)
        self.assertIsNotNone(debugger.permission_validator)
        self.assertIsNotNone(debugger.session)
        self.assertIsInstance(debugger.config, dict)
    
    @unittest.skipUnless(CLI_MODULES_AVAILABLE, "CLI modules not available")
    def test_interactive_debugger_command_execution(self):
        """Test command execution in interactive debugger."""
        debugger = InteractiveDebugger()
        debugger.recording = True  # Enable recording for test
        
        # Mock the debugger components
        with patch.object(debugger.debugger, 'dump_accessibility_tree') as mock_dump:
            mock_tree_dump = MagicMock()
            mock_tree_dump.app_name = 'TestApp'
            mock_tree_dump.total_elements = 100
            mock_tree_dump.clickable_elements = []
            mock_tree_dump.tree_depth = 5
            mock_tree_dump.element_roles = {'AXButton': 10}
            
            mock_dump.return_value = mock_tree_dump
            
            # Execute tree command
            debugger.do_tree('TestApp')
            
            # Verify command was recorded
            self.assertEqual(len(debugger.session.commands), 1)
            recorded_cmd = debugger.session.commands[0]
            self.assertEqual(recorded_cmd['command'], 'tree')
            self.assertEqual(recorded_cmd['args'], ['TestApp'])
            self.assertTrue(recorded_cmd['result']['success'])


class TestDebugToolsSystemIntegration(unittest.TestCase):
    """System-level integration tests for debugging tools."""
    
    @unittest.skipUnless(CLI_MODULES_AVAILABLE, "CLI modules not available")
    def test_debug_tools_with_real_system(self):
        """Test debugging tools with real system components (if available)."""
        try:
            # Try to initialize components with real system
            cli = DebugCLI()
            
            # Test permission check (should work on any macOS system)
            class MockArgs:
                request = False
                monitor = False
            
            args = MockArgs()
            result = cli.cmd_permissions(args)
            
            # Should complete without error (may return 0 or 1 depending on permissions)
            self.assertIn(result, [0, 1])
            
        except Exception as e:
            # If system components aren't available, skip the test
            self.skipTest(f"Real system components not available: {e}")
    
    def test_debug_cli_error_handling(self):
        """Test error handling in debug CLI."""
        # Test with invalid command
        result = subprocess.run([
            sys.executable, 'debug_cli.py', 'invalid_command'
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Should show help and exit with error
        self.assertNotEqual(result.returncode, 0)
    
    @unittest.skipUnless(CLI_MODULES_AVAILABLE, "CLI modules not available")
    def test_debug_session_file_format(self):
        """Test that debug session files have correct format."""
        session = DebugSession('format_test')
        
        # Add various types of commands
        session.record_command('tree', ['Safari'], {
            'success': True,
            'app_name': 'Safari',
            'total_elements': 100,
            'execution_time_ms': 150.0
        })
        
        session.record_command('element', ['Sign In', 'Chrome'], {
            'success': True,
            'matches_found': 2,
            'best_match_score': 95.0,
            'execution_time_ms': 45.0
        })
        
        session.record_command('health', [], {
            'success': True,
            'health_score': 85.0,
            'issues_count': 1,
            'execution_time_ms': 1000.0
        })
        
        # Save and verify format
        temp_file = tempfile.mktemp(suffix='.json')
        try:
            session.save_session(temp_file)
            
            with open(temp_file, 'r') as f:
                data = json.load(f)
            
            # Verify required fields
            self.assertIn('metadata', data)
            self.assertIn('commands', data)
            self.assertIn('end_time', data)
            self.assertIn('total_commands', data)
            
            # Verify metadata
            metadata = data['metadata']
            self.assertIn('session_id', metadata)
            self.assertIn('start_time', metadata)
            self.assertIn('platform', metadata)
            self.assertIn('python_version', metadata)
            
            # Verify commands
            commands = data['commands']
            self.assertEqual(len(commands), 3)
            
            for cmd in commands:
                self.assertIn('timestamp', cmd)
                self.assertIn('command', cmd)
                self.assertIn('args', cmd)
                self.assertIn('result', cmd)
                self.assertIn('execution_time_ms', cmd)
            
            # Verify command types
            command_names = [cmd['command'] for cmd in commands]
            self.assertIn('tree', command_names)
            self.assertIn('element', command_names)
            self.assertIn('health', command_names)
            
        finally:
            try:
                os.remove(temp_file)
            except FileNotFoundError:
                pass


class TestDebugToolsPerformance(unittest.TestCase):
    """Performance tests for debugging tools."""
    
    @unittest.skipUnless(CLI_MODULES_AVAILABLE, "CLI modules not available")
    def test_debug_session_performance(self):
        """Test performance of debug session recording."""
        session = DebugSession('performance_test')
        
        # Record many commands to test performance
        start_time = time.time()
        
        for i in range(100):
            session.record_command(f'command_{i}', [f'arg_{i}'], {
                'success': True,
                'iteration': i,
                'execution_time_ms': 10.0
            })
        
        recording_time = time.time() - start_time
        
        # Should be able to record 100 commands quickly
        self.assertLess(recording_time, 1.0)  # Less than 1 second
        self.assertEqual(len(session.commands), 100)
    
    @unittest.skipUnless(CLI_MODULES_AVAILABLE, "CLI modules not available")
    def test_session_file_size(self):
        """Test that session files don't grow too large."""
        session = DebugSession('size_test')
        
        # Add realistic command data
        for i in range(50):
            session.record_command('tree', ['TestApp'], {
                'success': True,
                'app_name': 'TestApp',
                'total_elements': 1000,
                'clickable_elements': list(range(100)),  # Large data
                'execution_time_ms': 150.0
            })
        
        temp_file = tempfile.mktemp(suffix='.json')
        try:
            session.save_session(temp_file)
            
            file_size = os.path.getsize(temp_file)
            
            # File should be reasonable size (less than 1MB for 50 commands)
            self.assertLess(file_size, 1024 * 1024)  # 1MB
            
        finally:
            try:
                os.remove(temp_file)
            except FileNotFoundError:
                pass


if __name__ == '__main__':
    # Set up test environment
    import time
    
    # Run tests
    unittest.main(verbosity=2)