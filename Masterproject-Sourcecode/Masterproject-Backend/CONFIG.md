# BPMN Security Analysis Tool - Backend Configuration Guide

## LLM Provider Setup

This backend supports two LLM providers:
- **Ollama** (local models)
- **Gemini** (Google Cloud models)

### Quick Start

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and configure your preferred provider.

### Ollama Configuration (Local Models)

Set these variables in `.env`:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=deepseek-r1:32b
OLLAMA_BASE_URL=http://localhost:11435
LLM_TEMPERATURE=0.3
```

**Available models**: Any model installed in your Ollama instance (deepseek-r1, llama3, mistral, etc.)

**Requirements**:
- Ollama installed and running
- Model pulled: `ollama pull deepseek-r1:32b`

### Gemini Configuration (Google Cloud)

Set these variables in `.env`:

```env
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
GOOGLE_API_KEY=your-actual-api-key-here
LLM_TEMPERATURE=0.3
```

**Available models**:
- `gemini-2.5-flash` (recommended, newest and fastest)
- `gemini-2.0-flash-exp` (experimental)
- `gemini-1.5-pro`
- `gemini-1.5-flash`

**Requirements**:
- Google Cloud account with Generative AI API enabled
- API key from https://aistudio.google.com/app/apikey
- Install library: `pip install google-genai`

### Installation

Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Server

```bash
python -m app.main
```

The server will automatically use the provider configured in `.env`.

### Switching Providers

Simply change `LLM_PROVIDER` in `.env`:

```env
# For local models
LLM_PROVIDER=ollama

# For Google Gemini
LLM_PROVIDER=gemini
```

No code changes needed - restart the server to apply.

### Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | Provider to use: `ollama` or `gemini` | `ollama` |
| `OLLAMA_MODEL` | Ollama model name | `deepseek-r1:32b` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11435` |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.5-flash` |
| `GOOGLE_API_KEY` | Google API key | (empty) |
| `LLM_TEMPERATURE` | Model temperature (0.0-1.0) | `0.3` |
| `LANCE_DB_PATH` | Vector database path | `lance_threat_db` |
| `KNOWLEDGE_BASE_PATH` | Knowledge base JSON path | `resources/...json` |

### Troubleshooting

**Gemini API errors**:
- Verify API key is correct
- Check API is enabled in Google Cloud Console
- Ensure billing is set up

**Ollama connection errors**:
- Verify Ollama is running: `ollama list`
- Check port matches OLLAMA_BASE_URL
- Ensure model is pulled: `ollama pull <model-name>`
