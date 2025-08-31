# AURA - Autonomous User-side Robotic Assistant

AURA is a hybrid perception-reasoning AI system that enables users to control their desktop computer through natural voice commands. The system combines local vision models for screen understanding with cloud-based reasoning models for action planning, creating an intelligent assistant that can perform complex desktop automation tasks through conversational interaction.

## Features

- 🎤 **Voice Control**: Activate with wake words and give natural language commands
- 👁️ **Screen Understanding**: Local vision models analyze your desktop in real-time
- 🧠 **Intelligent Planning**: Cloud-based LLMs create smart action sequences
- 🖱️ **Desktop Automation**: Precise GUI interactions with safety controls
- 🔊 **Audio Feedback**: Rich audio responses and status updates
- 📝 **Form Filling**: Automated web form completion through voice
- ❓ **Information Extraction**: Ask questions about screen content
- ⚙️ **Configurable**: Centralized configuration for easy customization

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

- **Local Vision**: LM Studio with multimodal models (Gemma-3-4b)
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

   - Load a multimodal model (e.g., google/gemma-3-4b)
   - Start the local server on port 1234

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

# Say the wake word: "Computer"
# Then give a command: "Click on the search button"
```

### Example Commands

- **Navigation**: "Click on the File menu"
- **Text Input**: "Type 'Hello World' in the text box"
- **Form Filling**: "Fill out this contact form with my information"
- **Information**: "What does this error message say?"
- **Web Browsing**: "Search for Python tutorials"

### Configuration Options

Edit `config.py` to customize:

- **API Endpoints**: Change vision and reasoning model URLs
- **Model Names**: Switch between different AI models
- **Wake Words**: Choose from available wake word options
- **Audio Settings**: Adjust TTS speed, volume, and sound effects
- **Automation**: Configure mouse movement speed and typing intervals

## Development

### Project Structure

```
AURA/
├── modules/                 # Core system modules
│   ├── __init__.py
│   ├── vision.py           # Screen capture and vision AI
│   ├── reasoning.py        # Cloud LLM reasoning
│   ├── audio.py            # Speech processing and wake words
│   ├── automation.py       # GUI automation
│   └── feedback.py         # Audio feedback system
├── assets/
│   └── sounds/             # Audio feedback files
├── config.py               # Central configuration
├── orchestrator.py         # Main coordinator
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
└── README.md              # This file
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

**"Vision model not responding"**

- Confirm LM Studio is running on port 1234
- Check that a multimodal model is loaded
- Verify network connectivity

**"Wake word not detected"**

- Test microphone access and permissions
- Verify Porcupine API key is valid
- Check audio input levels

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
