# Design Document

## Overview

This design document outlines the comprehensive system stabilization and refactoring plan for AURA. The design follows a phased approach that prioritizes system stability through proactive refactoring, systematic bug fixes, and foundational architecture improvements. The solution transforms the current monolithic Orchestrator into a modular, maintainable architecture while preserving all existing functionality.

## Architecture

### Current Architecture Analysis

The existing AURA system has several architectural challenges:

1. **Monolithic Orchestrator**: The `Orchestrator` class contains ~2000+ lines with mixed responsibilities
2. **Concurrency Issues**: Execution lock management causes deadlocks in deferred actions
3. **Content Quality Problems**: Generated content has formatting and duplication issues
4. **GUI Reliability Issues**: Basic commands like click and scroll fail intermittently
5. **Limited Intent Understanding**: Regex-based command classification is insufficient

### Target Architecture

The new architecture implements a **Handler-Based Command Processing System** with these key components:

```
┌─────────────────────────────────────────────────────────────┐
│                    AURA System Architecture                 │
├─────────────────────────────────────────────────────────────┤
│  User Input (Voice/Text)                                    │
│           ↓                                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Orchestrator                           │    │
│  │  - Intent Recognition                               │    │
│  │  - State Management                                 │    │
│  │  - Command Routing                                  │    │
│  │  - Execution Lock Management                        │    │
│  └─────────────────────────────────────────────────────┘    │
│           ↓                                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Handler Layer                          │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │    │
│  │  │ GUIHandler  │ │Conversation │ │ Deferred    │    │    │
│  │  │             │ │Handler      │ │ActionHandler│    │    │
│  │  │- Fast Path  │ │- Chat Logic │ │- Content    │    │    │
│  │  │- Vision     │ │- Personality│ │  Generation │    │    │
│  │  │  Fallback   │ │- Context    │ │- Mouse      │    │    │
│  │  │- Action     │ │  Management │ │  Listener   │    │    │
│  │  │  Execution  │ │             │ │- State Mgmt │    │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
│           ↓                                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Module Layer                           │    │
│  │  Vision | Reasoning | Automation | Audio | etc.     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Handler Base Class

```python
# handlers/base_handler.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseHandler(ABC):
    """Abstract base class for all command handlers."""

    def __init__(self, orchestrator_ref):
        self.orchestrator = orchestrator_ref
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def handle(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a command and return execution results.

        Args:
            command: The user command to process
            context: Additional context including intent recognition results

        Returns:
            Dictionary containing execution results and metadata
        """
        pass

    def _create_success_result(self, message: str, **kwargs) -> Dict[str, Any]:
        """Create a standardized success result."""
        return {
            "status": "success",
            "message": message,
            "timestamp": time.time(),
            **kwargs
        }

    def _create_error_result(self, message: str, **kwargs) -> Dict[str, Any]:
        """Create a standardized error result."""
        return {
            "status": "error",
            "message": message,
            "timestamp": time.time(),
            **kwargs
        }
```

### 2. GUI Handler

```python
# handlers/gui_handler.py
class GUIHandler(BaseHandler):
    """Handles GUI interaction commands with fast path and vision fallback."""

    def handle(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process GUI interaction commands using fast path with vision fallback.

        This method contains all the existing GUI automation logic from
        Orchestrator._execute_command_internal, organized and enhanced.
        """
        try:
            # Fast path attempt using accessibility API
            fast_path_result = self._attempt_fast_path(command, context)
            if fast_path_result["success"]:
                return self._create_success_result(
                    fast_path_result["message"],
                    method="fast_path",
                    execution_time=fast_path_result.get("execution_time")
                )

            # Vision fallback
            vision_result = self._attempt_vision_fallback(command, context)
            if vision_result["success"]:
                return self._create_success_result(
                    vision_result["message"],
                    method="vision_fallback",
                    execution_time=vision_result.get("execution_time")
                )

            return self._create_error_result(
                "Unable to execute GUI command using either fast path or vision"
            )

        except Exception as e:
            self.logger.error(f"GUI handler error: {e}")
            return self._create_error_result(f"GUI handler failed: {str(e)}")

    def _attempt_fast_path(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt fast path execution using accessibility API."""
        # Implementation migrated from existing Orchestrator logic
        pass

    def _attempt_vision_fallback(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to vision-based execution."""
        # Implementation migrated from existing Orchestrator logic
        pass
```

### 3. Conversation Handler

```python
# handlers/conversation_handler.py
class ConversationHandler(BaseHandler):
    """Handles conversational chat interactions."""

    def handle(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process conversational queries and provide natural responses."""
        try:
            # Use reasoning module with conversational prompt
            response = self.orchestrator.reasoning_module.process_query(
                query=command,
                prompt_template="CONVERSATIONAL_PROMPT",
                context=self._build_conversation_context()
            )

            # Speak the response
            self.orchestrator.audio_module.speak(response)

            # Update conversation history
            self._update_conversation_history(command, response)

            return self._create_success_result(
                "Conversational response provided",
                response=response,
                interaction_type="conversation"
            )

        except Exception as e:
            self.logger.error(f"Conversation handler error: {e}")
            return self._create_error_result(f"Conversation failed: {str(e)}")
```

### 4. Deferred Action Handler

```python
# handlers/deferred_action_handler.py
class DeferredActionHandler(BaseHandler):
    """Handles deferred action workflows for content generation."""

    def handle(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process deferred action requests."""
        try:
            # Generate content
            content = self._generate_content(command, context)

            # Clean and format content
            cleaned_content = self._clean_and_format_content(content, context)

            # Set up deferred action state
            self._setup_deferred_action_state(cleaned_content, context)

            # Start mouse listener
            self._start_mouse_listener()

            # Provide audio instructions
            self._provide_audio_instructions(context)

            return {
                "status": "waiting_for_user_action",
                "message": "Content generated, waiting for click location",
                "content_length": len(cleaned_content),
                "content_type": context.get("parameters", {}).get("content_type", "text")
            }

        except Exception as e:
            self.logger.error(f"Deferred action handler error: {e}")
            return self._create_error_result(f"Deferred action failed: {str(e)}")
```

### 5. Enhanced Orchestrator

The refactored Orchestrator becomes a lean coordinator:

```python
class Orchestrator:
    def __init__(self):
        # Initialize modules and handlers
        self._initialize_modules()
        self._initialize_handlers()

    def _initialize_handlers(self):
        """Initialize command handlers."""
        self.gui_handler = GUIHandler(self)
        self.conversation_handler = ConversationHandler(self)
        self.deferred_action_handler = DeferredActionHandler(self)

    def execute_command(self, command: str) -> Dict[str, Any]:
        """Main command execution with intent-based routing."""
        # Acquire execution lock
        with self.execution_lock:
            # Recognize intent
            intent_result = self._recognize_intent(command)

            # Route to appropriate handler
            handler = self._get_handler_for_intent(intent_result["intent"])

            # Execute with handler
            result = handler.handle(command, {
                "intent": intent_result,
                "timestamp": time.time()
            })

            # Handle special cases (deferred actions)
            if result.get("status") == "waiting_for_user_action":
                # Release lock early for deferred actions
                return result

            return result

    def _get_handler_for_intent(self, intent: str) -> BaseHandler:
        """Get the appropriate handler for an intent."""
        handler_map = {
            "gui_interaction": self.gui_handler,
            "conversational_chat": self.conversation_handler,
            "deferred_action": self.deferred_action_handler,
            "question_answering": self.gui_handler  # Reuse GUI handler for now
        }
        return handler_map.get(intent, self.gui_handler)  # Default to GUI
```

## Data Models

### Intent Recognition Result

```python
@dataclass
class IntentResult:
    intent: str  # gui_interaction, conversational_chat, deferred_action, question_answering
    confidence: float  # 0.0 to 1.0
    parameters: Dict[str, Any]  # Intent-specific parameters
    reasoning: str  # Explanation of classification
```

### Handler Context

```python
@dataclass
class HandlerContext:
    intent_result: IntentResult
    timestamp: float
    execution_id: str
    user_command: str
    system_state: Dict[str, Any]
```

### Deferred Action State

```python
@dataclass
class DeferredActionState:
    content: str
    content_type: str  # code, text, etc.
    start_time: float
    timeout_time: float
    mouse_listener_active: bool
    execution_id: str
```

## Error Handling

### Concurrency Management

The new design addresses concurrency issues through:

1. **Early Lock Release**: Deferred actions release the execution lock immediately after setup
2. **Timeout-based Locks**: All locks use timeouts to prevent indefinite blocking
3. **State Isolation**: Each handler manages its own state independently
4. **Graceful Interruption**: New commands can interrupt waiting states cleanly

```python
def execute_command(self, command: str) -> Dict[str, Any]:
    """Execute command with improved concurrency handling."""
    try:
        # Use timeout on execution lock
        if not self.execution_lock.acquire(timeout=30.0):
            return self._create_error_result("System busy, please try again")

        try:
            result = self._execute_with_routing(command)

            # Special handling for deferred actions
            if result.get("status") == "waiting_for_user_action":
                # Release lock immediately for deferred actions
                self.execution_lock.release()
                return result

            return result

        finally:
            # Ensure lock is released for non-deferred actions
            if self.execution_lock.locked():
                self.execution_lock.release()

    except Exception as e:
        # Always release lock on exception
        if self.execution_lock.locked():
            self.execution_lock.release()
        raise
```

### Content Quality Improvements

Content quality is enhanced through:

1. **Enhanced Prompts**: More specific instructions for formatting and structure
2. **Content Cleaning**: Comprehensive removal of unwanted prefixes and formatting
3. **Single-line Detection**: Automatic reformatting of improperly formatted code
4. **Timeout Management**: Removal of restrictive timeouts for content generation

````python
def _clean_and_format_content(self, content: str, context: Dict[str, Any]) -> str:
    """Clean and format generated content."""
    # Remove unwanted prefixes
    unwanted_prefixes = [
        "Here is the code:",
        "Here's the code:",
        "```python",
        "```javascript",
        "```",
        "The code is:",
        "Here is your code:"
    ]

    cleaned = content
    for prefix in unwanted_prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()

    # Remove unwanted suffixes
    unwanted_suffixes = ["```", "```python", "```javascript"]
    for suffix in unwanted_suffixes:
        if cleaned.endswith(suffix):
            cleaned = cleaned[:-len(suffix)].strip()

    # Format single-line code if needed
    if self._is_single_line_code(cleaned, context):
        cleaned = self._format_single_line_code(cleaned, context)

    return cleaned
````

### GUI Reliability Improvements

GUI reliability is enhanced through:

1. **Robust Application Detection**: AppleScript fallback for application identification
2. **Smart Scroll Targeting**: Automatic focus of scrollable areas before scrolling
3. **Enhanced Error Recovery**: Better error messages and recovery suggestions

```python
def _ensure_application_focus(self) -> Dict[str, Any]:
    """Ensure we can identify the focused application."""
    try:
        # Try primary method
        app_info = self.orchestrator.application_detector.get_active_application_info()
        if app_info and app_info.get("bundle_id"):
            return {"success": True, "app_info": app_info}
    except Exception as e:
        self.logger.warning(f"Primary app detection failed: {e}")

    # Fallback to AppleScript
    try:
        script = 'tell application "System Events" to get name of first process whose frontmost is true'
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            app_name = result.stdout.strip()
            return {
                "success": True,
                "app_info": {"name": app_name, "method": "applescript_fallback"}
            }
    except Exception as e:
        self.logger.error(f"AppleScript fallback failed: {e}")

    return {"success": False, "error": "Could not identify focused application"}
```

## Testing Strategy

### Unit Testing

Each handler will have comprehensive unit tests:

```python
# tests/test_gui_handler.py
class TestGUIHandler:
    def test_handle_click_command(self):
        """Test GUI handler processes click commands correctly."""

    def test_fast_path_fallback_to_vision(self):
        """Test fallback mechanism when fast path fails."""

    def test_error_handling(self):
        """Test error handling and recovery."""

# tests/test_deferred_action_handler.py
class TestDeferredActionHandler:
    def test_content_generation(self):
        """Test content generation and cleaning."""

    def test_mouse_listener_setup(self):
        """Test mouse listener initialization."""

    def test_concurrent_command_handling(self):
        """Test handling of commands during deferred action wait."""
```

### Integration Testing

Integration tests will verify:

1. **Handler Coordination**: Proper routing between handlers
2. **State Management**: Correct state transitions and cleanup
3. **Concurrency**: No deadlocks or race conditions
4. **Backward Compatibility**: All existing functionality preserved

### Performance Testing

Performance tests will measure:

1. **Intent Recognition Speed**: Classification time for different command types
2. **Handler Execution Time**: Performance of each handler type
3. **Memory Usage**: Memory footprint of new architecture
4. **Concurrency Performance**: Throughput under concurrent load

## Migration Strategy

### Phase 0: Refactoring Foundation

1. Create handler directory structure
2. Implement BaseHandler abstract class
3. Create empty handler classes with basic structure
4. Migrate GUI logic from Orchestrator to GUIHandler
5. Update Orchestrator to use handler routing

### Phase 1: Bug Fixes

1. Implement concurrency fixes in execution lock management
2. Enhance content generation and cleaning logic
3. Improve application detection and GUI reliability
4. Add comprehensive error handling and recovery

### Phase 2: Feature Enhancements

1. Implement intent recognition system
2. Add conversational chat capabilities
3. Enhance deferred action workflow
4. Implement audio responsiveness improvements

### Phase 3: Advanced Features

1. Add content comprehension fast path
2. Implement silence detection for audio
3. Add performance monitoring and optimization
4. Complete testing and validation

This design ensures a systematic, low-risk migration that preserves existing functionality while dramatically improving system architecture, reliability, and maintainability.
