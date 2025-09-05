Based on a thorough analysis of your existing codebase (`orchestrator.py`, `config.py`, and `main.py`), here is a detailed, step-by-step implementation plan to integrate the advanced conversational and deferred action features into AURA.

This plan is designed to be implemented sequentially and leverages your current modular architecture effectively.

### **Phase 1: Foundational Changes - Upgrading the Orchestrator for Intent Recognition and State Management**

The first step is to evolve the `Orchestrator` from a simple command classifier into a more intelligent intent recognizer and state manager.

**1.1. Add New State Variables to `Orchestrator.__init__`**

In `orchestrator.py`, update the `Orchestrator`'s `__init__` method to track the new stateful information.

```python
# In orchestrator.py, inside Orchestrator.__init__
# ... existing initializations

# Add these new properties for state management
self.is_waiting_for_user_action = False
self.pending_action_payload = None
self.deferred_action_type = None
self.mouse_listener_thread = None
```

**1.2. Create New Prompts in `config.py`**

Add the following prompts to `config.py`. These are crucial for the new intent recognition layer.

```python
# In config.py, add these new prompts

INTENT_RECOGNITION_PROMPT = """
Analyze the user's command to identify its primary intent and extract key entities.
Choose one primary intent from this list: ['gui_interaction', 'conversational_chat', 'deferred_action', 'question_answering'].

Command: "{command}"

Respond ONLY with a JSON object following this structure:
- For 'gui_interaction': {"intent": "gui_interaction", "command": "{original_command}"}
- For 'conversational_chat': {"intent": "conversational_chat", "query": "{original_command}"}
- For 'question_answering': {"intent": "question_answering", "question": "{original_command}"}
- For 'deferred_action': {"intent": "deferred_action", "content_request": "...", "final_action": "type"}
"""

CONVERSATIONAL_PROMPT = """
You are AURA, a helpful and friendly AI assistant.
Respond to the user's message in a conversational and helpful tone.
User's message: "{command}"
"""

CODE_GENERATION_PROMPT = """
You are an expert code generation assistant.
Generate a high-quality, well-formatted code snippet based on the user's request.
User's request: "{request}"
"""
```

**1.3. Create the Global Mouse Listener Utility**

This is a new component. Create a new file, `utils/mouse_listener.py` (you may need to create the `utils` directory). You will need to install a new dependency: `pip install pynput`.

```python
# In a new file: utils/mouse_listener.py
import threading
from pynput import mouse

class GlobalMouseListener:
    def __init__(self, callback):
        self.callback = callback
        self.listener = None
        self.listener_thread = None

    def on_click(self, x, y, button, pressed):
        if pressed:
            # On any mouse press, call the callback and stop listening
            self.callback()
            return False  # This stops the listener

    def start(self):
        if self.listener_thread and self.listener_thread.is_alive():
            return  # Listener is already running

        self.listener = mouse.Listener(on_click=self.on_click)
        # Run the listener in a daemon thread so it doesn't block the main app
        self.listener_thread = threading.Thread(target=self.listener.run, daemon=True)
        self.listener_thread.start()

    def stop(self):
        if self.listener:
            self.listener.stop()
```

### **Phase 2: Reworking the Command Execution Flow in `Orchestrator`**

Now, you will modify the core command execution logic to use the new intent recognition system.

**2.1. Create a New `_recognize_intent` Method**

In `orchestrator.py`, add a new method to handle the call to the reasoning model for intent recognition.

```python
# In orchestrator.py, inside the Orchestrator class
import json
from config import INTENT_RECOGNITION_PROMPT

# ...

    def _recognize_intent(self, command: str) -> Dict[str, Any]:
        """Uses the reasoning model to classify the user's intent."""
        try:
            prompt = INTENT_RECOGNITION_PROMPT.format(command=command)
            # We don't need screen context for this initial classification
            response_plan = self.reasoning_module.get_action_plan(prompt, {})
            # The 'plan' will contain the JSON response string
            intent_json = json.loads(response_plan.get('plan', '{}'))
            return intent_json
        except Exception as e:
            logger.error(f"Intent recognition failed: {e}")
            # Fallback to default GUI interaction for safety
            return {"intent": "gui_interaction", "command": command}
```

**2.2. Modify `_execute_command_internal` to Act as a Router**

This is the most important change. You will refactor `_execute_command_internal` to first recognize the intent and then route the command to the correct handler. Your old regex-based classification will now be a fallback within the `gui_interaction` path.

```python
# In orchestrator.py, REFACTOR the _execute_command_internal method

    def _execute_command_internal(self, command: str) -> Dict[str, Any]:
        """Internal command execution with intent recognition and routing."""
        execution_id = f"cmd_{int(time.time() * 1000)}"

        # New Step 1: Recognize Intent
        logger.info(f"[{execution_id}] Step 1: Recognizing intent for command: '{command}'")
        intent_data = self._recognize_intent(command)
        intent = intent_data.get("intent", "gui_interaction")

        # New Step 2: Route based on Intent
        logger.info(f"[{execution_id}] Intent recognized: {intent}. Routing to handler.")

        if self.is_waiting_for_user_action:
             # If AURA is waiting, assume the command is a cancellation
             logger.warning("Received a new command while waiting for user action. Cancelling deferred action.")
             self._reset_deferred_action_state()
             # Fall through to process the new command

        if intent == 'conversational_chat':
            return self._handle_conversational_query(execution_id, command)
        elif intent == 'deferred_action':
            return self._handle_deferred_action_request(execution_id, intent_data)
        elif intent == 'question_answering':
             # Your existing question answering logic
             execution_context = self._initialize_execution_context(execution_id, command)
             return self._route_to_question_answering(command, execution_context)
        elif intent == 'gui_interaction':
            # This is where your OLD _execute_command_internal logic now lives
            return self._handle_gui_interaction(execution_id, command)
        else:
            logger.warning(f"Unknown intent '{intent}'. Defaulting to GUI interaction.")
            return self._handle_gui_interaction(execution_id, command)

```

### **Phase 3: Implementing the New Handlers**

Now, create the new methods that `_execute_command_internal` will call.

**3.1. Create `_handle_conversational_query`**

This method handles general chat.

```python
# In orchestrator.py, inside the Orchestrator class
from config import CONVERSATIONAL_PROMPT

# ...

    def _handle_conversational_query(self, execution_id: str, query: str) -> Dict[str, Any]:
        """Handles a direct conversational query."""
        logger.info(f"[{execution_id}] Handling conversational query.")
        try:
            prompt = CONVERSATIONAL_PROMPT.format(command=query)
            response_plan = self.reasoning_module.get_action_plan(prompt, {})

            # For conversation, the response is in the 'plan' as a speak action
            # You may need to adjust your reasoning module's output for this
            response_message = "I'm not sure how to respond to that."
            if response_plan and response_plan.get('plan'):
                 # Assuming the LLM returns a speak action
                 speak_action = next((action for action in response_plan['plan'] if action.get("action") == "speak"), None)
                 if speak_action:
                     response_message = speak_action.get("message", response_message)

            self.feedback_module.speak(response_message)
            return {"status": "completed", "response": response_message}
        except Exception as e:
            logger.error(f"Conversational query failed: {e}")
            self.feedback_module.play("failure")
            return {"status": "failed", "error": str(e)}
```

**3.2. Create `_handle_deferred_action_request`**

This method starts the multi-step "write code" process.

```python
# In orchestrator.py, inside the Orchestrator class
from config import CODE_GENERATION_PROMPT
from utils.mouse_listener import GlobalMouseListener

# ...

    def _handle_deferred_action_request(self, execution_id: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handles the first part of a deferred action, like generating code."""
        logger.info(f"[{execution_id}] Handling deferred action request.")
        try:
            content_request = intent_data.get("content_request")
            self.deferred_action_type = intent_data.get("final_action", "type")

            # Step 1: Generate the content
            prompt = CODE_GENERATION_PROMPT.format(request=content_request)
            response_plan = self.reasoning_module.get_action_plan(prompt, {})

            # Assuming the generated code is in the 'plan' of the response
            self.pending_action_payload = response_plan.get('plan', "Error: Could not generate content.")

            # Step 2: Change state and prompt user
            self.is_waiting_for_user_action = True
            self.feedback_module.speak("Okay, I have the content ready. Please click where you want me to write it.")

            # Step 3: Start the mouse listener
            self.mouse_listener = GlobalMouseListener(callback=self._on_deferred_action_trigger)
            self.mouse_listener.start()

            return {"status": "waiting_for_user", "message": "Awaiting user click to continue."}
        except Exception as e:
            logger.error(f"Deferred action request failed: {e}")
            self._reset_deferred_action_state()
            return {"status": "failed", "error": str(e)}
```

**3.3. Create the Trigger Callback and State Reset Methods**

These methods will be called by the mouse listener and are essential for completing the workflow and ensuring AURA can switch back to general talking.

```python
# In orchestrator.py, inside the Orchestrator class

    def _on_deferred_action_trigger(self):
        """Callback function for when the user clicks to trigger the deferred action."""
        if not self.is_waiting_for_user_action:
            return

        logger.info("Deferred action triggered by user click.")

        # Stop the listener
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None

        try:
            # Construct and execute the final action plan
            final_plan = {
                "plan": [{
                    "action": self.deferred_action_type,
                    "text": self.pending_action_payload
                }]
            }
            # Create a dummy execution context for this final step
            execution_context = {"plan": final_plan, "execution_id": f"deferred_{int(time.time())}"}
            self._perform_action_execution(execution_context)
            self.feedback_module.play("success")
        except Exception as e:
            logger.error(f"Executing deferred action failed: {e}")
            self.feedback_module.play("failure")
        finally:
            # CRITICAL: Reset state to return to normal operation
            self._reset_deferred_action_state()

    def _reset_deferred_action_state(self):
        """Resets all state variables related to a deferred action."""
        logger.info("Resetting deferred action state.")
        self.is_waiting_for_user_action = False
        self.pending_action_payload = None
        self.deferred_action_type = None
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
```

By following this detailed plan, you will successfully upgrade AURA to be a stateful, context-aware conversational agent capable of handling complex, multi-step tasks while retaining the ability to seamlessly switch back to general conversation.
