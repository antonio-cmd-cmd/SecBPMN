# Integrazione Gemini con google-genai

Questo documento spiega l'integrazione di Gemini nel backend usando la nuova libreria `google-genai`.

## Caratteristiche

- ✅ Supporto per modello **gemini-2.5-flash** (ultimo disponibile)
- ✅ Utilizzo della libreria moderna `google-genai` (invece di `google-generativeai`)
- ✅ Compatibilità con l'architettura LangChain esistente
- ✅ Switching facile tra Ollama (locale) e Gemini (cloud)
- ✅ Configurazione via variabili d'ambiente

## Installazione

1. **Installa le dipendenze:**
   ```bash
   cd Masterproject-Backend
   pip install -r requirements.txt
   ```

2. **Configura l'ambiente:**
   ```bash
   cp .env.example .env
   ```

3. **Modifica `.env` con le tue credenziali:**
   ```env
   LLM_PROVIDER=gemini
   GEMINI_MODEL=gemini-2.5-flash
   GOOGLE_API_KEY=your-actual-api-key-here
   LLM_TEMPERATURE=0.7
   ```

## Ottenere la API Key di Google

1. Vai su [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Accedi con il tuo account Google
3. Clicca su "Get API key" o "Create API key"
4. Copia la chiave generata
5. Incollala nel file `.env` come valore di `GOOGLE_API_KEY`

## Test dell'Integrazione

È disponibile uno script di test completo:

```bash
cd Masterproject-Backend
python test_gemini_integration.py
```

Lo script esegue due test:
1. **Test diretto API**: Verifica che la connessione a Gemini funzioni
2. **Test integrazione backend**: Verifica che il wrapper LLM funzioni correttamente

## Utilizzo nel Codice

### Ottenere l'istanza LLM

```python
from app.llm.qa_chain import get_llm

# Ottiene automaticamente l'LLM configurato (Ollama o Gemini)
llm = get_llm()

# Usa l'LLM
response = llm._call("Il tuo prompt qui")
print(response)
```

### Chain con Retrieval

```python
from app.llm.qa_chain import build_qa_chain
from app.llm.vectorstore import get_vector_store

# Carica il vector store
vectorstore = get_vector_store()

# Crea la chain (usa automaticamente l'LLM configurato)
qa_chain = build_qa_chain(vectorstore)

# Esegui una query
result = qa_chain.invoke({"query": "Cos'è un insider threat?"})
print(result["result"])
```

## Differenze tra google-generativeai e google-genai

### Vecchia libreria (google-generativeai)
```python
import google.generativeai as genai

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.5-flash")
response = model.generate_content(prompt)
```

### Nuova libreria (google-genai) ✅
```python
from google import genai
from google.genai import types

client = genai.Client(api_key=API_KEY)
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(temperature=0.7)
)
```

## Architettura

### Componenti Principali

1. **`app/config.py`**: Gestisce le variabili d'ambiente e la configurazione
2. **`app/llm/qa_chain.py`**: Contiene la classe `GeminiLLM` e la funzione `get_llm()`
3. **`.env`**: File di configurazione con le credenziali

### Flusso di Esecuzione

```
API Request → routes.py → get_llm() → GeminiLLM o ChatOllama → LLM Response
```

## Modelli Disponibili

| Modello | Velocità | Capacità | Raccomandato per |
|---------|----------|----------|------------------|
| `gemini-2.5-flash` | ⚡⚡⚡ | Alta | Produzione (raccomandato) |
| `gemini-2.0-flash-exp` | ⚡⚡⚡ | Alta | Test |
| `gemini-1.5-pro` | ⚡⚡ | Molto Alta | Analisi complesse |
| `gemini-1.5-flash` | ⚡⚡⚡ | Media | Prototipazione rapida |

## Parametri di Configurazione

### Temperature
- **0.0-0.3**: Risposte molto deterministiche, ideale per analisi di sicurezza
- **0.4-0.7**: Bilanciato (valore predefinito)
- **0.8-1.0**: Più creatività, utile per generazione di suggerimenti

### Altri parametri disponibili
```python
config=types.GenerateContentConfig(
    temperature=0.7,
    max_output_tokens=8192,
    top_p=0.95,
    top_k=40,
)
```

## Switching tra Ollama e Gemini

### Per usare Gemini (Cloud)
```env
LLM_PROVIDER=gemini
```

### Per usare Ollama (Locale)
```env
LLM_PROVIDER=ollama
```

**Riavvia il server dopo aver cambiato il provider.**

## Troubleshooting

### Errore: "GOOGLE_API_KEY must be set"
- Verifica che il file `.env` esista e contenga `GOOGLE_API_KEY`
- Verifica che la chiave sia valida

### Errore: "Invalid API key"
- Rigenera la chiave su [Google AI Studio](https://aistudio.google.com/app/apikey)
- Verifica di aver copiato l'intera chiave

### Errore: "Model not found"
- Verifica che il nome del modello sia corretto in `.env`
- Usa uno dei modelli disponibili (es. `gemini-2.5-flash`)

### Errore: "Rate limit exceeded"
- Google AI Studio ha limiti gratuiti (es. 15 richieste/minuto)
- Attendi qualche secondo e riprova
- Considera di passare a un piano a pagamento per limiti più alti

## Costi

### Google AI Studio (Free Tier)
- Richieste al minuto: ~15
- Richieste al giorno: ~1,500
- Ideale per: Sviluppo e test

### Google Cloud (Pay-as-you-go)
- Gemini 2.5 Flash: ~$0.00125 per 1K caratteri di input
- Consulta i prezzi aggiornati su: https://cloud.google.com/vertex-ai/pricing

## Best Practices

1. **Non committare la API key**: Il file `.env` è nel `.gitignore`
2. **Usa temperature basse per analisi**: 0.3 è ottimale per threat analysis
3. **Monitora l'uso**: Tieni traccia delle richieste giornaliere
4. **Fallback a Ollama**: Per sviluppo offline, usa Ollama come backup

## Link Utili

- [Google AI Studio](https://aistudio.google.com/)
- [Documentazione google-genai](https://googleapis.github.io/python-genai/)
- [Modelli Gemini disponibili](https://ai.google.dev/models/gemini)
- [Prezzi Gemini](https://cloud.google.com/vertex-ai/pricing)

## Support

Per problemi o domande:
1. Controlla la sezione Troubleshooting sopra
2. Verifica i log del server
3. Esegui `python test_gemini_integration.py` per diagnosticare
