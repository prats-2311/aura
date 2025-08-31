# AURA - Autonomous User-side Robotic Assistant

AURA is a hybrid perception-reasoning AI system that enables users to control their desktop computer through natural voice commands. The system combines local vision models for screen understanding with cloud-based reasoning models for action planning, creating an intelligent assistant that can perform complex desktop automation tasks through conversational interaction.

## Features

### Core Capabilities

- 🎤 **Voice Control**: Activate with wake words and give natural language commands
- 👁️ **Screen Understanding**: Local vision models analyze your desktop in real-time
- 🧠 **Intelligent Planning**: Cloud-based LLMs create smart action sequences
- 🖱️ **Desktop Automation**: Precise GUI interactions with safety controls
- 🔊 **Audio Feedback**: Rich audio responses and status updates
- 📝 **Form Filling**: Automated web form completion through voice
- ❓ **Information Extraction**: Ask questions about screen content
- ⚙️ **Configurable**: Centralized configuration for easy customization

### Performance Optimizations

- ⚡ **Connection Pooling**: Optimized API calls with connection reuse and retry logic
- 🗄️ **Image Caching**: Intelligent caching with compression and deduplication
- 🔄 **Parallel Processing**: Concurrent execution of perception and reasoning tasks
- 📊 **Performance Monitoring**: Real-time metrics and optimization recommendations
- 🎯 **Automatic Optimization**: Self-tuning performance based on usage patterns
- 🚀 **Resource Management**: Efficient memory and CPU usage with cleanup routines

## Architecture

AURA follows a modular architecture with clear separation of concerns:

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│    Audio    │    │ Orchestrator │    │   Vision    │
│   Module    │◄──►│   (Central   │◄──►│   Module    │
│             │    │ Coordinator) │    │             │
└─────────────┘    └──────────────┘    └─────────────┘
                           │
                           ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Feedback   │    │    Config    │    │  Reasoning  │
│   Module    │◄──►│   Module     │◄──►│   Module    │
│             │    │              │    │             │
└─────────────┘    └──────────────┘    └─────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │  Automation  │
                   │   Module     │
                   │              │
                   └──────────────┘
```

## Technology Stack

- **Local Vision**: LM Studio with automatic model detection (works with any loaded model)
- **Cloud Reasoning**: Ollama Cloud or OpenAI API
- **Wake Word**: Picovoice Porcupine
- **Speech Recognition**: OpenAI Whisper
- **Text-to-Speech**: Piper TTS or system TTS
- **Screen Capture**: MSS (Multi-Screen Screenshot)
- **GUI Automation**: PyAutoGUI
- **Audio Playback**: Pygame

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 2GB free space for models and dependencies

### External Services

1. **LM Studio**: Download and install from [lmstudio.ai](https://lmstudio.ai)

   - Load **any model** you prefer (multimodal models recommended for vision tasks)
   - Start the local server on port 1234
   - AURA will automatically detect and use whatever model you have loaded

2. **Cloud Reasoning Service**: Choose one:

   - **Ollama Cloud**: Sign up at [ollama.ai](https://ollama.ai) for cloud access
   - **OpenAI**: Get API key from [platform.openai.com](https://platform.openai.com)

3. **Picovoice Console**: Get wake word detection key from [console.picovoice.ai](https://console.picovoice.ai)

## Installation

### 1. Environment Setup (Following plan.md)

**Step 1: Create the Conda Environment**

```bash
conda create --name aura python=3.11 -y
```

**Step 2: Activate the Environment**

```bash
conda activate aura
```

**Note:** All subsequent commands and development should be performed inside this activated environment, as specified in plan.md.

### 2. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Platform-specific installations may be required
# See requirements.txt for details
```

### 3. Configuration

```bash
# Copy and edit configuration
cp config.py config_local.py  # Optional: create local config

# API keys are already configured in config.py
# If you need to override them, you can set environment variables:
# export REASONING_API_KEY="your_custom_api_key_here"
# export PORCUPINE_API_KEY="your_custom_porcupine_key_here"

# Or create .env file to override defaults:
# echo "REASONING_API_KEY=your_custom_api_key_here" > .env
# echo "PORCUPINE_API_KEY=your_custom_porcupine_key_here" >> .env
```

### 4. Validate Setup

```bash
# Run comprehensive setup check
python setup_check.py

# Or test configuration only
python config.py

# Should output: ✅ Configuration is valid
```

## Usage

### Basic Usage

```bash
# Start AURA
python main.py

# Start with performance monitoring
python main.py --performance-dashboard

# Start in debug mode
python main.py --debug
```

#### Voice Interaction Flow

1. **Start AURA**: Run the application using one of the commands above
2. **Wake Word Detection**: AURA continuously listens for the wake word **"Computer"**
3. **Command Input**: After wake word detection, speak your command clearly
4. **Processing**: AURA will:
   - Capture and analyze your screen
   - Process your voice command
   - Plan the appropriate actions
   - Execute the command
   - Provide audio feedback
5. **Ready for Next Command**: AURA returns to listening for the wake word

#### Example Interaction

```
You: "Computer"
AURA: [Confirmation sound - ready for command]

You: "Click on the File menu"
AURA: [Processing sound] "I'll click on the File menu for you"
[Executes the click action]
AURA: [Success sound] "Done!"

[Returns to listening for wake word]
```

### Available Commands After Wake Word

After saying the wake word **"Computer"**, you can use any of the following command types:

#### 🖱️ **Click Commands**

- **"Click on [element]"** - Click on buttons, links, menus, etc.
  - Examples: "Click on the File menu", "Click the Submit button", "Press the OK button"
- **"Press [element]"** - Alternative to click
  - Examples: "Press the Enter key", "Press the Save button"
- **"Tap [element]"** - Touch-style interaction
  - Examples: "Tap on the search icon", "Tap the close button"

#### ⌨️ **Text Input Commands**

- **"Type '[text]'"** - Enter text into input fields
  - Examples: "Type 'Hello World'", "Type 'john@example.com'"
- **"Enter '[text]'"** - Alternative to type
  - Examples: "Enter 'password123'", "Enter 'My Name'"
- **"Input '[text]'"** - Another typing alternative
  - Examples: "Input 'Search query'", "Input 'Username'"
- **"Write '[text]'"** - Write text naturally
  - Examples: "Write 'Dear Sir or Madam'", "Write 'Thank you'"

#### 📜 **Scroll Commands**

- **"Scroll [direction]"** - Navigate through content
  - Examples: "Scroll down", "Scroll up", "Scroll left", "Scroll right"
- **"Scroll [direction] [number]"** - Scroll specific amount
  - Examples: "Scroll down 5", "Scroll up 3"
- **"Page [direction]"** - Page-based navigation
  - Examples: "Page down", "Page up"

#### ❓ **Question Commands**

**Simple Questions (Fast Response)**:

- **"What's on my screen?"** - Quick overview of screen content
- **"What is/are [subject]?"** - Get basic information about screen content
  - Examples: "What is this error message?", "What are the menu options?"
- **"Where is/are [element]?"** - Locate elements on screen
  - Examples: "Where is the save button?", "Where are the settings?"
- **"How do/can I [action]?"** - Get help with tasks
  - Examples: "How do I save this file?", "How can I change the font?"

**Detailed Questions (Comprehensive Analysis)**:

- **"Tell me what's on my screen in detail"** - Comprehensive screen analysis with coordinates
- **"Describe my screen in detail"** - Detailed element-by-element breakdown
- **"Give me a detailed analysis of my screen"** - Full structural analysis
- **"Analyze my screen in detail"** - Complete screen examination

**General Information**:

- **"Tell me about [subject]"** - Get information about specific elements
  - Examples: "Tell me about this dialog box", "Tell me about the current page"
- **"Explain [subject]"** - Get explanations
  - Examples: "Explain this error", "Explain the menu options"

#### 📝 **Form Filling Commands**

- **"Fill out the form"** - Automatically complete forms with your information
- **"Complete the form"** - Alternative form filling command
- **"Submit the form"** - Fill and submit forms

### Command Examples by Category

#### **Navigation & Interaction**

```
"Computer, click on the File menu"
"Computer, press the OK button"
"Computer, tap on the search icon"
"Computer, scroll down to see more options"
"Computer, page down"
```

#### **Text Entry**

```
"Computer, type 'Hello World' in the text box"
"Computer, enter 'john.doe@email.com' in the email field"
"Computer, write 'Thank you for your time'"
"Computer, input 'password123'"
```

#### **Information Gathering**

**Quick Questions**:

```
"Computer, what's on my screen?"
"Computer, what is this error message?"
"Computer, where is the save button?"
"Computer, how do I change the settings?"
```

**Detailed Analysis**:

```
"Computer, tell me what's on my screen in detail"
"Computer, describe my screen in detail"
"Computer, give me a detailed analysis of my screen"
"Computer, analyze my screen in detail"
```

**Specific Information**:

```
"Computer, tell me about this dialog box"
"Computer, explain what this button does"
```

#### **Form Automation**

```
"Computer, fill out this contact form"
"Computer, complete the registration form"
"Computer, submit the form with my information"
```

### Command Tips

- **Be Specific**: Use clear, descriptive terms for elements you want to interact with
- **Use Quotes**: Always put text to be typed in quotes: "Type 'your text here'"
- **Natural Language**: Commands support natural variations - "click", "press", and "tap" all work for clicking
- **Context Aware**: AURA understands your screen context and can find elements even with partial descriptions
- **Error Recovery**: If a command fails, AURA will provide helpful feedback and suggestions

### Performance Optimization

**Fast Commands (Recommended for most use cases)**:

- Simple questions like "What's on my screen?" use lightweight analysis (~2-5 seconds)
- GUI commands (click, type, scroll) use optimized screen capture for speed
- Form filling uses targeted form analysis

**Detailed Commands (Use when you need comprehensive information)**:

- Detailed questions like "Tell me what's on my screen in detail" provide complete analysis (~10-30 seconds)
- Include precise coordinates and comprehensive element descriptions
- Best for troubleshooting or when you need exact positioning information

**Tip**: Start with simple commands for faster responses, then use detailed commands when you need more information.

### Configuration Options

Edit `config.py` to customize:

- **API Endpoints**: Change vision and reasoning model URLs
- **Model Names**: Switch between different AI models
- **Wake Words**: Choose from available wake word options
- **Audio Settings**: Adjust TTS speed, volume, and sound effects
- **Automation**: Configure mouse movement speed and typing intervals

## Performance Monitoring

AURA includes comprehensive performance monitoring and optimization capabilities:

### Real-time Metrics

- **System Resources**: CPU, memory, disk usage monitoring
- **API Performance**: Response times, success rates, error tracking
- **Cache Efficiency**: Hit rates, compression ratios, storage optimization
- **Operation Timing**: Screen capture, vision analysis, reasoning, automation

### Performance Dashboard

Access performance metrics programmatically:

```python
from modules.performance_dashboard import performance_dashboard

# Get real-time metrics
metrics = performance_dashboard.get_real_time_metrics()
print(f"System Health: {metrics['health_status']}")
print(f"Cache Hit Rate: {metrics['cache_statistics']['hit_rate_percent']:.1f}%")

# Get optimization recommendations
recommendations = performance_dashboard.get_optimization_recommendations()
for rec in recommendations:
    print(f"- {rec['title']}: {rec['description']}")

# Export metrics for analysis
json_data = performance_dashboard.export_metrics(format='json')
```

### Automatic Optimizations

AURA automatically optimizes performance based on usage patterns:

- **Dynamic Cache Management**: Adjusts cache size based on memory usage
- **Connection Pool Optimization**: Manages HTTP connections for API efficiency
- **Parallel Processing Tuning**: Balances CPU usage with response time
- **Resource Cleanup**: Automatic garbage collection and resource management

### Performance Configuration

Customize performance settings in `performance_config.py`:

```python
# Connection pooling
CONNECTION_POOL_MAX_CONNECTIONS = 10
CONNECTION_POOL_MAX_RETRIES = 3

# Image caching
IMAGE_CACHE_MAX_SIZE_MB = 100
IMAGE_CACHE_MAX_ENTRIES = 50

# Parallel processing
PARALLEL_MAX_WORKERS = 4
PARALLEL_ENABLE_IO_PARALLELIZATION = True

# Performance monitoring
PERFORMANCE_MAX_METRICS = 1000
PERFORMANCE_SYSTEM_MONITORING_INTERVAL = 30
```

## Development

### Project Structure

```
AURA/
├── modules/                      # Core system modules
│   ├── __init__.py
│   ├── vision.py                # Screen capture and vision AI
│   ├── reasoning.py             # Cloud LLM reasoning
│   ├── audio.py                 # Speech processing and wake words
│   ├── automation.py            # GUI automation
│   ├── feedback.py              # Audio feedback system
│   ├── error_handler.py         # Comprehensive error handling
│   ├── performance.py           # Performance optimization utilities
│   └── performance_dashboard.py # Performance monitoring and metrics
├── tests/                       # Comprehensive test suite
│   ├── test_*.py               # Unit and integration tests
│   ├── conftest.py             # Test configuration
│   └── fixtures/               # Test data and fixtures
├── assets/
│   └── sounds/                 # Audio feedback files
├── config.py                   # Central configuration
├── performance_config.py       # Performance optimization settings
├── orchestrator.py             # Main coordinator
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── pytest.ini                 # Test configuration
└── README.md                  # This file
```

### Running Tests

```bash
# Install development dependencies
pip install -r requirements.txt

# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=modules tests/

# Type checking
mypy modules/

# Code formatting
black modules/ *.py
```

### Adding New Features

1. **Create Module**: Add new functionality in `modules/`
2. **Update Config**: Add configuration options in `config.py`
3. **Integrate**: Connect to orchestrator in `orchestrator.py`
4. **Test**: Add comprehensive tests
5. **Document**: Update README and docstrings

## Troubleshooting

### Common Issues

**"Configuration has errors"**

- Check that all API keys are set correctly
- Verify sound files exist in `assets/sounds/`
- Ensure external services are running

**"Cannot connect to LM Studio" or "No model detected"**

This is the most common issue. Follow these steps:

1. **Start LM Studio**: Make sure the LM Studio application is running
2. **Load a Model**: In LM Studio, go to "My Models" and click "Load" on any model
3. **Start the Server**: Go to "Local Server" tab and click "Start Server" (port 1234)
4. **Test Connection**: Run `python check_lmstudio.py` to verify everything is working
5. **Run AURA**: Once LM Studio is ready, AURA will automatically detect and use your model

**"Vision model not responding"**

- For vision tasks, use a multimodal model (LLaVA, Moondream, etc.)
- Text-only models will attempt vision tasks but may not work well
- Run `python test_dynamic_model.py` to test model detection

**"Wake word not detected"**

- Test microphone access and permissions
- Verify Porcupine API key is valid
- Check audio input levels
- Speak clearly and at normal volume
- Ensure minimal background noise

**"Command not understood"**

- Speak clearly and at a steady pace
- Use the exact command patterns listed above
- Put text to be typed in quotes
- Try rephrasing using alternative command words
- Check microphone quality and positioning

**"AURA responds but doesn't execute command"**

- Verify screen elements are visible and accessible
- Check if the target element has a clear, descriptive label
- Try using more specific descriptions
- Ensure the application window is in focus

**"GUI automation not working"**

- Ensure accessibility permissions are granted
- Check screen resolution and scaling settings
- Verify PyAutoGUI compatibility

### Debug Mode

```bash
# Enable debug logging
export AURA_DEBUG=true
python main.py

# Use mock APIs for testing
export AURA_MOCK_APIS=true
python main.py
```

## Security and Privacy

- **Local Processing**: Vision analysis happens locally when possible
- **Minimal Data**: Only necessary screen content sent to cloud services
- **API Security**: All cloud communications use HTTPS
- **Permissions**: Requires microphone and accessibility permissions
- **Audit Logging**: All actions are logged for security review

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [LM Studio](https://lmstudio.ai) for local model hosting
- [Picovoice](https://picovoice.ai) for wake word detection
- [OpenAI](https://openai.com) for Whisper speech recognition
- [Ollama](https://ollama.ai) for cloud model access

## Support

- 📧 Email: support@aura-assistant.com
- 💬 Discord: [AURA Community](https://discord.gg/aura)
- 📖 Documentation: [docs.aura-assistant.com](https://docs.aura-assistant.com)
- 🐛 Issues: [GitHub Issues](https://github.com/aura/aura/issues)

---

**AURA** - Making desktop automation as natural as conversation.
