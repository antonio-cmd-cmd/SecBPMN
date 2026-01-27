import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LLM Provider Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").lower()

# Ollama Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11435")

# Gemini Configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# LLM Temperature
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# LLM Max Output Tokens (for Gemini)
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "65536"))

# Database Configuration
LANCE_DB_PATH = os.getenv("LANCE_DB_PATH", "lance_threat_db")
KNOWLEDGE_BASE_PATH = os.getenv("KNOWLEDGE_BASE_PATH", "resources/knowledgeBaseLLMWithThreats.json")

# Legacy compatibility (deprecated)
LLM_MODEL = OLLAMA_MODEL  # For backward compatibility

