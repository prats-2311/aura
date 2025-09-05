"""
Debug Logger Module

Provides configurable debug logging infrastructure with structured output,
context information, and multiple debug levels for troubleshooting accessibility issues.
"""

import logging
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
from logging.handlers import RotatingFileHandler
import threading
import os

# Import config for debug settings
try:
    from config import (
        DEBUG_LEVEL, DEBUG_LEVELS, DEBUG_OUTPUT_FORMAT, DEBUG_INCLUDE_TIMESTAMPS,
        DEBUG_INCLUDE_CONTEXT, DEBUG_INCLUDE_STACK_TRACE, DEBUG_CATEGORIES,
        DEBUG_LOG_TO_FILE, DEBUG_LOG_TO_CONSOLE, DEBUG_LOG_FILE,
        DEBUG_LOG_MAX_SIZE, DEBUG_LOG_BACKUP_COUNT, DEBUG_STRUCTURED_FORMAT
    )
except ImportError:
    # Fallback defaults if config import fails
    DEBUG_LEVEL = "BASIC"
    DEBUG_LEVELS = {"BASIC": 1, "DETAILED": 2, "VERBOSE": 3}
    DEBUG_OUTPUT_FORMAT = "structured"
    DEBUG_INCLUDE_TIMESTAMPS = True
    DEBUG_INCLUDE_CONTEXT = True
    DEBUG_INCLUDE_STACK_TRACE = False
    DEBUG_CATEGORIES = {
        "accessibility": True, "permissions": True, "element_search": True,
        "performance": True, "error_recovery": True, "application_detection": True,
        "fuzzy_matching": True, "tree_inspection": True, "failure_analysis": True,
        "diagnostic_tools": True
    }
    DEBUG_LOG_TO_FILE = True
    DEBUG_LOG_TO_CONSOLE = True
    DEBUG_LOG_FILE = "aura_debug.log"
    DEBUG_LOG_MAX_SIZE = 10 * 1024 * 1024
    DEBUG_LOG_BACKUP_COUNT = 3
    DEBUG_STRUCTURED_FORMAT = {
        "timestamp": "%(asctime)s", "level": "%(levelname)s",
        "module": "%(name)s", "message": "%(message)s",
        "context": "%(context)s", "category": "%(category)s",
        "thread": "%(thread)d", "process": "%(process)d"
    }


class DebugContextFilter(logging.Filter):
    """Custom filter to add context information to log records."""
    
    def filter(self, record):
        # Add default context if not present
        if not hasattr(record, 'context'):
            record.context = {}
        if not hasattr(record, 'category'):
            record.category = 'general'
        
        # Convert context to string for formatting
        if isinstance(record.context, dict):
            record.context = json.dumps(record.context, default=str)
        
        return True


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured debug output."""
    
    def __init__(self, format_dict: Dict[str, str], output_format: str = "structured"):
        super().__init__()
        self.format_dict = format_dict
        self.output_format = output_format.lower()
    
    def format(self, record):
        if self.output_format == "json":
            return self._format_json(record)
        elif self.output_format == "plain":
            return self._format_plain(record)
        else:  # structured
            return self._format_structured(record)
    
    def _format_json(self, record):
        """Format log record as JSON."""
        log_data = {}
        for key, format_str in self.format_dict.items():
            try:
                if key == "message":
                    log_data[key] = record.getMessage()
                else:
                    log_data[key] = format_str % record.__dict__
            except (KeyError, ValueError):
                log_data[key] = "N/A"
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)
    
    def _format_plain(self, record):
        """Format log record as plain text."""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        context_str = ""
        if hasattr(record, 'context') and record.context and record.context != "{}":
            context_str = f" | Context: {record.context}"
        
        category_str = ""
        if hasattr(record, 'category') and record.category != 'general':
            category_str = f" | Category: {record.category}"
        
        return f"{timestamp} | {record.levelname} | {record.name} | {record.getMessage()}{category_str}{context_str}"
    
    def _format_structured(self, record):
        """Format log record with structured layout."""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Build structured output
        parts = [
            f"[{timestamp}]",
            f"[{record.levelname}]",
            f"[{record.name}]"
        ]
        
        if hasattr(record, 'category') and record.category != 'general':
            parts.append(f"[{record.category}]")
        
        parts.append(record.getMessage())
        
        if hasattr(record, 'context') and record.context and record.context != "{}":
            parts.append(f"Context: {record.context}")
        
        # Add exception info if present
        if record.exc_info:
            parts.append(f"Exception: {self.formatException(record.exc_info)}")
        
        return " | ".join(parts)


class DebugLogger:
    """
    Enhanced debug logger with configurable levels and structured output.
    
    Provides comprehensive debugging capabilities for accessibility issues,
    element detection failures, and system diagnostics.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.current_level = DEBUG_LEVELS.get(DEBUG_LEVEL, 1)
        self.loggers = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration with handlers and formatters."""
        # Create formatter
        formatter = StructuredFormatter(DEBUG_STRUCTURED_FORMAT, DEBUG_OUTPUT_FORMAT)
        
        # Set up file handler if enabled
        if DEBUG_LOG_TO_FILE:
            try:
                file_handler = RotatingFileHandler(
                    DEBUG_LOG_FILE,
                    maxBytes=DEBUG_LOG_MAX_SIZE,
                    backupCount=DEBUG_LOG_BACKUP_COUNT
                )
                file_handler.setFormatter(formatter)
                file_handler.addFilter(DebugContextFilter())
                self.file_handler = file_handler
            except Exception as e:
                print(f"Warning: Could not set up debug file logging: {e}")
                self.file_handler = None
        else:
            self.file_handler = None
        
        # Set up console handler if enabled
        if DEBUG_LOG_TO_CONSOLE:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.addFilter(DebugContextFilter())
            self.console_handler = console_handler
        else:
            self.console_handler = None
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger for the specified module."""
        if name not in self.loggers:
            logger = logging.getLogger(f"aura.debug.{name}")
            logger.setLevel(logging.DEBUG)
            
            # Remove existing handlers to avoid duplicates
            logger.handlers.clear()
            
            # Add our custom handlers
            if self.file_handler:
                logger.addHandler(self.file_handler)
            if self.console_handler:
                logger.addHandler(self.console_handler)
            
            # Prevent propagation to avoid duplicate logs
            logger.propagate = False
            
            self.loggers[name] = logger
        
        return self.loggers[name]
    
    def log(self, level: str, category: str, message: str, 
            context: Optional[Dict[str, Any]] = None, 
            module: str = "debug", **kwargs):
        """
        Log a debug message with specified level and category.
        
        Args:
            level: Debug level (BASIC, DETAILED, VERBOSE)
            category: Debug category (accessibility, permissions, etc.)
            message: Log message
            context: Additional context information
            module: Module name for the logger
            **kwargs: Additional context data
        """
        # Check if this level should be logged
        level_num = DEBUG_LEVELS.get(level, 1)
        if level_num > self.current_level:
            return
        
        # Check if this category is enabled
        if not DEBUG_CATEGORIES.get(category, True):
            return
        
        # Prepare context
        log_context = context or {}
        log_context.update(kwargs)
        
        # Get logger and log message
        logger = self.get_logger(module)
        
        # Create log record with extra fields
        extra = {
            'context': log_context,
            'category': category
        }
        
        # Map debug levels to logging levels
        if level == "VERBOSE":
            logger.debug(message, extra=extra)
        elif level == "DETAILED":
            logger.info(message, extra=extra)
        else:  # BASIC
            logger.warning(message, extra=extra)
    
    def basic(self, category: str, message: str, context: Optional[Dict[str, Any]] = None, 
              module: str = "debug", **kwargs):
        """Log a BASIC level debug message."""
        self.log("BASIC", category, message, context, module, **kwargs)
    
    def detailed(self, category: str, message: str, context: Optional[Dict[str, Any]] = None, 
                 module: str = "debug", **kwargs):
        """Log a DETAILED level debug message."""
        self.log("DETAILED", category, message, context, module, **kwargs)
    
    def verbose(self, category: str, message: str, context: Optional[Dict[str, Any]] = None, 
               module: str = "debug", **kwargs):
        """Log a VERBOSE level debug message."""
        self.log("VERBOSE", category, message, context, module, **kwargs)
    
    def log_accessibility_tree(self, tree_data: Dict[str, Any], app_name: str = "unknown"):
        """Log accessibility tree information."""
        self.detailed(
            "tree_inspection",
            f"Accessibility tree dump for {app_name}",
            context={
                "app_name": app_name,
                "total_elements": tree_data.get("total_elements", 0),
                "clickable_elements": len(tree_data.get("clickable_elements", [])),
                "tree_depth": tree_data.get("tree_depth", 0)
            },
            module="accessibility"
        )
        
        # Log full tree data at verbose level
        self.verbose(
            "tree_inspection",
            f"Complete accessibility tree data for {app_name}",
            context={"tree_data": tree_data},
            module="accessibility"
        )
    
    def log_element_search(self, target: str, search_params: Dict[str, Any], 
                          results: Dict[str, Any], app_name: str = "unknown"):
        """Log element search operation."""
        self.detailed(
            "element_search",
            f"Element search for '{target}' in {app_name}",
            context={
                "target": target,
                "app_name": app_name,
                "search_params": search_params,
                "found": results.get("found", False),
                "match_count": len(results.get("matches", [])),
                "search_duration_ms": results.get("duration_ms", 0)
            },
            module="accessibility"
        )
    
    def log_fuzzy_matching(self, target: str, candidates: list, scores: Dict[str, float], 
                          threshold: float, best_match: Optional[Dict[str, Any]] = None):
        """Log fuzzy matching operation."""
        self.detailed(
            "fuzzy_matching",
            f"Fuzzy matching for '{target}' with {len(candidates)} candidates",
            context={
                "target": target,
                "candidate_count": len(candidates),
                "threshold": threshold,
                "best_score": max(scores.values()) if scores else 0,
                "best_match": best_match,
                "all_scores": scores
            },
            module="accessibility"
        )
    
    def log_permission_check(self, permission_type: str, status: bool, 
                           details: Optional[Dict[str, Any]] = None):
        """Log permission validation."""
        self.basic(
            "permissions",
            f"Permission check for {permission_type}: {'GRANTED' if status else 'DENIED'}",
            context={
                "permission_type": permission_type,
                "status": status,
                "details": details or {}
            },
            module="permissions"
        )
    
    def log_performance_metric(self, operation: str, duration_ms: float, 
                             success: bool, details: Optional[Dict[str, Any]] = None):
        """Log performance metrics."""
        self.basic(
            "performance",
            f"Performance: {operation} took {duration_ms:.2f}ms ({'SUCCESS' if success else 'FAILED'})",
            context={
                "operation": operation,
                "duration_ms": duration_ms,
                "success": success,
                "details": details or {}
            },
            module="performance"
        )
    
    def log_error_recovery(self, error_type: str, recovery_action: str, 
                          success: bool, details: Optional[Dict[str, Any]] = None):
        """Log error recovery attempts."""
        self.basic(
            "error_recovery",
            f"Error recovery: {error_type} -> {recovery_action} ({'SUCCESS' if success else 'FAILED'})",
            context={
                "error_type": error_type,
                "recovery_action": recovery_action,
                "success": success,
                "details": details or {}
            },
            module="error_recovery"
        )
    
    def log_failure_analysis(self, command: str, target: str, failure_reasons: list, 
                           recommendations: list, app_name: str = "unknown"):
        """Log detailed failure analysis."""
        self.basic(
            "failure_analysis",
            f"Command failure analysis: '{command}' targeting '{target}' in {app_name}",
            context={
                "command": command,
                "target": target,
                "app_name": app_name,
                "failure_reasons": failure_reasons,
                "recommendations": recommendations,
                "failure_count": len(failure_reasons)
            },
            module="failure_analysis"
        )
    
    def log_diagnostic_result(self, diagnostic_type: str, results: Dict[str, Any], 
                            issues_found: int, recommendations: list):
        """Log diagnostic tool results."""
        self.basic(
            "diagnostic_tools",
            f"Diagnostic completed: {diagnostic_type} found {issues_found} issues",
            context={
                "diagnostic_type": diagnostic_type,
                "issues_found": issues_found,
                "recommendations": recommendations,
                "results": results
            },
            module="diagnostics"
        )
    
    def set_debug_level(self, level: str):
        """Change the current debug level."""
        if level in DEBUG_LEVELS:
            self.current_level = DEBUG_LEVELS[level]
            self.basic(
                "general",
                f"Debug level changed to {level}",
                context={"new_level": level, "level_num": self.current_level},
                module="debug_logger"
            )
    
    def enable_category(self, category: str):
        """Enable logging for a specific category."""
        DEBUG_CATEGORIES[category] = True
        self.basic(
            "general",
            f"Debug category '{category}' enabled",
            context={"category": category},
            module="debug_logger"
        )
    
    def disable_category(self, category: str):
        """Disable logging for a specific category."""
        DEBUG_CATEGORIES[category] = False
        self.basic(
            "general",
            f"Debug category '{category}' disabled",
            context={"category": category},
            module="debug_logger"
        )
    
    def get_debug_status(self) -> Dict[str, Any]:
        """Get current debug configuration status."""
        return {
            "current_level": DEBUG_LEVEL,
            "level_num": self.current_level,
            "output_format": DEBUG_OUTPUT_FORMAT,
            "log_to_file": DEBUG_LOG_TO_FILE,
            "log_to_console": DEBUG_LOG_TO_CONSOLE,
            "log_file": DEBUG_LOG_FILE,
            "enabled_categories": {k: v for k, v in DEBUG_CATEGORIES.items() if v},
            "disabled_categories": {k: v for k, v in DEBUG_CATEGORIES.items() if not v}
        }


# Global debug logger instance
debug_logger = DebugLogger()

# Convenience functions for easy access
def log_basic(category: str, message: str, context: Optional[Dict[str, Any]] = None, 
              module: str = "debug", **kwargs):
    """Log a BASIC level debug message."""
    debug_logger.basic(category, message, context, module, **kwargs)

def log_detailed(category: str, message: str, context: Optional[Dict[str, Any]] = None, 
                 module: str = "debug", **kwargs):
    """Log a DETAILED level debug message."""
    debug_logger.detailed(category, message, context, module, **kwargs)

def log_verbose(category: str, message: str, context: Optional[Dict[str, Any]] = None, 
                module: str = "debug", **kwargs):
    """Log a VERBOSE level debug message."""
    debug_logger.verbose(category, message, context, module, **kwargs)