# Insider Threat Modeler 2.0 – Backend

Backend API for insider threat modeling in BPMN 2.0, with advanced RAG pipeline and Dual-LLM system for iterative generation and validation of security mitigations.

---

## 📑 Table of Contents

- [Key Features](#key-features)
- [System Requirements](#system-requirements)
- [Quick Installation](#quick-installation)
- [Configuration](#configuration)
- [Dual-LLM System](#dual-llm-system)
- [Petri Net Validation](#petri-net-validation)
- [Execution](#execution)
- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Key Features

### Dual-LLM System
- **Generator LLM**: Creates mitigated BPMN XML with security controls
- **Validator LLM**: Validates and provides feedback for iterative refinement
- **Multi-Provider Support**: Ollama (local) and Gemini (cloud)
- **Flexibility**: Each LLM can use different providers
- **Configurable Iterations**: Automatic refinement up to MAX_LLM_ITERATIONS

### Petri Net Validation
- **Formal Verification**: Mathematical validation of BPMN soundness
- **Issue Detection**: Deadlocks, unbalanced gateways, missing flows
- **Auto-Correction**: Extra iterations for automatic fixing
- **Flexible Modes**: Strict mode (reject errors) or Warning mode (accept with warnings)

### RAG Pipeline
- **Vector Database**: LanceDB for semantic threat search
- **Knowledge Base**: Complete insider threat database
- **Advanced Retrieval**: Context-aware threat analysis

---

## 💻 System Requirements

- **Python**: 3.9 or higher
- **pip**: Python package manager
- **Ollama** (optional): For local LLM execution
- **Google Cloud Account** (optional): For Gemini API

---

## ⚡ Quick Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Masterproject-Backend
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Main dependencies:**
- `fastapi` - Web framework API
- `langchain` - LLM framework
- `lancedb` - Vector database
- `pm4py` - BPMN and Petri Net processing
- `ollama` - Ollama client
- `google-genai` - Google Gemini client

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit the `.env` file with your configurations (see Configuration section).

---

## ⚙️ Configuration

### Main Configuration Options

#### Legacy Mode (Single-LLM)

```env
# Disable dual-LLM to use legacy system
USE_DUAL_LLM=false

# Single LLM configuration
LLM_PROVIDER=ollama
OLLAMA_MODEL=gpt-oss:latest
OLLAMA_BASE_URL=http://localhost:11434
LLM_TEMPERATURE=0.3
```

#### Dual-LLM Mode (Recommended)

**Base Configuration:**
```env
# Enable dual-LLM system
USE_DUAL_LLM=true

# Maximum LLM iterations (2-5 recommended)
MAX_LLM_ITERATIONS=3
```

**Option A - Both Ollama (Local, Free):**
```env
# Generator LLM
GENERATOR_LLM_PROVIDER=ollama
GENERATOR_OLLAMA_MODEL=gpt-oss:latest
GENERATOR_OLLAMA_BASE_URL=http://localhost:11434
GENERATOR_LLM_TEMPERATURE=0.3

# Validator LLM
VALIDATOR_LLM_PROVIDER=ollama
VALIDATOR_OLLAMA_MODEL=gpt-oss:latest
VALIDATOR_OLLAMA_BASE_URL=http://localhost:11434
VALIDATOR_LLM_TEMPERATURE=0.2
```

**Option B - Both Gemini (Cloud, High Quality):**
```env
# Generator LLM
GENERATOR_LLM_PROVIDER=gemini
GENERATOR_GEMINI_MODEL=gemini-2.5-flash
GENERATOR_GOOGLE_API_KEY=your_api_key_here
GENERATOR_LLM_TEMPERATURE=0.3
GENERATOR_MAX_OUTPUT_TOKENS=65536

# Validator LLM
VALIDATOR_LLM_PROVIDER=gemini
VALIDATOR_GEMINI_MODEL=gemini-2.5-flash
VALIDATOR_GOOGLE_API_KEY=your_api_key_here
VALIDATOR_LLM_TEMPERATURE=0.2
VALIDATOR_MAX_OUTPUT_TOKENS=8192
```

**Option C - Mix (Generator Gemini + Validator Ollama):**
```env
# Generator LLM (Cloud)
GENERATOR_LLM_PROVIDER=gemini
GENERATOR_GEMINI_MODEL=gemini-2.5-flash
GENERATOR_GOOGLE_API_KEY=your_api_key_here
GENERATOR_LLM_TEMPERATURE=0.3

# Validator LLM (Local)
VALIDATOR_LLM_PROVIDER=ollama
VALIDATOR_OLLAMA_MODEL=gpt-oss:latest
VALIDATOR_OLLAMA_BASE_URL=http://localhost:11434
VALIDATOR_LLM_TEMPERATURE=0.2
```

#### Petri Net Validation

```env
# Enable formal validation with Petri Net
ENABLE_PETRI_NET_VALIDATION=true

# Number of extra iterations for fixing (0-5 recommended)
MAX_PETRI_NET_FIX_ITERATIONS=2

# Strict mode: reject BPMN if not sound (false = warning only)
PETRI_NET_STRICT_MODE=false
```

### Test Configuration

Before starting the backend, verify the configuration:

```bash
python test_dual_llm_config.py
```

The script will test:
- ✅ Loading `.env` variables
- ✅ LLM provider connectivity
- ✅ Generator and Validator instance creation
- ✅ Configured model validity

---

## 🚀 Execution

### Starting the Backend

```bash
# From Masterproject-Backend folder
python -m app.main
```

Expected output (Dual-LLM + Petri Net):
```
INFO: Loading configuration...
INFO: === Using DUAL-LLM Generation System ===
INFO: Creating Generator LLM: Ollama model gpt-oss:latest
INFO: Creating Validator LLM: Ollama model gpt-oss:latest
INFO: Petri Net validation enabled (strict_mode=false)
INFO: Started server process [PID]
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Verify Functionality

```bash
# Test health endpoint
curl http://localhost:8000/

# Expected: {"status": "ok"}
```

---

## 🔄 Dual-LLM System

### How It Works

```
┌─────────────────────────────────────────────────────────┐
│                  USER INPUT                              │
│  • Original BPMN                                         │
│  • Threat analysis                                       │
│  • Security principles                                   │
└──────────────────┬──────────────────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │  PHASE 1: LLM     │
         │  ITERATIONS       │
         └─────────┬─────────┘
                   │
    ┌──────────────▼──────────────┐
    │  Iteration 1:               │
    │  Generator → Validator      │
    │  Feedback → Generator       │
    │  ...                        │
    │  Iteration N (max 3-5)      │
    └──────────────┬──────────────┘
                   │
         ┌─────────▼─────────┐
         │  PHASE 2: PETRI   │
         │  NET VALIDATION   │
         │  (if enabled)     │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │  MITIGATED BPMN   │
         │  VALIDATED        │
         └───────────────────┘
```

### LLM Iterations

**Iteration 1:**
1. Generator creates initial BPMN with mitigations
2. Validator checks structure, security, BPMN compliance
3. If PASS → Proceed to Petri Net validation
4. If FAIL → Generate detailed feedback

**Iterations 2-N:**
1. Generator receives Validator feedback
2. Corrects/refines previous BPMN
3. Validator re-validates
4. Loop continues until PASS or MAX_LLM_ITERATIONS

### Validator Checks

The Validator LLM verifies:
- ✅ **BPMN Structure**: Well-formed XML, correct namespaces
- ✅ **Gateways**: Split/merge rules, balancing
- ✅ **Flows**: Valid connections, no orphan elements
- ✅ **Lanes**: Correct actor assignment
- ✅ **Security**: Correct mitigation implementation
- ✅ **Process Integrity**: Original process is preserved

### Dual-LLM Advantages

| Aspect | Single-LLM | Dual-LLM |
|---------|-----------|----------|
| **Output Quality** | Good | Excellent |
| **Validation** | Basic (XML) | In-depth (semantic) |
| **Error Correction** | Manual | Automatic (iterative) |
| **BPMN Soundness** | Not guaranteed | High probability |
| **Computational Cost** | Low | Medium-High |

---

## 🔍 Petri Net Validation

### Overview

After LLM iterations, the system can perform **formal validation** by converting the BPMN to a Petri Net and verifying **structural soundness**.

### What It Verifies

**Soundness Properties:**
- ✅ **No Deadlock**: Process cannot get stuck
- ✅ **Reachability**: All final states are reachable
- ✅ **Proper Completion**: Process can always terminate
- ✅ **No Dead Parts**: All activities are executable

**Gateway Balancing:**
- ✅ Parallel gateways have balanced split/join
- ✅ Exclusive gateways with all branches defined
- ✅ No missing sequence flows

### Petri Net Workflow

```
┌─────────────────────────────────────────────┐
│ BPMN (from LLM iterations)                  │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │ Conversion        │
         │ BPMN → Petri Net  │
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │ Soundness Analysis│
         │ (pm4py)           │
         └─────────┬─────────┘
                   │
              ┌────▼────┐
              │ Sound?  │
              └────┬────┘
                YES│  NO
                   │   │
                   │   └────────────┐
                   │                │
                   │    ┌───────────▼────────────┐
                   │    │ Extra Iterations       │
                   │    │ (MAX_PETRI_NET_FIX     │
                   │    │  _ITERATIONS)          │
                   │    │ Generator + feedback   │
                   │    └───────────┬────────────┘
                   │                │
                   │    ┌───────────▼────────────┐
                   │    │ Re-validate Petri Net  │
                   │    └───────────┬────────────┘
                   │                │
              ┌────▼────────────────▼────┐
              │ Strict Mode?             │
              └────┬────────────────┬────┘
                TRUE│            FALSE│
                    │                 │
         ┌──────────▼──────┐  ┌──────▼──────────┐
         │ Reject if not   │  │ Accept with     │
         │ sound           │  │ warning         │
         └─────────────────┘  └─────────────────┘
```

### Mode Configuration

**Strict Mode (PETRI_NET_STRICT_MODE=true):**
- Rejects BPMN if not sound after all iterations
- Maximum formal correctness
- Recommended for critical production

**Warning Mode (PETRI_NET_STRICT_MODE=false):**
- Accepts non-sound BPMN with warning
- More flexible for development
- Includes problem details in output

---

## 🏗️ Architecture

### Directory Structure

```
Masterproject-Backend/
├── app/
│   ├── main.py                    # Entry point
│   ├── config.py                  # Configuration from .env
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py              # API Endpoints
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── llm_factory.py         # LLM Factory (Generator/Validator)
│   │   ├── dual_llm_generator.py  # Dual-LLM Logic
│   │   ├── petri_net_refinement.py # Petri Net Validation
│   │   ├── qa_chain.py            # RAG pipeline
│   │   ├── query_builder.py       # Query construction
│   │   ├── response_processor.py  # Response parsing
│   │   ├── vectorstore.py         # LanceDB interface
│   │   └── prompts/               # LLM prompts
│   └── utils/
│       ├── __init__.py
│       ├── bpmn_validator.py      # XML validation
│       ├── document_utils.py      # Document processing
│       └── file_loader.py         # File I/O
├── resources/
│   └── knowledgeBaseLLMWithThreats.json  # Knowledge base
├── lance_threat_db/               # Vector database
├── debug_output/                  # Iteration logs
├── tests/                         # Test scripts
├── .env                           # Configuration (DO NOT commit)
├── .env.example                   # Configuration template
├── requirements.txt               # Python dependencies
├── README.md                      # This file
└── test_dual_llm_config.py       # Configuration test
```

### Key Components

#### LLM Factory (`llm_factory.py`)
- Creates Generator and Validator LLM instances
- Manages Ollama/Gemini authentication
- Unified interface for both providers

#### Dual-LLM Generator (`dual_llm_generator.py`)
- Implements iterative Generator ↔ Validator loop
- Structured Validator feedback parsing
- XML extraction and cleanup
- Error handling and fallback

#### Petri Net Refinement (`petri_net_refinement.py`)
- BPMN → Petri Net conversion (pm4py)
- Formal soundness analysis
- Extra iterations with Generator feedback
- Strict/Warning mode management

#### RAG Pipeline (`qa_chain.py`, `vectorstore.py`)
- Vector search on LanceDB
- Semantic insider threat retrieval
- Context enrichment for LLM

---

## 🌐 API Endpoints

### POST `/generate-mitigated-bpmn/`

Generates mitigated BPMN with Dual-LLM system + Petri Net validation.

**Request Body:**
```json
{
  "bpmn_xml": "<bpmn:definitions>...</bpmn:definitions>",
  "threat_analysis": "Threat description...",
  "security_principles": ["Principle 1", "Principle 2"],
  "context_info": "Additional context..."
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Mitigated BPMN generated successfully (LLM: 2 iterations, Petri Net: 0 iterations)",
  "mitigated_bpmn": "<bpmn:definitions>...</bpmn:definitions>",
  "llm_iterations": 2,
  "iteration_history": [
    {
      "iteration": 1,
      "validation_result": "FAIL",
      "issues": ["Gateway not balanced"],
      "timestamp": "2026-01-30T10:30:00"
    },
    {
      "iteration": 2,
      "validation_result": "PASS",
      "issues": [],
      "timestamp": "2026-01-30T10:31:00"
    }
  ],
  "petri_net_result": {
    "valid": true,
    "message": "BPMN is valid and sound",
    "petri_net_info": {
      "places": 12,
      "transitions": 8,
      "arcs": 24
    }
  },
  "petri_net_iterations": 0,
  "metadata": {
    "generator_provider": "ollama",
    "generator_model": "gpt-oss:latest",
    "validator_provider": "ollama",
    "validator_model": "gpt-oss:latest",
    "max_iterations": 3,
    "petri_net_enabled": true,
    "petri_net_valid": true,
    "petri_net_strict_mode": false
  },
  "warnings": null
}
```

**Response (Warning Mode - Not Sound but Accepted):**
```json
{
  "success": true,
  "message": "Mitigated BPMN generated with warnings",
  "mitigated_bpmn": "<bpmn:definitions>...</bpmn:definitions>",
  "petri_net_result": {
    "valid": false,
    "message": "BPMN is NOT sound (Warning mode)",
    "details": "Deadlock detected in gateway configuration"
  },
  "warnings": [
    "⚠️ Petri Net validation failed: BPMN may have structural issues (deadlocks, unreachable states, etc.)",
    "⚠️ The BPMN is returned because PETRI_NET_STRICT_MODE=false"
  ]
}
```

---

## 🐛 Troubleshooting

### Issue: "Ollama connection refused"

**Cause:** Ollama service not running or wrong URL

**Solution:**
```bash
# Verify Ollama is active
ollama list

# Check URL in .env
GENERATOR_OLLAMA_BASE_URL=http://localhost:11434

# Test connectivity
curl http://localhost:11434/api/tags
```

### Issue: "Gemini API key invalid"

**Cause:** Invalid or unconfigured API key

**Solution:**
1. Get API key from: https://aistudio.google.com/app/apikey
2. Verify in `.env`:
   ```env
   GENERATOR_GOOGLE_API_KEY=your_valid_key_here
   ```
3. Ensure Generative AI API is enabled in Google Cloud project

### Issue: "Max iterations reached without validation"

**Cause:** BPMN too complex or Validator too strict

**Solution:**
```env
# Increase iterations
MAX_LLM_ITERATIONS=5

# Reduce Validator temperature (more permissive)
VALIDATOR_LLM_TEMPERATURE=0.1

# Use Gemini for validation (more accurate)
VALIDATOR_LLM_PROVIDER=gemini
```

### Issue: "Petri Net validation always fails"

**Cause:** Structurally problematic BPMN or strict mode too rigid

**Solution:**
```env
# Use warning mode for development
PETRI_NET_STRICT_MODE=false

# Increase fixing iterations
MAX_PETRI_NET_FIX_ITERATIONS=3

# Temporarily disable for debug
ENABLE_PETRI_NET_VALIDATION=false
```

---

## 📊 Best Practices

### Development Configuration

```env
USE_DUAL_LLM=true
MAX_LLM_ITERATIONS=2
GENERATOR_LLM_PROVIDER=ollama
VALIDATOR_LLM_PROVIDER=ollama
ENABLE_PETRI_NET_VALIDATION=true
MAX_PETRI_NET_FIX_ITERATIONS=1
PETRI_NET_STRICT_MODE=false
```

**Pros:**
- ✅ Fast and free (local Ollama)
- ✅ Warning mode allows experimentation
- ✅ Few iterations for quick feedback

### Production Configuration

```env
USE_DUAL_LLM=true
MAX_LLM_ITERATIONS=3
GENERATOR_LLM_PROVIDER=gemini
VALIDATOR_LLM_PROVIDER=gemini
GENERATOR_GEMINI_MODEL=gemini-2.5-flash
VALIDATOR_GEMINI_MODEL=gemini-2.5-flash
ENABLE_PETRI_NET_VALIDATION=true
MAX_PETRI_NET_FIX_ITERATIONS=2
PETRI_NET_STRICT_MODE=true
```

**Pros:**
- ✅ Maximum quality (Gemini)
- ✅ Strict mode ensures soundness
- ✅ Moderate iterations to balance cost/quality

---

## 🔧 Complete Environment Variables

### Core System

| Variable | Description | Default | Values |
|-----------|-------------|---------|--------|
| `USE_DUAL_LLM` | Enable dual-LLM system | `false` | `true/false` |
| `MAX_LLM_ITERATIONS` | Max Generator-Validator iterations | `3` | `1-10` |

### Generator LLM

| Variable | Description | Default |
|-----------|-------------|---------|
| `GENERATOR_LLM_PROVIDER` | LLM Provider | `ollama` |
| `GENERATOR_OLLAMA_MODEL` | Ollama Model | `gpt-oss:latest` |
| `GENERATOR_OLLAMA_BASE_URL` | Ollama URL | `http://localhost:11434` |
| `GENERATOR_GEMINI_MODEL` | Gemini Model | `gemini-2.5-flash` |
| `GENERATOR_GOOGLE_API_KEY` | Google API key | - |
| `GENERATOR_LLM_TEMPERATURE` | Temperature (0.0-1.0) | `0.3` |
| `GENERATOR_MAX_OUTPUT_TOKENS` | Max output tokens | `65536` |

### Validator LLM

| Variable | Description | Default |
|-----------|-------------|---------|
| `VALIDATOR_LLM_PROVIDER` | LLM Provider | `ollama` |
| `VALIDATOR_OLLAMA_MODEL` | Ollama Model | `gpt-oss:latest` |
| `VALIDATOR_OLLAMA_BASE_URL` | Ollama URL | `http://localhost:11434` |
| `VALIDATOR_GEMINI_MODEL` | Gemini Model | `gemini-2.5-flash` |
| `VALIDATOR_GOOGLE_API_KEY` | Google API key | - |
| `VALIDATOR_LLM_TEMPERATURE` | Temperature (0.0-1.0) | `0.2` |
| `VALIDATOR_MAX_OUTPUT_TOKENS` | Max output tokens | `8192` |

### Petri Net Validation

| Variable | Description | Default |
|-----------|-------------|---------|
| `ENABLE_PETRI_NET_VALIDATION` | Enable validation | `true` |
| `MAX_PETRI_NET_FIX_ITERATIONS` | Fixing iterations | `2` |
| `PETRI_NET_STRICT_MODE` | Reject if not sound | `false` |

### Legacy Single-LLM

| Variable | Description | Default |
|-----------|-------------|---------|
| `LLM_PROVIDER` | Provider (if USE_DUAL_LLM=false) | `ollama` |
| `OLLAMA_MODEL` | Legacy Ollama model | `gpt-oss:latest` |
| `GEMINI_MODEL` | Legacy Gemini model | `gemini-2.5-flash` |
| `GOOGLE_API_KEY` | Legacy API key | - |
| `LLM_TEMPERATURE` | Legacy temperature | `0.3` |

### Database & Resources

| Variable | Description | Default |
|-----------|-------------|---------|
| `LANCE_DB_PATH` | LanceDB path | `lance_threat_db` |
| `KNOWLEDGE_BASE_PATH` | Knowledge base path | `resources/knowledgeBaseLLMWithThreats.json` |

---

## 📝 Final Notes

### Compatibility

- ✅ **Backward Compatible**: Legacy single-LLM system still supported
- ✅ **Gradual Migration**: Switch from single to dual-LLM without breaking changes
- ✅ **Flexibility**: Mix providers based on specific needs

### Performance

| Configuration | Average Time | Cost |
|----------------|-------------|-------|
| Single-LLM Ollama | ~30s | Free |
| Dual-LLM Ollama | ~45-90s | Free |
| Dual-LLM Gemini | ~20-40s | ~$0.01-0.05/request |
| Dual-LLM + Petri Net | +10-30s | Variable |

### Versioning

- **v1.0**: Base system with single-LLM
- **v2.0**: Dual-LLM system introduction
- **v2.1**: Petri Net validation added

---

**Last updated:** January 2026  
**Version:** 2.1.0
