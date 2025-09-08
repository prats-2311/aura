# Requirements Document

## Introduction

This document outlines the requirements for fixing three critical bugs in the AURA system that are affecting user experience and functionality:

1. **Bug 1**: Code formatting issues during typing - all content is typed on a single line instead of preserving proper formatting and indentation
2. **Bug 2**: Intent recognition routing failure - commands like "type, prateek srivastava" are incorrectly routed to LLM instead of fast path
3. **Bug 3**: Screen summarization failure - "what's on my screen" commands fail due to prompt length limits in the reasoning module

## Requirements

### Requirement 1: Fix Text Formatting During Typing

**User Story:** As a user, I want code and multi-line text to be typed with proper formatting and indentation, so that the generated content maintains its intended structure and readability.

#### Acceptance Criteria

1. WHEN the system types multi-line content THEN it SHALL preserve line breaks and indentation
2. WHEN the system types code content THEN it SHALL maintain proper code formatting including spaces, tabs, and newlines
3. WHEN using cliclick for typing THEN it SHALL handle newlines and special characters correctly
4. WHEN using AppleScript for typing THEN it SHALL preserve indentation and line structure
5. IF cliclick fails to preserve formatting THEN the system SHALL fall back to AppleScript with proper formatting handling

### Requirement 2: Fix Intent Recognition for Simple Commands

**User Story:** As a user, I want simple typing commands like "type, [text]" to be processed quickly through the fast path, so that I don't experience unnecessary delays from LLM processing.

#### Acceptance Criteria

1. WHEN a user says "type, [simple text]" THEN the system SHALL route it to gui_interaction intent
2. WHEN a command starts with "type" followed by simple text THEN it SHALL use fast path processing
3. WHEN the intent recognition system processes typing commands THEN it SHALL have higher confidence for gui_interaction
4. IF the command is a simple typing request THEN it SHALL NOT be sent to the LLM for processing
5. WHEN fallback intent classification runs THEN it SHALL correctly identify typing patterns

### Requirement 3: Fix Screen Summarization Prompt Length Limits

**User Story:** As a user, I want "what's on my screen" commands to work reliably even with large amounts of content, so that I can get summaries of complex documents and web pages.

#### Acceptance Criteria

1. WHEN processing screen content for summarization THEN the system SHALL handle content larger than 2000 characters
2. WHEN content exceeds prompt limits THEN the system SHALL intelligently truncate or chunk the content
3. WHEN summarizing large PDF content THEN it SHALL process the content in manageable segments
4. WHEN summarizing large web page content THEN it SHALL prioritize the most relevant sections
5. IF content is too large for a single request THEN the system SHALL provide a meaningful summary of the available portion
6. WHEN content processing fails due to length THEN it SHALL provide a helpful fallback response instead of a generic error

### Requirement 4: Improve Error Handling and User Feedback

**User Story:** As a user, I want clear feedback when the system encounters issues, so that I understand what happened and can take appropriate action.

#### Acceptance Criteria

1. WHEN typing fails due to formatting issues THEN the system SHALL provide specific feedback about the problem
2. WHEN intent recognition fails THEN the system SHALL fall back gracefully with appropriate user messaging
3. WHEN content summarization fails THEN the system SHALL explain the issue and suggest alternatives
4. WHEN any of these bugs occur THEN the system SHALL log detailed information for debugging
5. IF multiple fallback attempts fail THEN the system SHALL provide actionable guidance to the user
