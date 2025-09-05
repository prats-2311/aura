#!/usr/bin/env python3
"""
AURA Step-by-Step Command Debugging

Advanced step-by-step debugging for AURA commands with detailed logging,
breakpoints, and execution flow analysis.

Usage:
    python debug_step_by_step.py "Click on Sign In button"
    python debug_step_by_step.py --interactive
"""

import argparse
import sys
import time
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import logging
import traceback

# Import AURA modules
try:
    from modules.accessibility_debugger import AccessibilityDebugger
    from modules.reasoning import ReasoningModule
    from modules.accessibility import AccessibilityModule
    from orchestrator import Orchestrator
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Error: Could not import AURA modules: {e}")
    print("Make sure you're running from the AURA root directory")
    sys.exit(1)


class ExecutionStep:
    """Represents a single step in command execution."""
    
    def __init__(self, step_id: str, name: str, description: str, 
                 function: Callable, args: tuple = (), kwargs: dict = None):
        """Initialize execution step."""
        self.step_id = step_id
        self.name = name
        self.description = description
        self.function = function
        self.args = args
        self.kwargs = kwargs or {}
        
        # Execution state
        self.executed = False
        self.success = False
        self.result = None
        self.error = None
        self.execution_time_ms = 0.0
        self.timestamp = None
        
        # Debug information
        self.debug_info = {}
        self.breakpoint = False
    
    def execute(self, debug_mode: bool = True) -> Dict[str, Any]:
        """Execute the step and return results."""
        self.timestamp = datetime.now()
        start_time = time.time()
        
        try:
            if debug_mode:
                print(f"\n--- Executing Step: {self.name} ---")
                print(f"Description: {self.description}")
                print(f"Function: {self.function.__name__}")
                if self.args:
                    print(f"Args: {self.args}")
                if self.kwargs:
                    print(f"Kwargs: {self.kwargs}")
            
            # Execute the function
            self.result = self.function(*self.args, **self.kwargs)
            self.success = True
            
            if debug_mode:
                print(f"✅ Step completed successfully")
                if self.result:
                    print(f"Result: {self.result}")
            
        except Exception as e:
            self.success = False
            self.error = str(e)
            
            if debug_mode:
                print(f"❌ Step failed: {e}")
                traceback.print_exc()
        
        finally:
            self.executed = True
            self.execution_time_ms = (time.time() - start_time) * 1000
            
            if debug_mode:
                print(f"Execution time: {self.execution_time_ms:.1f}ms")
        
        return self.to_dict()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary for serialization."""
        return {
            'step_id': self.step_id,
            'name': self.name,
            'description': self.description,
            'executed': self.executed,
            'success': self.success,
            'result': self.result,
            'error': self.error,
            'execution_time_ms': self.execution_time_ms,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'debug_info': self.debug_info,
            'breakpoint': self.breakpoint
        }


class StepByStepDebugger:
    """Step-by-step command execution debugger."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the step-by-step debugger."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize AURA components
        self.debugger = AccessibilityDebugger(self.config)
        self.reasoning = ReasoningModule()
        self.accessibility = AccessibilityModule()
        self.orchestrator = Orchestrator()
        
        # Import and initialize permission validator
        try:
            from modules.permission_validator import PermissionValidator
            self.permission_validator = PermissionValidator(self.config)
        except ImportError:
            self.permission_validator = None
        
        # Execution state
        self.steps = []
        self.current_step_index = 0
        self.execution_context = {}
        self.breakpoints = set()
        
        # Debug settings
        self.interactive_mode = True
        self.auto_continue = False
        self.verbose_logging = True
        
        print("Step-by-step debugger initialized")
    
    def create_command_execution_steps(self, command: str) -> List[ExecutionStep]:
        """Create execution steps for a command."""
        steps = []
        
        # Step 1: Parse and analyze command
        steps.append(ExecutionStep(
            step_id='parse_command',
            name='Parse Command',
            description=f'Parse and analyze the command: "{command}"',
            function=self._step_parse_command,
            args=(command,)
        ))
        
        # Step 2: Check system permissions
        steps.append(ExecutionStep(
            step_id='check_permissions',
            name='Check Permissions',
            description='Verify accessibility permissions and system health',
            function=self._step_check_permissions
        ))
        
        # Step 3: Get accessibility tree
        steps.append(ExecutionStep(
            step_id='get_accessibility_tree',
            name='Get Accessibility Tree',
            description='Retrieve accessibility tree for target application',
            function=self._step_get_accessibility_tree
        ))
        
        # Step 4: Extract target information
        steps.append(ExecutionStep(
            step_id='extract_target',
            name='Extract Target',
            description='Extract target element information from command',
            function=self._step_extract_target,
            args=(command,)
        ))
        
        # Step 5: Find target element
        steps.append(ExecutionStep(
            step_id='find_element',
            name='Find Element',
            description='Locate target element in accessibility tree',
            function=self._step_find_element
        ))
        
        # Step 6: Validate element
        steps.append(ExecutionStep(
            step_id='validate_element',
            name='Validate Element',
            description='Validate that found element is actionable',
            function=self._step_validate_element
        ))
        
        # Step 7: Execute action
        steps.append(ExecutionStep(
            step_id='execute_action',
            name='Execute Action',
            description='Perform the requested action on the element',
            function=self._step_execute_action,
            args=(command,)
        ))
        
        # Step 8: Verify result
        steps.append(ExecutionStep(
            step_id='verify_result',
            name='Verify Result',
            description='Verify that the action was successful',
            function=self._step_verify_result
        ))
        
        return steps
    
    def execute_command_step_by_step(self, command: str) -> Dict[str, Any]:
        """Execute a command step by step with debugging."""
        print(f"\n=== Step-by-Step Execution: {command} ===")
        
        # Create execution steps
        self.steps = self.create_command_execution_steps(command)
        self.current_step_index = 0
        self.execution_context = {'command': command}
        
        execution_results = {
            'command': command,
            'start_time': datetime.now().isoformat(),
            'steps': [],
            'overall_success': False,
            'total_execution_time_ms': 0.0,
            'failed_step': None
        }
        
        start_time = time.time()
        
        try:
            for i, step in enumerate(self.steps):
                self.current_step_index = i
                
                # Check for breakpoint
                if step.breakpoint or step.step_id in self.breakpoints:
                    if self.interactive_mode:
                        self._handle_breakpoint(step)
                
                # Execute step
                step_result = step.execute(debug_mode=self.verbose_logging)
                execution_results['steps'].append(step_result)
                
                # Handle step failure
                if not step.success:
                    execution_results['failed_step'] = step.step_id
                    print(f"\n❌ Execution failed at step: {step.name}")
                    print(f"Error: {step.error}")
                    
                    if self.interactive_mode:
                        self._handle_step_failure(step)
                    
                    break
                
                # Update execution context with step results
                if step.result:
                    self.execution_context[step.step_id] = step.result
                
                # Interactive pause
                if self.interactive_mode and not self.auto_continue:
                    self._interactive_pause()
            
            # Check overall success
            execution_results['overall_success'] = all(step.success for step in self.steps if step.executed)
            
        except KeyboardInterrupt:
            print("\n❌ Execution interrupted by user")
            execution_results['overall_success'] = False
            execution_results['failed_step'] = 'user_interrupt'
        
        finally:
            execution_results['total_execution_time_ms'] = (time.time() - start_time) * 1000
            execution_results['end_time'] = datetime.now().isoformat()
        
        # Show execution summary
        self._show_execution_summary(execution_results)
        
        return execution_results
    
    def _step_parse_command(self, command: str) -> Dict[str, Any]:
        """Step 1: Parse and analyze command."""
        try:
            # Use reasoning module to get action plan
            action_plan = self.reasoning.get_action_plan(command, {})
            
            # Extract first action for simplicity
            actions = action_plan.get('actions', [])
            first_action = actions[0] if actions else {}
            metadata = action_plan.get('metadata', {})
            
            result = {
                'original_command': command,
                'parsed_command': action_plan,
                'action_type': first_action.get('action', 'unknown'),
                'target_text': first_action.get('target', ''),
                'confidence': metadata.get('confidence', 0.0)
            }
            
            print(f"   Action: {result['action_type']}")
            print(f"   Target: {result['target_text']}")
            print(f"   Confidence: {result['confidence']:.1%}")
            
            return result
            
        except Exception as e:
            raise Exception(f"Command parsing failed: {e}")
    
    def _step_check_permissions(self) -> Dict[str, Any]:
        """Step 2: Check system permissions."""
        try:
            # Check accessibility permissions
            if not self.permission_validator:
                raise Exception("Permission validator not available")
            
            permission_status = self.permission_validator.check_accessibility_permissions()
            
            result = {
                'has_permissions': permission_status.has_permissions,
                'permission_level': permission_status.permission_level,
                'missing_permissions': permission_status.missing_permissions,
                'can_request': permission_status.can_request_permissions
            }
            
            print(f"   Permission Status: {permission_status.get_summary()}")
            
            if not permission_status.has_permissions:
                raise Exception(f"Insufficient accessibility permissions: {permission_status.permission_level}")
            
            return result
            
        except Exception as e:
            raise Exception(f"Permission check failed: {e}")
    
    def _step_get_accessibility_tree(self) -> Dict[str, Any]:
        """Step 3: Get accessibility tree."""
        try:
            # Get focused application
            app_name = self.debugger._get_focused_application_name()
            if not app_name:
                raise Exception("No focused application found")
            
            # Dump accessibility tree
            tree_dump = self.debugger.dump_accessibility_tree(app_name)
            
            result = {
                'app_name': app_name,
                'total_elements': tree_dump.total_elements,
                'clickable_elements': len(tree_dump.clickable_elements),
                'tree_depth': tree_dump.tree_depth,
                'generation_time_ms': tree_dump.generation_time_ms
            }
            
            print(f"   Application: {app_name}")
            print(f"   Elements: {tree_dump.total_elements} total, {len(tree_dump.clickable_elements)} clickable")
            
            # Store tree dump in context
            self.execution_context['tree_dump'] = tree_dump
            self.execution_context['app_name'] = app_name
            
            return result
            
        except Exception as e:
            raise Exception(f"Accessibility tree retrieval failed: {e}")
    
    def _step_extract_target(self, command: str) -> Dict[str, Any]:
        """Step 4: Extract target information."""
        try:
            # Get parsed command from context
            parsed_command = self.execution_context.get('parse_command', {})
            target_text = parsed_command.get('target_text', '')
            
            if not target_text:
                raise Exception("No target text found in command")
            
            result = {
                'target_text': target_text,
                'action_type': parsed_command.get('action_type', 'unknown'),
                'search_strategies': ['exact', 'fuzzy', 'partial', 'role_based']
            }
            
            print(f"   Target Text: '{target_text}'")
            print(f"   Action Type: {result['action_type']}")
            
            return result
            
        except Exception as e:
            raise Exception(f"Target extraction failed: {e}")
    
    def _step_find_element(self) -> Dict[str, Any]:
        """Step 5: Find target element."""
        try:
            tree_dump = self.execution_context.get('tree_dump')
            target_info = self.execution_context.get('extract_target', {})
            target_text = target_info.get('target_text', '')
            
            if not tree_dump or not target_text:
                raise Exception("Missing tree dump or target text")
            
            # Analyze element detection
            analysis = self.debugger.analyze_element_detection_failure(
                command=self.execution_context['command'],
                target=target_text,
                app_name=self.execution_context.get('app_name')
            )
            
            result = {
                'target_text': target_text,
                'matches_found': analysis.matches_found,
                'best_match': analysis.best_match,
                'search_time_ms': analysis.search_time_ms,
                'recommendations': analysis.recommendations
            }
            
            print(f"   Matches Found: {analysis.matches_found}")
            if analysis.best_match:
                match = analysis.best_match
                print(f"   Best Match: {match.get('role', 'unknown')} - {match.get('title', 'N/A')}")
                print(f"   Match Score: {match.get('match_score', 0):.1f}%")
            
            if analysis.matches_found == 0:
                raise Exception(f"No matching elements found for '{target_text}'")
            
            # Store analysis in context
            self.execution_context['element_analysis'] = analysis
            
            return result
            
        except Exception as e:
            raise Exception(f"Element finding failed: {e}")
    
    def _step_validate_element(self) -> Dict[str, Any]:
        """Step 6: Validate element."""
        try:
            analysis = self.execution_context.get('element_analysis')
            if not analysis or not analysis.best_match:
                raise Exception("No element found to validate")
            
            element = analysis.best_match
            
            # Validate element properties
            is_clickable = element.get('role') in ['AXButton', 'AXLink', 'AXMenuItem']
            is_enabled = element.get('enabled', True)
            has_position = element.get('position') is not None
            
            result = {
                'element_role': element.get('role', 'unknown'),
                'element_title': element.get('title', 'N/A'),
                'is_clickable': is_clickable,
                'is_enabled': is_enabled,
                'has_position': has_position,
                'validation_passed': is_clickable and is_enabled and has_position
            }
            
            print(f"   Element Role: {result['element_role']}")
            print(f"   Clickable: {result['is_clickable']}")
            print(f"   Enabled: {result['is_enabled']}")
            print(f"   Has Position: {result['has_position']}")
            
            if not result['validation_passed']:
                raise Exception("Element validation failed - element may not be actionable")
            
            return result
            
        except Exception as e:
            raise Exception(f"Element validation failed: {e}")
    
    def _step_execute_action(self, command: str) -> Dict[str, Any]:
        """Step 7: Execute action."""
        try:
            analysis = self.execution_context.get('element_analysis')
            if not analysis or not analysis.best_match:
                raise Exception("No validated element to act on")
            
            element = analysis.best_match
            
            # For now, simulate action execution
            # In a real implementation, this would use the automation module
            result = {
                'action_type': 'click',
                'target_element': element.get('title', 'N/A'),
                'element_role': element.get('role', 'unknown'),
                'simulated': True,
                'success': True
            }
            
            print(f"   Action: {result['action_type']}")
            print(f"   Target: {result['target_element']}")
            print(f"   Status: Simulated (would execute in real system)")
            
            return result
            
        except Exception as e:
            raise Exception(f"Action execution failed: {e}")
    
    def _step_verify_result(self) -> Dict[str, Any]:
        """Step 8: Verify result."""
        try:
            action_result = self.execution_context.get('execute_action', {})
            
            # Simulate result verification
            result = {
                'verification_method': 'simulated',
                'action_successful': action_result.get('success', False),
                'verification_passed': True,
                'notes': 'Verification simulated - would check actual system state'
            }
            
            print(f"   Verification: {result['verification_method']}")
            print(f"   Action Success: {result['action_successful']}")
            print(f"   Overall Result: {'✅ PASSED' if result['verification_passed'] else '❌ FAILED'}")
            
            return result
            
        except Exception as e:
            raise Exception(f"Result verification failed: {e}")
    
    def _handle_breakpoint(self, step: ExecutionStep):
        """Handle breakpoint at a step."""
        print(f"\n🔴 BREAKPOINT: {step.name}")
        print(f"Description: {step.description}")
        
        while True:
            action = input("Action (c=continue, s=skip, i=inspect, q=quit): ").strip().lower()
            
            if action == 'c':
                break
            elif action == 's':
                step.executed = True
                step.success = True
                step.result = {'skipped': True}
                return
            elif action == 'i':
                self._inspect_execution_state()
            elif action == 'q':
                raise KeyboardInterrupt("User quit at breakpoint")
            else:
                print("Invalid action. Use c, s, i, or q")
    
    def _handle_step_failure(self, step: ExecutionStep):
        """Handle step failure in interactive mode."""
        print(f"\n🔴 STEP FAILURE: {step.name}")
        print(f"Error: {step.error}")
        
        while True:
            action = input("Action (c=continue, r=retry, i=inspect, q=quit): ").strip().lower()
            
            if action == 'c':
                break
            elif action == 'r':
                print("Retrying step...")
                step.executed = False
                step.success = False
                step.error = None
                step_result = step.execute(debug_mode=self.verbose_logging)
                if step.success:
                    print("✅ Retry successful")
                    break
                else:
                    print("❌ Retry failed")
            elif action == 'i':
                self._inspect_execution_state()
            elif action == 'q':
                raise KeyboardInterrupt("User quit after step failure")
            else:
                print("Invalid action. Use c, r, i, or q")
    
    def _interactive_pause(self):
        """Pause for interactive input."""
        if not self.auto_continue:
            action = input("\nPress Enter to continue, 'a' for auto-continue, 'q' to quit: ").strip().lower()
            
            if action == 'a':
                self.auto_continue = True
                print("Auto-continue enabled")
            elif action == 'q':
                raise KeyboardInterrupt("User quit execution")
    
    def _inspect_execution_state(self):
        """Inspect current execution state."""
        print("\n=== EXECUTION STATE ===")
        print(f"Current Step: {self.current_step_index + 1}/{len(self.steps)}")
        print(f"Command: {self.execution_context.get('command', 'N/A')}")
        
        if self.execution_context:
            print("\n--- Context ---")
            for key, value in self.execution_context.items():
                if key != 'tree_dump':  # Skip large objects
                    print(f"  {key}: {value}")
        
        print("\n--- Completed Steps ---")
        for i, step in enumerate(self.steps):
            if step.executed:
                status = "✅" if step.success else "❌"
                print(f"  {i+1}. {status} {step.name}")
        
        print()
    
    def _show_execution_summary(self, results: Dict[str, Any]):
        """Show execution summary."""
        print(f"\n=== EXECUTION SUMMARY ===")
        print(f"Command: {results['command']}")
        print(f"Overall Success: {'✅ YES' if results['overall_success'] else '❌ NO'}")
        print(f"Total Time: {results['total_execution_time_ms']:.1f}ms")
        
        if results['failed_step']:
            print(f"Failed Step: {results['failed_step']}")
        
        print(f"\n--- Step Results ---")
        for i, step_result in enumerate(results['steps'], 1):
            status = "✅" if step_result['success'] else "❌"
            print(f"  {i}. {status} {step_result['name']} ({step_result['execution_time_ms']:.1f}ms)")
            
            if not step_result['success'] and step_result['error']:
                print(f"      Error: {step_result['error']}")
    
    def set_breakpoint(self, step_id: str):
        """Set a breakpoint at a specific step."""
        self.breakpoints.add(step_id)
        print(f"Breakpoint set at step: {step_id}")
    
    def remove_breakpoint(self, step_id: str):
        """Remove a breakpoint."""
        self.breakpoints.discard(step_id)
        print(f"Breakpoint removed from step: {step_id}")
    
    def list_breakpoints(self):
        """List all breakpoints."""
        if self.breakpoints:
            print("Active breakpoints:")
            for bp in self.breakpoints:
                print(f"  - {bp}")
        else:
            print("No active breakpoints")


def main():
    """Main entry point for step-by-step debugging."""
    parser = argparse.ArgumentParser(
        description="AURA Step-by-Step Command Debugging",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('command', nargs='?', help='AURA command to debug')
    parser.add_argument('--interactive', action='store_true', help='Start in interactive mode')
    parser.add_argument('--auto-continue', action='store_true', help='Auto-continue without pauses')
    parser.add_argument('--quiet', action='store_true', help='Reduce verbose output')
    parser.add_argument('--output', help='Save execution results to file')
    
    args = parser.parse_args()
    
    if not args.command and not args.interactive:
        parser.print_help()
        return 1
    
    try:
        # Initialize debugger
        config = {
            'debug_level': 'BASIC' if args.quiet else 'VERBOSE',
            'performance_tracking': True
        }
        
        debugger = StepByStepDebugger(config)
        debugger.auto_continue = args.auto_continue
        debugger.verbose_logging = not args.quiet
        
        if args.interactive:
            # Interactive mode
            print("=== Interactive Step-by-Step Debugging ===")
            print("Commands:")
            print("  debug <command>     - Debug a command step by step")
            print("  breakpoint <step>   - Set breakpoint at step")
            print("  list-breakpoints    - List active breakpoints")
            print("  quit                - Exit")
            
            while True:
                try:
                    user_input = input("\n(step-debug) ").strip()
                    
                    if not user_input:
                        continue
                    elif user_input.lower() == 'quit':
                        break
                    elif user_input.startswith('debug '):
                        command = user_input[6:]
                        results = debugger.execute_command_step_by_step(command)
                        
                        if args.output:
                            with open(args.output, 'w') as f:
                                json.dump(results, f, indent=2, default=str)
                            print(f"Results saved to: {args.output}")
                    
                    elif user_input.startswith('breakpoint '):
                        step_id = user_input[11:]
                        debugger.set_breakpoint(step_id)
                    
                    elif user_input == 'list-breakpoints':
                        debugger.list_breakpoints()
                    
                    else:
                        print("Unknown command. Use 'debug <command>', 'breakpoint <step>', or 'quit'")
                
                except KeyboardInterrupt:
                    print("\nUse 'quit' to exit")
                except Exception as e:
                    print(f"Error: {e}")
        
        else:
            # Single command mode
            results = debugger.execute_command_step_by_step(args.command)
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                print(f"Results saved to: {args.output}")
            
            return 0 if results['overall_success'] else 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\nDebugging cancelled")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())