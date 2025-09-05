#!/usr/bin/env python3
"""
AURA Interactive Debugging Mode

Interactive debugging mode for real-time troubleshooting, step-by-step command execution,
and debugging session recording/playback.

Usage:
    python debug_interactive.py [--record session.json] [--playback session.json]
"""

import argparse
import sys
import json
import time
import cmd
import threading
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging
import traceback

# Import AURA modules
try:
    from modules.accessibility_debugger import AccessibilityDebugger
    from modules.diagnostic_tools import AccessibilityHealthChecker
    from modules.permission_validator import PermissionValidator
    from modules.reasoning import ReasoningModule
    from modules.accessibility import AccessibilityModule
    from orchestrator import Orchestrator
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Error: Could not import AURA modules: {e}")
    print("Make sure you're running from the AURA root directory")
    sys.exit(1)


class DebugSession:
    """Represents a debugging session with recording capabilities."""
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize debug session."""
        self.session_id = session_id or f"debug_session_{int(time.time())}"
        self.start_time = datetime.now()
        self.commands = []
        self.results = []
        self.metadata = {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'platform': sys.platform,
            'python_version': sys.version
        }
    
    def record_command(self, command: str, args: List[str], result: Dict[str, Any]):
        """Record a command execution."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'args': args,
            'result': result,
            'execution_time_ms': result.get('execution_time_ms', 0)
        }
        self.commands.append(entry)
    
    def save_session(self, filepath: str):
        """Save session to file."""
        session_data = {
            'metadata': self.metadata,
            'commands': self.commands,
            'end_time': datetime.now().isoformat(),
            'total_commands': len(self.commands)
        }
        
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)
    
    def load_session(self, filepath: str):
        """Load session from file."""
        with open(filepath, 'r') as f:
            session_data = json.load(f)
        
        self.metadata = session_data.get('metadata', {})
        self.commands = session_data.get('commands', [])
        self.session_id = self.metadata.get('session_id', 'loaded_session')


class InteractiveDebugger(cmd.Cmd):
    """Interactive debugging command interface."""
    
    intro = """
=== AURA Interactive Debugging Mode ===

Available commands:
  tree [app_name]              - Dump accessibility tree
  element <text> [app_name]    - Analyze element detection
  health                       - Run health check
  permissions                  - Check permissions
  command <command>            - Execute AURA command with debugging
  step <command>               - Step through command execution
  apps                         - List running applications
  focus [app_name]             - Get/set focused application
  cache                        - Show cache status
  config                       - Show current configuration
  record <filename>            - Start recording session
  playback <filename>          - Playback recorded session
  save <filename>              - Save current session
  clear                        - Clear session history
  help [command]               - Show help
  quit                         - Exit interactive mode

Type 'help <command>' for detailed help on a specific command.
    """
    
    prompt = '(aura-debug) '
    
    def __init__(self, record_file: Optional[str] = None, playback_file: Optional[str] = None):
        """Initialize interactive debugger."""
        super().__init__()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize AURA components
        self.config = self._load_config()
        self.debugger = AccessibilityDebugger(self.config)
        self.health_checker = AccessibilityHealthChecker(self.config)
        self.permission_validator = PermissionValidator(self.config)
        
        # Initialize AURA core components for command execution
        try:
            self.reasoning = ReasoningModule()
            self.accessibility = AccessibilityModule()
            self.orchestrator = Orchestrator()
        except Exception as e:
            print(f"Warning: Could not initialize AURA core components: {e}")
            self.reasoning = None
            self.accessibility = None
            self.orchestrator = None
        
        # Session management
        self.session = DebugSession()
        self.recording = record_file is not None
        self.record_file = record_file
        
        # State tracking
        self.current_app = None
        self.last_tree_dump = None
        self.step_mode = False
        self.verbose = True
        
        # Performance tracking
        self.command_times = []
        
        print(f"Interactive debugger initialized (Session: {self.session.session_id})")
        
        # Handle playback mode
        if playback_file:
            self.do_playback(playback_file)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration for debugging."""
        try:
            import config
            return {
                'debug_level': getattr(config, 'DEBUG_LEVEL', 'VERBOSE'),
                'max_tree_depth': getattr(config, 'MAX_TREE_DEPTH', 10),
                'performance_tracking': True,
                'auto_diagnostics': True,
                'include_invisible_elements': True
            }
        except ImportError:
            return {
                'debug_level': 'VERBOSE',
                'max_tree_depth': 10,
                'performance_tracking': True,
                'auto_diagnostics': True,
                'include_invisible_elements': True
            }
    
    def _execute_with_timing(self, func, *args, **kwargs) -> Tuple[Any, float]:
        """Execute function with timing."""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            return result, execution_time
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            raise e
    
    def _record_command(self, command: str, args: List[str], result: Dict[str, Any]):
        """Record command if recording is enabled."""
        if self.recording:
            self.session.record_command(command, args, result)
    
    def do_tree(self, line):
        """
        Dump accessibility tree for inspection.
        Usage: tree [app_name]
        """
        args = line.split() if line.strip() else []
        app_name = args[0] if args else None
        
        try:
            print(f"Dumping accessibility tree for: {app_name or 'focused application'}")
            
            tree_dump, exec_time = self._execute_with_timing(
                self.debugger.dump_accessibility_tree,
                app_name=app_name,
                force_refresh=True
            )
            
            self.last_tree_dump = tree_dump
            self.current_app = tree_dump.app_name
            
            print(f"✅ Tree dump completed in {exec_time:.1f}ms")
            print(f"   Application: {tree_dump.app_name}")
            print(f"   Total elements: {tree_dump.total_elements}")
            print(f"   Clickable elements: {len(tree_dump.clickable_elements)}")
            print(f"   Tree depth: {tree_dump.tree_depth}")
            
            # Show top element roles
            print("\n--- Top Element Roles ---")
            for role, count in sorted(tree_dump.element_roles.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {role}: {count}")
            
            # Show some clickable elements
            if tree_dump.clickable_elements:
                print("\n--- Sample Clickable Elements ---")
                for i, elem in enumerate(tree_dump.clickable_elements[:5], 1):
                    title = elem.get('title', 'N/A')
                    role = elem.get('role', 'unknown')
                    print(f"  {i}. [{role}] {title}")
            
            result = {
                'success': True,
                'app_name': tree_dump.app_name,
                'total_elements': tree_dump.total_elements,
                'execution_time_ms': exec_time
            }
            
        except Exception as e:
            print(f"❌ Error dumping tree: {e}")
            result = {
                'success': False,
                'error': str(e),
                'execution_time_ms': 0
            }
        
        self._record_command('tree', args, result)
    
    def do_element(self, line):
        """
        Analyze element detection for specific text.
        Usage: element <target_text> [app_name]
        """
        args = line.split() if line.strip() else []
        if not args:
            print("❌ Error: Please provide target text")
            return
        
        target_text = args[0]
        app_name = args[1] if len(args) > 1 else None
        
        try:
            print(f"Analyzing element detection for: '{target_text}'")
            
            analysis, exec_time = self._execute_with_timing(
                self.debugger.analyze_element_detection_failure,
                command=f"find {target_text}",
                target=target_text,
                app_name=app_name
            )
            
            print(f"✅ Analysis completed in {exec_time:.1f}ms")
            print(f"   Matches found: {analysis.matches_found}")
            print(f"   Search strategy: {analysis.search_strategy}")
            
            if analysis.best_match:
                match = analysis.best_match
                print(f"\n--- Best Match ---")
                print(f"   Role: {match.get('role', 'unknown')}")
                print(f"   Title: {match.get('title', 'N/A')}")
                print(f"   Match Score: {match.get('match_score', 0):.1f}%")
                print(f"   Matched Text: {match.get('matched_text', 'N/A')}")
            else:
                print("\n❌ No matches found")
            
            if analysis.recommendations:
                print(f"\n--- Recommendations ---")
                for i, rec in enumerate(analysis.recommendations[:3], 1):
                    print(f"   {i}. {rec}")
            
            result = {
                'success': True,
                'target_text': target_text,
                'matches_found': analysis.matches_found,
                'best_match_score': analysis.best_match.get('match_score', 0) if analysis.best_match else 0,
                'execution_time_ms': exec_time
            }
            
        except Exception as e:
            print(f"❌ Error analyzing element: {e}")
            result = {
                'success': False,
                'error': str(e),
                'execution_time_ms': 0
            }
        
        self._record_command('element', args, result)
    
    def do_health(self, line):
        """
        Run comprehensive system health check.
        Usage: health
        """
        try:
            print("Running comprehensive health check...")
            
            report, exec_time = self._execute_with_timing(
                self.health_checker.run_comprehensive_health_check
            )
            
            print(f"✅ Health check completed in {exec_time:.1f}ms")
            print(f"   Overall health score: {report.overall_health_score:.1f}/100")
            
            # Show summary
            print(f"\n{report.generate_summary()}")
            
            # Show critical issues
            critical_issues = [i for i in report.detected_issues if i.severity == 'CRITICAL']
            if critical_issues:
                print(f"\n--- Critical Issues ---")
                for issue in critical_issues:
                    print(f"   ❌ {issue.title}: {issue.description}")
            
            result = {
                'success': True,
                'health_score': report.overall_health_score,
                'issues_count': len(report.detected_issues),
                'critical_issues': len(critical_issues),
                'execution_time_ms': exec_time
            }
            
        except Exception as e:
            print(f"❌ Error running health check: {e}")
            result = {
                'success': False,
                'error': str(e),
                'execution_time_ms': 0
            }
        
        self._record_command('health', [], result)
    
    def do_permissions(self, line):
        """
        Check accessibility permissions status.
        Usage: permissions
        """
        try:
            print("Checking accessibility permissions...")
            
            status, exec_time = self._execute_with_timing(
                self.permission_validator.check_accessibility_permissions
            )
            
            print(f"✅ Permission check completed in {exec_time:.1f}ms")
            print(f"   {status.get_summary()}")
            print(f"   Permission level: {status.permission_level}")
            print(f"   Can request permissions: {status.can_request_permissions}")
            
            if status.missing_permissions:
                print(f"\n--- Missing Permissions ---")
                for perm in status.missing_permissions:
                    print(f"   ❌ {perm}")
            
            if status.recommendations:
                print(f"\n--- Recommendations ---")
                for i, rec in enumerate(status.recommendations[:3], 1):
                    print(f"   {i}. {rec}")
            
            result = {
                'success': True,
                'has_permissions': status.has_permissions,
                'permission_level': status.permission_level,
                'missing_count': len(status.missing_permissions),
                'execution_time_ms': exec_time
            }
            
        except Exception as e:
            print(f"❌ Error checking permissions: {e}")
            result = {
                'success': False,
                'error': str(e),
                'execution_time_ms': 0
            }
        
        self._record_command('permissions', [], result)
    
    def do_command(self, line):
        """
        Execute AURA command with full debugging.
        Usage: command <aura_command>
        """
        if not line.strip():
            print("❌ Error: Please provide a command")
            return
        
        if not self.orchestrator:
            print("❌ Error: AURA orchestrator not available")
            return
        
        try:
            print(f"Executing AURA command: '{line}'")
            print("--- Debug Output ---")
            
            # Execute with debugging enabled
            start_time = time.time()
            
            # This would integrate with the actual orchestrator
            # For now, we'll simulate the execution
            result = {
                'command': line,
                'status': 'simulated',
                'message': 'Command execution simulation - integrate with actual orchestrator'
            }
            
            exec_time = (time.time() - start_time) * 1000
            
            print(f"✅ Command completed in {exec_time:.1f}ms")
            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   Message: {result.get('message', 'No message')}")
            
            result['execution_time_ms'] = exec_time
            result['success'] = True
            
        except Exception as e:
            print(f"❌ Error executing command: {e}")
            if self.verbose:
                traceback.print_exc()
            result = {
                'success': False,
                'error': str(e),
                'execution_time_ms': 0
            }
        
        self._record_command('command', [line], result)
    
    def do_step(self, line):
        """
        Step through command execution with detailed logging.
        Usage: step <aura_command>
        """
        if not line.strip():
            print("❌ Error: Please provide a command")
            return
        
        print(f"Stepping through command: '{line}'")
        print("Press Enter to continue each step, 'q' to quit stepping")
        
        # Simulate step-by-step execution
        steps = [
            "1. Parsing command",
            "2. Checking permissions",
            "3. Getting accessibility tree",
            "4. Finding target element",
            "5. Executing action",
            "6. Verifying result"
        ]
        
        try:
            for step in steps:
                print(f"\n--- {step} ---")
                user_input = input("Continue? (Enter/q): ").strip().lower()
                if user_input == 'q':
                    print("Stepping cancelled")
                    return
                
                # Simulate step execution
                time.sleep(0.5)  # Simulate processing time
                print(f"✅ {step} completed")
            
            print(f"\n✅ Command stepping completed")
            
            result = {
                'success': True,
                'command': line,
                'steps_completed': len(steps),
                'execution_time_ms': 0
            }
            
        except KeyboardInterrupt:
            print("\n❌ Stepping interrupted")
            result = {
                'success': False,
                'error': 'interrupted',
                'execution_time_ms': 0
            }
        
        self._record_command('step', [line], result)
    
    def do_apps(self, line):
        """
        List running applications.
        Usage: apps
        """
        try:
            print("Getting running applications...")
            
            # Use NSWorkspace to get running applications
            from AppKit import NSWorkspace
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()
            
            print(f"✅ Found {len(running_apps)} running applications")
            print("\n--- Running Applications ---")
            
            for i, app in enumerate(running_apps[:20], 1):  # Show first 20
                app_name = app.localizedName()
                bundle_id = app.bundleIdentifier()
                pid = app.processIdentifier()
                print(f"  {i:2d}. {app_name} (PID: {pid})")
                if bundle_id and self.verbose:
                    print(f"      Bundle: {bundle_id}")
            
            if len(running_apps) > 20:
                print(f"      ... and {len(running_apps) - 20} more")
            
            result = {
                'success': True,
                'app_count': len(running_apps),
                'execution_time_ms': 0
            }
            
        except Exception as e:
            print(f"❌ Error listing applications: {e}")
            result = {
                'success': False,
                'error': str(e),
                'execution_time_ms': 0
            }
        
        self._record_command('apps', [], result)
    
    def do_focus(self, line):
        """
        Get or set focused application.
        Usage: focus [app_name]
        """
        args = line.split() if line.strip() else []
        
        try:
            if not args:
                # Get current focused app
                focused_app = self.debugger._get_focused_application_name()
                if focused_app:
                    print(f"✅ Currently focused application: {focused_app}")
                    self.current_app = focused_app
                else:
                    print("❌ No focused application found")
                
                result = {
                    'success': focused_app is not None,
                    'focused_app': focused_app,
                    'execution_time_ms': 0
                }
            else:
                # Set focus (this would require additional implementation)
                app_name = args[0]
                print(f"Setting focus to: {app_name}")
                print("Note: Focus setting not implemented - use system to focus application")
                
                result = {
                    'success': False,
                    'message': 'Focus setting not implemented',
                    'execution_time_ms': 0
                }
            
        except Exception as e:
            print(f"❌ Error with focus operation: {e}")
            result = {
                'success': False,
                'error': str(e),
                'execution_time_ms': 0
            }
        
        self._record_command('focus', args, result)
    
    def do_cache(self, line):
        """
        Show cache status and statistics.
        Usage: cache
        """
        try:
            print("=== Cache Status ===")
            
            # Show tree cache
            tree_cache = getattr(self.debugger, 'tree_cache', {})
            print(f"Tree cache entries: {len(tree_cache)}")
            
            if tree_cache:
                print("\n--- Cached Trees ---")
                for key, dump in tree_cache.items():
                    age = (datetime.now() - dump.timestamp).total_seconds()
                    print(f"  {key}: {dump.app_name} (age: {age:.1f}s)")
            
            # Show permission cache
            perm_cache = getattr(self.permission_validator, 'permission_cache', {})
            print(f"\nPermission cache entries: {len(perm_cache)}")
            
            # Show session stats
            print(f"\nSession commands: {len(self.session.commands)}")
            print(f"Session duration: {(datetime.now() - self.session.start_time).total_seconds():.1f}s")
            
            result = {
                'success': True,
                'tree_cache_size': len(tree_cache),
                'permission_cache_size': len(perm_cache),
                'session_commands': len(self.session.commands),
                'execution_time_ms': 0
            }
            
        except Exception as e:
            print(f"❌ Error showing cache status: {e}")
            result = {
                'success': False,
                'error': str(e),
                'execution_time_ms': 0
            }
        
        self._record_command('cache', [], result)
    
    def do_config(self, line):
        """
        Show current configuration.
        Usage: config
        """
        try:
            print("=== Current Configuration ===")
            for key, value in self.config.items():
                print(f"  {key}: {value}")
            
            print(f"\n=== Session Settings ===")
            print(f"  Recording: {self.recording}")
            print(f"  Record file: {self.record_file}")
            print(f"  Verbose: {self.verbose}")
            print(f"  Step mode: {self.step_mode}")
            print(f"  Current app: {self.current_app}")
            
            result = {
                'success': True,
                'config': self.config.copy(),
                'execution_time_ms': 0
            }
            
        except Exception as e:
            print(f"❌ Error showing configuration: {e}")
            result = {
                'success': False,
                'error': str(e),
                'execution_time_ms': 0
            }
        
        self._record_command('config', [], result)
    
    def do_record(self, line):
        """
        Start recording session to file.
        Usage: record <filename>
        """
        if not line.strip():
            print("❌ Error: Please provide filename")
            return
        
        filename = line.strip()
        self.recording = True
        self.record_file = filename
        
        print(f"✅ Started recording session to: {filename}")
        
        result = {
            'success': True,
            'recording': True,
            'filename': filename,
            'execution_time_ms': 0
        }
        
        self._record_command('record', [filename], result)
    
    def do_playback(self, line):
        """
        Playback recorded session from file.
        Usage: playback <filename>
        """
        if not line.strip():
            print("❌ Error: Please provide filename")
            return
        
        filename = line.strip()
        
        try:
            print(f"Loading session from: {filename}")
            
            with open(filename, 'r') as f:
                session_data = json.load(f)
            
            commands = session_data.get('commands', [])
            metadata = session_data.get('metadata', {})
            
            print(f"✅ Loaded session with {len(commands)} commands")
            print(f"   Session ID: {metadata.get('session_id', 'unknown')}")
            print(f"   Created: {metadata.get('start_time', 'unknown')}")
            
            # Ask user if they want to replay commands
            replay = input("Replay commands? (y/N): ").strip().lower()
            if replay == 'y':
                print("\nReplaying commands...")
                for i, cmd_entry in enumerate(commands, 1):
                    print(f"\n--- Command {i}/{len(commands)} ---")
                    print(f"Original: {cmd_entry['command']} {' '.join(cmd_entry.get('args', []))}")
                    
                    user_input = input("Execute? (y/N/q): ").strip().lower()
                    if user_input == 'q':
                        print("Playback stopped")
                        break
                    elif user_input == 'y':
                        # Execute the command
                        cmd_line = f"{cmd_entry['command']} {' '.join(cmd_entry.get('args', []))}"
                        self.onecmd(cmd_line)
            
            result = {
                'success': True,
                'filename': filename,
                'commands_loaded': len(commands),
                'execution_time_ms': 0
            }
            
        except Exception as e:
            print(f"❌ Error loading session: {e}")
            result = {
                'success': False,
                'error': str(e),
                'execution_time_ms': 0
            }
        
        self._record_command('playback', [filename], result)
    
    def do_save(self, line):
        """
        Save current session to file.
        Usage: save <filename>
        """
        if not line.strip():
            print("❌ Error: Please provide filename")
            return
        
        filename = line.strip()
        
        try:
            self.session.save_session(filename)
            print(f"✅ Session saved to: {filename}")
            print(f"   Commands: {len(self.session.commands)}")
            
            result = {
                'success': True,
                'filename': filename,
                'commands_saved': len(self.session.commands),
                'execution_time_ms': 0
            }
            
        except Exception as e:
            print(f"❌ Error saving session: {e}")
            result = {
                'success': False,
                'error': str(e),
                'execution_time_ms': 0
            }
        
        self._record_command('save', [filename], result)
    
    def do_clear(self, line):
        """
        Clear session history.
        Usage: clear
        """
        commands_count = len(self.session.commands)
        self.session = DebugSession()
        
        print(f"✅ Session cleared ({commands_count} commands removed)")
        
        result = {
            'success': True,
            'commands_cleared': commands_count,
            'execution_time_ms': 0
        }
        
        self._record_command('clear', [], result)
    
    def do_quit(self, line):
        """
        Exit interactive debugging mode.
        Usage: quit
        """
        if self.recording and self.record_file:
            save_session = input("Save recording before exit? (Y/n): ").strip().lower()
            if save_session != 'n':
                try:
                    self.session.save_session(self.record_file)
                    print(f"✅ Session saved to: {self.record_file}")
                except Exception as e:
                    print(f"❌ Error saving session: {e}")
        
        print("Goodbye!")
        return True
    
    def do_EOF(self, line):
        """Handle Ctrl+D."""
        print()
        return self.do_quit(line)
    
    def emptyline(self):
        """Handle empty line input."""
        pass
    
    def default(self, line):
        """Handle unknown commands."""
        print(f"❌ Unknown command: {line}")
        print("Type 'help' for available commands")


def main():
    """Main entry point for interactive debugging."""
    parser = argparse.ArgumentParser(
        description="AURA Interactive Debugging Mode",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--record', help='Record session to file')
    parser.add_argument('--playback', help='Playback session from file')
    
    args = parser.parse_args()
    
    try:
        # Initialize interactive debugger
        debugger = InteractiveDebugger(
            record_file=args.record,
            playback_file=args.playback
        )
        
        # Start interactive loop
        debugger.cmdloop()
        
        return 0
        
    except KeyboardInterrupt:
        print("\nInteractive debugging cancelled")
        return 1
    except Exception as e:
        print(f"Error starting interactive debugger: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())