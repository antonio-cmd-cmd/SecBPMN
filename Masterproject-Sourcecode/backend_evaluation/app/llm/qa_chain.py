from langchain.chains import RetrievalQA
from langchain_ollama import ChatOllama
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from google import genai
from google.genai import types
from typing import Any, List, Optional
from app.config import (
    LLM_PROVIDER,
    OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    GEMINI_MODEL,
    GOOGLE_API_KEY,
    LLM_TEMPERATURE,
    MAX_OUTPUT_TOKENS
)


class GeminiLLM(LLM):
    """Custom LLM wrapper for Google Generative AI (Gemini) using google-genai library."""
    
    model_name: str
    temperature: float = 0.7
    max_output_tokens: int = 65536
    
    _client: Any = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize the Gemini client with API key
        self._client = genai.Client(api_key=GOOGLE_API_KEY)
    
    @property
    def _llm_type(self) -> str:
        return "gemini"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        try:
            # Use the new google-genai API
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_output_tokens,
                    top_p=0.95,
                    top_k=40,
                )
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")


def get_llm():
    """
    Get the appropriate LLM based on the configured provider.
    
    Returns:
        LLM instance (ChatOllama or GeminiLLM)
    """
    if LLM_PROVIDER == "gemini":
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY must be set in .env file when using Gemini")
        
        print(f"Using Gemini model: {GEMINI_MODEL}")
        return GeminiLLM(
            model_name=GEMINI_MODEL,
            temperature=LLM_TEMPERATURE,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )
    
    elif LLM_PROVIDER == "ollama":
        print(f"Using Ollama model: {OLLAMA_MODEL} at {OLLAMA_BASE_URL}")
        return ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=LLM_TEMPERATURE,
        )
    
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}. Must be 'ollama' or 'gemini'")


def build_qa_chain(vectorstore):
    retriever = vectorstore.as_retriever(search_type="similarity", k=5)
    
    llm = get_llm()

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True
    )


def build_mitigation_qa_chain(mitigation_vectorstore):
    """
    Build a QA chain specifically for retrieving mitigation strategies.
    
    Args:
        mitigation_vectorstore: Vectorstore containing mitigation best practices
        
    Returns:
        RetrievalQA chain for mitigation queries
    """
    retriever = mitigation_vectorstore.as_retriever(search_type="similarity", k=10)
    
    llm = get_llm()

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True
    )

