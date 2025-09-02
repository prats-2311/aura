# universal_command_implementation.py
"""
Universal Command Implementation for AURA
Demonstrates how to extend the current system with scalable, universal commands
"""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CommandIntent(Enum):
    """Universal command intents that work across all contexts"""
    ACTIVATE = "activate"           # Click, select, choose, use, trigger
    NAVIGATE = "navigate"           # Move, scroll, go, browse
    INPUT = "input"                 # Type, enter, provide, supply
    ANALYZE = "analyze"             # Describe, explain, examine
    COMPLETE = "complete"           # Finish, submit, finalize
    MODIFY = "modify"               # Change, update, edit, configure


class ApplicationContext(Enum):
    """Different application contexts that affect command interpretation"""
    WEB_BROWSER = "web_browser"
    TEXT_EDITOR = "text_editor"
    FILE_MANAGER = "file_manager"
    EMAIL_CLIENT = "email_client"
    MEDIA_PLAYER = "media_player"
    FORM_APPLICATION = "form_application"
    GENERAL = "general"


@dataclass
class UniversalCommand:
    """Represents a parsed universal command"""
    intent: CommandIntent
    target: str
    context: Optional[str] = None
    modifiers: List[str] = None
    confidence: float = 0.0
    original_command: str = ""


class UniversalCommandProcessor:
    """
    Processes commands using universal patterns that scale across contexts
    """
    
    def __init__(self):
        self.universal_patterns = self._init_universal_patterns()
        self.context_adapters = self._init_context_adapters()
        self.legacy_patterns = self._init_legacy_patterns()
    
    def _init_universal_patterns(self) -> Dict[CommandIntent, Dict]:
        """Initialize universal command patterns that work across all contexts"""
        return {
            CommandIntent.ACTIVATE: {
                'verbs': [
                    'activate', 'select', 'choose', 'use', 'trigger', 'execute',
                    'click', 'press', 'tap', 'open', 'launch', 'start',
                    'access', 'engage', 'invoke', 'initiate'
                ],
                'patterns': [
                    r'(?:activate|select|choose|use|trigger|execute|click|press|tap|open|launch|start|access|engage|invoke|initiate)\s+(?:on\s+)?(?:the\s+)?(.+)',
                    r'(?:go\s+to|navigate\s+to|visit)\s+(.+)',
                    r'(?:find\s+and\s+)?(?:activate|select|click)\s+(.+)'
                ],
                'scope': 'any_interactive_element'
            },
            
            CommandIntent.NAVIGATE: {
                'verbs': [
                    'navigate', 'move', 'go', 'browse', 'scroll', 'travel',
                    'shift', 'advance', 'proceed', 'traverse', 'explore'
                ],
                'patterns': [
                    r'(?:navigate|move|go|browse|scroll|travel|shift|advance|proceed|traverse)\s+(up|down|left|right|forward|back|next|previous|to\s+.+)',
                    r'(?:page\s+)?(up|down|forward|back|next|previous)',
                    r'(?:show\s+me\s+)?(?:next|previous|more)\s*(.+)?'
                ],
                'scope': 'directional_movement'
            },
            
            CommandIntent.INPUT: {
                'verbs': [
                    'provide', 'enter', 'supply', 'give', 'input', 'type', 'write',
                    'specify', 'define', 'set', 'fill', 'populate', 'insert'
                ],
                'patterns': [
                    r'(?:provide|enter|supply|give|input|type|write|insert)\s+["\']?(.+?)["\']?(?:\s+(?:in|into|to)\s+(.+))?',
                    r'(?:set|specify|define)\s+(.+)\s+(?:to|as)\s+(.+)',
                    r'(?:fill|populate)\s+(.+)\s+with\s+(.+)'
                ],
                'scope': 'data_entry'
            },
            
            CommandIntent.ANALYZE: {
                'verbs': [
                    'analyze', 'examine', 'describe', 'explain', 'review', 'inspect',
                    'tell', 'show', 'display', 'reveal', 'identify', 'find'
                ],
                'patterns': [
                    r'(?:analyze|examine|describe|explain|review|inspect)\s+(.+)',
                    r'(?:what|how|where|when|why|which)\s+(.+)',
                    r'(?:tell\s+me\s+about|show\s+me|display|reveal)\s+(.+)',
                    r'(?:find|identify|locate)\s+(.+)'
                ],
                'scope': 'information_extraction'
            },
            
            CommandIntent.COMPLETE: {
                'verbs': [
                    'complete', 'finish', 'finalize', 'submit', 'process', 'handle',
                    'done', 'save', 'store', 'confirm', 'apply', 'execute'
                ],
                'patterns': [
                    r'(?:complete|finish|finalize|submit|process|handle)\s+(.+)',
                    r'(?:done|finished)\s+(?:with\s+)?(.+)',
                    r'(?:save|store|keep|confirm|apply)\s+(.+)'
                ],
                'scope': 'task_completion'
            },
            
            CommandIntent.MODIFY: {
                'verbs': [
                    'change', 'update', 'modify', 'edit', 'adjust', 'configure',
                    'alter', 'revise', 'correct', 'fix', 'customize', 'adapt'
                ],
                'patterns': [
                    r'(?:change|update|modify|edit|adjust|configure|alter|revise|correct|fix)\s+(.+)',
                    r'(?:customize|adapt|personalize)\s+(.+)',
                    r'(?:make\s+)?(.+)\s+(?:different|better|correct)'
                ],
                'scope': 'content_modification'
            }
        }
    
    def _init_context_adapters(self) -> Dict[ApplicationContext, Dict]:
        """Initialize context-specific adaptations for universal commands"""
        return {
            ApplicationContext.WEB_BROWSER: {
                CommandIntent.ACTIVATE: {
                    'button': 'click_element',
                    'link': 'navigate_to_url',
                    'menu': 'open_menu',
                    'tab': 'switch_tab'
                },
                CommandIntent.NAVIGATE: {
                    'forward': 'browser_forward',
                    'back': 'browser_back',
                    'up': 'scroll_up',
                    'down': 'scroll_down'
                },
                CommandIntent.COMPLETE: {
                    'form': 'submit_form',
                    'this': 'submit_current_form',
                    'task': 'complete_web_task'
                }
            },
            
            ApplicationContext.TEXT_EDITOR: {
                CommandIntent.ACTIVATE: {
                    'menu': 'open_menu',
                    'tool': 'select_tool',
                    'option': 'toggle_option'
                },
                CommandIntent.NAVIGATE: {
                    'up': 'cursor_up',
                    'down': 'cursor_down',
                    'forward': 'next_page',
                    'back': 'previous_page'
                },
                CommandIntent.COMPLETE: {
                    'document': 'save_document',
                    'this': 'save_current_document',
                    'task': 'finalize_editing'
                }
            },
            
            ApplicationContext.FORM_APPLICATION: {
                CommandIntent.ACTIVATE: {
                    'field': 'focus_field',
                    'button': 'click_button',
                    'option': 'select_option'
                },
                CommandIntent.INPUT: {
                    'text': 'fill_text_field',
                    'data': 'populate_field',
                    'information': 'enter_form_data'
                },
                CommandIntent.COMPLETE: {
                    'form': 'submit_form',
                    'this': 'submit_current_form',
                    'application': 'complete_application'
                }
            }
        }
    
    def _init_legacy_patterns(self) -> Dict:
        """Keep existing patterns for backward compatibility"""
        return {
            'click': [
                r'click\s+(?:on\s+)?(?:the\s+)?(.+)',
                r'press\s+(?:the\s+)?(.+)',
                r'tap\s+(?:on\s+)?(?:the\s+)?(.+)'
            ],
            'type': [
                r'type\s+["\'](.+)["\']',
                r'enter\s+["\'](.+)["\']',
                r'input\s+["\'](.+)["\']',
                r'write\s+["\'](.+)["\']'
            ],
            'scroll': [
                r'scroll\s+(up|down|left|right)',
                r'scroll\s+(up|down|left|right)\s+(\d+)',
                r'page\s+(up|down)'
            ]
        }
    
    def parse_command(self, command: str) -> UniversalCommand:
        """
        Parse a command using universal patterns
        
        Args:
            command: Natural language command from user
            
        Returns:
            UniversalCommand object with parsed intent and target
        """
        command = command.strip().lower()
        
        # Try universal patterns first
        universal_result = self._try_universal_patterns(command)
        if universal_result.confidence > 0.7:
            return universal_result
        
        # Fallback to legacy patterns
        legacy_result = self._try_legacy_patterns(command)
        if legacy_result.confidence > 0.5:
            return legacy_result
        
        # Default fallback
        return UniversalCommand(
            intent=CommandIntent.ANALYZE,
            target=command,
            confidence=0.3,
            original_command=command
        )
    
    def _try_universal_patterns(self, command: str) -> UniversalCommand:
        """Try to match command against universal patterns"""
        
        for intent, config in self.universal_patterns.items():
            for pattern in config['patterns']:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    target = match.group(1) if match.groups() else ""
                    context = match.group(2) if len(match.groups()) > 1 else None
                    
                    return UniversalCommand(
                        intent=intent,
                        target=target.strip(),
                        context=context.strip() if context else None,
                        confidence=0.9,
                        original_command=command
                    )
        
        return UniversalCommand(
            intent=CommandIntent.ANALYZE,
            target=command,
            confidence=0.0,
            original_command=command
        )
    
    def _try_legacy_patterns(self, command: str) -> UniversalCommand:
        """Try to match command against legacy patterns for backward compatibility"""
        
        # Map legacy patterns to universal intents
        legacy_to_universal = {
            'click': CommandIntent.ACTIVATE,
            'type': CommandIntent.INPUT,
            'scroll': CommandIntent.NAVIGATE
        }
        
        for legacy_type, patterns in self.legacy_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    target = match.group(1) if match.groups() else ""
                    
                    return UniversalCommand(
                        intent=legacy_to_universal.get(legacy_type, CommandIntent.ACTIVATE),
                        target=target.strip(),
                        confidence=0.8,
                        original_command=command
                    )
        
        return UniversalCommand(
            intent=CommandIntent.ANALYZE,
            target=command,
            confidence=0.0,
            original_command=command
        )
    
    def detect_application_context(self, screen_context: Dict) -> ApplicationContext:
        """
        Detect the current application context from screen analysis
        
        Args:
            screen_context: Screen analysis from vision module
            
        Returns:
            ApplicationContext enum value
        """
        description = screen_context.get('description', '').lower()
        elements = screen_context.get('elements', [])
        
        # Check for web browser indicators
        if any(keyword in description for keyword in ['browser', 'website', 'url', 'web page']):
            return ApplicationContext.WEB_BROWSER
        
        # Check for form indicators
        form_indicators = ['form', 'input field', 'text field', 'submit button', 'checkbox']
        if any(indicator in description for indicator in form_indicators):
            return ApplicationContext.FORM_APPLICATION
        
        # Check for text editor indicators
        if any(keyword in description for keyword in ['editor', 'document', 'text', 'writing']):
            return ApplicationContext.TEXT_EDITOR
        
        # Check for file manager indicators
        if any(keyword in description for keyword in ['folder', 'file', 'directory', 'explorer']):
            return ApplicationContext.FILE_MANAGER
        
        # Check for email indicators
        if any(keyword in description for keyword in ['email', 'inbox', 'message', 'compose']):
            return ApplicationContext.EMAIL_CLIENT
        
        # Check for media player indicators
        if any(keyword in description for keyword in ['play', 'pause', 'video', 'audio', 'media']):
            return ApplicationContext.MEDIA_PLAYER
        
        return ApplicationContext.GENERAL
    
    def generate_context_aware_action_plan(self, 
                                         universal_command: UniversalCommand, 
                                         screen_context: Dict) -> Dict[str, Any]:
        """
        Generate an action plan based on universal command and application context
        
        Args:
            universal_command: Parsed universal command
            screen_context: Current screen analysis
            
        Returns:
            Action plan dictionary
        """
        app_context = self.detect_application_context(screen_context)
        
        # Get context-specific adapter
        context_adapter = self.context_adapters.get(app_context, {})
        intent_adapter = context_adapter.get(universal_command.intent, {})
        
        # Generate base action plan
        base_plan = self._generate_base_action_plan(universal_command, screen_context)
        
        # Apply context-specific adaptations
        if intent_adapter:
            adapted_plan = self._apply_context_adaptations(base_plan, intent_adapter, universal_command)
            return adapted_plan
        
        return base_plan
    
    def _generate_base_action_plan(self, command: UniversalCommand, screen_context: Dict) -> Dict[str, Any]:
        """Generate base action plan for universal command"""
        
        if command.intent == CommandIntent.ACTIVATE:
            return self._generate_activation_plan(command, screen_context)
        elif command.intent == CommandIntent.NAVIGATE:
            return self._generate_navigation_plan(command, screen_context)
        elif command.intent == CommandIntent.INPUT:
            return self._generate_input_plan(command, screen_context)
        elif command.intent == CommandIntent.ANALYZE:
            return self._generate_analysis_plan(command, screen_context)
        elif command.intent == CommandIntent.COMPLETE:
            return self._generate_completion_plan(command, screen_context)
        elif command.intent == CommandIntent.MODIFY:
            return self._generate_modification_plan(command, screen_context)
        
        return {"plan": [], "metadata": {"confidence": 0.0}}
    
    def _generate_activation_plan(self, command: UniversalCommand, screen_context: Dict) -> Dict[str, Any]:
        """Generate plan for activation commands (click, select, etc.)"""
        
        # Find matching elements on screen
        target_elements = self._find_target_elements(command.target, screen_context)
        
        if target_elements:
            # Use the best matching element
            best_element = target_elements[0]
            coordinates = best_element.get('coordinates', [0, 0])
            
            return {
                "plan": [
                    {
                        "action": "click",
                        "coordinates": coordinates,
                        "target_description": command.target,
                        "element_info": best_element
                    }
                ],
                "metadata": {
                    "confidence": command.confidence,
                    "intent": command.intent.value,
                    "target_found": True
                }
            }
        else:
            return {
                "plan": [
                    {
                        "action": "speak",
                        "message": f"I couldn't find '{command.target}' on the screen. Could you be more specific?"
                    }
                ],
                "metadata": {
                    "confidence": 0.3,
                    "intent": command.intent.value,
                    "target_found": False
                }
            }
    
    def _generate_navigation_plan(self, command: UniversalCommand, screen_context: Dict) -> Dict[str, Any]:
        """Generate plan for navigation commands (scroll, move, etc.)"""
        
        direction = command.target.lower()
        
        # Map universal directions to specific actions
        direction_map = {
            'up': {'direction': 'up', 'amount': 100},
            'down': {'direction': 'down', 'amount': 100},
            'left': {'direction': 'left', 'amount': 100},
            'right': {'direction': 'right', 'amount': 100},
            'forward': {'direction': 'down', 'amount': 300},  # Page-like forward
            'back': {'direction': 'up', 'amount': 300},       # Page-like back
            'next': {'direction': 'down', 'amount': 200},
            'previous': {'direction': 'up', 'amount': 200}
        }
        
        scroll_params = direction_map.get(direction, {'direction': 'down', 'amount': 100})
        
        return {
            "plan": [
                {
                    "action": "scroll",
                    "direction": scroll_params['direction'],
                    "amount": scroll_params['amount']
                }
            ],
            "metadata": {
                "confidence": command.confidence,
                "intent": command.intent.value,
                "navigation_type": direction
            }
        }
    
    def _generate_input_plan(self, command: UniversalCommand, screen_context: Dict) -> Dict[str, Any]:
        """Generate plan for input commands (type, enter, etc.)"""
        
        # Extract text to input (remove quotes if present)
        text_to_input = command.target.strip('\'"')
        
        # Find input fields if context is specified
        if command.context:
            target_field = self._find_input_field(command.context, screen_context)
            if target_field:
                coordinates = target_field.get('coordinates', [0, 0])
                return {
                    "plan": [
                        {
                            "action": "click",
                            "coordinates": coordinates
                        },
                        {
                            "action": "type",
                            "text": text_to_input
                        }
                    ],
                    "metadata": {
                        "confidence": command.confidence,
                        "intent": command.intent.value,
                        "field_found": True
                    }
                }
        
        # Default: just type the text
        return {
            "plan": [
                {
                    "action": "type",
                    "text": text_to_input
                }
            ],
            "metadata": {
                "confidence": command.confidence * 0.8,  # Lower confidence without field targeting
                "intent": command.intent.value,
                "field_found": False
            }
        }
    
    def _generate_analysis_plan(self, command: UniversalCommand, screen_context: Dict) -> Dict[str, Any]:
        """Generate plan for analysis commands (describe, explain, etc.)"""
        
        # Analyze what the user is asking about
        target = command.target.lower()
        
        if 'screen' in target or 'this' in target:
            # General screen description
            description = screen_context.get('description', 'I can see the current screen.')
            elements = screen_context.get('elements', [])
            
            if elements:
                element_summary = f"I can see {len(elements)} interactive elements including: "
                element_types = [elem.get('type', 'element') for elem in elements[:3]]
                element_summary += ', '.join(element_types)
                if len(elements) > 3:
                    element_summary += f" and {len(elements) - 3} more."
            else:
                element_summary = "I don't see any clearly identifiable interactive elements."
            
            response = f"{description} {element_summary}"
        else:
            # Specific element analysis
            target_elements = self._find_target_elements(target, screen_context)
            if target_elements:
                element = target_elements[0]
                response = f"I found {target}: {element.get('description', 'an interactive element')} at coordinates {element.get('coordinates', 'unknown location')}."
            else:
                response = f"I couldn't find '{target}' on the current screen. Could you be more specific about what you're looking for?"
        
        return {
            "plan": [
                {
                    "action": "speak",
                    "message": response
                }
            ],
            "metadata": {
                "confidence": command.confidence,
                "intent": command.intent.value,
                "analysis_type": "screen_analysis"
            }
        }
    
    def _generate_completion_plan(self, command: UniversalCommand, screen_context: Dict) -> Dict[str, Any]:
        """Generate plan for completion commands (finish, submit, etc.)"""
        
        target = command.target.lower()
        
        # Look for submit buttons or completion elements
        completion_elements = []
        for element in screen_context.get('elements', []):
            element_text = element.get('text', '').lower()
            if any(keyword in element_text for keyword in ['submit', 'send', 'finish', 'complete', 'done', 'save']):
                completion_elements.append(element)
        
        if completion_elements:
            # Use the most relevant completion element
            best_element = completion_elements[0]
            coordinates = best_element.get('coordinates', [0, 0])
            
            return {
                "plan": [
                    {
                        "action": "click",
                        "coordinates": coordinates,
                        "target_description": f"completion button: {best_element.get('text', 'submit')}"
                    }
                ],
                "metadata": {
                    "confidence": command.confidence,
                    "intent": command.intent.value,
                    "completion_method": "button_click"
                }
            }
        else:
            return {
                "plan": [
                    {
                        "action": "speak",
                        "message": f"I don't see a clear way to complete '{target}' on this screen. Could you point me to the submit or finish button?"
                    }
                ],
                "metadata": {
                    "confidence": 0.4,
                    "intent": command.intent.value,
                    "completion_method": "not_found"
                }
            }
    
    def _generate_modification_plan(self, command: UniversalCommand, screen_context: Dict) -> Dict[str, Any]:
        """Generate plan for modification commands (change, update, etc.)"""
        
        return {
            "plan": [
                {
                    "action": "speak",
                    "message": f"I understand you want to modify '{command.target}'. This feature is still being developed. Could you be more specific about what changes you'd like to make?"
                }
            ],
            "metadata": {
                "confidence": 0.5,
                "intent": command.intent.value,
                "modification_type": "general"
            }
        }
    
    def _find_target_elements(self, target: str, screen_context: Dict) -> List[Dict]:
        """Find elements on screen that match the target description"""
        
        elements = screen_context.get('elements', [])
        matching_elements = []
        
        target_lower = target.lower()
        
        for element in elements:
            element_text = element.get('text', '').lower()
            element_type = element.get('type', '').lower()
            element_desc = element.get('description', '').lower()
            
            # Check for exact matches first
            if target_lower in element_text or target_lower in element_desc:
                matching_elements.append({**element, 'match_score': 1.0})
            # Check for partial matches
            elif any(word in element_text or word in element_desc for word in target_lower.split()):
                matching_elements.append({**element, 'match_score': 0.7})
            # Check for type matches
            elif target_lower in element_type:
                matching_elements.append({**element, 'match_score': 0.5})
        
        # Sort by match score
        matching_elements.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        return matching_elements
    
    def _find_input_field(self, field_description: str, screen_context: Dict) -> Optional[Dict]:
        """Find input field that matches the description"""
        
        elements = screen_context.get('elements', [])
        field_desc_lower = field_description.lower()
        
        for element in elements:
            element_type = element.get('type', '').lower()
            element_text = element.get('text', '').lower()
            
            # Look for input field types
            if 'input' in element_type or 'field' in element_type or 'text' in element_type:
                if field_desc_lower in element_text or any(word in element_text for word in field_desc_lower.split()):
                    return element
        
        return None
    
    def _apply_context_adaptations(self, base_plan: Dict, adapter: Dict, command: UniversalCommand) -> Dict:
        """Apply context-specific adaptations to the base plan"""
        
        # This is where you would implement context-specific logic
        # For now, return the base plan with context metadata
        
        adapted_plan = base_plan.copy()
        adapted_plan['metadata']['context_adapter'] = adapter
        adapted_plan['metadata']['application_context'] = True
        
        return adapted_plan


# Example usage and integration with existing AURA system
class EnhancedOrchestrator:
    """
    Enhanced orchestrator that uses universal command processing
    while maintaining backward compatibility
    """
    
    def __init__(self):
        # Initialize existing modules
        self.vision_module = None  # VisionModule()
        self.reasoning_module = None  # ReasoningModule()
        self.automation_module = None  # AutomationModule()
        
        # Add universal command processor
        self.universal_processor = UniversalCommandProcessor()
        
        # Keep legacy patterns for backward compatibility
        self.legacy_mode = True
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Enhanced command execution with universal command support
        """
        
        # Parse command using universal processor
        universal_command = self.universal_processor.parse_command(command)
        
        # Get screen context
        screen_context = self.vision_module.describe_screen() if self.vision_module else {}
        
        # Try universal processing first if confidence is high
        if universal_command.confidence > 0.7:
            action_plan = self.universal_processor.generate_context_aware_action_plan(
                universal_command, screen_context
            )
            
            # Execute the action plan
            return self._execute_action_plan(action_plan)
        
        # Fallback to legacy processing
        elif self.legacy_mode and self.reasoning_module:
            action_plan = self.reasoning_module.get_action_plan(command, screen_context)
            return self._execute_action_plan(action_plan)
        
        # Final fallback
        else:
            return {
                "status": "failed",
                "error": "Could not understand command",
                "suggestion": "Try rephrasing your command or being more specific"
            }
    
    def _execute_action_plan(self, action_plan: Dict) -> Dict[str, Any]:
        """Execute the generated action plan"""
        
        if not action_plan or "plan" not in action_plan:
            return {"status": "failed", "error": "Invalid action plan"}
        
        results = []
        for action in action_plan["plan"]:
            try:
                if self.automation_module:
                    self.automation_module.execute_action(action)
                results.append({"action": action, "status": "success"})
            except Exception as e:
                results.append({"action": action, "status": "failed", "error": str(e)})
        
        return {
            "status": "completed",
            "results": results,
            "metadata": action_plan.get("metadata", {})
        }


# Example of how to integrate this into the existing config.py
UNIVERSAL_COMMAND_CONFIG = {
    "enable_universal_commands": True,
    "fallback_to_legacy": True,
    "confidence_threshold": 0.7,
    "context_detection": True,
    "learning_mode": False  # For future ML enhancements
}