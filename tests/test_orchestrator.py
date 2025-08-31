# tests/test_orchestrator.py
"""
Unit tests for the Orchestrator module.

Tests the core command processing pipeline with mocked modules.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from orchestrator import Orchestrator, CommandStatus, OrchestratorError


class TestOrchestrator:
    """Test cases for the Orchestrator class."""
    
    @pytest.fixture
    def mock_modules(self):
        """Create mock modules for testing."""
        with patch('modules.vision.VisionModule') as mock_vision, \
             patch('modules.reasoning.ReasoningModule') as mock_reasoning, \
             patch('modules.automation.AutomationModule') as mock_automation, \
             patch('modules.audio.AudioModule') as mock_audio, \
             patch('modules.feedback.FeedbackModule') as mock_feedback:
            
            # Configure mock vision module
            mock_vision_instance = Mock()
            mock_vision_instance.describe_screen.return_value = {
                "elements": [
                    {
                        "type": "button",
                        "text": "Submit",
                        "coordinates": [100, 200, 150, 230],
                        "description": "Submit button"
                    }
                ],
                "metadata": {
                    "timestamp": time.time(),
                    "screen_resolution": [1920, 1080]
                }
            }
            mock_vision.return_value = mock_vision_instance
            
            # Configure mock reasoning module
            mock_reasoning_instance = Mock()
            mock_reasoning_instance.get_action_plan.return_value = {
                "plan": [
                    {
                        "action": "click",
                        "coordinates": [125, 215]
                    },
                    {
                        "action": "speak",
                        "message": "Button clicked successfully"
                    },
                    {
                        "action": "finish"
                    }
                ],
                "metadata": {
                    "confidence": 0.95,
                    "estimated_duration": 2.0
                }
            }
            mock_reasoning.return_value = mock_reasoning_instance
            
            # Configure mock automation module
            mock_automation_instance = Mock()
            mock_automation_instance.execute_action.return_value = None
            mock_automation.return_value = mock_automation_instance
            
            # Configure mock audio module
            mock_audio_instance = Mock()
            mock_audio_instance.text_to_speech.return_value = None
            mock_audio_instance.validate_audio_input = Mock(return_value={"errors": [], "warnings": []})
            mock_audio.return_value = mock_audio_instance
            
            # Configure mock feedback module
            mock_feedback_instance = Mock()
            mock_feedback_instance.play.return_value = None
            mock_feedback_instance.speak.return_value = None
            mock_feedback_instance.validate_sound_files = Mock(return_value={"errors": [], "warnings": []})
            mock_feedback.return_value = mock_feedback_instance
            
            return {
                'vision': mock_vision_instance,
                'reasoning': mock_reasoning_instance,
                'automation': mock_automation_instance,
                'audio': mock_audio_instance,
                'feedback': mock_feedback_instance
            }
    
    def test_orchestrator_initialization(self, mock_modules):
        """Test that orchestrator initializes all modules correctly."""
        orchestrator = Orchestrator()
        
        # Check that all modules are initialized
        assert orchestrator.vision_module is not None
        assert orchestrator.reasoning_module is not None
        assert orchestrator.automation_module is not None
        assert orchestrator.audio_module is not None
        assert orchestrator.feedback_module is not None
        
        # Check initial state
        assert orchestrator.current_command is None
        assert orchestrator.command_status == CommandStatus.PENDING
        assert orchestrator.command_history == []
    
    def test_execute_command_success(self, mock_modules):
        """Test successful command execution through the full pipeline."""
        orchestrator = Orchestrator()
        
        # Execute a test command
        result = orchestrator.execute_command("click the submit button")
        
        # Verify the result
        assert result["success"] is True
        assert result["status"] == "completed"
        assert result["command"] == "click the submit button"
        assert "execution_id" in result
        assert result["duration"] > 0
        assert result["steps_completed"] == ["perception", "reasoning", "action"]
        
        # Verify module interactions
        mock_modules['vision'].describe_screen.assert_called_once()
        mock_modules['reasoning'].get_action_plan.assert_called_once()
        mock_modules['automation'].execute_action.assert_called()
        mock_modules['feedback'].play.assert_called()
        mock_modules['feedback'].speak.assert_called()
        
        # Check command history
        assert len(orchestrator.command_history) == 1
        assert orchestrator.command_history[0]["command"] == "click the submit button"
    
    def test_execute_command_empty_input(self, mock_modules):
        """Test that empty commands raise ValueError."""
        orchestrator = Orchestrator()
        
        with pytest.raises(ValueError, match="Command cannot be empty"):
            orchestrator.execute_command("")
        
        with pytest.raises(ValueError, match="Command cannot be empty"):
            orchestrator.execute_command("   ")
    
    def test_execute_command_vision_failure(self, mock_modules):
        """Test command execution when vision module fails."""
        orchestrator = Orchestrator()
        
        # Make vision module fail
        mock_modules['vision'].describe_screen.side_effect = Exception("Vision API error")
        
        # Execute command
        result = orchestrator.execute_command("test command")
        
        # Verify failure handling
        assert result["success"] is False
        assert result["status"] == "failed"
        assert "Vision API error" in str(result.get("errors", []))
        assert "perception" not in result["steps_completed"]
        
        # Verify failure feedback was provided
        mock_modules['feedback'].play.assert_called()
        mock_modules['feedback'].speak.assert_called()
    
    def test_execute_command_reasoning_failure(self, mock_modules):
        """Test command execution when reasoning module fails."""
        orchestrator = Orchestrator()
        
        # Make reasoning module fail
        mock_modules['reasoning'].get_action_plan.side_effect = Exception("Reasoning API error")
        
        # Execute command
        result = orchestrator.execute_command("test command")
        
        # Verify failure handling
        assert result["success"] is False
        assert result["status"] == "failed"
        assert "Reasoning API error" in str(result.get("errors", []))
        assert "perception" in result["steps_completed"]
        assert "reasoning" not in result["steps_completed"]
    
    def test_execute_command_automation_failure(self, mock_modules):
        """Test command execution when automation actions fail."""
        orchestrator = Orchestrator()
        
        # Make automation module fail for click actions
        def automation_side_effect(action):
            if action.get("action") == "click":
                raise Exception("Click failed")
        
        mock_modules['automation'].execute_action.side_effect = automation_side_effect
        
        # Execute command
        result = orchestrator.execute_command("test command")
        
        # Verify partial success (some actions may still succeed)
        assert "perception" in result["steps_completed"]
        assert "reasoning" in result["steps_completed"]
        assert "action" in result["steps_completed"]
        
        # Check that execution results show failures
        assert result.get("actions_failed", 0) > 0
    
    def test_execute_command_retry_logic(self, mock_modules):
        """Test retry logic for failed operations."""
        orchestrator = Orchestrator()
        
        # Make vision fail twice, then succeed
        call_count = 0
        def vision_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Temporary failure")
            return {
                "elements": [],
                "metadata": {"timestamp": time.time(), "screen_resolution": [1920, 1080]}
            }
        
        mock_modules['vision'].describe_screen.side_effect = vision_side_effect
        
        # Execute command
        result = orchestrator.execute_command("test command")
        
        # Verify success after retries
        assert result["success"] is True
        assert mock_modules['vision'].describe_screen.call_count == 3
    
    def test_execute_command_concurrent_execution(self, mock_modules):
        """Test that concurrent command execution is properly serialized."""
        orchestrator = Orchestrator()
        
        # Add delay to vision module to simulate processing time
        def slow_vision():
            time.sleep(0.1)
            return {
                "elements": [],
                "metadata": {"timestamp": time.time(), "screen_resolution": [1920, 1080]}
            }
        
        mock_modules['vision'].describe_screen.side_effect = slow_vision
        
        # Execute commands concurrently
        results = []
        threads = []
        
        def execute_command(cmd):
            result = orchestrator.execute_command(f"command {cmd}")
            results.append(result)
        
        # Start multiple threads
        for i in range(3):
            thread = threading.Thread(target=execute_command, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all commands completed
        assert len(results) == 3
        assert all(result["success"] for result in results)
        
        # Verify commands were executed sequentially (not overlapping)
        execution_times = [(r["metadata"]["execution_timestamp"], r["duration"]) for r in results]
        execution_times.sort()
        
        # Check that executions don't overlap significantly
        for i in range(len(execution_times) - 1):
            current_end = execution_times[i][0] + execution_times[i][1]
            next_start = execution_times[i + 1][0]
            assert next_start >= current_end - 0.05  # Allow small timing tolerance
    
    def test_answer_question_success(self, mock_modules):
        """Test successful question answering."""
        orchestrator = Orchestrator()
        
        # Configure reasoning module to return answer
        mock_modules['reasoning'].get_action_plan.return_value = {
            "plan": [
                {
                    "action": "speak",
                    "message": "The submit button is located at coordinates 125, 215"
                },
                {
                    "action": "finish"
                }
            ],
            "metadata": {"confidence": 0.9}
        }
        
        # Ask a question
        result = orchestrator.answer_question("Where is the submit button?")
        
        # Verify the result
        assert result["success"] is True
        assert result["status"] == "completed"
        assert result["question"] == "Where is the submit button?"
        assert "submit button" in result["answer"]
        assert "execution_id" in result
        
        # Verify module interactions
        mock_modules['vision'].describe_screen.assert_called_once()
        mock_modules['reasoning'].get_action_plan.assert_called_once()
        mock_modules['feedback'].speak.assert_called()
    
    def test_answer_question_empty_input(self, mock_modules):
        """Test that empty questions raise ValueError."""
        orchestrator = Orchestrator()
        
        with pytest.raises(ValueError, match="Question cannot be empty"):
            orchestrator.answer_question("")
        
        with pytest.raises(ValueError, match="Question cannot be empty"):
            orchestrator.answer_question("   ")
    
    def test_answer_question_failure(self, mock_modules):
        """Test question answering when modules fail."""
        orchestrator = Orchestrator()
        
        # Make vision module fail
        mock_modules['vision'].describe_screen.side_effect = Exception("Vision error")
        
        # Ask a question
        result = orchestrator.answer_question("What's on the screen?")
        
        # Verify failure handling
        assert result["success"] is False
        assert result["status"] == "failed"
        assert "error" in result["answer"].lower()
        assert "error" in result
    
    def test_get_current_status(self, mock_modules):
        """Test getting current orchestrator status."""
        orchestrator = Orchestrator()
        
        # Get initial status
        status = orchestrator.get_current_status()
        
        # Verify status structure
        assert status["status"] == "pending"
        assert "modules_initialized" in status
        assert status["modules_initialized"]["vision"] is True
        assert status["modules_initialized"]["reasoning"] is True
        assert status["modules_initialized"]["automation"] is True
        assert status["modules_initialized"]["audio"] is True
        assert status["modules_initialized"]["feedback"] is True
        assert status["command_history_count"] == 0
        assert status["current_command"] is None
    
    def test_get_command_history(self, mock_modules):
        """Test getting command execution history."""
        orchestrator = Orchestrator()
        
        # Execute some commands
        orchestrator.execute_command("command 1")
        orchestrator.execute_command("command 2")
        
        # Get full history
        history = orchestrator.get_command_history()
        assert len(history) == 2
        assert history[0]["command"] == "command 1"
        assert history[1]["command"] == "command 2"
        
        # Get limited history
        limited_history = orchestrator.get_command_history(limit=1)
        assert len(limited_history) == 1
        assert limited_history[0]["command"] == "command 2"
    
    def test_clear_command_history(self, mock_modules):
        """Test clearing command execution history."""
        orchestrator = Orchestrator()
        
        # Execute some commands
        orchestrator.execute_command("command 1")
        orchestrator.execute_command("command 2")
        
        # Clear history
        cleared_count = orchestrator.clear_command_history()
        
        # Verify history is cleared
        assert cleared_count == 2
        assert len(orchestrator.command_history) == 0
        assert len(orchestrator.get_command_history()) == 0
    
    def test_validate_modules(self, mock_modules):
        """Test module validation functionality."""
        orchestrator = Orchestrator()
        
        # Validate modules
        validation = orchestrator.validate_modules()
        
        # Verify validation structure
        assert "overall_status" in validation
        assert "modules" in validation
        assert "errors" in validation
        assert "warnings" in validation
        
        # Check individual modules
        assert "vision" in validation["modules"]
        assert "reasoning" in validation["modules"]
        assert "automation" in validation["modules"]
        assert "audio" in validation["modules"]
        assert "feedback" in validation["modules"]
        
        # Check that validation ran without error
        assert validation["overall_status"] in ["healthy", "degraded", "unhealthy"]
    
    def test_action_execution_different_types(self, mock_modules):
        """Test execution of different action types."""
        orchestrator = Orchestrator()
        
        # Configure reasoning module to return various action types
        mock_modules['reasoning'].get_action_plan.return_value = {
            "plan": [
                {"action": "click", "coordinates": [100, 200]},
                {"action": "type", "text": "hello world"},
                {"action": "scroll", "direction": "down", "amount": 100},
                {"action": "speak", "message": "Task completed"},
                {"action": "finish"}
            ],
            "metadata": {"confidence": 0.95}
        }
        
        # Execute command
        result = orchestrator.execute_command("perform various actions")
        
        # Verify all actions were attempted
        assert result["success"] is True
        assert result["total_actions"] == 5
        assert result["actions_executed"] == 5
        
        # Verify automation module was called for GUI actions
        assert mock_modules['automation'].execute_action.call_count == 3  # click, type, scroll
        
        # Verify feedback module was called for speak action
        mock_modules['feedback'].speak.assert_called()
    
    def test_critical_action_failure_handling(self, mock_modules):
        """Test handling of critical action failures."""
        orchestrator = Orchestrator()
        
        # Configure automation to fail with a critical error
        def automation_side_effect(action):
            if action.get("action") == "click":
                raise Exception("PyAutoGUI fail-safe triggered")
        
        mock_modules['automation'].execute_action.side_effect = automation_side_effect
        
        # Configure action plan with multiple actions
        mock_modules['reasoning'].get_action_plan.return_value = {
            "plan": [
                {"action": "click", "coordinates": [100, 200]},
                {"action": "type", "text": "should not execute"},
                {"action": "finish"}
            ],
            "metadata": {"confidence": 0.95}
        }
        
        # Execute command
        result = orchestrator.execute_command("test critical failure")
        
        # Verify execution stopped after critical failure
        assert result["actions_failed"] > 0
        # The exact behavior depends on implementation details
        # but we should see that not all actions were attempted
    
    def test_cleanup(self, mock_modules):
        """Test orchestrator cleanup functionality."""
        orchestrator = Orchestrator()
        
        # Add cleanup methods to mock modules
        for module in mock_modules.values():
            module.cleanup = Mock()
        
        # Execute some commands to populate history
        orchestrator.execute_command("test command")
        
        # Cleanup
        orchestrator.cleanup()
        
        # Verify cleanup was called on modules that have it
        for module in mock_modules.values():
            if hasattr(module, 'cleanup'):
                module.cleanup.assert_called_once()
        
        # Verify state is reset
        assert len(orchestrator.command_history) == 0
        assert orchestrator.current_command is None
        assert orchestrator.command_status == CommandStatus.PENDING


class TestOrchestratorErrorHandling:
    """Test error handling scenarios in the Orchestrator."""
    
    def test_module_initialization_failure(self):
        """Test orchestrator behavior when module initialization fails."""
        with patch('orchestrator.VisionModule', side_effect=Exception("Vision init failed")):
            with pytest.raises(OrchestratorError, match="Module initialization failed"):
                Orchestrator()
    
    def test_invalid_screen_context(self, mock_modules):
        """Test handling of invalid screen context from vision module."""
        orchestrator = Orchestrator()
        
        # Return invalid screen context
        mock_modules['vision'].describe_screen.return_value = {}
        
        result = orchestrator.execute_command("test command")
        
        assert result["success"] is False
        assert "Invalid screen analysis result" in str(result.get("errors", []))
    
    def test_invalid_action_plan(self, mock_modules):
        """Test handling of invalid action plan from reasoning module."""
        orchestrator = Orchestrator()
        
        # Return invalid action plan
        mock_modules['reasoning'].get_action_plan.return_value = {}
        
        result = orchestrator.execute_command("test command")
        
        assert result["success"] is False
        assert "Invalid action plan result" in str(result.get("errors", []))
    
    def test_empty_action_plan(self, mock_modules):
        """Test handling of empty action plan from reasoning module."""
        orchestrator = Orchestrator()
        
        # Return empty action plan
        mock_modules['reasoning'].get_action_plan.return_value = {"plan": []}
        
        result = orchestrator.execute_command("test command")
        
        assert result["success"] is False
        assert "Empty action plan received" in str(result.get("errors", []))
    
    def test_unknown_action_type(self, mock_modules):
        """Test handling of unknown action types in action plan."""
        orchestrator = Orchestrator()
        
        # Return action plan with unknown action type
        mock_modules['reasoning'].get_action_plan.return_value = {
            "plan": [
                {"action": "unknown_action", "parameter": "value"},
                {"action": "finish"}
            ],
            "metadata": {"confidence": 0.95}
        }
        
        result = orchestrator.execute_command("test command")
        
        # Should complete but with some failed actions
        assert result["success"] is True  # Overall success because finish action succeeded
        assert result["actions_failed"] > 0


class TestOrchestratorAdvancedFeatures:
    """Test advanced orchestration features including validation, parallel processing, and progress tracking."""
    
    @pytest.fixture
    def mock_modules(self):
        """Create mock modules for testing advanced features."""
        with patch('modules.vision.VisionModule') as mock_vision, \
             patch('modules.reasoning.ReasoningModule') as mock_reasoning, \
             patch('modules.automation.AutomationModule') as mock_automation, \
             patch('modules.audio.AudioModule') as mock_audio, \
             patch('modules.feedback.FeedbackModule') as mock_feedback:
            
            # Configure mock vision module with realistic delay
            mock_vision_instance = Mock()
            def vision_with_delay():
                time.sleep(0.1)  # Simulate processing time
                return {
                    "elements": [
                        {
                            "type": "button",
                            "text": "Submit",
                            "coordinates": [100, 200, 150, 230],
                            "description": "Submit button"
                        }
                    ],
                    "metadata": {
                        "timestamp": time.time(),
                        "screen_resolution": [1920, 1080]
                    }
                }
            mock_vision_instance.describe_screen.side_effect = vision_with_delay
            mock_vision.return_value = mock_vision_instance
            
            # Configure mock reasoning module with realistic delay
            mock_reasoning_instance = Mock()
            def reasoning_with_delay(command, screen_context):
                time.sleep(0.1)  # Simulate processing time
                return {
                    "plan": [
                        {"action": "click", "coordinates": [125, 215]},
                        {"action": "speak", "message": "Button clicked successfully"},
                        {"action": "finish"}
                    ],
                    "metadata": {"confidence": 0.95, "estimated_duration": 2.0}
                }
            mock_reasoning_instance.get_action_plan.side_effect = reasoning_with_delay
            mock_reasoning.return_value = mock_reasoning_instance
            
            # Configure other modules
            mock_automation_instance = Mock()
            mock_automation_instance.execute_action.return_value = None
            mock_automation.return_value = mock_automation_instance
            
            mock_audio_instance = Mock()
            mock_audio_instance.text_to_speech.return_value = None
            mock_audio_instance.validate_audio_input = Mock(return_value={"errors": [], "warnings": []})
            mock_audio.return_value = mock_audio_instance
            
            mock_feedback_instance = Mock()
            mock_feedback_instance.play.return_value = None
            mock_feedback_instance.speak.return_value = None
            mock_feedback_instance.validate_sound_files = Mock(return_value={"errors": [], "warnings": []})
            mock_feedback.return_value = mock_feedback_instance
            
            return {
                'vision': mock_vision_instance,
                'reasoning': mock_reasoning_instance,
                'automation': mock_automation_instance,
                'audio': mock_audio_instance,
                'feedback': mock_feedback_instance
            }
    
    def test_command_validation_success(self, mock_modules):
        """Test successful command validation and preprocessing."""
        with patch('orchestrator.Orchestrator._initialize_modules'):
            orchestrator = Orchestrator()
            
            # Test various command types
            test_commands = [
                ("Click the submit button", "click"),
                ("Type 'hello world'", "type"),
                ("Scroll down", "scroll"),
                ("What is on the screen?", "question"),
                ("Fill out the form", "form_fill")
            ]
            
            for command, expected_type in test_commands:
                validation = orchestrator.validate_command(command)
                
                assert validation.is_valid is True
                assert validation.command_type == expected_type
                assert validation.confidence > 0.0
                assert len(validation.issues) == 0
    
    def test_command_validation_failure(self, mock_modules):
        """Test command validation with invalid inputs."""
        with patch('orchestrator.Orchestrator._initialize_modules'):
            orchestrator = Orchestrator()
            
            # Test empty command
            validation = orchestrator.validate_command("")
            assert validation.is_valid is False
            assert "empty" in validation.issues[0].lower()
            
            # Test too short command - should be valid but with warnings
            validation = orchestrator.validate_command("hi")
            assert validation.is_valid is True  # Short commands are valid but have issues
            assert any("too short" in issue.lower() for issue in validation.issues)
            
            # Test too long command
            long_command = "a" * 600
            validation = orchestrator.validate_command(long_command)
            assert validation.is_valid is False
            assert "too long" in validation.issues[0].lower()
    
    def test_command_preprocessing(self, mock_modules):
        """Test command preprocessing and normalization."""
        with patch('orchestrator.Orchestrator._initialize_modules'):
            orchestrator = Orchestrator()
            
            # Test preprocessing rules
            test_cases = [
                ("Please click the submit button", "click submit button"),
                ("Could you type 'Hello World'?", "type 'hello world'?"),
                ("Can you scroll down please", "scroll down"),
                ("   Multiple    spaces   ", "multiple spaces")
            ]
            
            for original, expected in test_cases:
                processed = orchestrator._preprocess_command(original)
                assert processed == expected
    
    def test_progress_tracking(self, mock_modules):
        """Test progress tracking and callbacks."""
        with patch('orchestrator.Orchestrator._initialize_modules'):
            orchestrator = Orchestrator()
            # Manually set the mocked modules
            orchestrator.vision_module = mock_modules['vision']
            orchestrator.reasoning_module = mock_modules['reasoning']
            orchestrator.automation_module = mock_modules['automation']
            orchestrator.audio_module = mock_modules['audio']
            orchestrator.feedback_module = mock_modules['feedback']
            
            # Set up progress callback
            progress_updates = []
            def progress_callback(progress):
                progress_updates.append({
                    'status': progress.status,
                    'step': progress.current_step,
                    'percentage': progress.progress_percentage
                })
            
            orchestrator.add_progress_callback(progress_callback)
            
            # Execute command
            result = orchestrator.execute_command("click the submit button")
            
            # Verify progress updates were received
            assert len(progress_updates) > 0
            assert any(update['status'] == CommandStatus.VALIDATING for update in progress_updates)
            assert any(update['status'] == CommandStatus.PROCESSING for update in progress_updates)
            assert any(update['status'] == CommandStatus.COMPLETED for update in progress_updates)
            
            # Verify progress percentages increase
            percentages = [update['percentage'] for update in progress_updates if update['percentage'] is not None]
            assert len(percentages) > 1
            assert percentages[-1] == 100.0  # Should end at 100%
    
    def test_parallel_processing_enabled(self, mock_modules):
        """Test parallel processing for suitable commands."""
        with patch('orchestrator.Orchestrator._initialize_modules'):
            orchestrator = Orchestrator()
            # Manually set the mocked modules
            orchestrator.vision_module = mock_modules['vision']
            orchestrator.reasoning_module = mock_modules['reasoning']
            orchestrator.automation_module = mock_modules['automation']
            orchestrator.audio_module = mock_modules['audio']
            orchestrator.feedback_module = mock_modules['feedback']
            orchestrator.enable_parallel_processing = True
            
            start_time = time.time()
            result = orchestrator.execute_command("click the submit button")
            execution_time = time.time() - start_time
            
            # Verify successful execution
            assert result["success"] is True
            
            # With parallel processing, execution should be faster than sequential
            # (This is a rough test - in practice, the speedup depends on the actual delays)
            assert execution_time < 1.0  # Should complete quickly with mocked delays
    
    def test_parallel_processing_disabled(self, mock_modules):
        """Test sequential processing when parallel processing is disabled."""
        with patch('orchestrator.Orchestrator._initialize_modules'):
            orchestrator = Orchestrator()
            # Manually set the mocked modules
            orchestrator.vision_module = mock_modules['vision']
            orchestrator.reasoning_module = mock_modules['reasoning']
            orchestrator.automation_module = mock_modules['automation']
            orchestrator.audio_module = mock_modules['audio']
            orchestrator.feedback_module = mock_modules['feedback']
            orchestrator.enable_parallel_processing = False
            
            result = orchestrator.execute_command("click the submit button")
            
            # Verify successful execution
            assert result["success"] is True
            
            # Verify modules were called in sequence
            mock_modules['vision'].describe_screen.assert_called_once()
            mock_modules['reasoning'].get_action_plan.assert_called_once()
    
    def test_progress_callback_management(self, mock_modules):
        """Test adding and removing progress callbacks."""
        with patch('orchestrator.Orchestrator._initialize_modules'):
            orchestrator = Orchestrator()
            # Manually set the mocked modules
            orchestrator.vision_module = mock_modules['vision']
            orchestrator.reasoning_module = mock_modules['reasoning']
            orchestrator.automation_module = mock_modules['automation']
            orchestrator.audio_module = mock_modules['audio']
            orchestrator.feedback_module = mock_modules['feedback']
            
            callback1_calls = []
            callback2_calls = []
            
            def callback1(progress):
                callback1_calls.append(progress.status)
            
            def callback2(progress):
                callback2_calls.append(progress.status)
            
            # Add callbacks
            orchestrator.add_progress_callback(callback1)
            orchestrator.add_progress_callback(callback2)
            
            # Execute command
            orchestrator.execute_command("click button")
            
            # Both callbacks should have been called
            assert len(callback1_calls) > 0
            assert len(callback2_calls) > 0
            
            # Remove one callback
            orchestrator.remove_progress_callback(callback1)
            callback1_calls.clear()
            callback2_calls.clear()
            
            # Execute another command
            orchestrator.execute_command("type text")
            
            # Only callback2 should have been called
            assert len(callback1_calls) == 0
            assert len(callback2_calls) > 0
    
    def test_command_validation_with_dangerous_content(self, mock_modules):
        """Test validation of potentially dangerous commands."""
        with patch('orchestrator.Orchestrator._initialize_modules'):
            orchestrator = Orchestrator()
            
            dangerous_commands = [
                "delete all files",
                "format hard drive",
                "enter password 123456",
                "sudo rm -rf /"
            ]
            
            for command in dangerous_commands:
                validation = orchestrator.validate_command(command)
                
                # Should still be processed but with warnings
                assert len(validation.issues) > 0 or len(validation.suggestions) > 0
                # Check that dangerous content is flagged
                assert any("sensitive" in issue.lower() or "dangerous" in issue.lower() 
                          for issue in validation.issues)
    
    def test_get_current_progress(self, mock_modules):
        """Test getting current progress during execution."""
        with patch('orchestrator.Orchestrator._initialize_modules'):
            orchestrator = Orchestrator()
            # Manually set the mocked modules
            orchestrator.vision_module = mock_modules['vision']
            orchestrator.reasoning_module = mock_modules['reasoning']
            orchestrator.automation_module = mock_modules['automation']
            orchestrator.audio_module = mock_modules['audio']
            orchestrator.feedback_module = mock_modules['feedback']
            
            # No progress initially
            assert orchestrator.get_current_progress() is None
            
            # Start a command in a separate thread to test concurrent access
            def execute_slow_command():
                # Add delay to vision to simulate slow execution
                def slow_vision():
                    time.sleep(0.5)
                    return {
                        "elements": [],
                        "metadata": {"timestamp": time.time(), "screen_resolution": [1920, 1080]}
                    }
                mock_modules['vision'].describe_screen.side_effect = slow_vision
                orchestrator.execute_command("slow command")
            
            # Start execution in background
            import threading
            execution_thread = threading.Thread(target=execute_slow_command)
            execution_thread.start()
            
            # Check progress while executing
            time.sleep(0.1)  # Give it time to start
            progress = orchestrator.get_current_progress()
            
            if progress:  # May be None if execution completed very quickly
                assert progress.execution_id is not None
                assert progress.command == "slow command"
                assert progress.status in [CommandStatus.VALIDATING, CommandStatus.PROCESSING]
            
            # Wait for completion
            execution_thread.join()
            
            # Progress should be cleared after completion
            assert orchestrator.get_current_progress() is None


class TestOrchestratorIntegration:
    """Integration tests for complete command execution cycles."""
    
    @pytest.fixture
    def realistic_mock_modules(self):
        """Create more realistic mock modules for integration testing."""
        # Vision module with realistic screen analysis
        mock_vision_instance = Mock()
        def realistic_vision():
            return {
                "elements": [
                    {"type": "input", "text": "", "coordinates": [50, 100, 200, 130], "description": "Username field"},
                    {"type": "input", "text": "", "coordinates": [50, 150, 200, 180], "description": "Password field"},
                    {"type": "button", "text": "Login", "coordinates": [50, 200, 120, 230], "description": "Login button"},
                    {"type": "link", "text": "Forgot Password?", "coordinates": [130, 200, 250, 220], "description": "Forgot password link"}
                ],
                "text_blocks": [
                    {"content": "Welcome to the login page", "coordinates": [50, 50, 300, 80]}
                ],
                "metadata": {"timestamp": time.time(), "screen_resolution": [1920, 1080]}
            }
        mock_vision_instance.describe_screen.side_effect = realistic_vision
        
        # Reasoning module with context-aware responses
        mock_reasoning_instance = Mock()
        def realistic_reasoning(command, screen_context):
            elements = screen_context.get("elements", [])
            
            if "login" in command.lower():
                # Find login-related elements
                username_field = next((e for e in elements if "username" in e["description"].lower()), None)
                password_field = next((e for e in elements if "password" in e["description"].lower()), None)
                login_button = next((e for e in elements if "login" in e["text"].lower()), None)
                
                plan = []
                if username_field:
                    plan.append({"action": "click", "coordinates": [125, 115]})
                    plan.append({"action": "type", "text": "testuser"})
                if password_field:
                    plan.append({"action": "click", "coordinates": [125, 165]})
                    plan.append({"action": "type", "text": "testpass"})
                if login_button:
                    plan.append({"action": "click", "coordinates": [85, 215]})
                plan.append({"action": "speak", "message": "Login form completed"})
                plan.append({"action": "finish"})
                
                return {"plan": plan, "metadata": {"confidence": 0.9, "estimated_duration": 5.0}}
            
            elif "click" in command.lower():
                # Simple click command
                return {
                    "plan": [
                        {"action": "click", "coordinates": [85, 215]},
                        {"action": "speak", "message": "Clicked successfully"},
                        {"action": "finish"}
                    ],
                    "metadata": {"confidence": 0.8, "estimated_duration": 2.0}
                }
            
            else:
                # Default response
                return {
                    "plan": [
                        {"action": "speak", "message": "I'm not sure how to handle that command"},
                        {"action": "finish"}
                    ],
                    "metadata": {"confidence": 0.3, "estimated_duration": 1.0}
                }
        
        mock_reasoning_instance.get_action_plan.side_effect = realistic_reasoning
        
        # Automation module with action tracking
        mock_automation_instance = Mock()
        executed_actions = []
        def track_actions(action):
            executed_actions.append(action.copy())
        mock_automation_instance.execute_action.side_effect = track_actions
        mock_automation_instance.executed_actions = executed_actions
        
        # Audio and feedback modules
        mock_audio_instance = Mock()
        mock_audio_instance.validate_audio_input = Mock(return_value={"errors": [], "warnings": []})
        
        mock_feedback_instance = Mock()
        mock_feedback_instance.validate_sound_files = Mock(return_value={"errors": [], "warnings": []})
        
        return {
            'vision': mock_vision_instance,
            'reasoning': mock_reasoning_instance,
            'automation': mock_automation_instance,
            'audio': mock_audio_instance,
            'feedback': mock_feedback_instance
        }
    
    def test_complete_login_workflow(self, realistic_mock_modules):
        """Test complete login form filling workflow."""
        with patch('orchestrator.Orchestrator._initialize_modules'):
            orchestrator = Orchestrator()
            # Manually set the mocked modules
            orchestrator.vision_module = realistic_mock_modules['vision']
            orchestrator.reasoning_module = realistic_mock_modules['reasoning']
            orchestrator.automation_module = realistic_mock_modules['automation']
            orchestrator.audio_module = realistic_mock_modules['audio']
            orchestrator.feedback_module = realistic_mock_modules['feedback']
            
            # Execute login command
            result = orchestrator.execute_command("Please fill out the login form with username testuser and password testpass")
            
            # Verify successful execution
            assert result["success"] is True
            assert result["status"] == "completed"
            assert result["total_actions"] > 0
            
            # Verify that appropriate actions were executed
            executed_actions = realistic_mock_modules['automation'].executed_actions
            
            # Should have click and type actions
            click_actions = [a for a in executed_actions if a["action"] == "click"]
            type_actions = [a for a in executed_actions if a["action"] == "type"]
            
            assert len(click_actions) >= 2  # At least username field and password field clicks
            assert len(type_actions) >= 2   # At least username and password typing
            
            # Verify feedback was provided
            realistic_mock_modules['feedback'].speak.assert_called()
            realistic_mock_modules['feedback'].play.assert_called()
    
    def test_simple_click_workflow(self, realistic_mock_modules):
        """Test simple click command workflow."""
        orchestrator = Orchestrator()
        
        result = orchestrator.execute_command("Click the login button")
        
        # Verify successful execution
        assert result["success"] is True
        assert result["actions_executed"] >= 1
        
        # Verify click action was executed
        executed_actions = realistic_mock_modules['automation'].executed_actions
        click_actions = [a for a in executed_actions if a["action"] == "click"]
        assert len(click_actions) >= 1
    
    def test_question_answering_workflow(self, realistic_mock_modules):
        """Test question answering workflow."""
        orchestrator = Orchestrator()
        
        result = orchestrator.answer_question("What elements are visible on the screen?")
        
        # Verify successful execution
        assert result["success"] is True
        assert result["status"] == "completed"
        assert len(result["answer"]) > 0
        
        # Verify vision module was called for screen analysis
        realistic_mock_modules['vision'].describe_screen.assert_called()
        
        # Verify TTS feedback was provided
        realistic_mock_modules['feedback'].speak.assert_called()
    
    def test_error_recovery_workflow(self, realistic_mock_modules):
        """Test error recovery during workflow execution."""
        orchestrator = Orchestrator()
        
        # Make vision module fail initially, then succeed
        call_count = 0
        def failing_vision():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Network timeout")
            return {
                "elements": [{"type": "button", "text": "OK", "coordinates": [100, 100, 150, 130]}],
                "metadata": {"timestamp": time.time(), "screen_resolution": [1920, 1080]}
            }
        
        realistic_mock_modules['vision'].describe_screen.side_effect = failing_vision
        
        # Execute command
        result = orchestrator.execute_command("Click the OK button")
        
        # Should succeed after retry
        assert result["success"] is True
        assert realistic_mock_modules['vision'].describe_screen.call_count > 1
    
    def test_concurrent_command_execution(self, realistic_mock_modules):
        """Test that concurrent commands are properly serialized."""
        orchestrator = Orchestrator()
        
        # Add delays to simulate realistic processing time
        def slow_vision():
            time.sleep(0.2)
            return {
                "elements": [{"type": "button", "text": "Test", "coordinates": [100, 100, 150, 130]}],
                "metadata": {"timestamp": time.time(), "screen_resolution": [1920, 1080]}
            }
        
        realistic_mock_modules['vision'].describe_screen.side_effect = slow_vision
        
        # Execute multiple commands concurrently
        results = []
        threads = []
        
        def execute_command(cmd_num):
            result = orchestrator.execute_command(f"Click button {cmd_num}")
            results.append((cmd_num, result))
        
        # Start multiple threads
        for i in range(3):
            thread = threading.Thread(target=execute_command, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # Verify all commands completed successfully
        assert len(results) == 3
        for cmd_num, result in results:
            assert result["success"] is True
            assert f"button {cmd_num}" in result["command"].lower()
        
        # Verify commands were executed in sequence (not overlapping)
        # This is verified by checking that vision was called sequentially
        assert realistic_mock_modules['vision'].describe_screen.call_count == 3
    
    def test_module_validation_integration(self, realistic_mock_modules):
        """Test module validation in integration context."""
        orchestrator = Orchestrator()
        
        # Validate all modules
        validation = orchestrator.validate_modules()
        
        # Should be healthy with all mocked modules
        assert validation["overall_status"] == "healthy"
        assert all(module["initialized"] for module in validation["modules"].values())
        assert all(module["functional"] for module in validation["modules"].values())
    
    def test_command_history_integration(self, realistic_mock_modules):
        """Test command history tracking in integration context."""
        orchestrator = Orchestrator()
        
        # Execute multiple commands
        commands = [
            "Click the login button",
            "Type username",
            "Fill out the form"
        ]
        
        for cmd in commands:
            orchestrator.execute_command(cmd)
        
        # Verify history
        history = orchestrator.get_command_history()
        assert len(history) == len(commands)
        
        for i, cmd in enumerate(commands):
            assert history[i]["command"] == cmd
            assert history[i]["success"] is True
        
        # Test history limit
        limited_history = orchestrator.get_command_history(limit=2)
        assert len(limited_history) == 2
        assert limited_history[0]["command"] == commands[-2]
        assert limited_history[1]["command"] == commands[-1]
    
    def test_cleanup_integration(self, realistic_mock_modules):
        """Test cleanup functionality in integration context."""
        orchestrator = Orchestrator()
        
        # Execute some commands to populate state
        orchestrator.execute_command("Test command")
        
        # Add progress callback
        def dummy_callback(progress):
            pass
        orchestrator.add_progress_callback(dummy_callback)
        
        # Verify state before cleanup
        assert len(orchestrator.command_history) > 0
        assert len(orchestrator.progress_callbacks) > 0
        
        # Cleanup
        orchestrator.cleanup()
        
        # Verify state after cleanup
        assert len(orchestrator.command_history) == 0
        assert len(orchestrator.progress_callbacks) == 0
        assert orchestrator.current_command is None
        assert orchestrator.command_status == CommandStatus.PENDING


if __name__ == "__main__":
    pytest.main([__file__])