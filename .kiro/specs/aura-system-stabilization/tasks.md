# Implementation Plan

## Phase 0: Refactoring and System Stabilization

###def fibona Task 0.0: Proactive Refactoring of the Orchestrator

- [x] 0.0 Create handler directory structure and base handler class

  - Create `handlers/` directory with `__init__.py`
  - Implement `handlers/base_handler.py` with abstract `BaseHandler` class
  - Define standardized `handle()` method interface and result creation methods
    function so - Add proper logging and error handling patterns for all handlers
  - _Requirements: 1.1, 1.2_

- [x] 0.1 Create GUI handler class and migrate existing logic

  - Create `handlers/gui_handler.py` inheriting from `BaseHandler`
  - Migrate entire GUI interaction logic from `Orchestrator._execute_command_internal` to `GUIHandler.handle()`
  - Preserve all existing fast path and vision fallback functionality
  - Implement `_attempt_fast_path()` and `_attempt_vision_fallback()` methods
  - Add comprehensive error handling and logging consistent with new architecture
  - _Requirements: 1.3, 1.4, 10.1, 10.2_

- [x] 0.2 Create conversation and deferred action handler classes

  - Create `handlers/conversation_handler.py` with basic structure for future conversational features
  - Create `handlers/deferred_action_handler.py` inheriting from `BaseHandler`
  - Migrate deferred action logic from Orchestrator to `DeferredActionHandler.handle()`
  - Implement content generation, cleaning, and mouse listener management
  - Add proper state management and cleanup methods
  - _Requirements: 1.5, 1.6_

- [x] 0.3 Refactor Orchestrator to use handler-based routing
  - Simplify `Orchestrator._execute_command_internal` to focus on intent recognition and routing
  - Add handler initialization in `Orchestrator.__init__()`
  - Implement `_get_handler_for_intent()` method for routing commands to appropriate handlers
  - Update command execution flow to instantiate handlers and call their `handle()` methods
  - Preserve all existing functionality while using new modular architecture
  - _Requirements: 1.7, 5.1, 5.2_

### Task 0.1: Fix Concurrency Deadlock in Deferred Actions

- [x] 0.4 Implement improved execution lock management

  - Update `Orchestrator.execute_command()` to use timeout-based lock acquisition
  - Implement early lock release for deferred actions returning 'waiting_for_user_action' status
  - Add proper lock cleanup in exception handling with try/finally blocks
  - Ensure `_on_deferred_action_trigger` re-acquires lock before executing final action
  - Add comprehensive logging for lock acquisition, release, and timeout events
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 0.5 Test and validate concurrent command handling
  - Write unit tests for concurrent deferred action scenarios
  - Implement test cases for command interruption during deferred action wait states
  - Validate that second commands process while first waits for user input
  - Add integration tests for lock timeout and recovery scenarios
  - Ensure no deadlocks occur under various concurrent usage patterns
  - _Requirements: 2.4, 2.5_

### Task 0.2: Resolve Deferred Action Content Generation Bugs

- [x] 0.6 Enhance content generation prompts and configuration

  - Update `CODE_GENERATION_PROMPT` in `config.py` with explicit formatting instructions
  - Add specific indentation requirements (4 spaces for Python, 2 for JavaScript/HTML/CSS)
  - Include instructions for proper line breaks, structure, and editor-ready formatting
  - Add content type detection and type-specific formatting rules
  - Remove or modify restrictive timeout parameters that interrupt long typing processes
  - _Requirements: 3.1, 3.4_

- [x] 0.7 Implement comprehensive content cleaning and formatting
  - Enhance `_clean_generated_content` method with expanded unwanted prefix/suffix lists
  - Add detection and removal of markdown code blocks, explanatory text, and duplicate content
  - Implement `_format_single_line_code` method for automatic code reformatting
  - Add content type-aware cleaning logic for different generation types (code, text, etc.)
  - Include proper indentation preservation and newline handling
  - _Requirements: 3.2, 3.3, 3.5_

### Task 0.3: Fix GUI Interaction Failures

- [x] 0.8 Implement robust application detection with fallback

  - Enhance `modules/application_detector.py` with comprehensive error handling
  - Add AppleScript fallback method using System Events for application identification
  - Implement `_ensure_application_focus()` method with primary and fallback detection
  - Add proper timeout handling and error recovery for application detection failures
  - Eliminate "No focused application found" errors through reliable fallback mechanisms
  - _Requirements: 4.1, 4.4, 4.5_

- [x] 0.9 Enhance scroll command reliability and context awareness
  - Add scroll context detection in `Orchestrator._perform_action_execution` method
  - Implement automatic identification and focusing of primary scrollable areas
  - Add click-to-focus functionality before scroll execution for better targeting
  - Implement fallback to current scroll behavior when no specific scrollable area found
  - Add comprehensive error handling and user feedback for scroll command failures
  - _Requirements: 4.2, 4.3_

## Phase 1: Foundational Architecture and Responsiveness

### Task 1.1: Implement Intent Recognition & Orchestrator Routing

- [ ] 1.0 Implement LLM-based intent recognition system

  - Add `INTENT_RECOGNITION_PROMPT` to `config.py` with clear classification instructions
  - Implement `_recognize_intent()` method in Orchestrator using reasoning module
  - Add intent classification for gui_interaction, conversational_chat, deferred_action, question_answering
  - Include confidence scoring and parameter extraction for each intent type
  - Add fallback to gui_interaction when intent recognition fails
  - _Requirements: 5.3, 5.4, 5.5_

- [ ] 1.1 Refactor command execution flow with intent-based routing
  - Update `_execute_command_internal` to perform intent recognition before processing
  - Implement intent-based routing that delegates to appropriate handler methods
  - Move existing GUI automation logic to `_handle_gui_interaction` method
  - Add proper error handling and logging for intent recognition and routing failures
  - Ensure backward compatibility with all existing command types and behaviors
  - _Requirements: 5.1, 5.2, 10.3, 10.4_

### Task 1.2: Implement Whisper Silence Detection

- [ ] 1.2 Enhance audio input pipeline with silence detection
  - Modify `modules/audio.py` speech_to_text method to record in chunks
  - Implement automatic silence detection to stop recording when user finishes speaking
  - Add configurable silence threshold and detection sensitivity settings
  - Implement fallback to fixed-duration recording when silence detection fails
  - Significantly reduce current 8-second recording delay for improved responsiveness
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

## Phase 2: Advanced Content Comprehension

### Task 2.1: Implement "Fast Path" for Content Summarization

- [ ] 2.0 Implement browser content extraction fast path

  - Create `get_page_text_content` method in `modules/browser_accessibility.py`
  - Use AppleScript and JavaScript to extract all text content from web pages
  - Add error handling and fallback mechanisms for different browser types
  - Implement content filtering and cleaning for better text extraction quality
  - Add support for multiple browser applications (Chrome, Safari, Firefox)
  - _Requirements: 7.1, 7.5_

- [ ] 2.1 Implement PDF content extraction capabilities

  - Create new `modules/pdf_handler.py` module for PDF text extraction
  - Implement file path detection for open PDF documents
  - Use `pdftotext` command-line tool for efficient text extraction
  - Add error handling for missing tools and unsupported PDF formats
  - Include content cleaning and formatting for extracted PDF text
  - _Requirements: 7.2_

- [ ] 2.2 Enhance application detection for content extraction

  - Update `modules/application_detector.py` to recognize PDF reader bundle IDs
  - Add detection for various PDF applications (Preview, Adobe Reader, etc.)
  - Implement application-specific content extraction strategies
  - Add proper error handling and fallback for unsupported applications
  - Include logging and debugging information for application detection
  - _Requirements: 7.3_

- [ ] 2.3 Integrate fast path content extraction with question answering
  - Refactor `answer_question` method in Orchestrator to use text-based fast path
  - Implement content type detection (browser vs PDF vs other applications)
  - Add seamless fallback to vision-based analysis when fast path fails
  - Include performance monitoring and comparison between fast path and vision methods
  - Ensure backward compatibility with existing question answering functionality
  - _Requirements: 7.4, 7.5_

## Phase 3: Final Feature Implementation

### Task 3.1: Implement the Conversational Chat Handler

- [ ] 3.0 Implement conversational prompt and personality system

  - Add `CONVERSATIONAL_PROMPT` to `config.py` defining AURA's chat personality
  - Include guidelines for helpful, friendly, and contextually appropriate responses
  - Add conversation context management and history tracking
  - Implement response style guidelines and tone consistency
  - Add support for different conversation types (casual, technical, help requests)
  - _Requirements: 8.1, 8.2_

- [ ] 3.1 Complete conversational handler implementation

  - Implement `ConversationHandler._handle_conversational_query` method
  - Use reasoning module with conversational prompt template for response generation
  - Add conversation context building and history management
  - Implement audio feedback integration for speaking responses to users
  - Add proper error handling and fallback for conversational query failures
  - _Requirements: 8.3, 8.4, 8.5_

- [ ] 3.2 Integrate conversational features with intent routing system
  - Connect conversational handler with intent-based routing in Orchestrator
  - Add conversation state management and context preservation
  - Implement seamless transitions between conversation and other interaction modes
  - Add comprehensive testing for conversational features and integration points
  - Ensure conversational commands work reliably with existing system architecture
  - _Requirements: 8.5, 9.1, 9.2, 9.3, 9.4, 10.1_

## System Integration and Validation

### Task 4.0: Comprehensive Testing and Validation

- [ ] 4.0 Implement comprehensive unit test coverage

  - Write unit tests for all handler classes (GUI, Conversation, DeferredAction)
  - Add tests for intent recognition accuracy and routing logic
  - Implement concurrency testing for deferred actions and lock management
  - Add content generation and cleaning validation tests
  - Include error handling and recovery scenario testing
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 4.1 Validate backward compatibility and system integration

  - Test all existing AURA commands to ensure identical behavior
  - Validate GUI automation functionality preservation
  - Test question answering with both fast path and vision fallback
  - Verify audio feedback and user experience consistency
  - Ensure no performance regressions in existing functionality
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 4.2 Performance optimization and monitoring
  - Implement performance monitoring for all handler types
  - Add metrics collection for intent recognition speed and accuracy
  - Monitor memory usage and resource consumption of new architecture
  - Optimize handler execution times and system responsiveness
  - Add performance regression detection and alerting
  - _Requirements: 9.5_
