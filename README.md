<p align="center">
  <img src="https://img.shields.io/badge/python-v3.11-brightgreen.svg?style=flat-square" alt="python" />
  <img src="https://img.shields.io/badge/pytorch-v2.0+-blue.svg?style=flat-square" alt="pytorch" />
  <a href="https://github.com/prats-2311/aura/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License: MIT" />
  </a>
  <a href="https://github.com/prats-2311/aura/blob/main/.github/contributing.md">
    <img src="https://img.shields.io/badge/contributions-welcome-orange.svg?style=flat-square" alt="Contributions Welcome" />
  </a>
  <img src="https://img.shields.io/badge/platform-macOS-black?style=flat-square" alt="Platform: macOS">
</p>

<p align="center">
  <img src="assets/aura-logo.png" alt="AURA Logo" width="200" />
</p>

# AURA - Autonomous User-side Robotic Assistant

AURA (Autonomous User-side Robotic Assistant) is an intelligent AI-powered desktop assistant that combines computer vision, natural language processing, and automation to help users interact with their computers through voice commands and visual understanding. The system can see what's on your screen, understand your voice commands, and perform automated actions to assist with various tasks.

## 🎥 Demo

**Watch AURA in Action:** [YouTube Demo](https://youtu.be/PZizPGygSSk)

## ✨ Key Features

- **🎤 Voice Activation**: Wake word detection using Porcupine for hands-free interaction
- **👁️ Computer Vision**: Real-time screen analysis and visual understanding
- **🧠 AI Reasoning**: Advanced language model integration for intelligent responses
- **🤖 Automation**: Cross-platform GUI automation and control
- **♿ Accessibility**: macOS Accessibility API integration for enhanced interaction
- **🔊 Audio Feedback**: Text-to-speech responses and audio notifications
- **📊 Performance Monitoring**: Real-time performance tracking and optimization
- **🌐 Web Integration**: Browser automation and web accessibility features

## 🏗️ Architecture

AURA follows a modular architecture with clear separation of concerns:

```
AURA/
├── modules/           # Core functionality modules
│   ├── vision.py      # Computer vision and screen analysis
│   ├── reasoning.py   # AI language model integration
│   ├── audio.py       # Voice processing and TTS
│   ├── automation.py  # GUI automation and control
│   ├── accessibility.py # macOS Accessibility API
│   └── feedback.py    # User feedback and notifications
├── handlers/          # Command and intent handlers
├── orchestrator.py    # Central coordination system
├── main.py           # Application entry point
└── config.py         # Configuration management
```

## 🛠️ Tech Stack

### Core Technologies

- **Python 3.11** - Primary programming language
- **PyTorch** - Machine learning framework
- **Transformers** - Hugging Face model integration
- **OpenAI Whisper** - Speech recognition
- **Porcupine** - Wake word detection

### Computer Vision & Automation

- **OpenCV** - Computer vision processing
- **Pillow (PIL)** - Image manipulation
- **PyAutoGUI** - Cross-platform GUI automation
- **MSS** - Fast screen capture
- **cliclick** - macOS automation (primary method)

### macOS Integration

- **PyObjC** - Complete macOS framework bindings
  - Cocoa, AppKit, ApplicationServices
  - Accessibility, CoreFoundation, CoreServices
  - Vision, Speech, AVFoundation frameworks

### Audio Processing

- **SoundDevice** - Audio I/O operations
- **PyDub** - Audio file manipulation
- **pyttsx3** - Text-to-speech synthesis

### Web & API

- **FastAPI** - Modern web framework
- **Uvicorn** - ASGI server
- **Requests/HTTPX** - HTTP client libraries
- **WebSockets** - Real-time communication

### Data & Analysis

- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computing
- **SciPy** - Scientific computing

### Development Tools

- **pytest** - Testing framework
- **Black** - Code formatting
- **Flake8** - Code linting
- **MyPy** - Static type checking

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

You will need the following properly installed on your computer:

- [Git](http://git-scm.com/)
- [Python 3.11](https://www.python.org/downloads/)
- [Conda](https://docs.conda.io/en/latest/miniconda.html) package manager
- [Homebrew](https://brew.sh/) (for macOS automation tools)
- macOS (primary support)

## Installing

In a terminal window run these commands:

```bash
$ git clone https://github.com/prats-2311/aura.git
$ cd aura
$ conda create --name aura python=3.11 -y
$ conda activate aura
$ pip install -r requirements.txt
$ brew install cliclick
```

### Configuration

Add necessary API keys to your `config.py` file:

- Set up your API keys in `config.py`
- Configure Porcupine API key for wake word detection
- Set up reasoning model API endpoints

### Running AURA

```bash
$ cd aura
$ conda activate aura
$ python main.py
```

You should be able to interact with AURA through voice commands after the wake word activation.

## 🎮 Usage

1. **Start AURA:** Run `python main.py` to start the assistant
2. **Wake Word:** Say the wake word to activate voice commands
3. **Voice Commands:** Speak naturally to interact with your computer
4. **Visual Tasks:** AURA can see and interact with screen elements
5. **Automation:** Perform complex multi-step tasks through voice

### Example Commands

- "Click on the search button"
- "What's on my screen?"
- "Open the settings menu"
- "Fill out this form"
- "Read me the text on the page"

## 📋 Configuration

Key configuration options in `config.py`:

- **API Keys**: Porcupine, reasoning models
- **Audio Settings**: Microphone, speaker configuration
- **Vision Models**: Local LM Studio integration
- **Performance**: Optimization and monitoring settings
- **Accessibility**: macOS permissions and features

## Testing

In a terminal window run these commands:

```bash
$ cd aura
$ conda activate aura
$ pytest tests/
```

<br>

In a terminal window run these commands to run the test suite with verbose output:

```bash
$ cd aura
$ pytest tests/ -v
```

In a terminal window run these commands to view the test coverage report:

```bash
$ cd aura
$ pytest tests/ --cov=modules --cov=handlers
$ pytest tests/ --cov=modules --cov=handlers --cov-report=html
```

In a terminal window run these commands for performance testing:

```bash
$ cd aura
$ python -m pytest tests/performance/
```

In a terminal window run these commands to run specific test categories:

```bash
$ cd aura
$ pytest tests/test_accessibility.py  # Accessibility tests
$ pytest tests/test_vision.py         # Computer vision tests
$ pytest tests/test_audio.py          # Audio processing tests
```

## 📊 Performance Monitoring

AURA includes comprehensive performance monitoring:

- Real-time latency tracking
- Resource usage monitoring
- Performance dashboard
- Optimization recommendations

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting issues and/or pull requests.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the [AURA Development Principles](.kiro/steering/AURA_Development_Principles.md)
4. Add tests for new functionality
5. Ensure all tests pass (`pytest tests/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Submit a pull request

[CONTRIBUTORS](https://github.com/prats-2311/aura/graphs/contributors)

## License

This project is licensed under the MIT License - please see [LICENSE](LICENSE) for more details.

## 🙏 Acknowledgments

- Picovoice for Porcupine wake word detection
- Hugging Face for transformer models
- OpenAI for Whisper speech recognition
- Apple for macOS Accessibility APIs

## Roadmap

Please checkout our [roadmap](ROADMAP.md) for details of upcoming features and development plans.

### Upcoming Features

- Cross-platform support (Windows, Linux)
- Enhanced natural language understanding
- Plugin system for extensibility
- Advanced automation workflows
- Improved accessibility features

## Support

For questions, issues, or contributions:

- **GitHub Issues**: [Report bugs or request features](https://github.com/prats-2311/aura/issues)
- **Discussions**: [Join the community discussion](https://github.com/prats-2311/aura/discussions)
- **Demo Video**: [Watch the YouTube demo](https://youtu.be/PZizPGygSSk)

---

**AURA** - Making human-computer interaction more natural and accessible through AI.
