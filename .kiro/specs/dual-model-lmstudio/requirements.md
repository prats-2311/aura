# Requirements Document

## Introduction

This feature enhances the AURA system to utilize both a vision model and a reasoning model (Gemma3) running on LMStudio simultaneously. Currently, the system uses LMStudio for vision analysis and a separate cloud API for reasoning. This enhancement will consolidate both capabilities to run locally on LMStudio, allowing for better performance, privacy, and reduced dependency on external APIs.

## Requirements

### Requirement 1

**User Story:** As a user, I want AURA to use both vision and reasoning models from LMStudio so that all AI processing happens locally without relying on external cloud APIs.

#### Acceptance Criteria

1. WHEN a user command requires both vision and reasoning processing THEN the system SHALL make API calls to both the vision model and Gemma3 model running on LMStudio
2. WHEN the system processes a screen analysis request THEN it SHALL use the vision model on LMStudio to analyze the screen content
3. WHEN the system needs to generate an action plan THEN it SHALL use the Gemma3 model on LMStudio for reasoning instead of cloud APIs
4. IF both models are not available on LMStudio THEN the system SHALL provide clear error messages indicating which models are missing

### Requirement 2

**User Story:** As a developer, I want the configuration system to support dual model detection so that the system can automatically identify and use both models running on LMStudio.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL detect all available models running on LMStudio
2. WHEN multiple models are detected THEN the system SHALL identify which model is suitable for vision tasks and which for reasoning tasks
3. WHEN model detection fails THEN the system SHALL fall back to configured model names with appropriate warnings
4. IF the required models are not found THEN the system SHALL provide setup instructions for loading the correct models in LMStudio

### Requirement 3

**User Story:** As a user, I want the system to coordinate between vision and reasoning models efficiently so that processing is fast and reliable.

#### Acceptance Criteria

1. WHEN both vision and reasoning are needed THEN the system SHALL coordinate API calls to prevent resource conflicts
2. WHEN one model request fails THEN the system SHALL retry with appropriate backoff strategies
3. WHEN models are overloaded THEN the system SHALL queue requests appropriately to prevent timeouts
4. IF a model becomes unavailable during processing THEN the system SHALL handle the error gracefully and inform the user

### Requirement 4

**User Story:** As a system administrator, I want clear configuration options to specify which models to use for vision and reasoning tasks.

#### Acceptance Criteria

1. WHEN configuring the system THEN there SHALL be separate configuration options for vision model name and reasoning model name
2. WHEN model names are not specified THEN the system SHALL attempt automatic detection based on model capabilities
3. WHEN configuration is updated THEN the system SHALL validate that the specified models are available on LMStudio
4. IF invalid model names are provided THEN the system SHALL provide clear error messages with available model options

### Requirement 5

**User Story:** As a user, I want the system to maintain backward compatibility so that existing functionality continues to work during the transition.

#### Acceptance Criteria

1. WHEN the new dual-model system is enabled THEN all existing vision analysis functionality SHALL continue to work
2. WHEN the new dual-model system is enabled THEN all existing reasoning functionality SHALL work with local models instead of cloud APIs
3. WHEN cloud API fallback is needed THEN the system SHALL provide an option to fall back to the previous cloud-based reasoning
4. IF the dual-model system fails THEN the system SHALL gracefully degrade to single-model operation where possible
