# Integrazione RAG per Mitigazioni - Documentazione

## Panoramica

Questa implementazione aggiunge un sistema RAG (Retrieval-Augmented Generation) dedicato per recuperare strategie di mitigazione da un database di best practice in formato JSON. Quando l'LLM analizza un processo BPMN, ora recupera automaticamente le mitigazioni più rilevanti basandosi sulle **threat specifiche** grazie al campo `mitigated_threats`.

## 🎯 Novità Principali

### Campo `mitigated_threats`
Il file JSON ora include per ogni best practice un campo `mitigated_threats` che elenca esplicitamente quali minacce quella pratica mitiga:

```json
{
  "id": 1,
  "best_practice": "Know and protect your critical assets",
  "mitigated_threats": [
    "Theft of Intellectual Property",
    "Corporate Espionage",
    "Sabotage of critical infrastructure",
    "Unintentional data loss"
  ],
  "mitigation_strategies": [
    "Identify and inventory all critical assets...",
    "Conduct risk assessments..."
  ]
}
```

Questo permette al sistema RAG di trovare **esattamente** le best practice rilevanti per una specifica minaccia.

## Modifiche Implementate

### 1. Nuovo File: `mitigation.json`
- **Posizione**: `Masterproject-Backend/resources/mitigation.json`
- **Contenuto**: Best practice per la mitigazione di insider threat
- **Struttura Aggiornata**: 
  ```json
  [
    {
      "id": 1,
      "best_practice": "Nome della best practice",
      "mitigated_threats": [
        "Threat 1",
        "Threat 2"
      ],
      "mitigation_strategies": [
        "Strategy 1",
        "Strategy 2"
      ]
    }
  ]
  ```

### 2. Aggiornamento: `mitigation_loader.py`
- **Posizione**: `app/utils/mitigation_loader.py`
- **Funzione**: Carica le best practice dal JSON e le converte in oggetti Document per il vectorstore
- **Funzione principale**: `load_mitigation_practices(json_path)`
- **Novità**: 
  - Include `mitigated_threats` nel contenuto del documento per migliorare la ricerca semantica
  - Formatta le threat in modo leggibile nel `page_content`
  - Aggiunge `mitigated_threats` ai metadata per filtraggio

### 3. **NUOVO**: `threat_extractor.py`
- **Posizione**: `app/utils/threat_extractor.py`
- **Funzioni**:
  - `extract_threat_keywords(principles, context)`: Estrae threat keywords basandosi sui principi di sicurezza e contesto
  - `build_targeted_mitigation_query(threat_keywords, context, principles)`: Costruisce query RAG mirate per threat specifiche
  - `format_mitigation_results(source_documents, max_results)`: Formatta i risultati in modo strutturato

### 4. Aggiornamento: `vectorstore.py`
- **Nuova funzione**: `setup_mitigation_vectorstore(docs, db_path="lance_mitigation_db")`
- **Scopo**: Crea un vectorstore separato specifico per le mitigazioni
- **Database**: `lance_mitigation_db/` (separato da quello delle threat)

### 5. Aggiornamento: `qa_chain.py`
- **Nuova funzione**: `build_mitigation_qa_chain(mitigation_vectorstore)`
- **Scopo**: Crea una QA chain dedicata per interrogare il vectorstore delle mitigazioni
- **Configurazione**: Recupera top 15 documenti più rilevanti (k=15)

### 6. Aggiornamento: `routes.py`
- **Variabile globale**: Aggiunta `mitigation_chain` per gestire le query di mitigazione
- **Inizializzazione**: Nel `lifespan`, carica il file JSON e inizializza il vectorstore delle mitigazioni
- **Integrazione**: Passa `mitigation_chain` alla funzione `build_analysis_query`

### 7. **AGGIORNAMENTO CHIAVE**: `query_builder.py`
- **Parametro aggiunto**: `mitigation_chain=None` alla funzione `build_analysis_query`
- **Logica RAG Migliorata**: 
  1. Estrae threat keywords basati su principi e contesto usando `extract_threat_keywords()`
  2. Costruisce una query mirata usando `build_targeted_mitigation_query()`
  3. Interroga il vectorstore delle mitigazioni
  4. Formatta i risultati usando `format_mitigation_results()`
  5. Include le mitigazioni nel prompt dell'LLM con informazioni sulle threat mitigate

### 8. Aggiornamento: `prompt_threat_analysis.py`
- **Nuova variabile input**: `mitigation_context`
- **Sezione aggiunta**: `{mitigation_context}` inserita nel template del prompt
- **Istruzioni aggiornate**: L'LLM ora riceve l'istruzione di prioritizzare le best practice recuperate dal RAG

## Flusso di Lavoro Migliorato

```
1. Avvio dell'applicazione
   ↓
2. Caricamento mitigation.json → Document objects
   (Include mitigated_threats nel contenuto)
   ↓
3. Creazione vectorstore mitigazioni (LanceDB)
   (Embedding con all-mpnet-base-v2)
   ↓
4. Build mitigation_chain (QA chain)
   ↓
5. Utente carica BPMN per analisi
   ↓
6. query_builder.py - FASE RAG INTELLIGENTE:
   
   a) extract_threat_keywords(principles, context)
      ├─ Mappa principi di sicurezza → threat keywords
      ├─ "Integrity" → ["Data Corruption", "Unauthorized Modification", ...]
      ├─ "Confidentiality" → ["Data Leakage", "Theft of IP", ...]
      └─ Analizza contesto per threat aggiuntive
   
   b) build_targeted_mitigation_query()
      ├─ Crea query specifica: "Find mitigations for: Data Corruption, 
      |                          Unauthorized Access, Data Leakage..."
      └─ Include contesto processo e tecnologie
   
   c) mitigation_chain.invoke(targeted_query)
      ├─ Cerca nel vectorstore usando similarità semantica
      ├─ Trova best practices che mitigation quelle threat
      └─ Grazie al campo mitigated_threats, trova match precisi!
   
   d) format_mitigation_results()
      ├─ Formatta top 15 risultati
      ├─ Include: best practice name + mitigated threats + strategies
      └─ Output strutturato per il prompt
   ↓
7. LLM riceve prompt con:
   - BPMN XML
   - Contesto processo
   - Principi di sicurezza
   - **Best practices mirate per threat specifiche** ← CHIAVE!
   ↓
8. LLM genera threat analysis con mitigazioni precise
```

## 🔍 Esempio Pratico

### Input:
- **Principio**: Confidentiality
- **Contesto**: "Customer data verification process using database"

### Processo RAG:

1. **Threat Extraction**:
   ```python
   extract_threat_keywords(["Confidentiality"], context)
   # Output: ["Data Leakage", "Unauthorized Access", 
   #          "Information Disclosure", "Theft of IP", 
   #          "Corporate Espionage", "Data Breach", 
   #          "PII Exposure"]
   ```

2. **Query Mirata**:
   ```
   Find mitigation strategies for: Data Leakage, Unauthorized Access, 
   Information Disclosure, Theft of Intellectual Property...
   Process context: Customer data verification process
   Technologies: database
   ```

3. **Retrieval**:
   Il vectorstore trova best practices con `mitigated_threats` che includono:
   - "Data Leakage" → "Monitor and control data exfiltration"
   - "Unauthorized Access" → "Implement strict access controls"
   - "PII Exposure" → "Encrypt sensitive data"

4. **Output nel Prompt**:
   ```markdown
   ### 1. Monitor and control data exfiltration
   **Addresses threats:** Data Leakage, Information Disclosure
   
   Mitigation Strategies:
     - Deploy DLP solutions
     - Monitor network traffic for anomalies
     - Restrict removable media usage
   ```

## Vantaggi della Nuova Implementazione

1. **Mitigazioni Precise**: Il campo `mitigated_threats` permette match esatti tra threat identificate e best practice
2. **Query Intelligenti**: L'estrazione automatica delle threat dai principi di sicurezza rende le query RAG molto più mirate
3. **Context-Aware**: Il sistema considera il contesto del processo per identificare threat aggiuntive
4. **Scalabilità**: Facile aggiungere nuove best practice con le loro threat associate
5. **Separazione Concerns**: Vectorstore separato per threat e mitigazioni
6. **Flessibilità**: L'LLM può ancora suggerire mitigazioni proprie se necessario
7. **Tracciabilità**: Ogni mitigation mostra esplicitamente quali threat indirizza

## Mappatura Principi → Threat

Il sistema include mappature predefinite:

- **Integrity** → Data Corruption, Unauthorized Modification, Data Falsification, Sabotage
- **Confidentiality** → Data Leakage, Unauthorized Access, Theft of IP, Corporate Espionage
- **Availability** → Denial of Service, Sabotage, System Disruption
- **Accountability** → Privilege Abuse, Unauthorized Activity
- **Authorization** → Privilege Escalation, Access Control Violations

Inoltre analizza il contesto per aggiungere threat specifiche del dominio.

## Testing

### Script di Test
Eseguire: `python test_mitigation_rag.py`

Il test verifica:
1. Caricamento del file JSON
2. Creazione del vectorstore
3. Recupero di mitigazioni rilevanti tramite query

### Test Manuale
1. Avviare il backend: `python -m app.main`
2. Caricare un BPMN tramite il frontend
3. Verificare che l'analisi includa mitigazioni specifiche e dettagliate

## Configurazione

### File Richiesti
- `resources/mitigation.json`: Database delle best practice

### Dipendenze
Nessuna nuova dipendenza richiesta. Utilizza le stesse librerie già presenti:
- `langchain`
- `langchain-huggingface`
- `lancedb`

### Database
Il sistema crea automaticamente:
- `lance_mitigation_db/`: Directory per il vectorstore delle mitigazioni

## Manutenzione

### Aggiungere Nuove Mitigazioni
1. Aprire `resources/mitigation.json`
2. Aggiungere nuove entry nell'array `best_practices`
3. Aggiornare `total_practices`
4. Riavviare il backend per ricaricare il vectorstore

### Ottimizzazione
- **k value**: Modificare in `qa_chain.py` → `build_mitigation_qa_chain` (attualmente k=10)
- **Risultati nel prompt**: Modificare in `query_builder.py` → limitazione `[:15]` (attualmente 15)

## Note Tecniche

- Il vectorstore usa lo stesso embedding model delle threat: `sentence-transformers/all-mpnet-base-v2`
- Le mitigazioni sono indicizzate per titolo, categoria e descrizione
- Il sistema è fault-tolerant: se il file JSON non esiste, l'app funziona senza RAG mitigazioni
