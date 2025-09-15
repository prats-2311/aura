# AURA Project: Core Development Principles

This document provides high-level steering for the AI when developing the AURA project.

## 1. Modularity and Separation of Concerns

- All core functionality must be encapsulated in its own module within the `/modules` directory (e.g., `VisionModule`, `AudioModule`).
- The `Orchestrator` is the central coordinator and should not contain implementation details of the modules.
- User intent logic must be placed in specialized handlers within the `/handlers` directory.

## 2. Robustness Through Fallbacks

- For any critical function that depends on an external system (like Accessibility APIs), always implement a fallback mechanism (like the Vision-based fallback).
- All public-facing methods should have comprehensive error handling.

## 3. Configuration-Driven Design

- Avoid hardcoding values. All important parameters, especially API keys, model names, and prompts, must be defined in `config.py`.
- This allows for easy modification and testing without altering the core application logic.

## 4. Clarity and Maintainability

- All public functions and classes must have clear docstrings explaining their purpose, arguments, and return values.
- Use descriptive variable and function names.
