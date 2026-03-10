# Insider Threat Modeler 2.0 – Production Backend

This is the **production backend** for the Insider Threat Modeler. It exposes a FastAPI REST API consumed by the React frontend (`Masteproject-Frontend/`) for interactive insider-threat analysis and BPMN mitigation generation.

> **Not to be confused with `backend_evaluation/`**, which is a separate copy of this server bundled with experiment scripts for research evaluations. See the [root README](../README.md) for the distinction.

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Configuration (.env)](#configuration-env)
5. [Starting the Server](#starting-the-server)
6. [Verify the Setup](#verify-the-setup)
7. [API Endpoints](#api-endpoints)
8. [Architecture Overview](#architecture-overview)
9. [Troubleshooting](#troubleshooting)

---

## What It Does

Given a BPMN 2.0 process file, this backend:

1. **Analyzes insider threats** – RAG-based retrieval over a curated threat knowledge base (LanceDB + LangChain).
2. **Generates a mitigated BPMN** – a **Dual-LLM** loop (Generator + structured Validator feedback) iteratively refines the BPMN until the Validator approves or the maximum number of rounds is reached.
3. **Validates BPMN soundness** – converts the BPMN to a Petri Net (pm4py) and checks for deadlocks, unreachable states, and unbalanced gateways.

### Core Components

| Component | Description |
|-----------|-------------|
| **Generator LLM** | Produces the mitigated BPMN XML incorporating security controls |
| **Validator LLM** | Reviews each generated BPMN and returns structured feedback |
| **Petri Net Validator** | Formally verifies BPMN soundness after the LLM loop |
| **RAG Pipeline** | LanceDB semantic retrieval over insider-threat and mitigation knowledge bases |

---

## System Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.9 or higher |
| pip | latest |
| **Ollama** *(for local LLMs)* | ≥ 0.4 |
| **Google Cloud account** *(for Gemini)* | optional |

---

## Installation

```bash
# 1. Enter this folder
cd Masterproject-Backend

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

> **Note on pm4py (Windows):** if installation fails try:
> ```bash
> pip install pm4py --no-build-isolation
> ```

---

## Configuration (.env)

Copy the example file and fill in your settings:

```bash
cp .env.example .env
```

> This `.env` file controls the production server only. It does **not** contain `EVAL_*` or `OLLAMA_KEEP_ALIVE` variables – those belong to `backend_evaluation/.env`.

### Dual-LLM (recommended)

```env
USE_DUAL_LLM=true
MAX_LLM_ITERATIONS=3          # Generator ↔ Validator rounds (2–5 recommended)
```

**Option A – Both Ollama (local, free)**

```env
GENERATOR_LLM_PROVIDER=ollama
GENERATOR_OLLAMA_MODEL=llama3.2:latest
GENERATOR_OLLAMA_BASE_URL=http://localhost:11434
GENERATOR_LLM_TEMPERATURE=0.3

VALIDATOR_LLM_PROVIDER=ollama
VALIDATOR_OLLAMA_MODEL=llama3.2:latest
VALIDATOR_OLLAMA_BASE_URL=http://localhost:11434
VALIDATOR_LLM_TEMPERATURE=0.2
```

**Option B – Both Gemini (cloud, higher quality)**

```env
GENERATOR_LLM_PROVIDER=gemini
GENERATOR_GEMINI_MODEL=gemini-2.5-flash
GENERATOR_GOOGLE_API_KEY=YOUR_KEY
GENERATOR_LLM_TEMPERATURE=0.3
GENERATOR_MAX_OUTPUT_TOKENS=65536

VALIDATOR_LLM_PROVIDER=gemini
VALIDATOR_GEMINI_MODEL=gemini-2.5-flash
VALIDATOR_GOOGLE_API_KEY=YOUR_KEY
VALIDATOR_LLM_TEMPERATURE=0.2
VALIDATOR_MAX_OUTPUT_TOKENS=8192
```

**Option C – Mixed (Gemini generator + Ollama validator)**

```env
GENERATOR_LLM_PROVIDER=gemini
GENERATOR_GEMINI_MODEL=gemini-2.5-flash
GENERATOR_GOOGLE_API_KEY=YOUR_KEY

VALIDATOR_LLM_PROVIDER=ollama
VALIDATOR_OLLAMA_MODEL=llama3.2:latest
VALIDATOR_OLLAMA_BASE_URL=http://localhost:11434
```

### Legacy single-LLM (backward-compatible)

```env
USE_DUAL_LLM=false
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:latest
OLLAMA_BASE_URL=http://localhost:11434
LLM_TEMPERATURE=0.3
```

### Petri Net Validation

```env
ENABLE_PETRI_NET_VALIDATION=true
MAX_PETRI_NET_FIX_ITERATIONS=2
PETRI_NET_STRICT_MODE=false    # true = reject on error; false = warn and accept
```

### Full Variable Reference

#### Dual-LLM

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_DUAL_LLM` | `false` | Enable the Generator + Validator loop |
| `MAX_LLM_ITERATIONS` | `3` | Maximum Generator↔Validator rounds |

#### Generator LLM

| Variable | Default |
|----------|---------|
| `GENERATOR_LLM_PROVIDER` | `ollama` |
| `GENERATOR_OLLAMA_MODEL` | – |
| `GENERATOR_OLLAMA_BASE_URL` | `http://localhost:11434` |
| `GENERATOR_GEMINI_MODEL` | `gemini-2.5-flash` |
| `GENERATOR_GOOGLE_API_KEY` | – |
| `GENERATOR_LLM_TEMPERATURE` | `0.3` |
| `GENERATOR_MAX_OUTPUT_TOKENS` | `65536` *(Gemini only)* |

#### Validator LLM

Same variables prefixed with `VALIDATOR_`. Default temperature: `0.2`.

#### Petri Net Validation

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_PETRI_NET_VALIDATION` | `true` | Run formal soundness check |
| `MAX_PETRI_NET_FIX_ITERATIONS` | `2` | Extra LLM iterations to fix errors |
| `PETRI_NET_STRICT_MODE` | `false` | Reject result if not sound |

#### Database & Resources

| Variable | Default |
|----------|---------|
| `LANCE_DB_PATH` | `lance_threat_db` |
| `KNOWLEDGE_BASE_PATH` | `resources/knowledgeBaseLLMWithThreats.json` |

---

## Starting the Server

```bash
# From Masterproject-Backend/ (venv active)
python -m app.main
```

Expected startup output:

```
INFO: Loading configuration...
INFO: === Using DUAL-LLM Generation System ===
INFO: Creating Generator LLM: Ollama model llama3.2:latest
INFO: Creating Validator LLM: Ollama model llama3.2:latest
INFO: Petri Net validation enabled (strict_mode=false)
INFO: Uvicorn running on http://0.0.0.0:8000
```

> **Ollama users:** start the Ollama daemon first in a separate terminal:
> ```bash
> ollama serve
> ollama pull llama3.2:latest   # or your chosen model
> ```

---

## Verify the Setup

Before connecting the frontend, confirm the server is healthy:

```bash
# Health check
curl http://localhost:8000/
# Expected: {"status": "ok"}
```

You can also run a smoke-test of the LLM configuration:

```bash
python test_dual_llm_config.py
```

Interactive Swagger docs are available at `http://localhost:8000/docs`.

---

## API Endpoints

Both the production backend and the evaluation backend expose the same endpoints.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Health check |
| `POST` | `/validate-bpmn/` | Validate a BPMN file (XML + Petri net soundness) |
| `POST` | `/analyze-xml/` | Run RAG-based insider-threat analysis |
| `POST` | `/generate-mitigated-bpmn/` | Generate a mitigated BPMN (Dual-LLM pipeline) |
| `POST` | `/download-bpmn/` | Download a BPMN XML as a file |

**Example – generate a mitigated BPMN via curl:**

```bash
curl -X POST http://localhost:8000/generate-mitigated-bpmn/ \
  -F "file=@process.bpmn;type=application/xml" \
  -F 'context={"process_name":"Order management"}' \
  -F 'principles=["Integrity"]' \
  -F 'threat_analysis=<threat_analysis.md' \
  -o mitigated.json
```

---

## Architecture Overview

```
Masterproject-Backend/
├── app/
│   ├── main.py                   ← entry point  →  python -m app.main
│   ├── config.py                 ← all settings loaded from .env
│   ├── api/routes.py             ← FastAPI endpoints
│   ├── llm/
│   │   ├── llm_factory.py        ← creates Generator/Validator instances
│   │   ├── dual_llm_generator.py ← Generator ↔ Validator iterative loop
│   │   ├── petri_net_refinement.py ← Petri Net soundness + fix loop
│   │   ├── qa_chain.py           ← RAG chain (LangChain + LanceDB)
│   │   ├── vectorstore.py        ← LanceDB setup
│   │   ├── mitigation_retriever.py ← per-threat mitigation retrieval
│   │   └── prompts/              ← raw LLM prompt templates
│   └── utils/
│       ├── bpmn_validator.py     ← XML structural validation
│       ├── threat_extractor.py   ← threat element parsing
│       └── ...
├── resources/
│   └── knowledgeBaseLLMWithThreats.json
├── requirements.txt
├── .env.example                  ← configuration template (commit this)
├── .env                          ← your local settings (DO NOT commit)
└── test_dual_llm_config.py       ← LLM smoke test
```

### Dual-LLM flow

```
Original BPMN + Threat Analysis
          │
          ▼
    Generator LLM ──► Mitigated BPMN (v1)
          ▲                  │
          │                  ▼
          └──── Feedback ◄── Validator LLM
         (up to MAX_LLM_ITERATIONS rounds)
                             │
                             ▼
                    Petri Net Validation
                    (BPMN → Petri Net → soundness check)
                             │
                    ┌────────▼────────┐
                    │  Sound?         │
                    │  YES → accept   │
                    │  NO  → fix loop │
                    └─────────────────┘
```

---

## Troubleshooting

### "Ollama connection refused" on `localhost:11434`

Ollama is not running. Start it with:

```bash
ollama serve
```

### "Gemini API key invalid"

Get a key at <https://aistudio.google.com/app/apikey> and set:

```env
GENERATOR_GOOGLE_API_KEY=your_key_here
```

### Petri Net validation always fails

Lower strictness for development:

```env
PETRI_NET_STRICT_MODE=false
MAX_PETRI_NET_FIX_ITERATIONS=3
```

Or temporarily disable it:

```env
ENABLE_PETRI_NET_VALIDATION=false
```

### Max iterations reached without validation pass

```env
MAX_LLM_ITERATIONS=5
VALIDATOR_LLM_TEMPERATURE=0.1
```

### pm4py installation fails (Windows)

```bash
pip install pm4py --no-build-isolation
```

---

## Security Note

`Masterproject-Backend/.env` may contain API keys.
**Never commit it to version control.**
Only `.env.example` (no real credentials) should be committed.

---

*Version 2.1.0 – March 2026*


