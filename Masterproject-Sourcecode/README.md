# Insider Threat Modeler 2.0

A research system for **automated insider-threat modeling in BPMN 2.0** processes, combining a Retrieval-Augmented Generation (RAG) pipeline with a **Dual-LLM** architecture (Generator + Validator) for iterative, formally-verified security mitigation.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [System Requirements](#system-requirements)
4. [Quick Start: Full Application (Frontend + Backend)](#quick-start-full-application-frontend--backend)
5. [Quick Start: Experiments Only](#quick-start-experiments-only)
6. [Configuration Reference (.env)](#configuration-reference-env)
   - [Production Backend (.env)](#production-backend-env)
   - [Evaluation Backend (.env)](#evaluation-backend-env)
7. [Running Experiments](#running-experiments)
   - [Single Evaluation](#single-evaluation)
   - [Iterations Sweep](#iterations-sweep)
   - [Runs Sweep (Stochastic Variability)](#runs-sweep-stochastic-variability)
8. [Generating Plots](#generating-plots)
9. [Auxiliary Scripts](#auxiliary-scripts)
10. [API Endpoints](#api-endpoints)
11. [Experiment Reproducibility Notes](#experiment-reproducibility-notes)

---

## Project Overview

The system takes a BPMN 2.0 process file as input, identifies insider-threat elements via RAG over a curated knowledge base, and produces a **mitigated BPMN** enriched with security controls.

### Core Components

| Component | Description |
|-----------|-------------|
| **Generator LLM** | Produces the mitigated BPMN XML given the original process and threat analysis |
| **Validator LLM** | Reviews each generated BPMN, returning structured feedback for the next iteration |
| **Petri Net Validator** | Formally checks BPMN soundness (deadlocks, unbalanced gateways, missing flows) |
| **RAG Pipeline** | LanceDB-backed semantic retrieval over insider-threat and mitigation knowledge bases |

### Evaluation Metrics

| Metric | Description |
|--------|-------------|
| **RGED** (Relative Graph Edit Distance) | Normalized structural distance between original and mitigated BPMN |
| **Cross-Fitness** (Behavioral Similarity) | pm4py token-replay score measuring how well each BPMN replays traces from the other |
| **LLM Sub-iteration Quality** | Tracks XML validity and Validator issues per Generator↔Validator iteration |
| **Generation Time** | Wall-clock time for the full mitigation pipeline |

---

## Repository Structure

This repository contains **three components** and **two separate backends** with distinct purposes:

| Component | Folder | Purpose |
|-----------|--------|---------|
| **Production Backend** | `Masterproject-Backend/` | FastAPI server used together with the React frontend for interactive use |
| **Evaluation Backend** | `backend_evaluation/` | Same API server **plus** experiment scripts for research evaluation |
| **Frontend** | `Masteproject-Frontend/` | React web application for interactive threat modeling |

> **Important – Two Backends, Two `.env` Files:**
> - `Masterproject-Backend/.env` – LLM and Petri Net settings only; used when running the full application with the UI.
> - `backend_evaluation/.env` – same LLM/Petri Net settings **plus** `EVAL_*` variables that control experiment execution; used only for research sweeps.
> Never mix the two `.env` files.

```
Masterproject-Sourcecode/
├── README.md                         ← this file
│
├── Masterproject-Backend/            ← PRODUCTION BACKEND (use with the frontend)
│   ├── app/
│   │   ├── config.py                 ← settings loaded from .env
│   │   ├── main.py                   ← entry point  →  python -m app.main
│   │   ├── api/routes.py             ← REST endpoints
│   │   ├── llm/                      ← Dual-LLM, Petri Net, RAG modules
│   │   └── utils/                    ← BPMN validator, threat extractor, …
│   ├── resources/
│   │   └── knowledgeBaseLLMWithThreats.json
│   ├── requirements.txt
│   ├── .env.example                  ← template – copy to .env and fill in
│   └── README.md                     ← detailed backend setup guide
│
├── backend_evaluation/               ← EVALUATION BACKEND (experiments & research)
│   ├── app/                          ← identical API server as Masterproject-Backend
│   ├── evaluation_script.py          ← experiment driver (single / sweep / runs_sweep)
│   ├── plot_sweep_results.py         ← unified chart generator
│   ├── Fitness_graph_analyzer.py     ← legacy iterations-sweep plotter
│   ├── check_bpmn_soundness.py       ← batch soundness checker
│   ├── test_dual_llm_config.py       ← smoke-test LLM configuration
│   ├── test_mitigation_rag.py        ← smoke-test RAG retrieval
│   ├── 1.bpmn                        ← sample BPMN used in experiments
│   ├── requirements.txt
│   ├── .env.example                  ← template – includes EVAL_* variables
│   └── README.md                     ← detailed experiment guide
│
└── Masteproject-Frontend/            ← REACT FRONTEND
    ├── src/
    ├── package.json
    └── README.md                     ← frontend setup guide
```

---

## System Requirements

### Backend (both `Masterproject-Backend` and `backend_evaluation`)

| Requirement | Version |
|-------------|---------|
| Python | 3.9 or higher |
| pip | latest |
| **Ollama** *(optional – for local LLMs)* | ≥ 0.4 |
| **Google Cloud account** *(optional – for Gemini)* | – |

### Frontend

| Requirement | Version |
|-------------|---------|
| Node.js | ≥ 16 |
| npm | ≥ 8 |

---

## Quick Start: Full Application (Frontend + Backend)

Use this path when you want to run the **complete web application** – the React UI backed by the production server in `Masterproject-Backend/`.

### 1. Set up the production backend

```bash
cd Masterproject-Backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt

# Copy the configuration template and fill in your LLM settings
cp .env.example .env
```

> See [Production Backend (.env)](#production-backend-env) for every available option.

### 2. Start the production backend

```bash
# From Masterproject-Backend/ (venv active)
python -m app.main
```

The API is now available at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### 3. Start the frontend

```bash
cd Masteproject-Frontend
npm install
npm start
```

Open `http://localhost:3000` in your browser.

---

## Quick Start: Experiments Only

Use this path when you want to run **research experiments** with `evaluation_script.py` (sweeps, metrics, plots). The `backend_evaluation/` folder contains its own copy of the API server that must be running while experimenting.

### 1. Set up the evaluation backend

```bash
cd backend_evaluation

python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

> **Note on pm4py (Windows):** if installation fails, try `pip install pm4py --no-build-isolation`.

### 2. Configure the evaluation backend

```bash
cp .env.example .env
```

Edit `.env` to set your LLM provider, model names, and experiment parameters. See [Evaluation Backend (.env)](#evaluation-backend-env) for all options.

### 3. Start the evaluation backend (terminal 1)

```bash
# From backend_evaluation/ (venv active)
python -m uvicorn app.api.routes:app --host 0.0.0.0 --port 8000 --reload
```

Expected output:
```
INFO:     QA chain setup complete.
INFO:     Mitigation chain setup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

> **Ollama users:** start the daemon first in a separate terminal: `ollama serve`

### 4. Run an experiment (terminal 2)

```bash
# From backend_evaluation/ (same venv active)
python evaluation_script.py
```

Results are saved to `evaluation_results/session_YYYYMMDD_HHMMSS/`.

### 5. Generate plots (optional)

```bash
python plot_sweep_results.py          # auto-detect latest session
python plot_sweep_results.py --save   # save charts to disk
```

---

## Configuration Reference (.env)

Each backend has its **own `.env` file** that must be configured independently.

---

### Production Backend (.env)

**File:** `Masterproject-Backend/.env`  
**Template:** `Masterproject-Backend/.env.example`

This file controls the LLM pipeline and Petri Net validation used by the production server. It does **not** contain any `EVAL_*` or `OLLAMA_KEEP_ALIVE` variables.

#### Dual-LLM

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_DUAL_LLM` | `true` | Enable the Generator + Validator loop |
| `MAX_LLM_ITERATIONS` | `3` | Maximum Generator↔Validator rounds |

#### Generator LLM

| Variable | Default | Description |
|----------|---------|-------------|
| `GENERATOR_LLM_PROVIDER` | `ollama` | `ollama` or `gemini` |
| `GENERATOR_OLLAMA_MODEL` | – | Model name (e.g. `llama3.2:latest`) |
| `GENERATOR_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `GENERATOR_GEMINI_MODEL` | – | Model name (e.g. `gemini-2.5-flash`) |
| `GENERATOR_GOOGLE_API_KEY` | – | Google AI Studio API key |
| `GENERATOR_LLM_TEMPERATURE` | `0.3` | Sampling temperature (0 = deterministic) |
| `GENERATOR_MAX_OUTPUT_TOKENS` | `65536` | Max tokens (Gemini only) |

#### Validator LLM

Same variables prefixed with `VALIDATOR_` instead of `GENERATOR_`. Default temperature is `0.2`.

#### Petri Net Validation

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_PETRI_NET_VALIDATION` | `true` | Run formal soundness check after generation |
| `MAX_PETRI_NET_FIX_ITERATIONS` | `2` | Extra LLM iterations to fix soundness errors |
| `PETRI_NET_STRICT_MODE` | `false` | `true` = reject result on any error; `false` = warn |

#### Database & Resources

| Variable | Default | Description |
|----------|---------|-------------|
| `LANCE_DB_PATH` | `lance_threat_db` | Path to the LanceDB vector store |
| `KNOWLEDGE_BASE_PATH` | `resources/knowledgeBaseLLMWithThreats.json` | Insider-threat knowledge base |

---

### Evaluation Backend (.env)

**File:** `backend_evaluation/.env`  
**Template:** `backend_evaluation/.env.example`

This file contains all the same LLM/Petri Net variables as the production backend **plus** additional variables for controlling experiments and plots.

All LLM, Petri Net, and Database variables are the same as in the production backend (see above), with these additions:

#### Ollama Context Isolation

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_KEEP_ALIVE` | `0` | `0` = unload model after each call (max isolation for sweeps); `-1` = never unload; `"5m"` = Ollama default |

> Set to `"0"` for experiments so each run starts with a fresh model state and no KV-cache from previous calls.

#### Evaluation Script (`EVAL_*`)

| Variable | Default | Description |
|----------|---------|-------------|
| `EVAL_RUN_MODE` | `runs_sweep` | `single` / `sweep` / `runs_sweep` |
| `EVAL_BACKEND_URL` | `http://localhost:8000` | Evaluation backend URL |
| `EVAL_BPMN_TEST_PATH` | `./1.bpmn` | Path to the input BPMN file |
| `EVAL_FIXED_LLM_ITERATIONS` | `15` | Fixed iteration count (used by `runs_sweep`) |
| `EVAL_NUM_RUNS` | `30` | Number of independent runs (used by `runs_sweep`) |
| `EVAL_ITERATIONS_RANGE` | `2,3,...,15` | Comma-separated iteration values (used by `sweep`) |
| `EVAL_FLUSH_OLLAMA_BETWEEN_RUNS` | `true` | Unload Ollama models between runs to reset KV-cache |
| `EVAL_CONTEXT` | `{}` | Process context JSON (e.g. `{"process_name":"Order management"}`) |
| `EVAL_PRINCIPLES` | `Integrity` | Security principles: `Integrity`, `Confidentiality`, `Availability` |
| `EVAL_OUTPUT_DIR` | `evaluation_results` | Root output folder |

#### Plot Script (`EVAL_PLOT_*`)

| Variable | Default | Description |
|----------|---------|-------------|
| `EVAL_PLOT_SESSION_DIR` | *(latest)* | Session folder to plot; empty = auto-detect latest |
| `EVAL_PLOT_MODE` | *(auto)* | `runs_sweep` or `sweep`; empty = auto-detect |
| `EVAL_PLOT_SAVE` | `true` | `true` = save to disk; `false` = interactive window |
| `EVAL_PLOT_OUTPUT_DIR` | `<session>/plots/` | Directory for saved chart files |

---

## Running Experiments

> All experiment commands below must be run from the **`backend_evaluation/`** directory with its virtual environment active.
> The evaluation backend server must be running in a separate terminal (see [Quick Start: Experiments Only](#quick-start-experiments-only)).

All experiments are driven by `evaluation_script.py`. Set `EVAL_RUN_MODE` in `backend_evaluation/.env`, then:

```bash
# From backend_evaluation/ with venv active
python evaluation_script.py
```

Results are saved under `evaluation_results/session_YYYYMMDD_HHMMSS/`.

### Single Evaluation

```ini
# .env
EVAL_RUN_MODE=single
EVAL_BPMN_TEST_PATH=./1.bpmn
EVAL_PRINCIPLES=Integrity
```

Produces a full evaluation report for a single BPMN + LLM configuration.

### Iterations Sweep

Varies `max_llm_iterations` from a list of values and measures RGED, Cross-Fitness, and generation time for each.

```ini
# .env
EVAL_RUN_MODE=sweep
EVAL_ITERATIONS_RANGE=1,2,3,4,5,7,10,15
EVAL_BPMN_TEST_PATH=./1.bpmn
```

**Output files** (inside the session folder):

| File | Description |
|------|-------------|
| `sweep_iterations_results.csv` | One row per `max_llm_iterations` value: RGED, Cross-Fitness, timing |
| `sweep_llm_iterations_detail.csv` | One row per Generator↔Validator sub-iteration: XML validity, issues count |
| `sweep_iterations_results.json` | Complete raw data in JSON |
| `sweep_iter_N/mitigated_bpmn_iterN.xml` | Generated BPMN for each iteration count |
| `sweep_iter_N/ged_analysis.json` | GED details for each N |
| `sweep_iter_N/behavioral_similarity.json` | Fitness details for each N |

### Runs Sweep (Stochastic Variability)

Fixes `max_llm_iterations` and repeats the generation `EVAL_NUM_RUNS` times to characterize LLM stochasticity.

```ini
# .env
EVAL_RUN_MODE=runs_sweep
EVAL_FIXED_LLM_ITERATIONS=15
EVAL_NUM_RUNS=100
EVAL_FLUSH_OLLAMA_BETWEEN_RUNS=true
```

**Output files** (inside the session folder):

| File | Description |
|------|-------------|
| `runs_sweep_results.csv` | One row per run: RGED, Cross-Fitness, timing |
| `runs_sweep_llm_detail.csv` | One row per sub-iteration per run |
| `run_N/mitigated_bpmn_runN.xml` | Generated BPMN for each run |

> **Reproducibility tip:** Set `EVAL_FLUSH_OLLAMA_BETWEEN_RUNS=true` and `OLLAMA_KEEP_ALIVE=0` to ensure each run starts from a completely fresh model state (no KV-cache residue). This adds ~10–60 s of model-reload time per run but guarantees statistically independent measurements.

---

## Generating Plots

After running any sweep, use `plot_sweep_results.py` to visualize results:

```bash
# Auto-detect latest session and mode:
python plot_sweep_results.py

# Force a specific mode:
python plot_sweep_results.py --mode runs_sweep
python plot_sweep_results.py --mode sweep

# Point to a specific session folder:
python plot_sweep_results.py --session evaluation_results/session_YYYYMMDD_HHMMSS

# Save charts to disk instead of showing interactively:
python plot_sweep_results.py --save
```

**Chart descriptions:**

| Figure | Sweep mode | Content |
|--------|-----------|---------|
| Fig 1 | both | Generation time (s) vs X-axis |
| Fig 2 | both | RGED and Cross-Fitness vs X-axis |
| Fig 3 | both | XML errors, Validator issues vs X-axis |
| Fig 4 | both | Per-sub-iteration state heatmap |

The legacy `Fitness_graph_analyzer.py` plots only the iterations sweep (backward-compatible with older session formats):

```bash
python Fitness_graph_analyzer.py                        # latest session
python Fitness_graph_analyzer.py <session_dir>
python Fitness_graph_analyzer.py <sweep_iterations_results.csv>
```

---

## Auxiliary Scripts

> All scripts below live in `backend_evaluation/` and require the evaluation backend to be running.

### Verify LLM configuration

Run before any experiment to confirm `.env` is loaded correctly and LLM providers are reachable:

```bash
python test_dual_llm_config.py
```

### Test RAG retrieval

Verifies the mitigation vector store returns relevant results:

```bash
python test_mitigation_rag.py
```

### Batch BPMN soundness check

Validates a folder of BPMN files via the `/validate-bpmn/` endpoint:

```bash
# Edit BPMN_FOLDER_PATH inside check_bpmn_soundness.py, then:
python check_bpmn_soundness.py
```

Results are saved to `soundness_results/`.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/validate-bpmn/` | Validate a BPMN file (XML + Petri net soundness) |
| `POST` | `/analyze-xml/` | Run RAG-based insider-threat analysis |
| `POST` | `/generate-mitigated-bpmn/` | Generate a mitigated BPMN (Dual-LLM pipeline) |
| `POST` | `/download-bpmn/` | Download a BPMN XML as a file |

Full interactive documentation is available at `http://localhost:8000/docs` when the server is running.

**Example: generate a mitigated BPMN via curl**

```bash
curl -X POST http://localhost:8000/generate-mitigated-bpmn/ \
  -F "file=@1.bpmn;type=application/xml" \
  -F 'context={"process_name":"Order management"}' \
  -F 'principles=["Integrity"]' \
  -F 'threat_analysis=<threat_analysis.md' \
  -o mitigated.json
```

---

## Experiment Reproducibility Notes

### LLM Models Used in the Paper

| Role | Provider | Model |
|------|----------|-------|
| Generator | Ollama (local) | set `GENERATOR_OLLAMA_MODEL` in `.env` |
| Validator | Ollama (local) | set `VALIDATOR_OLLAMA_MODEL` in `.env` |

> The specific model names depend on what you have pulled in Ollama. Run `ollama list` to see available models. Pull any model with `ollama pull <model-name>`.

### Determinism Considerations

- LLM outputs are **non-deterministic** even at `temperature=0` due to GPU floating-point parallelism.
- Set `EVAL_FLUSH_OLLAMA_BETWEEN_RUNS=true` and `OLLAMA_KEEP_ALIVE=0` to eliminate KV-cache influence across runs.
- Each `runs_sweep` session creates a separate timestamped directory so results are never overwritten.

### Hardware Requirements for Full Sweep

Running 100 independent Ollama runs with `pm4py` metrics is compute-intensive. Minimum recommended:

- **GPU:** 24 GB VRAM (for 32-billion-parameter models)
- **RAM:** 32 GB
- **Disk:** ~5 GB for evaluation outputs

For lighter experiments, reduce `EVAL_NUM_RUNS` or use a smaller model.

### Step-by-Step Replication

```bash
# Terminal 1 – Ollama daemon
ollama serve
ollama pull <generator-model>
ollama pull <validator-model>

# Terminal 2 – Evaluation backend
cd backend_evaluation
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in model names and EVAL_* settings
python -m uvicorn app.api.routes:app --host 0.0.0.0 --port 8000

# Terminal 3 – Experiment runner (once the backend is ready)
cd backend_evaluation
source .venv/bin/activate
python evaluation_script.py

# Terminal 3 – Plot results after the sweep finishes
python plot_sweep_results.py --save
```

---

## Security Note

Both `.env` files may contain API keys.
**Never commit `Masterproject-Backend/.env` or `backend_evaluation/.env` to version control.**
Use the `.env.example` templates (no real credentials) as the only committed reference.

---

## Acknowledgements

The initial version of this tool was developed by **Lukas Sager** and **Jamine Hochuli** as part of their master's thesis *"Threat Identification and Mitigation using Process Models"*, supervised by **Jan von der Assen** and **Thomas Grüsbl**.
