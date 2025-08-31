Of course. This is the perfect use case for a spec-driven IDE like Kiro. I will provide a complete, in-depth, phased implementation plan.

This document is structured as a series of specifications ("specs") that you can provide directly to Kiro. Each spec describes a component of the AURA project, and the phased plan tells Kiro the exact order in which to build and integrate them.

---

### **AURA - Kiro IDE Implementation Specification (v2.2)**

**Project:** AURA (Autonomous User-side Robotic Assistant)
**Target IDE:** Kiro IDE
**Architecture:** Hybrid Perception-Reasoning Model

### **Environment and Project Setup**

**Objective:** To create a self-contained Conda environment for AURA, ensuring all dependencies are isolated. We will also establish the project's folder structure.

**Workflow:** This is a foundational, one-time setup. You will execute these commands in your terminal. Kiro will then be used within this activated environment to build the project files.

---

#### **Spec 1: Conda Environment Setup**

**Instruction:** "First, I will set up the Conda environment. I will perform these steps in my terminal."

1.  **Create the Conda Environment:**

    ```bash
    conda create --name aura python=3.11 -y
    ```

2.  **Activate the Environment:**

    ```bash
    conda activate aura
    ```

    _(**Note:** All subsequent commands and development should be performed inside this activated environment.)_

---

### **Phase 0: Project Setup and Configuration**

**Objective:** To establish the foundational configuration and folder structure for the project. This phase ensures all API keys, model names, and settings are centralized for easy management.

**Workflow:** Kiro will create the initial project files and directories. The most critical file is `config.py`, which will act as the single source of truth for all settings.

---

#### **Spec 1: Project Structure**

**Instruction to Kiro:** "Kiro, set up the following project structure."

```
/AURA/
|-- /modules/
|   |-- __init__.py
|   |-- vision.py
|   |-- reasoning.py
|   |-- audio.py
|   |-- automation.py
|   |-- feedback.py
|-- /assets/
|   |-- /sounds/
|       |-- success.wav
|       |-- failure.wav
|       |-- thinking.wav
|-- config.py
|-- orchestrator.py
|-- main.py
|-- requirements.txt
|-- README.md
```

---

#### **Spec 2: Configuration File (`config.py`)**

**Instruction to Kiro:** "Kiro, create the file `config.py` with the following spec. This file will hold all configuration variables for the AURA agent."

```python
# config.py

# -- API Endpoints and Keys --
# Local server for vision model
VISION_API_BASE = "http://localhost:1234/v1"
# Cloud endpoint for reasoning model
REASONING_API_BASE = "https://api.ollama.ai/v1" # Example URL from a turbo plan
REASONING_API_KEY = "your_ollama_cloud_api_key_here" # API Key for the cloud service

# -- Model Names --
VISION_MODEL = "google/gemma-3-4b" # The model name in LM Studio
REASONING_MODEL = "gpt-oss:latest" # The model name in your Ollama cloud service

# -- Wake Word Configuration --
# Get your key from Picovoice Console
PORCUPINE_API_KEY = "your_porcupine_api_key_here"
WAKE_WORD = "computer" # or "jarvis", "aura", etc.

# -- Prompt Engineering --
# The generic prompt to get a description of the screen from the vision model
VISION_PROMPT = """
Analyze the provided screenshot and describe it in structured JSON format. Identify all interactive elements including buttons, links, and input fields. For each element, provide a description, its text content if any, and its bounding box coordinates [x1, y1, x2, y2]. Also, transcribe any significant text blocks.
"""

# The meta-prompt for the reasoning model
REASONING_META_PROMPT = """
You are AURA, an AI assistant. Your goal is to help a user by controlling their computer. You will be given a user's command and a JSON object describing the current state of their screen. Your task is to reason about this information and return a precise action plan in JSON format. The action plan should be a list of simple, atomic steps. Possible actions are: 'click', 'double_click', 'type', 'scroll', 'speak', and 'finish'. For 'click' and 'double_click', provide the target coordinates [x, y]. For 'type', provide the text to type. For 'speak', provide the message for the user. The 'finish' action indicates the task is complete.
"""

# -- Audio Settings --
# Path to sound effects for feedback
SOUNDS = {
    "success": "assets/sounds/success.wav",
    "failure": "assets/sounds/failure.wav",
    "thinking": "assets/sounds/thinking.wav"
}
```

---

### **Phase 1: Building and Validating the Core AI Modules**

**Objective:** To implement the classes that will communicate with the local vision model and the cloud reasoning model. The goal is to ensure the API connections are working correctly before building more complex logic.

#### **Spec 3: Vision Module (`modules/vision.py`)**

**Instruction to Kiro:** "Kiro, create the file `modules/vision.py` with a `VisionModule` class. Implement the `describe_screen` method."

```python
# modules/vision.py
import requests
import json
from mss import mss
import base64
import config

class VisionModule:
    """Handles screen capture and communication with the local VLM."""

    def __init__(self):
        self.api_base = config.VISION_API_BASE
        self.model = config.VISION_MODEL
        self.prompt = config.VISION_PROMPT

    def capture_screen_as_base64(self) -> str:
        """Captures the screen and encodes it as a base64 string."""
        with mss() as sct:
            sct_img = sct.grab(sct.monitors[1])
            # Convert to bytes
            img_bytes = sct.shot(output=None, mon=1)
            return base64.b64encode(img_bytes).decode('utf-8')

    def describe_screen(self) -> dict:
        """Sends the screen capture to the VLM and gets a JSON description."""
        base64_image = self.capture_screen_as_base64()

        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                }
            ],
            "max_tokens": 2048,
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(f"{self.api_base}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"ERROR in VisionModule: {e}")
            return {"error": str(e)}

```

---

#### **Spec 4: Reasoning Module (`modules/reasoning.py`)**

**Instruction to Kiro:** "Kiro, create the file `modules/reasoning.py` with a `ReasoningModule` class. Implement the `get_action_plan` method."

```python
# modules/reasoning.py
import requests
import json
import config

class ReasoningModule:
    """Handles communication with the cloud-based reasoning LLM."""

    def __init__(self):
        self.api_base = config.REASONING_API_BASE
        self.api_key = config.REASONING_API_KEY
        self.model = config.REASONING_MODEL
        self.meta_prompt = config.REASONING_META_PROMPT

    def get_action_plan(self, user_command: str, screen_context: dict) -> dict:
        """Sends the command and screen context to the LLM to get an action plan."""

        prompt_content = f"""
        User Command: "{user_command}"

        Screen Context (JSON):
        {json.dumps(screen_context, indent=2)}
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.meta_prompt},
                {"role": "user", "content": prompt_content}
            ],
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(f"{self.api_base}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            # The response content is often a stringified JSON, so parse it.
            return json.loads(response.json()['choices'][0]['message']['content'])
        except Exception as e:
            print(f"ERROR in ReasoningModule: {e}")
            return {"error": str(e), "plan": [{"action": "speak", "message": "I encountered an error in my reasoning module."}]}

```

---

### **Phase 2: Implementing the Core Logic and Automation**

**Objective:** To build the orchestrator that connects the vision and reasoning modules. This phase creates a functional, text-controlled agent.

#### **Spec 5: Automation Module (`modules/automation.py`)**

**Instruction to Kiro:** "Kiro, create `modules/automation.py`. Implement an `AutomationModule` class to wrap `pyautogui` functions for executing the action plan."

```python
# modules/automation.py
import pyautogui

class AutomationModule:
    """Handles the execution of GUI actions."""

    def execute_action(self, action: dict):
        """Parses and executes a single action from the action plan."""
        action_type = action.get("action")

        if action_type == "click" or action_type == "double_click":
            coords = action.get("coordinates")
            if coords and len(coords) == 2:
                x, y = coords
                pyautogui.moveTo(x, y, duration=0.25)
                if action_type == "click":
                    pyautogui.click()
                else:
                    pyautogui.doubleClick()
                print(f"Executed {action_type} at ({x}, {y})")

        elif action_type == "type":
            text = action.get("text")
            if text:
                pyautogui.write(text, interval=0.05)
                print(f"Typed: {text}")

        elif action_type == "scroll":
            direction = action.get("direction", "down")
            amount = action.get("amount", 100)
            scroll_amount = -amount if direction == "down" else amount
            pyautogui.scroll(scroll_amount)
            print(f"Scrolled {direction} by {amount}")

        # The 'speak' and 'finish' actions will be handled by the orchestrator
```

---

#### **Spec 6: The Orchestrator (`orchestrator.py`)**

**Instruction to Kiro:** "Kiro, create `orchestrator.py`. Implement the `Orchestrator` class. This class will manage the main loop of receiving a command, using the vision and reasoning modules, and executing the plan."

```python
# orchestrator.py
from modules.vision import VisionModule
from modules.reasoning import ReasoningModule
from modules.automation import AutomationModule
# We will add audio and feedback later

class Orchestrator:
    def __init__(self):
        self.vision = VisionModule()
        self.reasoning = ReasoningModule()
        self.automation = AutomationModule()
        # self.audio = None # To be added in Phase 3
        # self.feedback = None # To be added in Phase 5

    def execute_command(self, command: str):
        print(f"Orchestrator received command: '{command}'")

        # 1. Perception: Understand the screen
        print("Perceiving screen state...")
        screen_context = self.vision.describe_screen()
        if "error" in screen_context:
            print(f"Failed to get screen context: {screen_context['error']}")
            # Handle error, maybe speak to user
            return

        # 2. Reasoning: Create an action plan
        print("Formulating action plan...")
        action_plan = self.reasoning.get_action_plan(command, screen_context)
        if "error" in action_plan:
            print(f"Failed to get action plan: {action_plan['error']}")
            # Handle error
            return

        # 3. Execution: Carry out the plan
        print("Executing plan...")
        if "plan" in action_plan:
            for step in action_plan["plan"]:
                action_type = step.get("action")
                if action_type in ["click", "double_click", "type", "scroll"]:
                    self.automation.execute_action(step)
                elif action_type == "speak":
                    # For now, just print. Will be replaced by TTS.
                    print(f"AURA says: {step.get('message')}")
                elif action_type == "finish":
                    print("Task finished.")
                    break
        else:
            print("No valid plan found in the response.")
```

---

### **Phase 3: Integrating the Voice Interface**

**Objective:** To enable full conversational control by implementing the audio modules and the main application loop with wake word detection.

#### **Spec 7: Audio & Main Application (`modules/audio.py` and `main.py`)**

**Instruction to Kiro:** "Kiro, first, implement the `AudioModule` in `modules/audio.py` for STT and TTS. Second, create `main.py` to handle the wake word detection and trigger the orchestrator."

_(This spec would contain the Python code for the `AudioModule` class using Whisper and Piper/say, and the `main.py` file using Porcupine to listen for the wake word and call `orchestrator.execute_command`. This code would be similar to the examples discussed previously.)_

---

### **Phase 4 & 5: Feature Implementation and Polish**

**Objective:** To implement the specific JAU features and add the final layer of polish with advanced audio feedback.

**Instruction to Kiro:** "Kiro, now let's refine the system.

1.  **For Web Form Filling:** Update the `REASONING_META_PROMPT` in `config.py` to include specific instructions for handling forms, asking it to identify a sequence of 'click' and 'type' actions.
2.  **For Information Extraction:** Create a new method in the `Orchestrator` called `answer_question`. If a user's command is a question, this method will instruct the `ReasoningModule` to analyze the screen context and generate a `speak` action with the answer, rather than a GUI action.
3.  **For Audio Feedback:** Create and implement the `FeedbackModule` in `modules/feedback.py` using `pygame.mixer`. Modify the `Orchestrator` to call `feedback.play('thinking')` before querying the models, and `feedback.play('success')` after the plan is complete."
