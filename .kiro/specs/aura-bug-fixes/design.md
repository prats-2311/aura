# Design Document

## Overview

This design document outlines the technical approach to fix three critical bugs in the AURA system. The fixes focus on improving text formatting during typing, correcting intent recognition for simple commands, and resolving prompt length limits in screen summarization.

## Architecture

The fixes will be implemented across multiple modules:

1. **Automation Module** (`modules/automation.py`) - Text formatting fixes
2. **Orchestrator** (`orchestrator.py`) - Intent recognition improvements
3. **Reasoning Module** (`modules/reasoning.py`) - Prompt length handling
4. **Question Answering Handler** (`handlers/question_answering_handler.py`) - Content processing improvements

## Components and Interfaces

### 1. Text Formatting Component

**Location**: `modules/automation.py`

**Key Methods**:

- `_cliclick_type()` - Enhanced to handle newlines and formatting
- `_macos_type()` - Improved AppleScript formatting preservation
- `_format_text_for_typing()` - New method for text preprocessing

**Interface Changes**:

```python
def _cliclick_type(self, text: str, fast_path: bool = False, element_info: Optional[Dict[str, Any]] = None) -> bool:
    # Enhanced implementation with proper newline handling

def _format_text_for_typing(self, text: str, method: str) -> str:
    # New method to prepare text based on typing method
```

### 2. Intent Recognition Component

**Location**: `orchestrator.py`

**Key Methods**:

- `_fallback_intent_classification()` - Enhanced pattern matching
- `_recognize_intent()` - Improved error handling

**Interface Changes**:

```python
def _fallback_intent_classification(self, command: str) -> Dict[str, Any]:
    # Enhanced with better typing command detection
```

### 3. Content Processing Component

**Location**: `modules/reasoning.py` and `handlers/question_answering_handler.py`

**Key Methods**:

- `process_query()` - Enhanced length handling
- `_process_content_for_summarization()` - Intelligent content chunking
- `_chunk_content_intelligently()` - New content segmentation method

**Interface Changes**:

```python
def process_query(self, query: str, prompt_template: str = None, context: Dict[str, Any] = None, max_length: int = 2000) -> str:
    # Enhanced with configurable length limits

def _chunk_content_intelligently(self, content: str, max_chunk_size: int) -> List[str]:
    # New method for smart content chunking
```

## Data Models

### Text Formatting Configuration

```python
@dataclass
class TypingConfiguration:
    preserve_formatting: bool = True
    handle_newlines: bool = True
    escape_special_chars: bool = True
    method_preference: List[str] = field(default_factory=lambda: ['cliclick', 'applescript'])
```

### Content Processing Configuration

```python
@dataclass
class ContentProcessingConfig:
    max_prompt_length: int = 2000
    chunk_overlap: int = 200
    prioritize_sections: List[str] = field(default_factory=lambda: ['main', 'content', 'article'])
    fallback_summary_length: int = 500
```

## Error Handling

### 1. Text Formatting Errors

- **Detection**: Monitor typing success/failure rates
- **Recovery**: Automatic fallback between cliclick and AppleScript
- **Logging**: Detailed formatting preservation metrics
- **User Feedback**: Specific error messages about formatting issues

### 2. Intent Recognition Errors

- **Detection**: Monitor classification confidence scores
- **Recovery**: Enhanced fallback patterns with typing command detection
- **Logging**: Intent classification decision trails
- **User Feedback**: Transparent routing decisions

### 3. Content Processing Errors

- **Detection**: Monitor prompt length and processing failures
- **Recovery**: Intelligent content chunking and summarization
- **Logging**: Content size and processing metrics
- **User Feedback**: Clear explanations of content limitations

## Testing Strategy

### 1. Text Formatting Tests

```python
def test_multiline_code_formatting():
    # Test Python code with proper indentation
    # Test JavaScript with nested structures
    # Test mixed content with special characters

def test_typing_method_fallback():
    # Test cliclick -> AppleScript fallback
    # Test formatting preservation across methods
```

### 2. Intent Recognition Tests

```python
def test_typing_command_recognition():
    # Test "type, [text]" patterns
    # Test various typing command formats
    # Test confidence scoring

def test_fallback_classification():
    # Test pattern matching accuracy
    # Test edge cases and ambiguous commands
```

### 3. Content Processing Tests

```python
def test_large_content_handling():
    # Test PDF content > 2000 characters
    # Test web page content chunking
    # Test summarization quality

def test_prompt_length_management():
    # Test automatic content truncation
    # Test intelligent section prioritization
```

### 4. Integration Tests

```python
def test_end_to_end_bug_fixes():
    # Test complete workflow for each bug scenario
    # Test error recovery and user feedback
    # Test performance impact of fixes
```

## Implementation Approach

### Phase 1: Text Formatting Fix

1. Enhance `_cliclick_type()` to handle newlines properly
2. Improve `_macos_type()` AppleScript formatting
3. Add text preprocessing for different typing methods
4. Implement comprehensive testing

### Phase 2: Intent Recognition Fix

1. Update fallback classification patterns
2. Add specific typing command detection
3. Improve confidence scoring for simple commands
4. Test routing accuracy

### Phase 3: Content Processing Fix

1. Add configurable prompt length limits
2. Implement intelligent content chunking
3. Enhance error handling and fallback responses
4. Optimize summarization for large content

### Phase 4: Integration and Testing

1. End-to-end testing of all fixes
2. Performance impact assessment
3. User experience validation
4. Documentation updates

## Performance Considerations

- **Text Formatting**: Minimal impact, preprocessing is lightweight
- **Intent Recognition**: Improved fast-path routing reduces LLM calls
- **Content Processing**: Chunking may increase processing time but improves reliability
- **Overall**: Net positive impact through better fast-path utilization

## Security Considerations

- **Text Escaping**: Proper handling of special characters in AppleScript
- **Content Validation**: Sanitization of large content before processing
- **Error Information**: Avoid exposing sensitive content in error messages
