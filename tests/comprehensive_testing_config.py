"""
Comprehensive Testing Configuration

Configuration settings for the comprehensive testing suite that validates
Task 4.0 requirements including unit test coverage, backward compatibility,
and performance monitoring.
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class TestingThresholds:
    """Testing thresholds and limits."""
    # Performance thresholds
    max_gui_execution_time: float = 2.0  # seconds
    max_conversation_execution_time: float = 3.0  # seconds
    max_deferred_action_setup_time: float = 5.0  # seconds
    max_intent_recognition_time: float = 0.5  # seconds
    
    # Memory usage thresholds
    max_handler_memory_usage: float = 50.0  # MB
    max_conversation_memory_usage: float = 30.0  # MB
    max_deferred_action_memory_usage: float = 100.0  # MB
    
    # Success rate thresholds
    min_unit_test_success_rate: float = 0.8  # 80%
    min_compatibility_success_rate: float = 0.9  # 90%
    min_performance_success_rate: float = 0.8  # 80%
    min_overall_success_rate: float = 0.85  # 85%
    
    # Regression detection thresholds
    performance_regression_threshold: float = 20.0  # 20% increase
    memory_regression_threshold: float = 25.0  # 25% increase
    success_rate_regression_threshold: float = 10.0  # 10% decrease


@dataclass
class TestConfiguration:
    """Test configuration settings."""
    # Test execution settings
    verbose_output: bool = True
    save_detailed_reports: bool = True
    generate_performance_graphs: bool = False
    run_stress_tests: bool = False
    
    # Test coverage settings
    require_all_handlers_tested: bool = True
    require_intent_recognition_tested: bool = True
    require_concurrency_tested: bool = True
    require_error_handling_tested: bool = True
    
    # Backward compatibility settings
    test_all_gui_commands: bool = True
    test_question_answering: bool = True
    test_audio_feedback: bool = True
    test_existing_workflows: bool = True
    
    # Performance monitoring settings
    monitor_execution_time: bool = True
    monitor_memory_usage: bool = True
    monitor_cpu_usage: bool = True
    detect_performance_regressions: bool = True
    
    # Reporting settings
    generate_json_report: bool = True
    generate_html_report: bool = False
    send_email_report: bool = False
    
    # Test data settings
    use_mock_data: bool = True
    mock_api_responses: bool = True
    simulate_real_conditions: bool = False


# Default testing configuration
DEFAULT_CONFIG = TestConfiguration()

# Default testing thresholds
DEFAULT_THRESHOLDS = TestingThresholds()

# Test suite definitions
TEST_SUITES = {
    'unit_tests': {
        'description': 'Comprehensive unit test coverage for all handler classes',
        'requirements': ['9.1', '9.2', '9.3', '9.4'],
        'test_classes': [
            'TestBaseHandler',
            'TestGUIHandler', 
            'TestConversationHandler',
            'TestDeferredActionHandler',
            'TestIntentRecognitionAndRouting',
            'TestConcurrencyAndLockManagement',
            'TestContentGenerationAndCleaning',
            'TestErrorHandlingAndRecovery'
        ],
        'min_success_rate': 0.8,
        'max_execution_time': 300  # 5 minutes
    },
    'backward_compatibility': {
        'description': 'Validate backward compatibility and system integration',
        'requirements': ['10.1', '10.2', '10.3', '10.4', '10.5'],
        'test_classes': [
            'TestBackwardCompatibilityGUICommands',
            'TestBackwardCompatibilityQuestionAnswering',
            'TestBackwardCompatibilityAudioFeedback',
            'TestSystemIntegrationPreservation',
            'TestPerformanceRegressionPrevention',
            'TestExistingWorkflowPreservation'
        ],
        'min_success_rate': 0.9,
        'max_execution_time': 600  # 10 minutes
    },
    'performance_monitoring': {
        'description': 'Performance optimization and monitoring',
        'requirements': ['9.5'],
        'test_classes': [
            'TestHandlerPerformanceMonitoring',
            'TestIntentRecognitionPerformance',
            'TestMemoryUsageMonitoring',
            'TestExecutionTimeOptimization',
            'TestPerformanceRegressionDetection'
        ],
        'min_success_rate': 0.8,
        'max_execution_time': 900  # 15 minutes
    }
}

# Performance benchmarks for different operations
PERFORMANCE_BENCHMARKS = {
    'gui_operations': {
        'click_command': {'max_time': 1.0, 'max_memory': 20.0},
        'type_command': {'max_time': 1.5, 'max_memory': 25.0},
        'scroll_command': {'max_time': 0.8, 'max_memory': 15.0},
        'complex_command': {'max_time': 3.0, 'max_memory': 40.0}
    },
    'conversation_operations': {
        'simple_query': {'max_time': 2.0, 'max_memory': 20.0},
        'complex_query': {'max_time': 4.0, 'max_memory': 35.0},
        'context_query': {'max_time': 3.0, 'max_memory': 30.0}
    },
    'deferred_actions': {
        'code_generation': {'max_time': 8.0, 'max_memory': 80.0},
        'text_generation': {'max_time': 6.0, 'max_memory': 60.0},
        'content_cleaning': {'max_time': 2.0, 'max_memory': 40.0}
    },
    'intent_recognition': {
        'simple_intent': {'max_time': 0.3, 'max_memory': 10.0},
        'complex_intent': {'max_time': 0.8, 'max_memory': 20.0},
        'parameter_extraction': {'max_time': 0.5, 'max_memory': 15.0}
    }
}

# Test data for various scenarios
TEST_DATA = {
    'gui_commands': [
        "click the submit button",
        "type hello world",
        "scroll down",
        "press enter",
        "double-click the file",
        "right-click the item",
        "click the red button",
        'type "user@example.com"',
        "scroll to the bottom",
        "click button with text 'Continue'"
    ],
    'conversation_queries': [
        "Hello, how are you?",
        "What can you help me with?",
        "Tell me a joke",
        "How's the weather?",
        "What time is it?",
        "Good morning",
        "Thank you",
        "Goodbye",
        "Can you explain this?",
        "What are your capabilities?"
    ],
    'deferred_action_requests': [
        ("Write a Python function for sorting", "code"),
        ("Create an email template", "text"),
        ("Generate a summary", "text"),
        ("Write a SQL query", "code"),
        ("Create a list of items", "text"),
        ("Write JavaScript code", "code"),
        ("Draft a letter", "text"),
        ("Generate documentation", "text")
    ],
    'question_answering_queries': [
        "What does this page say?",
        "Summarize this document",
        "What's the main content here?",
        "Read me the text on screen",
        "What information is displayed?",
        "Tell me about this PDF",
        "What's in this email?",
        "Describe what you see"
    ]
}

# Error scenarios for testing error handling
ERROR_SCENARIOS = {
    'module_unavailable': {
        'description': 'Test behavior when required modules are unavailable',
        'scenarios': [
            'accessibility_module_missing',
            'automation_module_missing',
            'vision_module_missing',
            'reasoning_module_missing',
            'audio_module_missing'
        ]
    },
    'api_failures': {
        'description': 'Test behavior when API calls fail',
        'scenarios': [
            'reasoning_api_timeout',
            'reasoning_api_error',
            'vision_api_failure',
            'accessibility_api_failure'
        ]
    },
    'resource_constraints': {
        'description': 'Test behavior under resource constraints',
        'scenarios': [
            'low_memory_condition',
            'high_cpu_usage',
            'network_unavailable',
            'disk_space_low'
        ]
    },
    'concurrency_issues': {
        'description': 'Test behavior under concurrent access',
        'scenarios': [
            'multiple_deferred_actions',
            'concurrent_gui_commands',
            'lock_timeout_scenarios',
            'race_condition_tests'
        ]
    }
}

# Compliance requirements mapping
COMPLIANCE_REQUIREMENTS = {
    'task_4_0': {
        'description': 'Implement comprehensive unit test coverage',
        'requirements': [
            'Write unit tests for all handler classes (GUI, Conversation, DeferredAction)',
            'Add tests for intent recognition accuracy and routing logic',
            'Implement concurrency testing for deferred actions and lock management',
            'Add content generation and cleaning validation tests',
            'Include error handling and recovery scenario testing'
        ],
        'success_criteria': {
            'min_test_coverage': 0.8,
            'min_success_rate': 0.8,
            'max_execution_time': 600
        }
    },
    'task_4_1': {
        'description': 'Validate backward compatibility and system integration',
        'requirements': [
            'Test all existing AURA commands to ensure identical behavior',
            'Validate GUI automation functionality preservation',
            'Test question answering with both fast path and vision fallback',
            'Verify audio feedback and user experience consistency',
            'Ensure no performance regressions in existing functionality'
        ],
        'success_criteria': {
            'min_compatibility_rate': 0.9,
            'max_performance_regression': 0.2,
            'min_success_rate': 0.9
        }
    },
    'task_4_2': {
        'description': 'Performance optimization and monitoring',
        'requirements': [
            'Implement performance monitoring for all handler types',
            'Add metrics collection for intent recognition speed and accuracy',
            'Monitor memory usage and resource consumption of new architecture',
            'Optimize handler execution times and system responsiveness',
            'Add performance regression detection and alerting'
        ],
        'success_criteria': {
            'max_execution_time_regression': 0.2,
            'max_memory_usage_regression': 0.25,
            'min_performance_monitoring_coverage': 0.8
        }
    }
}


def get_test_config() -> TestConfiguration:
    """Get the current test configuration."""
    return DEFAULT_CONFIG


def get_test_thresholds() -> TestingThresholds:
    """Get the current testing thresholds."""
    return DEFAULT_THRESHOLDS


def get_test_suite_config(suite_name: str) -> Dict[str, Any]:
    """Get configuration for a specific test suite."""
    return TEST_SUITES.get(suite_name, {})


def get_performance_benchmark(category: str, operation: str) -> Dict[str, float]:
    """Get performance benchmark for a specific operation."""
    return PERFORMANCE_BENCHMARKS.get(category, {}).get(operation, {})


def get_test_data(category: str) -> List[Any]:
    """Get test data for a specific category."""
    return TEST_DATA.get(category, [])


def get_error_scenarios(category: str) -> Dict[str, Any]:
    """Get error scenarios for testing."""
    return ERROR_SCENARIOS.get(category, {})


def get_compliance_requirements(task: str) -> Dict[str, Any]:
    """Get compliance requirements for a specific task."""
    return COMPLIANCE_REQUIREMENTS.get(task, {})