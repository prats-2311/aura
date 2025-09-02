---

### **AURA Performance Upgrade: Hybrid Architecture Implementation Plan**

**Project:** AURA (Autonomous User-side Robotic Assistant)
**Upgrade Strategy:** Implement a Hybrid "Fast Path / Slow Path" Architecture to drastically reduce latency for GUI automation tasks.

### **1. Requirement Specification (What we are building)**

#### **Requirement 11: High-Speed, Non-Visual Element Detection ("Fast Path")**

- **User Story:** As a user, I want AURA to respond to my GUI commands almost instantly for standard applications, so the interaction feels fluid and efficient.
- **Acceptance Criteria:**
  1.  WHEN a user issues a GUI command (e.g., "click the 'File' menu"), the system SHALL first attempt to locate the element using the operating system's Accessibility API.
  2.  IF the element is found via the Accessibility API, the system SHALL retrieve its coordinates and execute the action _without_ capturing the screen or using the vision model.
  3.  WHEN using the Accessibility API, the time from command recognition to action execution SHALL be less than 2 seconds.
  4.  THE system MUST be able to find elements in native macOS applications (like Finder, System Settings) and in major web browsers (like Safari or Chrome).

#### **Requirement 12: Vision Model Fallback ("Slow Path")**

- **User Story:** As a user, I want AURA to still be able to control any application, even if it's non-standard or doesn't support accessibility features.
- **Acceptance Criteria:**
  1.  IF the Accessibility API fails to find a requested element, the system SHALL automatically and seamlessly fall back to the existing vision-based workflow.
  2.  WHEN falling back, the system SHALL capture a screenshot, send it to the local vision model (`Gemma 3`), and proceed with the perception-reasoning loop as currently implemented.
  3.  THE system MAY provide subtle audio feedback (e.g., a slightly different "thinking" sound) to indicate it is using the more intensive visual analysis.

---

### **2. Design Document Update (How it will work)**

#### **2.1. New Component: Accessibility Module (`modules/accessibility.py`)**

- **Purpose:** To provide a high-speed, non-visual interface for querying the OS about the UI elements of the currently active application. It acts as the "Fast Path".
- **Dependencies:** `pyobjc`, specifically the `AppKit` and `Accessibility` frameworks (which are already in your Conda environment).
- **Key Methods:**
  ```python
  class AccessibilityModule:
      def find_element(self, role: str, label: str) -> Optional[Dict[str, Any]]:
          """
          Finds a UI element and returns its details, including coordinates.
          Returns None if not found.
          """
          pass
  ```

#### **2.2. Updated High-Level Architecture**

The `Orchestrator`'s workflow for GUI commands will be fundamentally changed.

- **New Conceptual Flow Diagram:**

  ```mermaid
  graph TD
      subgraph Command Execution
          UserCommand[User GUI Command] --> Orchestrator
          Orchestrator -- "1. Attempt Fast Path" --> Accessibility[Accessibility Module]
          Accessibility -- "Success (Coords Found)" --> Orchestrator
          Orchestrator -- "4a. Execute Action" --> Automation[Automation Module]
          Automation --> Desktop

          Accessibility -- "Failure (Not Found)" --> Orchestrator
          Orchestrator -- "2. Fallback to Slow Path" --> Vision[Vision Module]
          Vision -- "Screen Context" --> Orchestrator
          Orchestrator -- "3. Reason" --> Reasoning[Reasoning Module]
          Reasoning -- "Action Plan" --> Orchestrator
          Orchestrator -- "4b. Execute Action" --> Automation
      end
  ```

---

### **3. Implementation Plan and Tasks (The "How-To" for Kiro)**

#### **Phase 1: Environment and Dependency Validation**

- **Objective:** Confirm that the necessary Python bindings for macOS Accessibility are present and functional.
- **Tasks:**
  1.  **Validate Dependencies:** From your `conda list`, we can confirm `pyobjc-framework-Accessibility` is installed. This is the key dependency.
  2.  **Create a Test Script:**
      - **Instruction to Kiro:** "Kiro, create a new test file named `test_accessibility_api.py`. This script will import the `AppKit` and `Accessibility` frameworks and attempt to get the title of the frontmost application window to verify the connection to the OS Accessibility API is working."

#### **Phase 2: Building the Accessibility Module**

- **Objective:** To implement the core logic for the "Fast Path" element detection.
- **Tasks:**
  1.  **Create the Module File:**
      - **Instruction to Kiro:** "Kiro, create a new file at `aura/modules/accessibility.py`."
  2.  **Implement the `AccessibilityModule` Class:**
      - **Instruction to Kiro:** "Kiro, in `accessibility.py`, implement the `AccessibilityModule` class. It needs to recursively traverse the accessibility tree of the active application to find UI elements that match a given role (like 'AXButton') and label (like 'Sign In'). When an element is found, the method should return a dictionary containing its coordinates and size."

#### **Phase 3: Integrating the Hybrid Logic into the Orchestrator**

- **Objective:** To modify the `Orchestrator` to use the new hybrid model, prioritizing the "Fast Path".
- **Tasks:**
  1.  **Import and Initialize:**
      - **Instruction to Kiro:** "Kiro, modify `orchestrator.py` to import and initialize the new `AccessibilityModule` in its `__init__` method."
  2.  **Modify the `execute_command` Method:**
      - **Instruction to Kiro:** "Kiro, refactor the `execute_command` method in `orchestrator.py`. For GUI-related command types ('click', 'type', etc.), it must first call the `accessibility_module.find_element()` method. If this returns valid coordinates, it should build a simple action plan and send it directly to the `AutomationModule`, completely bypassing the `VisionModule` and `ReasoningModule`. Only if it returns `None` should it proceed with the existing `_perform_screen_perception` workflow."
  3.  **Refine the Automation Call:** Your automation module already uses the reliable `cliclick` tool. The coordinates returned by the Accessibility API can be passed directly to your existing `cliclick`-based click functions.

#### **Phase 4: Testing and Validation**

- **Objective:** To ensure the new hybrid system is working correctly and providing the expected speed benefits.
- **Tasks:**
  1.  **Unit Tests:**
      - **Instruction to Kiro:** "Kiro, create a new test file `tests/test_accessibility.py` to write unit tests for the `AccessibilityModule`. We will need to mock the responses from the OS API."
  2.  **Integration Tests:**
      - **Instruction to Kiro:** "Kiro, create a new integration test file `tests/test_hybrid_orchestration.py`. This test will run a command like 'click the File menu' on a native application (like Finder). It should assert that the `VisionModule` was _not_ called, verifying that the 'Fast Path' was successfully used."
  3.  **Manual E2E Testing:**
      - Manually test AURA against a variety of targets:
        - **Native App (e.g., Finder):** Should be nearly instant.
        - **Standard Web Page (e.g., Wikipedia):** Should be nearly instant.
        - **Web App with Canvas (e.g., a web-based game):** Should be slower, as it will correctly fall back to the vision model.
