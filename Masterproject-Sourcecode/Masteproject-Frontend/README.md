# Insider Threat Modeler 2.0 – Frontend

React-based web interface for the Insider Threat Modeler. Provides a guided, multi-step workflow to upload a BPMN 2.0 process, configure security context, trigger threat analysis and BPMN mitigation, and visually inspect the results side-by-side.

> The **production backend** (`Masterproject-Backend/`) must be running before using the frontend.
> Do not use `backend_evaluation/` with the UI – that backend is reserved for research experiments.
>
> For full setup instructions, see the [root README](../README.md).

---

## Features

- **BPMN upload & validation** – upload a `.bpmn` file; the app validates it against the backend before proceeding
- **Context configuration** – specify process name, participants, and other context information
- **Security principles selection** – choose among Integrity, Confidentiality, and Availability
- **Threat analysis** – RAG-based insider-threat analysis returned as a structured report
- **Mitigated BPMN generation** – triggers the Dual-LLM pipeline and displays the enriched BPMN
- **Side-by-side BPMN viewer** – compare original and mitigated diagrams using the embedded `bpmn-js` renderer
- **Download** – export the mitigated BPMN XML file

---

## Requirements

| Requirement | Version |
|-------------|---------|
| Node.js | ≥ 16 |
| npm | ≥ 8 |

---

## Setup & Run

### 1. Start the production backend first

```bash
cd ../Masterproject-Backend
# (activate venv, then)
python -m app.main
```

The backend must be reachable at `http://localhost:8000` before the frontend is useful.

### 2. Install frontend dependencies and start

```bash
cd Masteproject-Frontend
npm install
npm start
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm start` | Start the development server at http://localhost:3000 |
| `npm test` | Run the test suite |
| `npm run build` | Build a production bundle in `build/` |

---

## Project Structure

```
src/
├── App.js                  ← main application shell and page routing
├── App.css                 ← global styles
├── components/
│   ├── StartPage.js        ← landing page
│   ├── ContextPage.js      ← process context form
│   ├── BpmnModelViewer.js  ← bpmn-js based diagram viewer
│   └── ...
├── models/
│   └── securityPrinciples.js  ← security principle definitions
└── resources/              ← static assets
```

---

*This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).*


