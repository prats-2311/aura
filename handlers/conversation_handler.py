"""
Conversation Handler for AURA Command Processing

This module handles conversational chat interactions, providing natural language
responses for general questions, greetings, and casual conversation beyond
GUI automation tasks.
"""

import time
from typing import Dict, Any
from .base_handler import BaseHandler


class ConversationHandler(BaseHandler):
    """
    Handles conversational chat interactions.
    
    This handler processes natural conversation commands like:
    - Greetings ("Hello", "Good morning")
    - General questions ("Tell me a joke", "How are you?")
    - Help requests ("What can you do?", "How can you help me?")
    - Casual conversation and small talk
    
    The handler uses the reasoning module with conversational prompts to
    generate appropriate, contextual responses that are then spoken to the user.
    """
    
    def handle(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process conversational queries and provide natural responses.
        
        Args:
            command: Conversational query (e.g., "Hello, how are you?")
            context: Execution context with intent and system state
            
        Returns:
            Execution result with conversational response
        """
        # Validate input
        if not self._validate_command(command):
            return self._create_error_result("Invalid or empty conversational query")
        
        # Log execution start
        start_time = self._log_execution_start(command, context)
        execution_id = context.get('execution_id', f"conv_{int(time.time())}")
        
        try:
            self.logger.info(f"[{execution_id}] Processing conversational query: {command[:50]}...")
            
            # TODO: Full implementation will be completed in Task 3.1
            # For now, provide basic structure and placeholder response
            
            # Build conversation context
            conversation_context = self._build_conversation_context()
            
            # Generate conversational response (placeholder for now)
            response = self._generate_conversational_response(command, conversation_context, execution_id)
            
            # Speak the response
            self._speak_response(response, execution_id)
            
            # Update conversation history
            self._update_conversation_history(command, response)
            
            result = self._create_success_result(
                "Conversational response provided",
                interaction_type="conversation",
                response=response,
                conversation_context=conversation_context
            )
            
            # Log execution end
            self._log_execution_end(start_time, result, context)
            return result
            
        except Exception as e:
            return self._handle_module_error("conversation_handler", e, "conversational query processing")
    
    def _generate_conversational_response(self, query: str, context: Dict[str, Any], execution_id: str) -> str:
        """
        Generate a conversational response using the reasoning module.
        
        Args:
            query: User's conversational query
            context: Conversation context
            execution_id: Unique execution identifier
            
        Returns:
            Generated conversational response
        """
        try:
            self.logger.debug(f"[{execution_id}] Generating conversational response for: {query[:50]}...")
            
            reasoning_module = self._get_module_safely('reasoning_module')
            if reasoning_module:
                # Use the new process_query method with conversational prompt template
                response = reasoning_module.process_query(
                    query=query,
                    prompt_template='CONVERSATIONAL_PROMPT',
                    context=context
                )
                
                # Validate and clean the response
                if response and isinstance(response, str):
                    response = response.strip()
                    if len(response) > 500:  # Reasonable limit for conversational responses
                        response = response[:500] + "..."
                        self.logger.debug(f"[{execution_id}] Response truncated to 500 characters")
                    
                    self.logger.info(f"[{execution_id}] Generated conversational response: {response[:100]}...")
                    return response
                else:
                    self.logger.warning(f"[{execution_id}] Invalid response from reasoning module: {type(response)}")
                    return "I'm having trouble generating a proper response. Could you try rephrasing your question?"
            else:
                # Fallback response when reasoning module is not available
                self.logger.warning(f"[{execution_id}] Reasoning module not available")
                return "I'm here to help! However, my conversational features are currently unavailable. Please try again later."
                
        except Exception as e:
            self.logger.error(f"[{execution_id}] Conversational response generation failed: {e}")
            return self._get_error_fallback_response(str(e))
    
    def _get_error_fallback_response(self, error_message: str) -> str:
        """
        Generate an appropriate fallback response based on the error type.
        
        Args:
            error_message: The error message that occurred
            
        Returns:
            Appropriate fallback response
        """
        error_lower = error_message.lower()
        
        if "timeout" in error_lower or "timed out" in error_lower:
            return "I'm taking a bit longer than usual to think about that. Could you try asking again?"
        elif "connection" in error_lower or "network" in error_lower:
            return "I'm having trouble with my connection right now. Please try again in a moment."
        elif "api" in error_lower or "service" in error_lower:
            return "My reasoning service is having some issues. Please try again shortly."
        elif "empty" in error_lower or "invalid" in error_lower:
            return "I didn't quite understand that. Could you rephrase your question?"
        else:
            return "I'm having a bit of trouble right now. Please try again, and I'll do my best to help!"
    
    def _speak_response(self, response: str, execution_id: str) -> None:
        """
        Speak the conversational response to the user.
        
        Args:
            response: Response text to speak
            execution_id: Unique execution identifier
        """
        try:
            # Try feedback module first
            feedback_module = self._get_module_safely('feedback_module')
            if feedback_module:
                try:
                    feedback_module.speak(response)
                    self.logger.debug(f"[{execution_id}] Response spoken via feedback module")
                    return
                except Exception as e:
                    self.logger.warning(f"[{execution_id}] Feedback module speech failed: {e}")
            
            # Fallback to audio module
            audio_module = self._get_module_safely('audio_module')
            if audio_module:
                try:
                    audio_module.text_to_speech(response)
                    self.logger.debug(f"[{execution_id}] Response spoken via audio module")
                    return
                except Exception as e:
                    self.logger.warning(f"[{execution_id}] Audio module speech failed: {e}")
            
            self.logger.warning(f"[{execution_id}] No audio modules available for speaking response")
            
        except Exception as e:
            self.logger.error(f"[{execution_id}] Error speaking conversational response: {e}")
    
    def _build_conversation_context(self) -> Dict[str, Any]:
        """
        Build conversation context from history and current state.
        
        Returns:
            Conversation context for prompt generation
        """
        try:
            # Get conversation history
            conversation_history = getattr(self, '_conversation_history', [])
            
            # Get system state from orchestrator if available
            system_state = 'ready'
            if hasattr(self.orchestrator, 'get_system_state'):
                try:
                    system_state = self.orchestrator.get_system_state()
                except Exception as e:
                    self.logger.debug(f"Could not get system state: {e}")
            
            # Build comprehensive context
            context = {
                'conversation_history': conversation_history,
                'system_state': system_state,
                'timestamp': time.time(),
                'conversation_length': len(conversation_history),
                'user_preferences': self._get_user_preferences(),
                'session_info': {
                    'start_time': getattr(self, '_session_start_time', time.time()),
                    'total_exchanges': len(conversation_history)
                }
            }
            
            self.logger.debug(f"Built conversation context with {len(conversation_history)} history items")
            return context
            
        except Exception as e:
            self.logger.warning(f"Error building conversation context: {e}")
            return {
                'conversation_history': [],
                'system_state': 'ready',
                'timestamp': time.time()
            }
    
    def _get_user_preferences(self) -> Dict[str, Any]:
        """
        Get user preferences for conversational interactions.
        
        Returns:
            User preferences dictionary
        """
        try:
            # TODO: In the future, this could load from user settings
            # For now, return default preferences
            return {
                'response_style': 'friendly',
                'verbosity': 'moderate',
                'technical_level': 'adaptive'
            }
        except Exception as e:
            self.logger.debug(f"Error getting user preferences: {e}")
            return {}
    
    def _update_conversation_history(self, query: str, response: str) -> None:
        """
        Update conversation history with the latest exchange.
        
        Args:
            query: User's conversational query
            response: AURA's response
        """
        try:
            # Initialize conversation history if needed
            if not hasattr(self, '_conversation_history'):
                self._conversation_history = []
                self._session_start_time = time.time()
            
            # Create exchange record with metadata
            exchange = {
                'timestamp': time.time(),
                'user_query': query.strip(),
                'aura_response': response.strip(),
                'query_length': len(query),
                'response_length': len(response),
                'exchange_id': f"conv_{int(time.time() * 1000)}"
            }
            
            # Add the exchange to history
            self._conversation_history.append(exchange)
            
            # Manage history size based on configuration
            max_history_size = getattr(self.orchestrator, 'config', {}).get('CONVERSATION_CONTEXT_SIZE', 10)
            if len(self._conversation_history) > max_history_size:
                # Remove oldest exchanges but keep the structure
                removed_count = len(self._conversation_history) - max_history_size
                self._conversation_history = self._conversation_history[-max_history_size:]
                self.logger.debug(f"Trimmed {removed_count} old exchanges from conversation history")
            
            self.logger.debug(f"Updated conversation history: {len(self._conversation_history)} exchanges, "
                            f"latest query: '{query[:50]}...', response: '{response[:50]}...'")
            
            # Optional: Persist conversation history for future sessions
            self._persist_conversation_history()
            
        except Exception as e:
            self.logger.warning(f"Error updating conversation history: {e}")
    
    def _persist_conversation_history(self) -> None:
        """
        Persist conversation history for future sessions (optional feature).
        """
        try:
            # TODO: In the future, this could save to a file or database
            # For now, just keep in memory
            pass
        except Exception as e:
            self.logger.debug(f"Error persisting conversation history: {e}")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current conversation session.
        
        Returns:
            Conversation session summary
        """
        try:
            history = getattr(self, '_conversation_history', [])
            session_start = getattr(self, '_session_start_time', time.time())
            
            if not history:
                return {
                    'status': 'no_conversation',
                    'message': 'No conversation history available'
                }
            
            # Calculate session statistics
            total_exchanges = len(history)
            session_duration = time.time() - session_start
            avg_query_length = sum(ex.get('query_length', 0) for ex in history) / total_exchanges
            avg_response_length = sum(ex.get('response_length', 0) for ex in history) / total_exchanges
            
            # Get recent topics (simple keyword extraction from recent queries)
            recent_queries = [ex['user_query'] for ex in history[-3:]]
            
            return {
                'status': 'active',
                'total_exchanges': total_exchanges,
                'session_duration_minutes': round(session_duration / 60, 1),
                'avg_query_length': round(avg_query_length, 1),
                'avg_response_length': round(avg_response_length, 1),
                'recent_queries': recent_queries,
                'session_start': session_start,
                'last_exchange': history[-1]['timestamp'] if history else None
            }
            
        except Exception as e:
            self.logger.warning(f"Error generating conversation summary: {e}")
            return {
                'status': 'error',
                'message': f'Error generating summary: {str(e)}'
            }