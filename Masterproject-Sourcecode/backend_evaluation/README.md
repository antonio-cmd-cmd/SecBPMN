# backend_evaluation – Evaluation Backend & Experiment Runner

This folder contains the **research evaluation environment** for the Insider Threat Modeler. It packages:

- **`app/`** – a copy of the same FastAPI backend as `Masterproject-Backend/`, used here as the experiment server.
- **`evaluation_script.py`** – experiment driver that calls the API, computes metrics (RGED, Cross-Fitness), and saves results.
- **`plot_sweep_results.py`** – chart generator for sweep results.
- **`check_bpmn_soundness.py`** – batch soundness checker.
- Support scripts: `test_dual_llm_config.py`, `test_mitigation_rag.py`.

> **Not to be confused with `Masterproject-Backend/`**, which is the production backend paired with the React frontend. This folder is for running research experiments only.
>
> The two backends have **separate `.env` files**: `backend_evaluation/.env` includes additional `EVAL_*` and `OLLAMA_KEEP_ALIVE` variables not present in `Masterproject-Backend/.env`.

For the full project description and frontend setup, see the [root README](../README.md).

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration (.env)](#configuration-env)
   - [LLM Options](#llm-options)
   - [Petri Net Validation](#petri-net-validation-options)
   - [Ollama Context Isolation](#ollama-context-isolation)
   - [Evaluation Options](#evaluation-options)
   - [Plot Options](#plot-options)
4. [Starting the Backend Server](#starting-the-backend-server)
5. [Running Experiments](#running-experiments)
   - [1. Single Evaluation](#1-single-evaluation)
   - [2. Iterations Sweep](#2-iterations-sweep)
   - [3. Runs Sweep – Stochastic Variability](#3-runs-sweep--stochastic-variability)
6. [Generating Plots](#generating-plots)
7. [Auxiliary Scripts](#auxiliary-scripts)
8. [API Endpoints](#api-endpoints)
9. [Troubleshooting](#troubleshooting)

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
cd backend_evaluation

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

This `.env` file is **exclusive to `backend_evaluation/`**. Do not copy it to `Masterproject-Backend/`.

---

### LLM Options

#### Dual-LLM system (recommended)

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

#### Legacy single-LLM (backward-compatible)

```env
USE_DUAL_LLM=false
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:latest
OLLAMA_BASE_URL=http://localhost:11434
LLM_TEMPERATURE=0.3
```

---

### Petri Net Validation Options

```env
ENABLE_PETRI_NET_VALIDATION=true   # formal soundness check after LLM iterations
MAX_PETRI_NET_FIX_ITERATIONS=2     # extra correction iterations on failure
PETRI_NET_STRICT_MODE=false        # true = reject on error; false = warn and accept
```

---

### Ollama Context Isolation

> **Only present in `backend_evaluation/.env`** – not found in `Masterproject-Backend/.env`.

```env
# "0"   → unload model immediately after each response (max isolation for sweeps)
# "-1"  → never unload (fastest, but no KV-cache isolation between runs)
# "5m"  → Ollama default (keep loaded for 5 minutes)
OLLAMA_KEEP_ALIVE=0
```

Set to `"0"` when running evaluation sweeps to ensure each run starts with a completely fresh model state and no KV-cache residue from previous calls.

---

### Evaluation Options

> **Only present in `backend_evaluation/.env`** – not found in `Masterproject-Backend/.env`.

These variables control `evaluation_script.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `EVAL_RUN_MODE` | `runs_sweep` | `single` / `sweep` / `runs_sweep` |
| `EVAL_BACKEND_URL` | `http://localhost:8000` | Evaluation backend URL |
| `EVAL_BPMN_TEST_PATH` | `./1.bpmn` | Path to the input BPMN file |
| `EVAL_FIXED_LLM_ITERATIONS` | `15` | Fixed iteration count (used by `runs_sweep`) |
| `EVAL_NUM_RUNS` | `30` | Number of independent runs (used by `runs_sweep`) |
| `EVAL_ITERATIONS_RANGE` | `2,3,...,15` | Comma-separated iteration values (used by `sweep`) |
| `EVAL_FLUSH_OLLAMA_BETWEEN_RUNS` | `true` | Unload Ollama model between runs to reset KV-cache |
| `EVAL_CONTEXT` | `{}` | Process context JSON (e.g. `{"process_name":"Order management"}`) |
| `EVAL_PRINCIPLES` | `Integrity` | Security principles: `Integrity`, `Confidentiality`, `Availability` |
| `EVAL_OUTPUT_DIR` | `evaluation_results` | Root output folder |

---

### Plot Options

| Variable | Default | Description |
|----------|---------|-------------|
| `EVAL_PLOT_SESSION_DIR` | *(latest)* | Session folder to plot; empty = auto-detect latest |
| `EVAL_PLOT_MODE` | *(auto)* | `runs_sweep` or `sweep`; empty = auto-detect from CSVs |
| `EVAL_PLOT_SAVE` | `true` | `true` = save to disk; `false` = interactive window |
| `EVAL_PLOT_OUTPUT_DIR` | `<session>/plots/` | Directory for saved chart files |

---

## Starting the Backend Server

The backend **must be running** before launching any experiment script. Open a dedicated terminal:

```bash
# From backend_evaluation/ (with venv active)
python -m uvicorn app.api.routes:app --host 0.0.0.0 --port 8000 --reload
```

Expected startup output:

```
INFO:     QA chain setup complete.
INFO:     Mitigation chain setup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: `curl http://localhost:8000/` → `{"status": "ok"}`

> **Ollama users:** start the Ollama daemon first in a separate terminal:
> ```bash
> ollama serve
> ollama pull llama3.2:latest   # or your chosen model
> ```

---

## Running Experiments

All experiment modes are driven by **`evaluation_script.py`**.  
Set `EVAL_RUN_MODE` in `backend_evaluation/.env`, then run in a second terminal (keep the server running in the first):

```bash
# From backend_evaluation/ (venv active, server already running)
python evaluation_script.py
```

Results are saved under `evaluation_results/session_YYYYMMDD_HHMMSS/`.

---

### 1. Single Evaluation

Runs the full pipeline once on a single BPMN file. Use this to quickly validate your setup or inspect one result in detail.

```env
# backend_evaluation/.env
EVAL_RUN_MODE=single
EVAL_BPMN_TEST_PATH=./1.bpmn
EVAL_PRINCIPLES=Integrity
EVAL_CONTEXT={"process_name": "Purchase order"}
```

```bash
python evaluation_script.py
```

**Output** (inside `evaluation_results/session_.../`):

| File | Content |
|------|---------|
| `mitigated_bpmn.xml` | The generated mitigated BPMN |
| `threat_analysis.md` | RAG-based threat report |
| `ged_analysis.json` | RGED details |
| `behavioral_similarity.json` | Cross-Fitness details |
| `evaluation_report.json` | Full metrics summary |

---

### 2. Iterations Sweep

Varies `MAX_LLM_ITERATIONS` across a list of values and records RGED, Cross-Fitness, and generation time for each. Use this to understand how the number of Generator↔Validator rounds affects output quality.

```env
# backend_evaluation/.env
EVAL_RUN_MODE=sweep
EVAL_ITERATIONS_RANGE=1,2,3,5,7,10,15
EVAL_BPMN_TEST_PATH=./1.bpmn
EVAL_PRINCIPLES=Integrity
```

```bash
python evaluation_script.py
```

**Output** (inside the session folder):

| File | Content |
|------|---------|
| `sweep_iterations_results.csv` | One row per `MAX_LLM_ITERATIONS` value: RGED, Cross-Fitness, timing |
| `sweep_llm_iterations_detail.csv` | One row per Generator↔Validator sub-iteration: XML validity, issue count |
| `sweep_iterations_results.json` | Complete raw data in JSON |
| `sweep_iter_N/mitigated_bpmn_iterN.xml` | Generated BPMN for each N |
| `sweep_iter_N/ged_analysis.json` | RGED details for each N |
| `sweep_iter_N/behavioral_similarity.json` | Fitness details for each N |

---

### 3. Runs Sweep – Stochastic Variability

Fixes `MAX_LLM_ITERATIONS` and repeats the generation `EVAL_NUM_RUNS` times to characterize the natural variability of LLM outputs. Use this to quantify reproducibility and compute mean ± std statistics.

```env
# backend_evaluation/.env
EVAL_RUN_MODE=runs_sweep
EVAL_FIXED_LLM_ITERATIONS=15
EVAL_NUM_RUNS=30
EVAL_FLUSH_OLLAMA_BETWEEN_RUNS=true   # reset KV-cache between runs
OLLAMA_KEEP_ALIVE=0
```

```bash
python evaluation_script.py
```

**Output** (inside the session folder):

| File | Content |
|------|---------|
| `runs_sweep_results.csv` | One row per run: RGED, Cross-Fitness, timing |
| `runs_sweep_llm_detail.csv` | One row per sub-iteration per run |
| `run_N/mitigated_bpmn_runN.xml` | Generated BPMN for each run N |

> **Reproducibility tip:** `EVAL_FLUSH_OLLAMA_BETWEEN_RUNS=true` + `OLLAMA_KEEP_ALIVE=0` reloads the model from disk before every run, eliminating KV-cache residue. This adds ~10–60 s per run but guarantees statistically independent samples.

> **Hardware:** 100 runs with a 32 B-parameter Ollama model requires ≥ 24 GB VRAM and ≥ 32 GB RAM. Reduce `EVAL_NUM_RUNS` for lighter experiments.

---

## Generating Plots

After any sweep, use `plot_sweep_results.py` to visualize results:

```bash
# Auto-detect latest session and mode (recommended)
python plot_sweep_results.py

# Force a specific mode
python plot_sweep_results.py --mode runs_sweep
python plot_sweep_results.py --mode sweep

# Point to a specific session folder
python plot_sweep_results.py --session evaluation_results/session_YYYYMMDD_HHMMSS

# Save charts to PNG files instead of opening an interactive window
python plot_sweep_results.py --save
```

**Generated charts:**

| Figure | Content |
|--------|---------|
| Fig 1 | Generation time (s) |
| Fig 2 | RGED and Cross-Fitness |
| Fig 3 | XML errors and Validator issues per iteration |
| Fig 4 | Per-sub-iteration state heatmap |

The legacy `Fitness_graph_analyzer.py` plots only the iterations sweep (backward-compatible with older session formats):

```bash
python Fitness_graph_analyzer.py                         # latest session
python Fitness_graph_analyzer.py <session_dir>
python Fitness_graph_analyzer.py <sweep_iterations_results.csv>
```

---

## Auxiliary Scripts

### Verify LLM configuration

Run this **before starting any experiment** to confirm `.env` is loaded correctly and LLM providers are reachable:

```bash
python test_dual_llm_config.py
```

### Test RAG retrieval

Verifies the mitigation vector store is reachable and returns relevant results:

```bash
python test_mitigation_rag.py
```

### Batch BPMN soundness check

Sends a folder of BPMN files to the `/validate-bpmn/` endpoint and saves a soundness report to `soundness_results/`:

```bash
# Edit BPMN_FOLDER_PATH inside check_bpmn_soundness.py, then:
python check_bpmn_soundness.py
```

---

## API Endpoints

The server exposes the same endpoints as `Masterproject-Backend/`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Health check |
| `POST` | `/validate-bpmn/` | Validate a BPMN file (XML + Petri net soundness) |
| `POST` | `/analyze-xml/` | Run RAG-based insider-threat analysis |
| `POST` | `/generate-mitigated-bpmn/` | Generate a mitigated BPMN (full Dual-LLM pipeline) |
| `POST` | `/download-bpmn/` | Download a BPMN XML as a file |

Full interactive documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

**Example – generate a mitigated BPMN via curl:**

```bash
curl -X POST http://localhost:8000/generate-mitigated-bpmn/ \
  -F "file=@1.bpmn;type=application/xml" \
  -F 'context={"process_name":"Order management"}' \
  -F 'principles=["Integrity"]' \
  -F 'threat_analysis=<threat_analysis.md' \
  -o mitigated.json
```

---

## Troubleshooting

### "Connection refused" on `localhost:11434`

Ollama is not running. Start it with `ollama serve` in a separate terminal.

### "Gemini API key invalid"

Obtain a key at <https://aistudio.google.com/app/apikey> and set:

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

### pm4py installation fails (Windows)

```bash
pip install pm4py --no-build-isolation
```

---

## Security Note

`backend_evaluation/.env` may contain API keys.
**Never commit it to version control.**
Only `.env.example` (no real credentials) should be committed.

---

*Version 2.1.0 – March 2026*


