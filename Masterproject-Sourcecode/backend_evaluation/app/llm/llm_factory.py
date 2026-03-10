"""
LLM Factory Module

This module provides factory functions to create LLM instances
for both Ollama and Gemini providers.
"""

from langchain_ollama import ChatOllama
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from google import genai
from google.genai import types
from typing import Any, List, Optional
from app.config import (
    GENERATOR_LLM_PROVIDER,
    GENERATOR_OLLAMA_MODEL,
    GENERATOR_OLLAMA_BASE_URL,
    GENERATOR_GEMINI_MODEL,
    GENERATOR_GOOGLE_API_KEY,
    GENERATOR_LLM_TEMPERATURE,
    GENERATOR_MAX_OUTPUT_TOKENS,
    VALIDATOR_LLM_PROVIDER,
    VALIDATOR_OLLAMA_MODEL,
    VALIDATOR_OLLAMA_BASE_URL,
    VALIDATOR_GEMINI_MODEL,
    VALIDATOR_GOOGLE_API_KEY,
    VALIDATOR_LLM_TEMPERATURE,
    VALIDATOR_MAX_OUTPUT_TOKENS,
    OLLAMA_KEEP_ALIVE,
)


class GeminiLLM(LLM):
    """Custom LLM wrapper for Google Generative AI (Gemini) using google-genai library."""
    
    model_name: str
    temperature: float = 0.7
    max_output_tokens: int = 65536
    
    _client: Any = None
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(**kwargs)
        # Initialize the Gemini client with API key
        self._client = genai.Client(api_key=api_key)
    
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


def create_generator_llm():
    """
    Create the generator LLM instance based on configuration.
    
    Returns:
        LLM instance (ChatOllama or GeminiLLM)
    
    Raises:
        ValueError: If configuration is invalid
    """
    if GENERATOR_LLM_PROVIDER == "gemini":
        if not GENERATOR_GOOGLE_API_KEY:
            raise ValueError("GENERATOR_GOOGLE_API_KEY must be set in .env file when using Gemini for generator")
        
        print(f"Creating Generator LLM: Gemini model {GENERATOR_GEMINI_MODEL}")
        return GeminiLLM(
            api_key=GENERATOR_GOOGLE_API_KEY,
            model_name=GENERATOR_GEMINI_MODEL,
            temperature=GENERATOR_LLM_TEMPERATURE,
            max_output_tokens=GENERATOR_MAX_OUTPUT_TOKENS,
        )
    
    elif GENERATOR_LLM_PROVIDER == "ollama":
        print(
            f"Creating Generator LLM: Ollama model {GENERATOR_OLLAMA_MODEL} "
            f"at {GENERATOR_OLLAMA_BASE_URL} (keep_alive={OLLAMA_KEEP_ALIVE})"
        )
        # keep_alive controls how long the Ollama server retains the model in memory
        # after a request. Set OLLAMA_KEEP_ALIVE=0 in .env to force immediate unload
        # between calls, guaranteeing no KV-cache reuse across evaluation sweep runs.
        return ChatOllama(
            model=GENERATOR_OLLAMA_MODEL,
            base_url=GENERATOR_OLLAMA_BASE_URL,
            temperature=GENERATOR_LLM_TEMPERATURE,
            keep_alive=OLLAMA_KEEP_ALIVE,
        )
    
    else:
        raise ValueError(f"Unsupported GENERATOR_LLM_PROVIDER: {GENERATOR_LLM_PROVIDER}. Must be 'ollama' or 'gemini'")


def create_validator_llm():
    """
    Create the validator LLM instance based on configuration.
    
    Returns:
        LLM instance (ChatOllama or GeminiLLM)
    
    Raises:
        ValueError: If configuration is invalid
    """
    if VALIDATOR_LLM_PROVIDER == "gemini":
        if not VALIDATOR_GOOGLE_API_KEY:
            raise ValueError("VALIDATOR_GOOGLE_API_KEY must be set in .env file when using Gemini for validator")
        
        print(f"Creating Validator LLM: Gemini model {VALIDATOR_GEMINI_MODEL}")
        return GeminiLLM(
            api_key=VALIDATOR_GOOGLE_API_KEY,
            model_name=VALIDATOR_GEMINI_MODEL,
            temperature=VALIDATOR_LLM_TEMPERATURE,
            max_output_tokens=VALIDATOR_MAX_OUTPUT_TOKENS,
        )
    
    elif VALIDATOR_LLM_PROVIDER == "ollama":
        print(
            f"Creating Validator LLM: Ollama model {VALIDATOR_OLLAMA_MODEL} "
            f"at {VALIDATOR_OLLAMA_BASE_URL} (keep_alive={OLLAMA_KEEP_ALIVE})"
        )
        # Same keep_alive policy as the generator — see comment above.
        return ChatOllama(
            model=VALIDATOR_OLLAMA_MODEL,
            base_url=VALIDATOR_OLLAMA_BASE_URL,
            temperature=VALIDATOR_LLM_TEMPERATURE,
            keep_alive=OLLAMA_KEEP_ALIVE,
        )
    
    else:
        raise ValueError(f"Unsupported VALIDATOR_LLM_PROVIDER: {VALIDATOR_LLM_PROVIDER}. Must be 'ollama' or 'gemini'")


def invoke_llm(llm_instance, prompt: str) -> str:
    """
    Invoke an LLM with a prompt and return the response.
    
    Args:
        llm_instance: The LLM instance (ChatOllama or GeminiLLM)
        prompt: The prompt to send to the LLM
        
    Returns:
        The LLM response as a string
    """
    try:
        # For ChatOllama (which uses invoke with messages)
        if isinstance(llm_instance, ChatOllama):
            response = llm_instance.invoke(prompt)
            # ChatOllama returns an AIMessage object
            return response.content if hasattr(response, 'content') else str(response)
        
        # For GeminiLLM (which has direct _call method)
        elif isinstance(llm_instance, GeminiLLM):
            return llm_instance._call(prompt)
        
        # Fallback for other LLM types
        else:
            response = llm_instance.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
            
    except Exception as e:
        raise RuntimeError(f"Error invoking LLM: {str(e)}")
