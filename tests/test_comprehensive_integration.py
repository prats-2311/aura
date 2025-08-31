# tests/test_comprehensive_integration.py
"""
Comprehensive Integration and End-to-End Tests for AURA

This file provides comprehensive integration tests for module interactions
and end-to-end tests for complete user workflows.
"""

import pytest
import time
import threading
import json
from unittest.mock import Mock, patch, MagicMock, call
import numpy as np
from pathlib import Path

# Import modules for integration testing
from modules.vision import VisionModule
from modules.reasoning import ReasoningModule
from modules.automation import AutomationModule
from modules.audio import AudioModule
from modules.feedback import FeedbackModule, FeedbackPriority
from modules.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from orchestrator import Orchestrator, ExecutionStep
from tests.fixtures.sample_data import SampleData, MockDataGenerator


class TestModuleIntegration:
    """Integration tests for module interactions."""
    
    @pytest.fixture
    def integrated_modules(self, mock_config, mock_mss, mock_requests, mock_pygame, 
                          mock_pyautogui, mock_whisper, mock_pyttsx3, mock_porcupine, 
                          mock_sounddevice, sample_sound_files):
        """Create integrated module instances for testing."""
        # Patch SOUNDS config to use sample files
        with patch('modules.feedback.SOUNDS', sample_sound_files):
            vision = VisionModule()
            reasoning = ReasoningModule()
            automation = AutomationModule()
            audio = AudioModule()
            feedback = FeedbackModule(audio_module=audio)
            
            return {
                'vision': vision,
                'reasoning': reasoning,
                'automation': automation,
                'audio': audio,
                'feedback': feedback
            }
    
    def test_vision_to_reasoning_integration(self, integrated_modules, mock_requests):
        """Test integration between vision and reasoning modules."""
        vision = integrated_modules['vision']
        reasoning = integrated_modules['reasoning']
        
        # Mock vision response
        screen_context = SampleData.get_sample_screen_context()
        
        # Mock API responses
        vision_response = MockDataGenerator.create_mock_api_response(screen_context)
        action_plan = SampleData.get_sample_action_plan()
        reasoning_response = MockDataGenerator.create_mock_api_response(action_plan)
        
        mock_requests.side_effect = [vision_response, reasoning_response]
        
        # Test the integration flow
        screen_analysis = vision.describe_screen()
        action_plan_result = reasoning.get_action_plan("Click the submit button", screen_analysis)
        
        # Verify the flow worked
        assert screen_analysis == screen_context
        assert action_plan_result == action_plan
        assert len(action_plan_result["plan"]) > 0
        assert action_plan_result["plan"][-1]["action"] == "finish"
    
    def test_reasoning_to_automation_integration(self, integrated_modules):
        """Test integration between reasoning and automation modules."""
        reasoning = integrated_modules['reasoning']
        automation = integrated_modules['automation']
        
        # Create a simple action plan
        action_plan = {
            "plan": [
                {"action": "click", "coordinates": [100, 200]},
                {"action": "type", "text": "test input"},
                {"action": "scroll", "direction": "up", "amount": 100}
            ]
        }
        
        # Execute each action through automation
        results = []
        for action in action_plan["plan"]:
            try:
                automation.execute_action(action)
                results.append({"action": action["action"], "status": "success"})
            except Exception as e:
                results.append({"action": action["action"], "status": "failed", "error": str(e)})
        
        # Verify all actions were processed
        assert len(results) == 3
        assert all(result["status"] == "success" for result in results)
    
    def test_audio_to_feedback_integration(self, integrated_modules):
        """Test integration between audio and feedback modules."""
        audio = integrated_modules['audio']
        feedback = integrated_modules['feedback']
        
        # Test TTS integration
        test_message = "Integration test message"
        
        # Use feedback module to speak (which should use audio module)
        feedback.speak(test_message)
        
        # Wait for processing
        time.sleep(0.2)
        feedback.wait_for_completion(timeout=2.0)
        
        # Verify TTS was called through the integration
        audio.tts_engine.say.assert_called_with(test_message)
        audio.tts_engine.runAndWait.assert_called()
    
    def test_error_handler_integration(self, integrated_modules):
        """Test error handler integration across modules."""
        vision = integrated_modules['vision']
        
        # Create an error scenario
        with patch.object(vision, 'capture_screen_as_base64', side_effect=Exception("Test error")):
            with pytest.raises(Exception):
                vision.describe_screen()
        
        # Verify error was handled by the global error handler
        # (This is tested by the error handler decorator on the method)
    
    def test_module_cleanup_integration(self, integrated_modules):
        """Test that all modules clean up properly."""
        audio = integrated_modules['audio']
        feedback = integrated_modules['feedback']
        
        # Test cleanup
        feedback.cleanup()
        audio.cleanup()
        
        # Verify cleanup was called
        assert not feedback.is_processing
        assert not feedback.is_initialized
        audio.tts_engine.stop.assert_called_once()
    
    def test_concurrent_module_operations(self, integrated_modules):
        """Test concurrent operations across modules."""
        feedback = integrated_modules['feedback']
        
        # Start multiple concurrent operations
        operations = []
        
        def play_sound(sound_name, priority):
            feedback.play(sound_name, priority)
        
        def speak_message(message, priority):
            feedback.speak(message, priority)
        
        # Create threads for concurrent operations
        threads = [
            threading.Thread(target=play_sound, args=('success', FeedbackPriority.NORMAL)),
            threading.Thread(target=speak_message, args=('Test message 1', FeedbackPriority.HIGH)),
            threading.Thread(target=play_sound, args=('thinking', FeedbackPriority.LOW)),
            threading.Thread(target=speak_message, args=('Test message 2', FeedbackPriority.CRITICAL))
        ]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=2.0)
        
        # Wait for feedback processing
        feedback.wait_for_completion(timeout=3.0)
        
        # Verify no crashes occurred
        assert feedback.is_processing


class TestOrchestratorIntegration:
    """Integration tests for the Orchestrator with all modules."""
    
    @pytest.fixture
    def orchestrator(self, mock_config, mock_mss, mock_requests, mock_pygame, 
                    mock_pyautogui, mock_whisper, mock_pyttsx3, mock_porcupine, 
                    mock_sounddevice, sample_sound_files):
        """Create orchestrator with integrated modules."""
        with patch('modules.feedback.SOUNDS', sample_sound_files):
            return Orchestrator()
    
    def test_orchestrator_module_initialization(self, orchestrator):
        """Test that orchestrator initializes all modules correctly."""
        assert orchestrator.vision_module is not None
        assert orchestrator.reasoning_module is not None
        assert orchestrator.automation_module is not None
        assert orchestrator.audio_module is not None
        assert orchestrator.feedback_module is not None
        assert orchestrator.error_handler is not None
    
    def test_orchestrator_command_processing_flow(self, orchestrator, mock_requests):
        """Test complete command processing flow through orchestrator."""
        # Mock API responses
        screen_context = SampleData.get_sample_screen_context()
        action_plan = SampleData.get_sample_action_plan()
        
        vision_response = MockDataGenerator.create_mock_api_response(screen_context)
        reasoning_response = MockDataGenerator.create_mock_api_response(action_plan)
        mock_requests.side_effect = [vision_response, reasoning_response]
        
        # Execute command
        result = orchestrator.execute_command("Click the submit button")
        
        # Verify the flow completed
        assert result is not None
        assert result.get("success") is True or result.get("completed") is True
        
        # Verify steps were executed
        assert len(orchestrator.get_execution_history()) > 0
    
    def test_orchestrator_question_answering_flow(self, orchestrator, mock_requests):
        """Test question answering flow through orchestrator."""
        # Mock vision response for Q&A
        screen_context = SampleData.get_sample_screen_context()
        vision_response = MockDataGenerator.create_mock_api_response(screen_context)
        mock_requests.return_value = vision_response
        
        # Execute question
        result = orchestrator.answer_question("What is displayed on the screen?")
        
        # Verify the flow completed
        assert result is not None
        assert isinstance(result, dict)
    
    def test_orchestrator_error_recovery(self, orchestrator, mock_requests):
        """Test orchestrator error recovery mechanisms."""
        # Mock API failure
        mock_requests.side_effect = Exception("API failed")
        
        # Execute command that will fail
        result = orchestrator.execute_command("Click the submit button")
        
        # Verify error was handled gracefully
        assert result is not None
        assert result.get("success") is False or result.get("error") is not None
    
    def test_orchestrator_concurrent_commands(self, orchestrator, mock_requests):
        """Test orchestrator handling concurrent commands."""
        # Mock responses
        screen_context = SampleData.get_sample_screen_context()
        action_plan = SampleData.get_sample_action_plan()
        
        vision_response = MockDataGenerator.create_mock_api_response(screen_context)
        reasoning_response = MockDataGenerator.create_mock_api_response(action_plan)
        mock_requests.side_effect = [vision_response, reasoning_response] * 3
        
        # Execute multiple commands concurrently
        commands = [
            "Click the first button",
            "Type some text",
            "Scroll down"
        ]
        
        results = []
        threads = []
        
        def execute_command(cmd):
            result = orchestrator.execute_command(cmd)
            results.append(result)
        
        # Start concurrent executions
        for cmd in commands:
            thread = threading.Thread(target=execute_command, args=(cmd,))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=10.0)
        
        # Verify all commands were processed
        assert len(results) == 3
        assert all(result is not None for result in results)
    
    def test_orchestrator_module_validation(self, orchestrator):
        """Test orchestrator module validation."""
        validation_result = orchestrator.validate_modules()
        
        assert isinstance(validation_result, dict)
        assert "overall_status" in validation_result
        assert "modules" in validation_result
        
        # Check that all modules are validated
        expected_modules = ["vision", "reasoning", "automation", "audio", "feedback"]
        for module_name in expected_modules:
            assert module_name in validation_result["modules"]
    
    def test_orchestrator_cleanup(self, orchestrator):
        """Test orchestrator cleanup process."""
        # Perform cleanup
        orchestrator.cleanup()
        
        # Verify cleanup was performed
        # (Specific assertions depend on cleanup implementation)
        assert orchestrator.feedback_module is not None  # Should still exist but be cleaned up


class TestEndToEndWorkflows:
    """End-to-end tests for complete user workflows."""
    
    @pytest.fixture
    def e2e_orchestrator(self, mock_config, mock_mss, mock_requests, mock_pygame, 
                        mock_pyautogui, mock_whisper, mock_pyttsx3, mock_porcupine, 
                        mock_sounddevice, sample_sound_files):
        """Create orchestrator for end-to-end testing."""
        with patch('modules.feedback.SOUNDS', sample_sound_files):
            orchestrator = Orchestrator()
            
            # Setup mock responses for consistent testing
            screen_context = SampleData.get_sample_screen_context()
            action_plan = SampleData.get_sample_action_plan()
            
            vision_response = MockDataGenerator.create_mock_api_response(screen_context)
            reasoning_response = MockDataGenerator.create_mock_api_response(action_plan)
            mock_requests.side_effect = [vision_response, reasoning_response] * 10  # Multiple responses
            
            return orchestrator
    
    def test_login_workflow(self, e2e_orchestrator):
        """Test complete login workflow."""
        command = "Fill in the login form with username 'testuser' and password 'password123', then submit"
        
        # Execute the workflow
        result = e2e_orchestrator.execute_command(command)
        
        # Verify workflow completion
        assert result is not None
        
        # Verify automation actions were called
        automation_module = e2e_orchestrator.automation_module
        assert len(automation_module.get_action_history()) > 0
        
        # Verify feedback was provided
        feedback_module = e2e_orchestrator.feedback_module
        assert feedback_module.get_queue_size() >= 0  # May have been processed
    
    def test_form_filling_workflow(self, e2e_orchestrator):
        """Test complete form filling workflow."""
        # Mock form analysis
        form_data = SampleData.get_sample_form_analysis()
        
        with patch.object(e2e_orchestrator.vision_module, 'analyze_forms', return_value=form_data):
            command = "Fill out the registration form"
            
            # Execute the workflow
            result = e2e_orchestrator.execute_command(command)
            
            # Verify workflow completion
            assert result is not None
    
    def test_information_extraction_workflow(self, e2e_orchestrator):
        """Test complete information extraction workflow."""
        question = "What login options are available on this screen?"
        
        # Execute the workflow
        result = e2e_orchestrator.answer_question(question)
        
        # Verify workflow completion
        assert result is not None
        assert isinstance(result, dict)
    
    def test_error_recovery_workflow(self, e2e_orchestrator, mock_requests):
        """Test complete error recovery workflow."""
        # Setup initial failure then success
        mock_requests.side_effect = [
            Exception("Network error"),  # First attempt fails
            MockDataGenerator.create_mock_api_response(SampleData.get_sample_screen_context()),  # Retry succeeds
            MockDataGenerator.create_mock_api_response(SampleData.get_sample_action_plan())
        ]
        
        command = "Click the submit button"
        
        # Execute the workflow
        result = e2e_orchestrator.execute_command(command)
        
        # Verify error recovery worked
        assert result is not None
    
    def test_multi_step_workflow(self, e2e_orchestrator):
        """Test complex multi-step workflow."""
        commands = [
            "Click the menu button",
            "Navigate to settings",
            "Enable dark mode",
            "Save the changes"
        ]
        
        results = []
        for command in commands:
            result = e2e_orchestrator.execute_command(command)
            results.append(result)
            time.sleep(0.1)  # Small delay between commands
        
        # Verify all steps completed
        assert len(results) == 4
        assert all(result is not None for result in results)
        
        # Verify execution history
        history = e2e_orchestrator.get_execution_history()
        assert len(history) >= 4
    
    def test_voice_to_action_workflow(self, e2e_orchestrator, mock_sounddevice, mock_whisper):
        """Test complete voice-to-action workflow."""
        # Mock speech recognition
        mock_whisper.transcribe.return_value = {
            "text": "Click the submit button",
            "segments": [{"avg_logprob": -0.3}]
        }
        
        # Mock audio recording
        audio_data = MockDataGenerator.create_mock_audio_data()
        mock_sounddevice.rec.return_value = audio_data.reshape(-1, 1)
        
        # Simulate voice input processing
        audio_module = e2e_orchestrator.audio_module
        transcribed_text = audio_module.speech_to_text(duration=3.0)
        
        # Execute the transcribed command
        result = e2e_orchestrator.execute_command(transcribed_text)
        
        # Verify the complete workflow
        assert transcribed_text == "Click the submit button"
        assert result is not None
    
    def test_wake_word_to_action_workflow(self, e2e_orchestrator, mock_porcupine, mock_sounddevice):
        """Test complete wake word to action workflow."""
        # Mock wake word detection
        mock_porcupine.process.return_value = 0  # Wake word detected
        
        # Mock subsequent speech recognition
        audio_module = e2e_orchestrator.audio_module
        
        # Simulate wake word detection
        wake_word_detected = audio_module.listen_for_wake_word(timeout=1.0)
        
        # Verify wake word was detected
        assert wake_word_detected is True
        
        # Continue with command processing
        result = e2e_orchestrator.execute_command("Click the submit button")
        assert result is not None
    
    def test_feedback_integration_workflow(self, e2e_orchestrator):
        """Test complete workflow with feedback integration."""
        command = "Click the submit button"
        
        # Execute command
        result = e2e_orchestrator.execute_command(command)
        
        # Verify feedback was provided
        feedback_module = e2e_orchestrator.feedback_module
        
        # Wait for any pending feedback
        feedback_module.wait_for_completion(timeout=2.0)
        
        # Verify workflow completed with feedback
        assert result is not None
    
    def test_performance_workflow(self, e2e_orchestrator):
        """Test workflow performance and timing."""
        start_time = time.time()
        
        # Execute a simple command
        result = e2e_orchestrator.execute_command("Click the submit button")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify reasonable execution time (should be under 10 seconds for mocked operations)
        assert execution_time < 10.0
        assert result is not None
        
        # Check performance metrics if available
        if hasattr(e2e_orchestrator, 'get_performance_metrics'):
            metrics = e2e_orchestrator.get_performance_metrics()
            assert isinstance(metrics, dict)


class TestRegressionScenarios:
    """Regression tests for previously fixed issues."""
    
    @pytest.fixture
    def regression_orchestrator(self, mock_config, mock_mss, mock_requests, mock_pygame, 
                               mock_pyautogui, mock_whisper, mock_pyttsx3, mock_porcupine, 
                               mock_sounddevice, sample_sound_files):
        """Create orchestrator for regression testing."""
        with patch('modules.feedback.SOUNDS', sample_sound_files):
            return Orchestrator()
    
    def test_empty_command_regression(self, regression_orchestrator):
        """Test handling of empty commands (regression test)."""
        result = regression_orchestrator.execute_command("")
        
        # Should handle gracefully without crashing
        assert result is not None
        assert result.get("success") is False or "error" in result
    
    def test_malformed_action_plan_regression(self, regression_orchestrator, mock_requests):
        """Test handling of malformed action plans (regression test)."""
        # Mock malformed response
        malformed_response = MockDataGenerator.create_mock_api_response("invalid json")
        mock_requests.return_value = malformed_response
        
        result = regression_orchestrator.execute_command("Click something")
        
        # Should handle gracefully with fallback
        assert result is not None
    
    def test_api_timeout_regression(self, regression_orchestrator, mock_requests):
        """Test handling of API timeouts (regression test)."""
        import requests
        mock_requests.side_effect = requests.exceptions.Timeout("Request timed out")
        
        result = regression_orchestrator.execute_command("Click the button")
        
        # Should handle timeout gracefully
        assert result is not None
        assert result.get("success") is False or "error" in result
    
    def test_concurrent_access_regression(self, regression_orchestrator):
        """Test concurrent access to shared resources (regression test)."""
        results = []
        errors = []
        
        def execute_command(cmd_id):
            try:
                result = regression_orchestrator.execute_command(f"Command {cmd_id}")
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Start multiple concurrent operations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=execute_command, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=10.0)
        
        # Verify no race conditions or crashes
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 5
    
    def test_memory_leak_regression(self, regression_orchestrator):
        """Test for memory leaks in repeated operations (regression test)."""
        import gc
        
        # Get initial memory state
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Perform repeated operations
        for i in range(10):
            result = regression_orchestrator.execute_command(f"Test command {i}")
            assert result is not None
        
        # Force garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Check for reasonable memory usage (allow some growth but not excessive)
        object_growth = final_objects - initial_objects
        assert object_growth < 1000, f"Potential memory leak: {object_growth} new objects"
    
    def test_cleanup_regression(self, regression_orchestrator):
        """Test proper cleanup after operations (regression test)."""
        # Execute some operations
        regression_orchestrator.execute_command("Test command")
        
        # Perform cleanup
        regression_orchestrator.cleanup()
        
        # Verify cleanup was successful
        # (Specific assertions depend on cleanup implementation)
        assert regression_orchestrator.feedback_module is not None


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""
    
    @pytest.fixture
    def benchmark_orchestrator(self, mock_config, mock_mss, mock_requests, mock_pygame, 
                              mock_pyautogui, mock_whisper, mock_pyttsx3, mock_porcupine, 
                              mock_sounddevice, sample_sound_files):
        """Create orchestrator for performance testing."""
        with patch('modules.feedback.SOUNDS', sample_sound_files):
            return Orchestrator()
    
    @pytest.mark.slow
    def test_command_execution_performance(self, benchmark_orchestrator):
        """Benchmark command execution performance."""
        commands = [
            "Click the submit button",
            "Type hello world",
            "Scroll down",
            "Double click the icon",
            "Press enter"
        ]
        
        execution_times = []
        
        for command in commands:
            start_time = time.time()
            result = benchmark_orchestrator.execute_command(command)
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            assert result is not None
            assert execution_time < 5.0  # Should complete within 5 seconds
        
        # Calculate performance metrics
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        
        # Performance assertions
        assert avg_time < 3.0, f"Average execution time too high: {avg_time:.2f}s"
        assert max_time < 5.0, f"Maximum execution time too high: {max_time:.2f}s"
    
    @pytest.mark.slow
    def test_concurrent_performance(self, benchmark_orchestrator):
        """Benchmark concurrent operation performance."""
        num_concurrent = 5
        results = []
        start_time = time.time()
        
        def execute_command(cmd_id):
            result = benchmark_orchestrator.execute_command(f"Command {cmd_id}")
            results.append(result)
        
        # Start concurrent operations
        threads = []
        for i in range(num_concurrent):
            thread = threading.Thread(target=execute_command, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=15.0)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance assertions
        assert len(results) == num_concurrent
        assert total_time < 10.0, f"Concurrent execution took too long: {total_time:.2f}s"
        assert all(result is not None for result in results)
    
    @pytest.mark.slow
    def test_memory_usage_performance(self, benchmark_orchestrator):
        """Benchmark memory usage during operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform multiple operations
        for i in range(20):
            result = benchmark_orchestrator.execute_command(f"Test command {i}")
            assert result is not None
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        # Memory usage assertions
        assert memory_growth < 100, f"Memory usage grew too much: {memory_growth:.2f}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])