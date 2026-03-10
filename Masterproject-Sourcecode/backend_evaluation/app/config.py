import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ===== DUAL LLM CONFIGURATION =====
USE_DUAL_LLM = os.getenv("USE_DUAL_LLM", "false").lower() == "true"
MAX_LLM_ITERATIONS = int(os.getenv("MAX_LLM_ITERATIONS", "3"))

# ===== GENERATOR LLM CONFIGURATION =====
GENERATOR_LLM_PROVIDER = os.getenv("GENERATOR_LLM_PROVIDER", "ollama").lower()

# Ollama Configuration for Generator
GENERATOR_OLLAMA_MODEL = os.getenv("GENERATOR_OLLAMA_MODEL", "")
GENERATOR_OLLAMA_BASE_URL = os.getenv("GENERATOR_OLLAMA_BASE_URL", "http://localhost:11434")

# Ollama keep_alive: how long the server keeps the model loaded after the last request.
# Set to "0" for immediate unload (ensures no KV-cache reuse across sweep iterations).
# Set to "-1" to keep the model loaded indefinitely.
# Default is "5m" (Ollama server default).
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "0")

# Gemini Configuration for Generator
GENERATOR_GEMINI_MODEL = os.getenv("GENERATOR_GEMINI_MODEL", "")
GENERATOR_GOOGLE_API_KEY = os.getenv("GENERATOR_GOOGLE_API_KEY", "")

# Generator LLM Temperature
GENERATOR_LLM_TEMPERATURE = float(os.getenv("GENERATOR_LLM_TEMPERATURE", "0.3"))

# Max Output Tokens for Generator (for Gemini)
GENERATOR_MAX_OUTPUT_TOKENS = int(os.getenv("GENERATOR_MAX_OUTPUT_TOKENS", "65536"))

# ===== VALIDATOR LLM CONFIGURATION =====
VALIDATOR_LLM_PROVIDER = os.getenv("VALIDATOR_LLM_PROVIDER", "ollama").lower()

# Ollama Configuration for Validator
VALIDATOR_OLLAMA_MODEL = os.getenv("VALIDATOR_OLLAMA_MODEL", "")
VALIDATOR_OLLAMA_BASE_URL = os.getenv("VALIDATOR_OLLAMA_BASE_URL", "http://localhost:11434")

# Gemini Configuration for Validator
VALIDATOR_GEMINI_MODEL = os.getenv("VALIDATOR_GEMINI_MODEL", "")
VALIDATOR_GOOGLE_API_KEY = os.getenv("VALIDATOR_GOOGLE_API_KEY", "")

# Validator LLM Temperature
VALIDATOR_LLM_TEMPERATURE = float(os.getenv("VALIDATOR_LLM_TEMPERATURE", "0.2"))

# Max Output Tokens for Validator (for Gemini)
VALIDATOR_MAX_OUTPUT_TOKENS = int(os.getenv("VALIDATOR_MAX_OUTPUT_TOKENS", "8192"))

# ===== PETRI NET VALIDATION CONFIGURATION =====
ENABLE_PETRI_NET_VALIDATION = os.getenv("ENABLE_PETRI_NET_VALIDATION", "true").lower() == "true"
MAX_PETRI_NET_FIX_ITERATIONS = int(os.getenv("MAX_PETRI_NET_FIX_ITERATIONS", "2"))
PETRI_NET_STRICT_MODE = os.getenv("PETRI_NET_STRICT_MODE", "false").lower() == "true"

# ===== LEGACY SINGLE LLM CONFIGURATION (for backward compatibility) =====
LLM_PROVIDER = os.getenv("LLM_PROVIDER", GENERATOR_LLM_PROVIDER).lower()

# Ollama Configuration (legacy - fallback to generator config)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", GENERATOR_OLLAMA_MODEL)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", GENERATOR_OLLAMA_BASE_URL)

# Gemini Configuration (legacy - fallback to generator config)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", GENERATOR_GEMINI_MODEL)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", GENERATOR_GOOGLE_API_KEY)

# LLM Temperature (legacy - fallback to generator config)
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", str(GENERATOR_LLM_TEMPERATURE)))

# LLM Max Output Tokens (legacy - fallback to generator config)
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", str(GENERATOR_MAX_OUTPUT_TOKENS)))

# ===== DATABASE CONFIGURATION =====
LANCE_DB_PATH = os.getenv("LANCE_DB_PATH", "lance_threat_db")
KNOWLEDGE_BASE_PATH = os.getenv("KNOWLEDGE_BASE_PATH", "resources/knowledgeBaseLLMWithThreats.json")

# Legacy compatibility (deprecated)
LLM_MODEL = OLLAMA_MODEL  # For backward compatibility

