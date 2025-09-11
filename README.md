
### Testing Instructions

This guide provides the necessary steps to set up and test the AURA project. The primary testing path is configured to use a locally-hosted `gpt-oss` model via Ollama, showcasing AURA's capabilities as a true local agent.

#### **Prerequisites**

Before you begin, please ensure you have the following installed:

1.  **Python 3.11**
2.  **Conda** (for environment management)
3.  **Homebrew** (for installing macOS command-line tools)
4.  **Ollama:** for running the `gpt-oss` reasoning model locally. ([Download here](https://ollama.com/))
5.  **LM Studio:** for running the vision model locally. ([Download here](https://lmstudio.ai/))
6.  **Git** for cloning the repository.

#### **1. Environment Setup**

First, clone the repository and set up the Python environment.

```bash
# Clone the repository
git clone [Your-Public-Repo-URL]
cd aura

# Create and activate the Conda environment
conda create --name aura python=3.11 -y
conda activate aura

# Install required Python packages
pip install -r requirements.txt

# Install macOS command-line tools required by the AutomationModule
brew install cliclick
```

#### **2. Enabling Accessibility Permissions (Critical Step)**

AURA requires Accessibility permissions to see and control other applications on your Mac. This is essential for the "fast path" accessibility features and GUI automation to work.

1.  Open **System Settings** on your Mac.
2.  Navigate to **Privacy & Security**.
3.  Scroll down and click on **Accessibility**.
4.  You will see a list of applications. You need to grant permission to the application you will use to **run the AURA script**.
      * If you are running `python aura/main.py` from the standard **Terminal**, find `Terminal` in the list and toggle the switch **ON**.
      * If you are using another terminal like **iTerm2**, enable it for that application.
      * If you are running the script from within **Visual Studio Code's** integrated terminal, you must grant permissions to `Visual Studio Code`.
5.  You may be prompted to enter your password to make this change.

*AURA's internal `PermissionValidator` will check for these permissions at startup, and a success message will be logged in `aura.log`*.

#### **3. Local Model Setup**

For this demonstration, AURA uses two local models.

**A. Reasoning Model (Ollama):**

1.  **Pull the `gpt-oss` Model:** Open your terminal and run the following command to download and serve the required reasoning model with Ollama.
    ```bash
    ollama run gpt-oss:120b
    ```
    *Note: This is a large model and may take some time to download. You can leave this running in a separate terminal window.*

**B. Vision Model (LM Studio):**

1.  Open the LM Studio application.
2.  Search for and download a vision-capable model (e.g., `llava`, `Phi-3-vision`).
3.  Navigate to the Local Server tab ( **\<-\>** icon) and select the downloaded vision model.
4.  Click **"Start Server"**. This will host the vision model at `http://localhost:1234/v1`.

#### **4. AURA Configuration**

You must configure AURA to use your local models.

1.  **Open the configuration file:** `aura/config.py`
2.  **Configure the Reasoning Model:**
      * Find the `REASONING_API_BASE` variable and change it to your local Ollama endpoint:
        ```python
        # old
        # REASONING_API_BASE = "https://ollama.com"
        # new
        REASONING_API_BASE = "http://localhost:11434"
        ```
      * Find the `REASONING_API_KEY` variable and clear it, as a local server does not require a key:
        ```python
        # old
        # REASONING_API_KEY = os.getenv(...)
        # new
        REASONING_API_KEY = ""
        ```
3.  **Verify the Vision Model Endpoint:**
      * Ensure the `VISION_API_BASE` is set to the LM Studio default:
        ```python
        VISION_API_BASE = "http://localhost:1234/v1"
        ```
4.  Save the `config.py` file.

#### **5. Running AURA**

With the environment and configuration set up, you can now run the application.

```bash
# From the root directory of the project
python aura/main.py
```

Upon successful startup, you will see a message "✅ AURA is running. Press Ctrl+C to stop." and AURA will begin listening for the wake word.

#### **6. Sample Commands to Test**

To test AURA's core features, please use the wake word **"Computer"** before each command.

**A. Test Basic Conversation & Introduction**

  * `"Computer, introduce yourself."`
  * `"Computer, how are you today?"`

**B. Test GUI Automation**

  * (With your browser open) `"Computer, search for the OpenAI Open Model Hackathon."`
  * (With a text editor open) `"Computer, type 'Hello, world!'"`

**C. Test Stateful Task Context (Deferred Action - *Wildcard* Feature)**

1.  Open a code editor (like VS Code or TextEdit) with a blank file.
2.  Say: `"Computer, write a Python function that calculates the Fibonacci sequence."`
3.  AURA will respond: *"Code generated. Click where you want me to place it."*
4.  Click your mouse anywhere in the blank file. AURA will type the complete, formatted function.

**D. Test Conversational Context (Follow-up Command)**

1.  Immediately after the Fibonacci function is written, say:
2.  `"Computer, now can you write that in TensorFlow?"`
3.  AURA should understand that "that" refers to the previous request and generate a new machine learning-focused code snippet.

**E. Test Visual & Accessibility Context ("Explain Selected Text" - *Wildcard* Feature)**

1.  Open any webpage or PDF with a substantial amount of text.
2.  Use your mouse to highlight a paragraph.
3.  Say: `"Computer, can you explain the selected text?"`
4.  AURA will provide a spoken summary and explanation of the text you highlighted.

-----
