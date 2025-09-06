"""
GUI Handler for AURA Command Processing

This module handles GUI interaction commands including clicks, typing, scrolling,
and other desktop automation tasks. It implements both fast path (accessibility API)
and vision fallback approaches for maximum reliability.
"""

import time
import re
from typing import Dict, Any, Optional
from .base_handler import BaseHandler


class GUIHandler(BaseHandler):
    """
    Handles GUI interaction commands with fast path and vision fallback.
    
    This handler processes traditional GUI automation commands like:
    - Click operations (click, double-click, right-click)
    - Text input (type, enter text)
    - Navigation (scroll, page up/down)
    - Form interactions (fill forms, submit)
    
    The handler uses a two-tier approach:
    1. Fast path: Uses accessibility API for quick, precise actions
    2. Vision fallback: Uses computer vision when fast path fails
    """
    
    def handle(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process GUI interaction commands using fast path with vision fallback.
        
        This method contains the migrated GUI automation logic from
        Orchestrator._execute_command_internal, organized and enhanced with
        the new handler architecture.
        
        Args:
            command: GUI command to execute (e.g., "click the submit button")
            context: Execution context with intent and system state
            
        Returns:
            Execution result with status, message, and metadata
        """
        # Validate input
        if not self._validate_command(command):
            return self._create_error_result("Invalid or empty command")
        
        # Log execution start
        start_time = self._log_execution_start(command, context)
        
        try:
            # Check system health before GUI interaction
            system_health = self._check_system_health()
            if system_health.get('overall_health') == 'critical':
                return self._create_error_result(
                    "System health is critical. Please try again later.",
                    system_health=system_health
                )
            
            # Attempt fast path execution first
            fast_path_result = self._attempt_fast_path(command, context)
            if fast_path_result.get('success'):
                result = self._create_success_result(
                    fast_path_result.get('message', 'GUI command executed successfully'),
                    method="fast_path",
                    execution_time=fast_path_result.get('execution_time'),
                    element_found=fast_path_result.get('element_found'),
                    action_result=fast_path_result.get('action_result')
                )
                self._log_execution_end(start_time, result, context)
                return result
            
            # Fast path failed, attempt vision fallback
            self.logger.info("Fast path failed, attempting vision fallback")
            vision_result = self._attempt_vision_fallback(command, context)
            
            if vision_result.get('success'):
                result = self._create_success_result(
                    vision_result.get('message', 'GUI command executed via vision fallback'),
                    method="vision_fallback",
                    execution_time=vision_result.get('execution_time'),
                    actions_executed=vision_result.get('actions_executed', 0),
                    total_actions=vision_result.get('total_actions', 0)
                )
                self._log_execution_end(start_time, result, context)
                return result
            
            # Both methods failed
            error_message = "Unable to execute GUI command using either fast path or vision fallback"
            if fast_path_result.get('error'):
                error_message += f". Fast path error: {fast_path_result['error']}"
            if vision_result.get('error'):
                error_message += f". Vision fallback error: {vision_result['error']}"
            
            result = self._create_error_result(
                error_message,
                fast_path_result=fast_path_result,
                vision_result=vision_result
            )
            self._log_execution_end(start_time, result, context)
            return result
            
        except Exception as e:
            return self._handle_module_error("gui_handler", e, "GUI command processing")
    
    def _attempt_fast_path(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt fast path execution using accessibility API.
        
        Args:
            command: GUI command to execute
            context: Execution context
            
        Returns:
            Fast path execution result with success/failure status
        """
        try:
            # Get accessibility module
            accessibility_module = self._get_module_safely('accessibility_module')
            automation_module = self._get_module_safely('automation_module')
            
            if not accessibility_module or not automation_module:
                return {
                    'success': False,
                    'error': 'Required modules (accessibility/automation) not available',
                    'method': 'fast_path'
                }
            
            # Check if fast path is enabled
            if not getattr(self.orchestrator, 'fast_path_enabled', True):
                return {
                    'success': False,
                    'error': 'Fast path execution is disabled',
                    'method': 'fast_path'
                }
            
            # Check accessibility module status
            accessibility_status = accessibility_module.get_accessibility_status()
            if not accessibility_status.get('api_initialized', False):
                return {
                    'success': False,
                    'error': 'Accessibility API not initialized',
                    'method': 'fast_path',
                    'accessibility_status': accessibility_status
                }
            
            start_time = time.time()
            
            # Validate command and extract GUI elements
            command_info = self._validate_and_preprocess_command(command)
            if not command_info.get('is_valid', False):
                return {
                    'success': False,
                    'error': f"Command validation failed: {command_info.get('error', 'Unknown validation error')}",
                    'method': 'fast_path'
                }
            
            # Handle direct typing commands (no GUI element needed)
            if command_info.get('command_type') == 'type':
                return self._execute_direct_typing_command(command, command_info, automation_module)
            
            # Extract GUI elements from command for other types
            gui_elements = self._extract_gui_elements_from_command(command)
            if not gui_elements:
                return {
                    'success': False,
                    'error': 'No GUI elements detected in command',
                    'method': 'fast_path'
                }
            
            # Use enhanced element finding
            enhanced_result = accessibility_module.find_element_enhanced(
                role=gui_elements.get('role', ''),
                label=gui_elements.get('label', ''),
                app_name=gui_elements.get('app_name')
            )
            
            element_result = enhanced_result.element if enhanced_result and enhanced_result.found else None
            
            if not element_result:
                return {
                    'success': False,
                    'error': 'Element not found via accessibility search',
                    'method': 'fast_path',
                    'gui_elements': gui_elements,
                    'enhanced_search_details': enhanced_result.to_dict() if enhanced_result else None
                }
            
            # Execute the action using automation module
            action_type = gui_elements.get('action', 'click')
            coordinates = element_result['center_point']
            
            action_result = automation_module.execute_fast_path_action(
                action_type=action_type,
                coordinates=coordinates,
                element_info=element_result
            )
            
            execution_time = time.time() - start_time
            
            if not action_result.get('success', False):
                return {
                    'success': False,
                    'error': f"Fast path action failed: {action_result.get('error', 'Unknown error')}",
                    'method': 'fast_path',
                    'action_result': action_result,
                    'element_found': element_result
                }
            
            return {
                'success': True,
                'execution_time': execution_time,
                'method': 'fast_path',
                'element_found': element_result,
                'action_result': action_result,
                'message': f"Successfully executed {action_type} on {element_result.get('title', 'element')} using fast path"
            }
            
        except Exception as e:
            self.logger.error(f"Fast path execution failed: {e}")
            return {
                'success': False,
                'error': f"Fast path execution exception: {str(e)}",
                'method': 'fast_path'
            }
    
    def _attempt_vision_fallback(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback to vision-based execution when fast path fails.
        
        Args:
            command: GUI command to execute
            context: Execution context
            
        Returns:
            Vision fallback execution result with success/failure status
        """
        try:
            # Get required modules
            vision_module = self._get_module_safely('vision_module')
            reasoning_module = self._get_module_safely('reasoning_module')
            automation_module = self._get_module_safely('automation_module')
            
            if not vision_module or not reasoning_module or not automation_module:
                return {
                    'success': False,
                    'error': 'Required modules (vision/reasoning/automation) not available for fallback',
                    'method': 'vision_fallback'
                }
            
            start_time = time.time()
            
            # Step 1: Screen perception
            self.logger.info("Performing screen perception for vision fallback")
            screen_context = self._perform_screen_perception(vision_module)
            
            if not screen_context:
                return {
                    'success': False,
                    'error': 'Screen perception failed',
                    'method': 'vision_fallback'
                }
            
            # Step 2: Command reasoning
            self.logger.info("Performing command reasoning for vision fallback")
            action_plan = self._perform_command_reasoning(reasoning_module, command, screen_context)
            
            if not action_plan or not action_plan.get('plan'):
                return {
                    'success': False,
                    'error': 'Command reasoning failed or produced empty action plan',
                    'method': 'vision_fallback',
                    'screen_context': screen_context
                }
            
            # Step 3: Action execution
            self.logger.info(f"Executing {len(action_plan['plan'])} actions via vision fallback")
            execution_results = self._perform_action_execution(automation_module, action_plan['plan'])
            
            execution_time = time.time() - start_time
            
            # Check if execution was successful
            if execution_results['successful_actions'] == 0:
                return {
                    'success': False,
                    'error': 'All actions failed during vision fallback execution',
                    'method': 'vision_fallback',
                    'execution_results': execution_results
                }
            
            # Partial or complete success
            success_rate = execution_results['successful_actions'] / execution_results['total_actions']
            is_complete_success = success_rate == 1.0
            
            return {
                'success': is_complete_success,
                'execution_time': execution_time,
                'method': 'vision_fallback',
                'actions_executed': execution_results['successful_actions'],
                'total_actions': execution_results['total_actions'],
                'success_rate': success_rate,
                'execution_results': execution_results,
                'message': f"Vision fallback executed {execution_results['successful_actions']}/{execution_results['total_actions']} actions successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Vision fallback execution failed: {e}")
            return {
                'success': False,
                'error': f"Vision fallback execution exception: {str(e)}",
                'method': 'vision_fallback'
            }
    
    def _check_system_health(self) -> Dict[str, Any]:
        """
        Check system health before GUI operations.
        
        Returns:
            System health status dictionary
        """
        try:
            if hasattr(self.orchestrator, 'get_system_health'):
                return self.orchestrator.get_system_health()
            else:
                # Fallback health check
                return {
                    'overall_health': 'healthy',
                    'module_health': {
                        'vision': 'healthy' if self._get_module_safely('vision_module') else 'unavailable',
                        'reasoning': 'healthy' if self._get_module_safely('reasoning_module') else 'unavailable',
                        'automation': 'healthy' if self._get_module_safely('automation_module') else 'unavailable',
                        'accessibility': 'healthy' if self._get_module_safely('accessibility_module') else 'unavailable'
                    }
                }
        except Exception as e:
            self.logger.warning(f"System health check failed: {e}")
            return {'overall_health': 'unknown', 'error': str(e)}
    
    def _validate_and_preprocess_command(self, command: str) -> Dict[str, Any]:
        """
        Validate and preprocess a GUI command.
        
        Args:
            command: Raw command string
            
        Returns:
            Validation result with command info
        """
        try:
            # Basic validation
            if not command or not command.strip():
                return {'is_valid': False, 'error': 'Empty command'}
            
            command = command.strip().lower()
            
            # Determine command type
            command_type = 'unknown'
            if any(word in command for word in ['click', 'press', 'tap']):
                command_type = 'click'
            elif any(word in command for word in ['type', 'enter', 'input', 'write']):
                command_type = 'type'
            elif any(word in command for word in ['scroll', 'page']):
                command_type = 'scroll'
            
            return {
                'is_valid': True,
                'command_type': command_type,
                'normalized_command': command,
                'original_command': command
            }
            
        except Exception as e:
            return {'is_valid': False, 'error': f"Command preprocessing failed: {str(e)}"}
    
    def _extract_gui_elements_from_command(self, command: str) -> Optional[Dict[str, Any]]:
        """
        Extract GUI element information from command text.
        
        Args:
            command: Command string to analyze
            
        Returns:
            Dictionary with GUI element info or None if no elements found
        """
        try:
            command_lower = command.lower()
            
            # Determine action type
            action = 'click'  # default
            if any(word in command_lower for word in ['type', 'enter', 'input', 'write']):
                action = 'type'
            elif any(word in command_lower for word in ['scroll']):
                action = 'scroll'
            elif any(word in command_lower for word in ['double', 'double-click']):
                action = 'double_click'
            elif any(word in command_lower for word in ['right-click', 'right click']):
                action = 'right_click'
            
            # Extract target element text
            # Common patterns: "click the button", "click on submit", "press login"
            patterns = [
                r'(?:click|press|tap)(?:\s+on)?\s+(?:the\s+)?(.+)',
                r'(?:type|enter|input|write)(?:\s+in)?\s+(?:the\s+)?(.+)',
                r'scroll\s+(?:in\s+)?(?:the\s+)?(.+)'
            ]
            
            label = None
            for pattern in patterns:
                match = re.search(pattern, command_lower)
                if match:
                    label = match.group(1).strip()
                    break
            
            if not label:
                return None
            
            # Determine likely role based on label and action
            role = self._infer_element_role(label, action)
            
            return {
                'action': action,
                'label': label,
                'role': role,
                'app_name': None  # Will be determined by accessibility module
            }
            
        except Exception as e:
            self.logger.error(f"GUI element extraction failed: {e}")
            return None
    
    def _infer_element_role(self, label: str, action: str) -> str:
        """
        Infer the likely accessibility role of an element based on its label and action.
        
        Args:
            label: Element label/text
            action: Action being performed
            
        Returns:
            Inferred accessibility role
        """
        label_lower = label.lower()
        
        # Button indicators
        if any(word in label_lower for word in ['button', 'btn', 'submit', 'login', 'sign in', 'ok', 'cancel', 'apply']):
            return 'button'
        
        # Link indicators
        if any(word in label_lower for word in ['link', 'href', 'url']):
            return 'link'
        
        # Text field indicators
        if action == 'type' or any(word in label_lower for word in ['field', 'input', 'text', 'search', 'email', 'password']):
            return 'textfield'
        
        # Menu/list indicators
        if any(word in label_lower for word in ['menu', 'dropdown', 'select', 'list']):
            return 'menu'
        
        # Default to button for click actions, textfield for type actions
        if action == 'type':
            return 'textfield'
        else:
            return 'button'
    
    def _execute_direct_typing_command(self, command: str, command_info: Dict[str, Any], automation_module) -> Dict[str, Any]:
        """
        Execute a direct typing command without needing to find GUI elements.
        
        Args:
            command: Original command
            command_info: Preprocessed command information
            automation_module: Automation module instance
            
        Returns:
            Execution result
        """
        try:
            # Extract text to type from command
            text_to_type = self._extract_text_to_type(command)
            if not text_to_type:
                return {
                    'success': False,
                    'error': 'Could not extract text to type from command',
                    'method': 'direct_typing'
                }
            
            # Execute typing action
            action_result = automation_module.execute_fast_path_action(
                action_type='type',
                coordinates=None,  # Not needed for typing
                element_info={'text': text_to_type}
            )
            
            if action_result.get('success', False):
                return {
                    'success': True,
                    'method': 'direct_typing',
                    'text_typed': text_to_type,
                    'action_result': action_result,
                    'message': f"Successfully typed: {text_to_type}"
                }
            else:
                return {
                    'success': False,
                    'error': f"Direct typing failed: {action_result.get('error', 'Unknown error')}",
                    'method': 'direct_typing'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Direct typing exception: {str(e)}",
                'method': 'direct_typing'
            }
    
    def _extract_text_to_type(self, command: str) -> Optional[str]:
        """
        Extract the text to type from a typing command.
        
        Args:
            command: Command string
            
        Returns:
            Text to type or None if not found
        """
        # Patterns to match quoted text
        quoted_patterns = [
            r'type\s+["\'](.+?)["\']',
            r'enter\s+["\'](.+?)["\']',
            r'input\s+["\'](.+?)["\']',
            r'write\s+["\'](.+?)["\']'
        ]
        
        for pattern in quoted_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Fallback: extract text after type/enter/input/write
        unquoted_patterns = [
            r'type\s+(.+)',
            r'enter\s+(.+)',
            r'input\s+(.+)',
            r'write\s+(.+)'
        ]
        
        for pattern in unquoted_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                text = match.group(1).strip()
                # Remove common prefixes
                for prefix in ['the text', 'text', 'the']:
                    if text.startswith(prefix + ' '):
                        text = text[len(prefix) + 1:]
                return text
        
        return None
    
    def _perform_screen_perception(self, vision_module) -> Optional[Dict[str, Any]]:
        """
        Perform screen perception using the vision module.
        
        Args:
            vision_module: Vision module instance
            
        Returns:
            Screen analysis results or None if failed
        """
        try:
            screen_context = vision_module.describe_screen(analysis_type="simple")
            
            if not screen_context or not screen_context.get("description"):
                self.logger.warning("Invalid screen analysis result")
                return None
            
            return screen_context
            
        except Exception as e:
            self.logger.error(f"Screen perception failed: {e}")
            return None
    
    def _perform_command_reasoning(self, reasoning_module, command: str, screen_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Perform command reasoning using the reasoning module.
        
        Args:
            reasoning_module: Reasoning module instance
            command: Command to process
            screen_context: Screen analysis results
            
        Returns:
            Action plan or None if failed
        """
        try:
            action_plan = reasoning_module.get_action_plan(command, screen_context)
            
            if not action_plan or "plan" not in action_plan:
                self.logger.warning("Invalid action plan result")
                return None
            
            if not action_plan["plan"]:
                self.logger.warning("Empty action plan received")
                return None
            
            return action_plan
            
        except Exception as e:
            self.logger.error(f"Command reasoning failed: {e}")
            return None
    
    def _perform_action_execution(self, automation_module, actions: list) -> Dict[str, Any]:
        """
        Execute a list of actions using the automation module.
        
        Args:
            automation_module: Automation module instance
            actions: List of actions to execute
            
        Returns:
            Execution results summary
        """
        execution_results = {
            "total_actions": len(actions),
            "successful_actions": 0,
            "failed_actions": 0,
            "action_details": [],
            "errors": []
        }
        
        for i, action in enumerate(actions):
            action_start_time = time.time()
            action_result = {
                "index": i,
                "action": action.copy(),
                "start_time": action_start_time,
                "status": "pending"
            }
            
            try:
                # Execute the action
                automation_module.execute_action(action)
                action_result["status"] = "success"
                execution_results["successful_actions"] += 1
                
            except Exception as e:
                action_result["status"] = "failed"
                action_result["error"] = str(e)
                execution_results["failed_actions"] += 1
                execution_results["errors"].append(f"Action {i + 1} failed: {str(e)}")
                self.logger.error(f"Action {i + 1} failed: {e}")
            
            action_result["end_time"] = time.time()
            action_result["duration"] = action_result["end_time"] - action_start_time
            execution_results["action_details"].append(action_result)
        
        return execution_results