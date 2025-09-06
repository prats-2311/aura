"""
AURA Handler Module

This module contains the handler classes that implement the modular command processing
architecture for AURA. Each handler specializes in a specific type of user interaction:

- BaseHandler: Abstract base class defining the handler interface
- GUIHandler: Handles GUI automation commands (click, type, scroll, etc.)
- ConversationHandler: Handles conversational chat interactions
- DeferredActionHandler: Handles content generation and deferred placement workflows

The handler architecture provides:
- Clean separation of concerns
- Standardized error handling and logging
- Consistent result formats
- Modular extensibility for new interaction types
"""

from .base_handler import BaseHandler
from .gui_handler import GUIHandler
from .conversation_handler import ConversationHandler
from .deferred_action_handler import DeferredActionHandler

__all__ = [
    'BaseHandler',
    'GUIHandler', 
    'ConversationHandler',
    'DeferredActionHandler'
]