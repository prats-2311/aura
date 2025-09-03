# Minimal AURA Configuration for Testing

# Vision API (Local LM Studio)
VISION_API_BASE = "http://localhost:1234/v1"
VISION_MODEL = "google/gemma-3-4b"

# Reasoning API (OpenAI compatible)
REASONING_API_BASE = "http://localhost:1234/v1"
REASONING_MODEL = "google/gemma-3-4b"

# Audio Configuration
ENABLE_WAKE_WORD = True
WAKE_WORD = "computer"
ENABLE_AUDIO_FEEDBACK = True

# Fast Path Configuration
ENABLE_FAST_PATH = True
FAST_PATH_TIMEOUT = 2.0

# Logging
LOG_LEVEL = "INFO"
DEBUG_MODE = False

# API Keys (set to dummy values for local testing)
PORCUPINE_API_KEY = "dummy_key_for_local_testing"
REASONING_API_KEY = "dummy_key_for_local_testing"
