# Design Document

## Overview

The Content Comprehension Fast Path feature will dramatically improve the performance of "what's on my screen" commands by implementing a dedicated question answering handler that leverages existing browser and PDF text extraction capabilities. This design addresses the current architectural issue where question answering is incorrectly routed to the GUIHandler and relies on slow vision-based processing.

The solution introduces a new QuestionAnsweringHandler that implements a fast path using text-based content extraction before falling back to the existing vision-based approach. This will reduce response times from 10-30 seconds to under 5 seconds for supported applications.

## Architecture

### Current Architecture Issues

- Question answering intents are incorrectly routed to GUIHandler in `orchestrator.py`
- All screen content queries rely on slow vision processing
- Existing fast text extraction modules (BrowserAccessibilityHandler, PDFHandler) are not integrated into the question answering flow
- No application-specific optimization for content extraction

### Proposed Architecture

```
User Command → Intent Recognition → QuestionAnsweringHandler → Fast Path Detection
                                                           ↓
                                    ApplicationDetector → Browser/PDF Detection
                                                           ↓
                                    Text Extraction → ReasoningModule → Audio Response
                                                           ↓
                                    Vision Fallback (if text extraction fails)
```

### Key Architectural Changes

1. **New Handler**: Create `QuestionAnsweringHandler` inheriting from `BaseHandler`
2. **Intent Routing**: Update orchestrator to route `question_answering` intent to new handler
3. **Fast Path Integration**: Integrate existing `BrowserAccessibilityHandler` and `PDFHandler`
4. **Application Detection**: Leverage existing `ApplicationDetector` for app type identification
5. **Graceful Fallback**: Maintain existing vision-based processing as fallback

## Components and Interfaces

### QuestionAnsweringHandler

**Location**: `handlers/question_answering_handler.py`

**Key Methods**:

- `handle(command: str, context: Dict[str, Any]) -> Dict[str, Any]`
- `_try_fast_path(command: str) -> Optional[str]`
- `_extract_browser_content() -> Optional[str]`
- `_extract_pdf_content() -> Optional[str]`
- `_fallback_to_vision(command: str) -> Dict[str, Any]`

**Dependencies**:

- `ApplicationDetector` for app type detection
- `BrowserAccessibilityHandler` for web content extraction
- `PDFHandler` for PDF text extraction
- `ReasoningModule` for text summarization
- `AudioModule` for response delivery

### Integration Points

**Orchestrator Updates**:

- `_get_handler_for_intent()`: Route `question_answering` to `QuestionAnsweringHandler`
- Remove question answering logic from `answer_question()` method
- Update intent recognition to properly classify question answering requests

**ApplicationDetector Integration**:

- Use existing `detect_application_type()` method
- Leverage `ApplicationType.WEB_BROWSER` and `ApplicationType.PDF_READER` classifications
- Utilize existing browser type detection for optimization

**Content Extraction Integration**:

- `BrowserAccessibilityHandler.get_page_text_content()` for web browsers
- `PDFHandler.extract_text_from_open_document()` for PDF readers
- Existing error handling and timeout mechanisms

## Data Models

### HandlerResult Extensions

```python
@dataclass
class QuestionAnsweringResult(HandlerResult):
    """Extended result for question answering operations."""
    extraction_method: str  # "fast_path_browser", "fast_path_pdf", "vision_fallback"
    content_length: Optional[int] = None
    extraction_time: Optional[float] = None
    application_type: Optional[str] = None
```

### Fast Path Context

```python
@dataclass
class FastPathContext:
    """Context information for fast path processing."""
    application_name: str
    application_type: ApplicationType
    browser_type: Optional[BrowserType] = None
    extraction_method: str
    content_available: bool
    fallback_reason: Optional[str] = None
```

## Error Handling

### Fast Path Error Scenarios

1. **Application Detection Failure**

   - Fallback: Use vision-based approach
   - Logging: Warn about detection failure
   - User Impact: Transparent fallback, slightly slower response

2. **Browser Content Extraction Failure**

   - Fallback: Vision-based screen analysis
   - Logging: Log extraction failure with browser type
   - User Impact: Seamless fallback to existing behavior

3. **PDF Content Extraction Failure**

   - Fallback: Vision-based screen analysis
   - Logging: Log PDF extraction failure and reason
   - User Impact: Seamless fallback to existing behavior

4. **Text Summarization Failure**
   - Fallback: Return raw extracted text (truncated if needed)
   - Logging: Log reasoning module failure
   - User Impact: Less polished but still fast response

### Error Recovery Strategy

- **Graceful Degradation**: Always fallback to existing vision-based approach
- **Transparent Failures**: User should not notice when fast path fails
- **Performance Monitoring**: Track fast path success rates and performance
- **Timeout Handling**: Implement timeouts for each extraction method

## Testing Strategy

### Unit Tests

**File**: `tests/test_question_answering_handler.py`

**Test Coverage**:

- Handler initialization and configuration
- Fast path detection logic
- Browser content extraction integration
- PDF content extraction integration
- Vision fallback behavior
- Error handling and recovery
- Performance timing validation

### Integration Tests

**File**: `tests/test_fast_path_integration.py`

**Test Scenarios**:

- End-to-end question answering with Chrome browser
- End-to-end question answering with Safari browser
- End-to-end question answering with PDF reader
- Fallback behavior when applications not detected
- Performance comparison between fast path and vision fallback
- Intent routing validation

### Browser-Specific Tests

**Files**:

- `tests/test_browser_fast_path.py`
- `tests/test_pdf_fast_path.py`

**Test Coverage**:

- Chrome-specific content extraction
- Safari-specific content extraction
- Firefox-specific content extraction
- Preview.app PDF extraction
- Adobe Reader PDF extraction
- Content quality validation

### Performance Tests

**File**: `tests/test_fast_path_performance.py`

**Performance Metrics**:

- Response time under 5 seconds for fast path
- Response time comparison with vision fallback
- Memory usage during text extraction
- CPU usage during text processing
- Success rate of fast path detection

### Backward Compatibility Tests

**File**: `tests/test_question_answering_compatibility.py`

**Compatibility Validation**:

- Existing question answering commands work unchanged
- Vision fallback maintains identical behavior
- No regression in non-browser/PDF applications
- Configuration compatibility
- Error message consistency

## Implementation Phases

### Phase 1: Core Handler Implementation

1. Create `QuestionAnsweringHandler` class structure
2. Implement basic fast path detection logic
3. Integrate with `ApplicationDetector`
4. Add basic error handling and logging

### Phase 2: Content Extraction Integration

1. Integrate `BrowserAccessibilityHandler` for web content
2. Integrate `PDFHandler` for PDF content
3. Implement text summarization pipeline
4. Add performance monitoring

### Phase 3: Orchestrator Integration

1. Update intent routing in orchestrator
2. Remove question answering logic from existing handlers
3. Update intent recognition configuration
4. Validate end-to-end flow

### Phase 4: Testing and Optimization

1. Implement comprehensive test suite
2. Performance optimization and tuning
3. Error handling refinement
4. Documentation and logging improvements

## Performance Considerations

### Target Performance Metrics

- **Fast Path Response Time**: < 5 seconds end-to-end
- **Browser Content Extraction**: < 2 seconds
- **PDF Content Extraction**: < 2 seconds
- **Text Summarization**: < 3 seconds
- **Fallback Detection**: < 1 second

### Optimization Strategies

- **Caching**: Leverage existing browser tree caching in `BrowserAccessibilityHandler`
- **Parallel Processing**: Extract content while preparing reasoning context
- **Content Filtering**: Extract only relevant content sections for summarization
- **Timeout Management**: Aggressive timeouts to ensure fast fallback

### Memory Management

- **Content Size Limits**: Limit extracted text to reasonable sizes (e.g., 50KB)
- **Cache Management**: Use existing cache TTL mechanisms
- **Resource Cleanup**: Ensure proper cleanup of temporary resources

## Security Considerations

### Content Privacy

- **Local Processing**: All text extraction happens locally
- **No External Transmission**: Extracted content stays within AURA system
- **Temporary Storage**: No persistent storage of extracted content

### Application Permissions

- **Accessibility Permissions**: Leverage existing accessibility permission framework
- **Application Detection**: Use existing secure application detection methods
- **Error Information**: Avoid exposing sensitive information in error messages

## Monitoring and Observability

### Performance Metrics

- Fast path success rate by application type
- Average response time by extraction method
- Fallback frequency and reasons
- Content extraction success rates

### Logging Strategy

- **Debug Level**: Detailed extraction process information
- **Info Level**: Performance metrics and success/failure outcomes
- **Warning Level**: Fallback scenarios and degraded performance
- **Error Level**: Extraction failures and system errors

### Health Checks

- Validate browser accessibility handler availability
- Validate PDF handler tool availability
- Monitor reasoning module performance
- Track overall system health impact
