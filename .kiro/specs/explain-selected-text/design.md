# Design Document

## Overview

The "Explain Selected Text" feature extends AURA's capabilities by enabling users to select text in any macOS application and receive spoken explanations through voice commands. This feature integrates seamlessly with AURA's existing architecture, utilizing the established handler pattern, accessibility modules, and reasoning capabilities.

The design follows a two-tiered approach for text capture: primary accessibility API access with clipboard simulation fallback, ensuring robust functionality across applications with varying accessibility support levels.

## Architecture

### System Integration

The feature integrates into AURA's existing modular architecture:

```
User Voice Command
       ↓
   Orchestrator (Intent Recognition)
       ↓
ExplainSelectionHandler
       ↓
AccessibilityModule (Text Capture)
       ↓
ReasoningModule (Explanation Generation)
       ↓
FeedbackModule (Spoken Response)
```

### Handler Pattern Integration

Following AURA's established handler pattern, the feature implements:

- `ExplainSelectionHandler` inheriting from `BaseHandler`
- Integration with the orchestrator's intent recognition system
- Standardized error handling and result formatting
- Consistent logging and performance tracking

### Text Capture Strategy

The design implements a robust two-tier text capture approach:

1. **Primary Method**: Accessibility API

   - Direct access via `AXSelectedText` attribute
   - Fast, reliable for accessibility-compliant applications
   - No clipboard interference

2. **Fallback Method**: Clipboard Simulation
   - Preserves original clipboard content
   - Uses `Cmd+C` simulation via AutomationModule
   - Universal compatibility across all applications

## Components and Interfaces

### ExplainSelectionHandler

**Location**: `handlers/explain_selection_handler.py`

**Key Methods**:

- `handle(command: str, context: Dict[str, Any]) -> Dict[str, Any]`
- Inherits error handling and result formatting from `BaseHandler`

**Responsibilities**:

- Coordinate text capture and explanation workflow
- Handle edge cases (no text selected, capture failures)
- Provide appropriate user feedback
- Log performance metrics

### AccessibilityModule Extensions

**New Methods**:

- `get_selected_text() -> Optional[str]` - Main public interface
- `get_selected_text_via_accessibility() -> Optional[str]` - Primary method
- `get_selected_text_via_clipboard() -> Optional[str]` - Fallback method (delegated to AutomationModule)

**Integration Points**:

- Utilizes existing accessibility API infrastructure
- Leverages current error handling and logging systems
- Maintains compatibility with existing caching mechanisms

### AutomationModule Extensions

**New Methods**:

- `get_selected_text_via_clipboard() -> Optional[str]` - Clipboard-based capture
- `_preserve_clipboard_content() -> str` - Utility for clipboard preservation
- `_restore_clipboard_content(content: str) -> None` - Utility for clipboard restoration

**Dependencies**:

- `pyperclip` library for clipboard operations
- Existing `Cmd+C` automation capabilities
- Current error handling and retry mechanisms

### Configuration Extensions

**New Configuration Variables**:

```python
# Intent recognition update
INTENT_RECOGNITION_PROMPT = """
...existing intents...
- "explain_selected_text": User has highlighted text and is asking for an explanation, summary, or definition of it.
...
"""

# Explanation prompt template
EXPLAIN_TEXT_PROMPT = """
You are AURA, a helpful AI assistant. Please provide a clear and concise explanation of the following text. The explanation should be in simple language.

Text to explain:
---
{selected_text}
---
"""
```

## Data Models

### Text Capture Result

```python
@dataclass
class TextCaptureResult:
    """Result from text capture operations."""
    text: Optional[str]
    method_used: str  # "accessibility_api" | "clipboard_fallback"
    success: bool
    error_message: Optional[str] = None
    capture_time_ms: float = 0.0
```

### Explanation Request

```python
@dataclass
class ExplanationRequest:
    """Request for text explanation."""
    selected_text: str
    context: Dict[str, Any]
    timestamp: float
    source_application: Optional[str] = None
```

### Handler Context Extensions

The existing handler context will be extended to include:

```python
{
    "intent": {
        "intent": "explain_selected_text",
        "confidence": float,
        "parameters": {
            "action_type": "explain_text",
            "target": "selected text content",
            "content_type": "explanation"
        }
    },
    "execution_id": str,
    "timestamp": float,
    "system_state": Dict[str, Any]
}
```

## Error Handling

### Error Categories

1. **Text Capture Errors**

   - No text selected
   - Accessibility API unavailable
   - Clipboard operation failures
   - Permission issues

2. **Explanation Generation Errors**

   - Reasoning module unavailable
   - API timeout or failure
   - Empty or invalid response

3. **System Integration Errors**
   - Handler initialization failures
   - Intent recognition failures
   - Feedback module issues

### Error Recovery Strategy

```python
def handle_text_capture_error(self, error: Exception) -> Dict[str, Any]:
    """
    Error recovery strategy:
    1. Try accessibility API first
    2. Fall back to clipboard method
    3. Provide clear user feedback
    4. Log for debugging
    """
```

### User Feedback for Errors

- **No text selected**: "I couldn't find any selected text. Please highlight some text and try your command again."
- **Capture failure**: "I'm having trouble accessing the selected text. Please try selecting the text again."
- **Explanation failure**: "I encountered an issue generating an explanation. Please try again."

## Testing Strategy

### Unit Tests

1. **Text Capture Testing**

   - Mock accessibility API responses
   - Test clipboard preservation/restoration
   - Validate error handling for each method

2. **Handler Testing**

   - Test intent recognition integration
   - Validate error result formatting
   - Test performance logging

3. **Integration Testing**
   - Test with various applications
   - Validate fallback mechanism
   - Test edge cases (empty text, special characters)

### Application Testing Matrix

| Application Type | Primary Method    | Fallback Expected | Test Cases                      |
| ---------------- | ----------------- | ----------------- | ------------------------------- |
| Web Browsers     | Accessibility API | Rarely            | HTML content, JavaScript text   |
| PDF Readers      | Accessibility API | Sometimes         | Formatted text, images          |
| Text Editors     | Accessibility API | Rarely            | Code, plain text, special chars |
| Native Apps      | Mixed             | Often             | Varies by app accessibility     |

### Performance Testing

- Text capture speed benchmarking
- Memory usage during clipboard operations
- Explanation generation timing
- End-to-end workflow performance

### Edge Case Testing

1. **Text Content Variations**

   - Very long text selections
   - Special characters and Unicode
   - Code snippets and technical content
   - Multiple languages

2. **System State Variations**

   - No text selected
   - Multiple text selections
   - Clipboard already in use
   - Accessibility permissions denied

3. **Application Compatibility**
   - Applications with poor accessibility support
   - Web applications vs native applications
   - Applications with custom text rendering

## Implementation Phases

### Phase 1: Core Text Capture (Requirements 1, 2)

- Implement accessibility API method
- Implement clipboard fallback method
- Create public interface method
- Basic error handling and logging

### Phase 2: Handler Integration (Requirements 4, 5)

- Create ExplainSelectionHandler class
- Integrate with orchestrator intent recognition
- Implement standardized error handling
- Add performance monitoring

### Phase 3: Explanation Generation (Requirement 3)

- Create explanation prompt template
- Integrate with ReasoningModule
- Implement contextual explanation logic
- Add explanation quality validation

### Phase 4: Testing and Refinement (All Requirements)

- Comprehensive application testing
- Performance optimization
- Edge case handling
- User experience refinement

## Security and Privacy Considerations

### Clipboard Security

- Temporary clipboard access only
- Original content always restored
- No persistent clipboard data storage
- Secure cleanup of temporary data

### Text Content Privacy

- Selected text not logged in detail
- Explanation requests use secure API channels
- No persistent storage of user text
- Configurable privacy modes

### Permission Handling

- Graceful degradation when accessibility permissions unavailable
- Clear user guidance for permission setup
- No unauthorized system access attempts
- Respect user privacy preferences

## Performance Considerations

### Optimization Strategies

- Cache accessibility API connections
- Minimize clipboard access time
- Parallel processing where possible
- Efficient error recovery

### Performance Targets

- Text capture: < 500ms for accessibility API
- Text capture: < 1000ms for clipboard fallback
- End-to-end explanation: < 10 seconds
- Memory usage: < 50MB additional overhead

### Monitoring and Metrics

- Capture method success rates
- Performance timing by application type
- Error frequency and recovery success
- User satisfaction indicators
