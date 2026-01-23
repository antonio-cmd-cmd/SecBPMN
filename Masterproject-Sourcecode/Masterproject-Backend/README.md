# Insider Threat Modeler 2.0– Backend

This backend provides the API for the Insider Threat Modeler in BPMN 2.0, including the RAG pipeline with Anthropic's Claude models.

---

## Requirements

-   Python **3.9+**
-   pip

---

## API Key Configuration

1. **Get an API Key**

2. **Add the API Key to `config.py`**

    ```python
    ANTHROPIC_API_KEY = "your_api_key_here"
    ```

---

## Running the Backend

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the backend:

```bash
python -m app.main
```

---

## Database Notes

-   **RAG** is powered by LangChain with Anthropic Claude as the LLM.
-   Knowledge base documents are stored in:  
    `resources/knowledgeBaseLLMWithThreats.json`
-   Vector database is created in:  
    `lance_threat_db`
-   If you need to reset the vector DB, delete that folder:

```bash
rm -rf lance_threat_db
```

(Windows: `rmdir /s /q lance_threat_db`)
