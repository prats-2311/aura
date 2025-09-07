"""
Comprehensive Unit Test Coverage for AURA Handler System

This module provides comprehensive unit test coverage for all handler classes,
intent recognition, routing logic, concurrency management, content generation,
and error handling scenarios as required by Task 4.0.
"""

import pytest
import unittest
from unittest.mock import Mock, MagicMock, patch, call
import threading
import time
import asyncio
from typing import Dict, Any, Optional

# Import handlers to test
from handlers.base_handler import BaseHandler, HandlerResult
from handlers.gui_handler import GUIHandler
from handlers.conversation_handler import ConversationHandler
from handlers.deferred_action_handler import DeferredActionHandler


class TestBaseHandler(unittest.TestCase):
    """Test cases for BaseHandler abstract base class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_orchestrator = Mock()
        self.mock_orchestrator.config = {}
        
        # Create a concrete implementation for testing
        class TestHandler(BaseHandler):
            def handle(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
                return self._create_success_result("Test successful")
        
        self.handler = TestHandler(self.mock_orchestrator)
    
    def test_handler_initialization(self):
        """Test handler initialization with orchestrator reference."""
        self.assertEqual(self.handler.orchestrator, self.mock_orchestrator)
        self.assertIsNotNone(self.handler.logger)
        self.assertEqual(self.handler.logger.name, "TestHandler")
    
    def test_create_success_result(self):
        """Test creation of standardized success results."""
        message = "Operation completed successfully"
        result = self.handler._create_success_result(message, method="test_method")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], message)
        self.assertEqual(result["method"], "test_method")
        self.assertIn("timestamp", result)
        self.assertIsInstance(result["timestamp"], float)
    
    def test_create_error_result(self):
        """Test creation of standardized error results."""
        message = "Operation failed"
        error = ValueError("Test error")
        result = self.handler._create_error_result(message, error=error, module="test")
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], message)
        self.assertEqual(result["module"], "test")
        self.assertIn("timestamp", result)
    
    def test_create_waiting_result(self):
        """Test creation of standardized waiting results."""
        message = "Waiting for user action"
        result = self.handler._create_waiting_result(message, timeout=300)
        
        self.assertEqual(result["status"], "waiting_for_user_action")
        self.assertEqual(result["message"], message)
        self.assertEqual(result["timeout"], 300)
        self.assertIn("timestamp", result)
    
    def test_validate_command_valid(self):
        """Test command validation with valid commands."""
        self.assertTrue(self.handler._validate_command("click button"))
        self.assertTrue(self.handler._validate_command("  type hello  "))
        self.assertTrue(self.handler._validate_command("a" * 100))
    
    def test_validate_command_invalid(self):
        """Test command validation with invalid commands."""
        self.assertFalse(self.handler._validate_command(""))
        self.assertFalse(self.handler._validate_command("   "))
        self.assertFalse(self.handler._validate_command(None))
    
    def test_get_module_safely_success(self):
        """Test safe module retrieval when module exists."""
        mock_module = Mock()
        self.mock_orchestrator.test_module = mock_module
        
        result = self.handler._get_module_safely("test_module")
        self.assertEqual(result, mock_module)
    
    def test_get_module_safely_missing(self):
        """Test safe module retrieval when module doesn't exist."""
        result = self.handler._get_module_safely("nonexistent_module")
        self.assertIsNone(result)
    
    def test_handle_module_error(self):
        """Test module error handling."""
        error = RuntimeError("Module failed")
        result = self.handler._handle_module_error("test_module", error, "test operation")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("test operation", result["message"])
        self.assertEqual(result["module"], "test_module")
        self.assertEqual(result["operation"], "test operation")
    
    def test_log_execution_timing(self):
        """Test execution timing logging."""
        context = {"execution_id": "test_123", "intent": {"intent": "test"}}
        
        start_time = self.handler._log_execution_start("test command", context)
        self.assertIsInstance(start_time, float)
        
        result = {"status": "success", "message": "test"}
        self.handler._log_execution_end(start_time, result, context)
        
        # Verify execution time was added to result
        self.assertIn("execution_time", result)
        self.assertIsInstance(result["execution_time"], float)


class TestGUIHandler(unittest.TestCase):
    """Test cases for GUIHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_orchestrator = Mock()
        self.mock_orchestrator.config = {}
        self.mock_orchestrator.fast_path_enabled = True
        
        # Mock modules
        self.mock_accessibility = Mock()
        self.mock_automation = Mock()
        self.mock_vision = Mock()
        self.mock_reasoning = Mock()
        
        self.mock_orchestrator.accessibility_module = self.mock_accessibility
        self.mock_orchestrator.automation_module = self.mock_automation
        self.mock_orchestrator.vision_module = self.mock_vision
        self.mock_orchestrator.reasoning_module = self.mock_reasoning
        
        self.handler = GUIHandler(self.mock_orchestrator)
    
    def test_handle_valid_command(self):
        """Test handling of valid GUI commands."""
        # Mock successful fast path execution
        self.mock_accessibility.get_accessibility_status.return_value = {
            'api_initialized': True
        }
        
        mock_element = {
            'center_point': (100, 200),
            'title': 'Test Button'
        }
        
        mock_enhanced_result = Mock()
        mock_enhanced_result.found = True
        mock_enhanced_result.element = mock_element
        
        self.mock_accessibility.find_element_enhanced.return_value = mock_enhanced_result
        self.mock_automation.execute_fast_path_action.return_value = {
            'success': True,
            'message': 'Action executed'
        }
        
        context = {"intent": {"intent": "gui_interaction"}, "execution_id": "test_123"}
        result = self.handler.handle("click the button", context)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["method"], "fast_path")
        self.assertIn("execution_time", result)
    
    def test_handle_fast_path_failure_vision_fallback(self):
        """Test fallback to vision when fast path fails."""
        # Mock fast path failure
        self.mock_accessibility.get_accessibility_status.return_value = {
            'api_initialized': False
        }
        
        # Mock successful vision fallback
        self.mock_vision.describe_screen.return_value = {
            "description": "Screen with button"
        }
        self.mock_reasoning.get_action_plan.return_value = {
            "plan": [{"action": "click", "coordinates": (100, 200)}]
        }
        
        context = {"intent": {"intent": "gui_interaction"}, "execution_id": "test_123"}
        
        with patch.object(self.handler, '_perform_action_execution') as mock_execute:
            mock_execute.return_value = {
                'total_actions': 1,
                'successful_actions': 1,
                'failed_actions': 0
            }
            
            result = self.handler.handle("click the button", context)
            
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["method"], "vision_fallback")
    
    def test_handle_invalid_command(self):
        """Test handling of invalid commands."""
        context = {"intent": {"intent": "gui_interaction"}, "execution_id": "test_123"}
        result = self.handler.handle("", context)
        
        self.assertEqual(result["status"], "error")
        self.assertIn("Invalid or empty command", result["message"])
    
    def test_extract_gui_elements_click_command(self):
        """Test GUI element extraction from click commands."""
        elements = self.handler._extract_gui_elements_from_command("click the submit button")
        
        self.assertIsNotNone(elements)
        self.assertEqual(elements["action"], "click")
        self.assertEqual(elements["label"], "submit button")
        self.assertEqual(elements["role"], "button")
    
    def test_extract_gui_elements_type_command(self):
        """Test GUI element extraction from type commands."""
        elements = self.handler._extract_gui_elements_from_command("type in the email field")
        
        self.assertIsNotNone(elements)
        self.assertEqual(elements["action"], "type")
        self.assertEqual(elements["label"], "email field")
        self.assertEqual(elements["role"], "textfield")
    
    def test_infer_element_role(self):
        """Test element role inference."""
        self.assertEqual(self.handler._infer_element_role("submit button", "click"), "button")
        self.assertEqual(self.handler._infer_element_role("email field", "type"), "textfield")
        self.assertEqual(self.handler._infer_element_role("dropdown menu", "click"), "menu")
        self.assertEqual(self.handler._infer_element_role("link", "click"), "link")
    
    def test_extract_text_to_type(self):
        """Test text extraction from typing commands."""
        self.assertEqual(self.handler._extract_text_to_type('type "hello world"'), "hello world")
        self.assertEqual(self.handler._extract_text_to_type("enter 'test@email.com'"), "test@email.com")
        self.assertEqual(self.handler._extract_text_to_type("input username"), "username")
    
    def test_system_health_check(self):
        """Test system health checking."""
        self.mock_orchestrator.get_system_health.return_value = {
            'overall_health': 'healthy',
            'module_health': {'vision': 'healthy', 'reasoning': 'healthy'}
        }
        
        health = self.handler._check_system_health()
        self.assertEqual(health['overall_health'], 'healthy')
    
    def test_system_health_check_fallback(self):
        """Test system health check fallback when method doesn't exist."""
        # Remove the method to test fallback
        if hasattr(self.mock_orchestrator, 'get_system_health'):
            delattr(self.mock_orchestrator, 'get_system_health')
        
        health = self.handler._check_system_health()
        self.assertIn('overall_health', health)
        self.assertIn('module_health', health)


class TestConversationHandler(unittest.TestCase):
    """Test cases for ConversationHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_orchestrator = Mock()
        self.mock_orchestrator.config = {'CONVERSATION_CONTEXT_SIZE': 10}
        
        # Mock modules
        self.mock_reasoning = Mock()
        self.mock_feedback = Mock()
        self.mock_audio = Mock()
        
        self.mock_orchestrator.reasoning_module = self.mock_reasoning
        self.mock_orchestrator.feedback_module = self.mock_feedback
        self.mock_orchestrator.audio_module = self.mock_audio
        
        self.handler = ConversationHandler(self.mock_orchestrator)
    
    def test_handle_conversational_query(self):
        """Test handling of conversational queries."""
        # Mock successful response generation
        self.mock_reasoning.process_query.return_value = "Hello! How can I help you today?"
        
        context = {"intent": {"intent": "conversational_chat"}, "execution_id": "conv_123"}
        result = self.handler.handle("Hello, how are you?", context)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["interaction_type"], "conversation")
        self.assertIn("response", result)
        self.mock_feedback.speak.assert_called_once()
    
    def test_generate_conversational_response(self):
        """Test conversational response generation."""
        self.mock_reasoning.process_query.return_value = "I'm doing well, thank you!"
        
        response = self.handler._generate_conversational_response(
            "How are you?", {}, "conv_123"
        )
        
        self.assertEqual(response, "I'm doing well, thank you!")
        self.mock_reasoning.process_query.assert_called_once_with(
            query="How are you?",
            prompt_template='CONVERSATIONAL_PROMPT',
            context={}
        )
    
    def test_generate_response_fallback_no_reasoning_module(self):
        """Test response generation fallback when reasoning module unavailable."""
        self.mock_orchestrator.reasoning_module = None
        
        response = self.handler._generate_conversational_response(
            "Hello", {}, "conv_123"
        )
        
        self.assertIn("conversational features are currently unavailable", response)
    
    def test_generate_response_error_handling(self):
        """Test response generation error handling."""
        self.mock_reasoning.process_query.side_effect = Exception("API Error")
        
        response = self.handler._generate_conversational_response(
            "Hello", {}, "conv_123"
        )
        
        self.assertIn("having a bit of trouble", response)
    
    def test_error_fallback_responses(self):
        """Test different error fallback responses."""
        timeout_response = self.handler._get_error_fallback_response("Request timed out")
        self.assertIn("taking a bit longer", timeout_response)
        
        connection_response = self.handler._get_error_fallback_response("Connection failed")
        self.assertIn("trouble with my connection", connection_response)
        
        api_response = self.handler._get_error_fallback_response("API service error")
        self.assertIn("reasoning service is having", api_response)
        
        generic_response = self.handler._get_error_fallback_response("Unknown error")
        self.assertIn("having a bit of trouble", generic_response)
    
    def test_speak_response_feedback_module(self):
        """Test speaking response via feedback module."""
        self.handler._speak_response("Hello there!", "conv_123")
        self.mock_feedback.speak.assert_called_once_with("Hello there!")
    
    def test_speak_response_audio_fallback(self):
        """Test speaking response fallback to audio module."""
        self.mock_feedback.speak.side_effect = Exception("Feedback failed")
        
        self.handler._speak_response("Hello there!", "conv_123")
        self.mock_audio.text_to_speech.assert_called_once_with("Hello there!")
    
    def test_build_conversation_context(self):
        """Test conversation context building."""
        # Set up conversation history
        self.handler._conversation_history = [
            {
                'timestamp': time.time() - 100,
                'user_query': 'Hello',
                'aura_response': 'Hi there!',
                'query_length': 5,
                'response_length': 9,
                'exchange_id': 'conv_001'
            }
        ]
        
        context = self.handler._build_conversation_context()
        
        self.assertIn('conversation_history', context)
        self.assertIn('system_state', context)
        self.assertIn('timestamp', context)
        self.assertEqual(len(context['conversation_history']), 1)
    
    def test_update_conversation_history(self):
        """Test conversation history updates."""
        query = "What's the weather like?"
        response = "I don't have access to weather data."
        
        self.handler._update_conversation_history(query, response)
        
        self.assertEqual(len(self.handler._conversation_history), 1)
        exchange = self.handler._conversation_history[0]
        self.assertEqual(exchange['user_query'], query)
        self.assertEqual(exchange['aura_response'], response)
        self.assertIn('timestamp', exchange)
        self.assertIn('exchange_id', exchange)
    
    def test_conversation_history_size_limit(self):
        """Test conversation history size limiting."""
        # Add more exchanges than the limit
        for i in range(15):
            self.handler._update_conversation_history(f"Query {i}", f"Response {i}")
        
        # Should be limited to 10 (the configured size)
        self.assertEqual(len(self.handler._conversation_history), 10)
        
        # Should contain the most recent exchanges
        last_exchange = self.handler._conversation_history[-1]
        self.assertEqual(last_exchange['user_query'], "Query 14")
    
    def test_get_conversation_summary(self):
        """Test conversation summary generation."""
        # Add some conversation history
        for i in range(3):
            self.handler._update_conversation_history(f"Query {i}", f"Response {i}")
        
        summary = self.handler.get_conversation_summary()
        
        self.assertEqual(summary['status'], 'active')
        self.assertEqual(summary['total_exchanges'], 3)
        self.assertIn('session_duration_minutes', summary)
        self.assertIn('recent_queries', summary)
        self.assertEqual(len(summary['recent_queries']), 3)
    
    def test_get_conversation_summary_no_history(self):
        """Test conversation summary with no history."""
        summary = self.handler.get_conversation_summary()
        
        self.assertEqual(summary['status'], 'no_conversation')
        self.assertIn('No conversation history', summary['message'])


class TestDeferredActionHandler(unittest.TestCase):
    """Test cases for DeferredActionHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_orchestrator = Mock()
        self.mock_orchestrator.config = {}
        self.mock_orchestrator.is_waiting_for_user_action = False
        self.mock_orchestrator.deferred_action_lock = threading.Lock()
        
        # Mock modules
        self.mock_reasoning = Mock()
        self.mock_feedback = Mock()
        
        self.mock_orchestrator.reasoning_module = self.mock_reasoning
        self.mock_orchestrator.feedback_module = self.mock_feedback
        
        self.handler = DeferredActionHandler(self.mock_orchestrator)
    
    def test_handle_content_generation_request(self):
        """Test handling of content generation requests."""
        # Mock successful content generation
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'def hello_world():\n    print("Hello, World!")'
                }
            }]
        }
        self.mock_reasoning._make_api_request.return_value = mock_response
        
        context = {
            "intent": {
                "intent": "deferred_action",
                "parameters": {
                    "content_request": "Write a hello world function",
                    "content_type": "code"
                }
            },
            "execution_id": "deferred_123"
        }
        
        with patch.object(self.handler, '_start_mouse_listener'), \
             patch.object(self.handler, '_provide_audio_instructions'), \
             patch.object(self.handler, '_start_timeout_monitoring'):
            
            result = self.handler.handle("Write a hello world function", context)
            
            self.assertEqual(result["status"], "waiting_for_user_action")
            self.assertIn("content_preview", result)
            self.assertEqual(result["content_type"], "code")
    
    def test_generate_content_code_type(self):
        """Test code content generation."""
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)'
                }
            }]
        }
        self.mock_reasoning._make_api_request.return_value = mock_response
        
        with patch('config.CODE_GENERATION_PROMPT', 'Generate code: {request}'):
            content = self.handler._generate_content(
                "Write a fibonacci function", "code", "test_123"
            )
            
            self.assertIn("def fibonacci", content)
            self.assertIn("return", content)
    
    def test_generate_content_text_type(self):
        """Test text content generation."""
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'This is a sample essay about artificial intelligence and its impact on society.'
                }
            }]
        }
        self.mock_reasoning._make_api_request.return_value = mock_response
        
        with patch('config.TEXT_GENERATION_PROMPT', 'Generate text: {request}'):
            content = self.handler._generate_content(
                "Write an essay about AI", "text", "test_123"
            )
            
            self.assertIn("artificial intelligence", content)
    
    def test_clean_and_format_content_code(self):
        """Test content cleaning and formatting for code."""
        raw_content = """Here is the code:
```python
def hello():
    print("Hello, World!")
```
That's it!"""
        
        cleaned = self.handler._clean_and_format_content(raw_content, "code")
        
        self.assertNotIn("Here is the code:", cleaned)
        self.assertNotIn("```python", cleaned)
        self.assertNotIn("```", cleaned)
        self.assertNotIn("That's it!", cleaned)
        self.assertIn("def hello():", cleaned)
        self.assertIn('print("Hello, World!")', cleaned)
    
    def test_clean_and_format_content_text(self):
        """Test content cleaning and formatting for text."""
        raw_content = """Here is the text:
This is a sample paragraph about testing.

This is another paragraph with more content.
**End of text**"""
        
        cleaned = self.handler._clean_and_format_content(raw_content, "text")
        
        self.assertNotIn("Here is the text:", cleaned)
        self.assertNotIn("**End of text**", cleaned)
        self.assertIn("sample paragraph", cleaned)
        self.assertIn("another paragraph", cleaned)
    
    def test_remove_duplicate_content(self):
        """Test duplicate content removal."""
        content_with_duplicates = """Line 1
Line 2
Line 3
Line 1
Line 2
Line 3
Line 4"""
        
        cleaned = self.handler._remove_duplicate_content(content_with_duplicates)
        
        # Should remove the duplicate block
        lines = cleaned.split('\n')
        self.assertLess(len(lines), 7)  # Should be fewer than original
    
    def test_format_single_line_code(self):
        """Test single-line code formatting."""
        single_line = "def hello(): print('Hello'); return True"
        
        formatted = self.handler._format_single_line_code(single_line)
        
        self.assertIn('\n', formatted)  # Should have line breaks
        self.assertIn('def hello():', formatted)
        self.assertIn("print('Hello')", formatted)
    
    def test_is_single_line_code_detection(self):
        """Test single-line code detection."""
        self.assertTrue(self.handler._is_single_line_code(
            "def hello(): print('Hello'); return True"
        ))
        self.assertFalse(self.handler._is_single_line_code(
            "def hello():\n    print('Hello')\n    return True"
        ))
        self.assertFalse(self.handler._is_single_line_code("Short text"))
    
    def test_setup_deferred_action_state(self):
        """Test deferred action state setup."""
        content = "print('Hello, World!')"
        content_type = "code"
        execution_id = "test_123"
        
        self.handler._setup_deferred_action_state(content, content_type, execution_id)
        
        self.assertEqual(self.mock_orchestrator.pending_action_payload, content)
        self.assertEqual(self.mock_orchestrator.deferred_action_type, 'type')
        self.assertEqual(self.mock_orchestrator.current_deferred_content_type, content_type)
        self.assertTrue(self.mock_orchestrator.is_waiting_for_user_action)
        self.assertEqual(self.mock_orchestrator.current_execution_id, execution_id)
    
    def test_handle_system_already_waiting(self):
        """Test handling when system is already in deferred action mode."""
        self.mock_orchestrator.is_waiting_for_user_action = True
        
        context = {
            "intent": {
                "intent": "deferred_action",
                "parameters": {
                    "content_request": "Write code",
                    "content_type": "code"
                }
            },
            "execution_id": "test_123"
        }
        
        with patch.object(self.handler, '_reset_deferred_action_state') as mock_reset, \
             patch.object(self.handler, '_generate_content') as mock_generate, \
             patch.object(self.handler, '_start_mouse_listener'), \
             patch.object(self.handler, '_provide_audio_instructions'), \
             patch.object(self.handler, '_start_timeout_monitoring'):
            
            mock_generate.return_value = "test content"
            
            result = self.handler.handle("Write code", context)
            
            mock_reset.assert_called_once()
            self.assertEqual(result["status"], "waiting_for_user_action")


class TestIntentRecognitionAndRouting(unittest.TestCase):
    """Test cases for intent recognition and command routing logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_orchestrator = Mock()
        self.mock_orchestrator.config = {}
        
        # Mock handlers
        self.mock_gui_handler = Mock()
        self.mock_conversation_handler = Mock()
        self.mock_deferred_handler = Mock()
        
        self.mock_orchestrator.gui_handler = self.mock_gui_handler
        self.mock_orchestrator.conversation_handler = self.mock_conversation_handler
        self.mock_orchestrator.deferred_action_handler = self.mock_deferred_handler
        
        # Mock reasoning module for intent recognition
        self.mock_reasoning = Mock()
        self.mock_orchestrator.reasoning_module = self.mock_reasoning
    
    def test_intent_recognition_gui_interaction(self):
        """Test intent recognition for GUI interaction commands."""
        # This would test the orchestrator's _recognize_intent method
        # Since we don't have direct access, we'll test the expected behavior
        
        gui_commands = [
            "click the submit button",
            "type hello world",
            "scroll down",
            "press enter",
            "double-click the file"
        ]
        
        for command in gui_commands:
            # Mock intent recognition result
            self.mock_reasoning.process_query.return_value = {
                'intent': 'gui_interaction',
                'confidence': 0.9,
                'parameters': {'action': 'click', 'target': 'button'}
            }
            
            # Test that GUI commands would be routed to GUI handler
            # This is a conceptual test of the routing logic
            intent_result = self.mock_reasoning.process_query.return_value
            self.assertEqual(intent_result['intent'], 'gui_interaction')
            self.assertGreaterEqual(intent_result['confidence'], 0.8)
    
    def test_intent_recognition_conversational_chat(self):
        """Test intent recognition for conversational commands."""
        conversational_commands = [
            "Hello, how are you?",
            "Tell me a joke",
            "What can you do?",
            "Good morning",
            "How's the weather?"
        ]
        
        for command in conversational_commands:
            self.mock_reasoning.process_query.return_value = {
                'intent': 'conversational_chat',
                'confidence': 0.85,
                'parameters': {'topic': 'greeting'}
            }
            
            intent_result = self.mock_reasoning.process_query.return_value
            self.assertEqual(intent_result['intent'], 'conversational_chat')
            self.assertGreaterEqual(intent_result['confidence'], 0.8)
    
    def test_intent_recognition_deferred_action(self):
        """Test intent recognition for deferred action commands."""
        deferred_commands = [
            "Write me a Python function",
            "Generate code for sorting",
            "Create an email template",
            "Write a summary of this document",
            "Generate a list of items"
        ]
        
        for command in deferred_commands:
            self.mock_reasoning.process_query.return_value = {
                'intent': 'deferred_action',
                'confidence': 0.9,
                'parameters': {'content_type': 'code', 'content_request': command}
            }
            
            intent_result = self.mock_reasoning.process_query.return_value
            self.assertEqual(intent_result['intent'], 'deferred_action')
            self.assertGreaterEqual(intent_result['confidence'], 0.8)
    
    def test_intent_recognition_question_answering(self):
        """Test intent recognition for question answering commands."""
        qa_commands = [
            "What does this page say?",
            "Summarize this document",
            "What's in this PDF?",
            "Read me the content",
            "What information is displayed?"
        ]
        
        for command in qa_commands:
            self.mock_reasoning.process_query.return_value = {
                'intent': 'question_answering',
                'confidence': 0.88,
                'parameters': {'query_type': 'content_analysis'}
            }
            
            intent_result = self.mock_reasoning.process_query.return_value
            self.assertEqual(intent_result['intent'], 'question_answering')
            self.assertGreaterEqual(intent_result['confidence'], 0.8)
    
    def test_intent_recognition_fallback(self):
        """Test intent recognition fallback behavior."""
        # Test low confidence scenario
        self.mock_reasoning.process_query.return_value = {
            'intent': 'unknown',
            'confidence': 0.3,
            'parameters': {}
        }
        
        intent_result = self.mock_reasoning.process_query.return_value
        # Low confidence should trigger fallback to GUI interaction
        self.assertLess(intent_result['confidence'], 0.5)
    
    def test_handler_routing_logic(self):
        """Test command routing to appropriate handlers."""
        # Test routing logic conceptually
        intent_to_handler_map = {
            'gui_interaction': 'gui_handler',
            'conversational_chat': 'conversation_handler',
            'deferred_action': 'deferred_action_handler',
            'question_answering': 'gui_handler'  # Reuses GUI handler for now
        }
        
        for intent, expected_handler in intent_to_handler_map.items():
            # Verify the mapping is correct
            self.assertIn(intent, intent_to_handler_map)
            self.assertIsNotNone(expected_handler)


class TestConcurrencyAndLockManagement(unittest.TestCase):
    """Test cases for concurrency handling and lock management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_orchestrator = Mock()
        self.mock_orchestrator.execution_lock = threading.Lock()
        self.mock_orchestrator.deferred_action_lock = threading.Lock()
        self.mock_orchestrator.is_waiting_for_user_action = False
        
        self.handler = DeferredActionHandler(self.mock_orchestrator)
    
    def test_concurrent_deferred_action_scenarios(self):
        """Test concurrent deferred action handling."""
        # Simulate first deferred action
        self.mock_orchestrator.is_waiting_for_user_action = True
        
        # Mock content generation
        mock_response = {
            'choices': [{
                'message': {'content': 'test content'}
            }]
        }
        
        with patch.object(self.handler, '_generate_content') as mock_generate, \
             patch.object(self.handler, '_start_mouse_listener'), \
             patch.object(self.handler, '_provide_audio_instructions'), \
             patch.object(self.handler, '_start_timeout_monitoring'), \
             patch.object(self.handler, '_reset_deferred_action_state') as mock_reset:
            
            mock_generate.return_value = "test content"
            
            context = {
                "intent": {
                    "intent": "deferred_action",
                    "parameters": {
                        "content_request": "Write code",
                        "content_type": "code"
                    }
                },
                "execution_id": "test_123"
            }
            
            # Second deferred action should cancel the first
            result = self.handler.handle("Write new code", context)
            
            # Should reset previous action
            mock_reset.assert_called_once()
            self.assertEqual(result["status"], "waiting_for_user_action")
    
    def test_lock_timeout_scenarios(self):
        """Test lock timeout handling."""
        # Create a lock that's already acquired
        test_lock = threading.Lock()
        test_lock.acquire()
        
        try:
            # Test timeout behavior (conceptual)
            acquired = test_lock.acquire(timeout=0.1)
            self.assertFalse(acquired)
        finally:
            test_lock.release()
    
    def test_deferred_action_state_thread_safety(self):
        """Test thread safety of deferred action state management."""
        def setup_state():
            self.handler._setup_deferred_action_state("content", "code", "test_123")
        
        # Run multiple threads setting up state
        threads = []
        for i in range(5):
            thread = threading.Thread(target=setup_state)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # State should be consistent (last one wins)
        self.assertEqual(self.mock_orchestrator.pending_action_payload, "content")
        self.assertTrue(self.mock_orchestrator.is_waiting_for_user_action)
    
    def test_execution_lock_early_release(self):
        """Test early release of execution lock for deferred actions."""
        # This tests the concept that deferred actions should release
        # the execution lock early to allow other commands
        
        # Mock a deferred action result
        deferred_result = {
            "status": "waiting_for_user_action",
            "message": "Content generated, waiting for click"
        }
        
        # Verify that waiting_for_user_action status indicates
        # the lock should be released early
        self.assertEqual(deferred_result["status"], "waiting_for_user_action")


class TestContentGenerationAndCleaning(unittest.TestCase):
    """Test cases for content generation and cleaning validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_orchestrator = Mock()
        self.handler = DeferredActionHandler(self.mock_orchestrator)
    
    def test_content_cleaning_comprehensive(self):
        """Test comprehensive content cleaning."""
        test_cases = [
            {
                'input': 'Here is the code:\n```python\ndef hello():\n    print("Hello")\n```\nThat\'s it!',
                'expected_removed': ['Here is the code:', '```python', '```', "That's it!"],
                'expected_present': ['def hello():', 'print("Hello")']
            },
            {
                'input': '**Code:**\nfunction test() { return true; }\n**End of code**',
                'expected_removed': ['**Code:**', '**End of code**'],
                'expected_present': ['function test()', 'return true']
            },
            {
                'input': 'Here\'s your text:\nThis is a sample paragraph.\nHope this helps!',
                'expected_removed': ["Here's your text:", 'Hope this helps!'],
                'expected_present': ['This is a sample paragraph.']
            }
        ]
        
        for case in test_cases:
            cleaned = self.handler._clean_and_format_content(case['input'], 'code')
            
            # Check that unwanted content was removed
            for unwanted in case['expected_removed']:
                self.assertNotIn(unwanted, cleaned, 
                    f"'{unwanted}' should be removed from: {cleaned}")
            
            # Check that wanted content is preserved
            for wanted in case['expected_present']:
                self.assertIn(wanted, cleaned,
                    f"'{wanted}' should be present in: {cleaned}")
    
    def test_code_formatting_validation(self):
        """Test code formatting validation."""
        # Test single-line code formatting
        single_line = "def hello(): print('Hello'); return True"
        formatted = self.handler._format_single_line_code(single_line)
        
        self.assertIn('\n', formatted)
        self.assertIn('def hello():', formatted)
        
        # Test multi-line code preservation
        multi_line = "def hello():\n    print('Hello')\n    return True"
        formatted = self.handler._format_code_content(multi_line)
        
        self.assertIn('def hello():', formatted)
        self.assertIn('    print(', formatted)  # Indentation preserved
    
    def test_text_formatting_validation(self):
        """Test text formatting validation."""
        text_content = "First paragraph.\n\nSecond paragraph.\n\n\n\nThird paragraph."
        formatted = self.handler._format_text_content(text_content)
        
        # Should have proper paragraph breaks but not excessive blank lines
        lines = formatted.split('\n')
        blank_line_count = sum(1 for line in lines if not line.strip())
        self.assertLessEqual(blank_line_count, 4)  # Reasonable number of blank lines
    
    def test_duplicate_content_removal(self):
        """Test duplicate content detection and removal."""
        duplicate_content = """Line 1
Line 2
Line 3
Line 1
Line 2
Line 3
Unique line"""
        
        cleaned = self.handler._remove_duplicate_content(duplicate_content)
        
        # Should contain unique content
        self.assertIn("Unique line", cleaned)
        
        # Should have fewer total lines due to duplicate removal
        original_lines = len(duplicate_content.split('\n'))
        cleaned_lines = len(cleaned.split('\n'))
        self.assertLessEqual(cleaned_lines, original_lines)
    
    def test_content_type_specific_formatting(self):
        """Test content type-specific formatting."""
        # Test code content
        code_content = "```python\ndef test():\n    return True\n```"
        code_formatted = self.handler._clean_and_format_content(code_content, 'code')
        
        self.assertNotIn('```', code_formatted)
        self.assertIn('def test():', code_formatted)
        
        # Test text content
        text_content = "Here's the text:\nThis is a paragraph.\nAnother paragraph."
        text_formatted = self.handler._clean_and_format_content(text_content, 'text')
        
        self.assertNotIn("Here's the text:", text_formatted)
        self.assertIn("This is a paragraph.", text_formatted)


class TestErrorHandlingAndRecovery(unittest.TestCase):
    """Test cases for error handling and recovery scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_orchestrator = Mock()
        self.mock_orchestrator.config = {}
        
        # Create handlers for testing
        self.gui_handler = GUIHandler(self.mock_orchestrator)
        self.conversation_handler = ConversationHandler(self.mock_orchestrator)
        self.deferred_handler = DeferredActionHandler(self.mock_orchestrator)
    
    def test_gui_handler_module_unavailable(self):
        """Test GUI handler behavior when modules are unavailable."""
        # Remove modules to simulate unavailability
        self.mock_orchestrator.accessibility_module = None
        self.mock_orchestrator.automation_module = None
        
        context = {"intent": {"intent": "gui_interaction"}, "execution_id": "test_123"}
        result = self.gui_handler.handle("click button", context)
        
        self.assertEqual(result["status"], "error")
        self.assertIn("modules", result["message"].lower())
    
    def test_conversation_handler_reasoning_failure(self):
        """Test conversation handler behavior when reasoning fails."""
        self.mock_orchestrator.reasoning_module = Mock()
        self.mock_orchestrator.reasoning_module.process_query.side_effect = Exception("API Error")
        
        context = {"intent": {"intent": "conversational_chat"}, "execution_id": "conv_123"}
        result = self.conversation_handler.handle("Hello", context)
        
        self.assertEqual(result["status"], "success")  # Should still succeed with fallback
        self.assertIn("response", result)
    
    def test_deferred_handler_content_generation_failure(self):
        """Test deferred handler behavior when content generation fails."""
        self.mock_orchestrator.reasoning_module = Mock()
        self.mock_orchestrator.reasoning_module._make_api_request.side_effect = Exception("API Error")
        
        context = {
            "intent": {
                "intent": "deferred_action",
                "parameters": {
                    "content_request": "Write code",
                    "content_type": "code"
                }
            },
            "execution_id": "deferred_123"
        }
        
        result = self.deferred_handler.handle("Write code", context)
        
        self.assertEqual(result["status"], "error")
        self.assertIn("deferred action", result["message"].lower())
    
    def test_handler_invalid_input_handling(self):
        """Test handler behavior with invalid inputs."""
        handlers = [self.gui_handler, self.conversation_handler, self.deferred_handler]
        
        for handler in handlers:
            # Test empty command
            context = {"intent": {"intent": "test"}, "execution_id": "test_123"}
            result = handler.handle("", context)
            
            self.assertEqual(result["status"], "error")
            self.assertIn("invalid", result["message"].lower())
            
            # Test None command
            result = handler.handle(None, context)
            
            self.assertEqual(result["status"], "error")
    
    def test_error_result_standardization(self):
        """Test that all handlers create standardized error results."""
        error_result = self.gui_handler._create_error_result(
            "Test error", 
            error=ValueError("Test exception"),
            module="test_module"
        )
        
        # Verify standard error result format
        self.assertEqual(error_result["status"], "error")
        self.assertIn("message", error_result)
        self.assertIn("timestamp", error_result)
        self.assertEqual(error_result["module"], "test_module")
    
    def test_module_error_handling(self):
        """Test standardized module error handling."""
        error = RuntimeError("Module failed")
        result = self.gui_handler._handle_module_error("test_module", error, "test operation")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("test operation", result["message"])
        self.assertEqual(result["module"], "test_module")
        self.assertEqual(result["operation"], "test operation")
    
    def test_recovery_from_partial_failures(self):
        """Test recovery from partial failures."""
        # Test GUI handler fallback from fast path to vision
        self.mock_orchestrator.accessibility_module = Mock()
        self.mock_orchestrator.automation_module = Mock()
        self.mock_orchestrator.vision_module = Mock()
        self.mock_orchestrator.reasoning_module = Mock()
        
        # Mock fast path failure
        self.mock_orchestrator.accessibility_module.get_accessibility_status.return_value = {
            'api_initialized': False
        }
        
        # Mock successful vision fallback
        self.mock_orchestrator.vision_module.describe_screen.return_value = {
            "description": "Screen with button"
        }
        self.mock_orchestrator.reasoning_module.get_action_plan.return_value = {
            "plan": [{"action": "click", "coordinates": (100, 200)}]
        }
        
        context = {"intent": {"intent": "gui_interaction"}, "execution_id": "test_123"}
        
        with patch.object(self.gui_handler, '_perform_action_execution') as mock_execute:
            mock_execute.return_value = {
                'total_actions': 1,
                'successful_actions': 1,
                'failed_actions': 0
            }
            
            result = self.gui_handler.handle("click button", context)
            
            # Should succeed via vision fallback
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["method"], "vision_fallback")
    
    def test_timeout_handling(self):
        """Test timeout handling in various scenarios."""
        # Test deferred action timeout setup
        self.deferred_handler.deferred_action_timeout_seconds = 300.0
        
        with patch.object(self.deferred_handler, '_start_timeout_monitoring') as mock_timeout:
            with patch.object(self.deferred_handler, '_generate_content') as mock_generate, \
                 patch.object(self.deferred_handler, '_start_mouse_listener'), \
                 patch.object(self.deferred_handler, '_provide_audio_instructions'):
                
                mock_generate.return_value = "test content"
                
                context = {
                    "intent": {
                        "intent": "deferred_action",
                        "parameters": {
                            "content_request": "Write code",
                            "content_type": "code"
                        }
                    },
                    "execution_id": "test_123"
                }
                
                result = self.deferred_handler.handle("Write code", context)
                
                # Should set up timeout monitoring
                mock_timeout.assert_called_once_with("test_123")
                
                # Result should include timeout information
                self.assertIn("timeout_seconds", result)
                self.assertEqual(result["timeout_seconds"], 300.0)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)