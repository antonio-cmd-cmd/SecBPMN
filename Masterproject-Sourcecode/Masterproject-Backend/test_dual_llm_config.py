"""
Test script for Dual-LLM configuration

This script verifies that the dual-LLM system is properly configured.
Run this from the backend directory:
    python test_dual_llm_config.py
"""

import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import (
    USE_DUAL_LLM,
    MAX_LLM_ITERATIONS,
    GENERATOR_LLM_PROVIDER,
    GENERATOR_OLLAMA_MODEL,
    GENERATOR_OLLAMA_BASE_URL,
    GENERATOR_GEMINI_MODEL,
    GENERATOR_GOOGLE_API_KEY,
    VALIDATOR_LLM_PROVIDER,
    VALIDATOR_OLLAMA_MODEL,
    VALIDATOR_OLLAMA_BASE_URL,
    VALIDATOR_GEMINI_MODEL,
    VALIDATOR_GOOGLE_API_KEY,
)

def test_configuration():
    """Test that the dual-LLM configuration is valid."""
    
    print("=" * 60)
    print("DUAL-LLM CONFIGURATION TEST")
    print("=" * 60)
    
    # Check if dual-LLM is enabled
    print(f"\n1. Dual-LLM Mode: {'ENABLED ✓' if USE_DUAL_LLM else 'DISABLED (using legacy single-LLM)'}")
    print(f"   Max Iterations: {MAX_LLM_ITERATIONS}")
    
    if not USE_DUAL_LLM:
        print("\n⚠️  Dual-LLM is disabled. Set USE_DUAL_LLM=true in .env to enable it.")
        return
    
    # Check Generator LLM configuration
    print(f"\n2. Generator LLM Configuration:")
    print(f"   Provider: {GENERATOR_LLM_PROVIDER.upper()}")
    
    if GENERATOR_LLM_PROVIDER == "ollama":
        print(f"   Ollama Model: {GENERATOR_OLLAMA_MODEL}")
        print(f"   Ollama URL: {GENERATOR_OLLAMA_BASE_URL}")
        
        if not GENERATOR_OLLAMA_MODEL:
            print("   ❌ ERROR: GENERATOR_OLLAMA_MODEL is not set!")
            return False
        
        # Test Ollama connection
        try:
            import requests
            response = requests.get(f"{GENERATOR_OLLAMA_BASE_URL}/api/version", timeout=2)
            if response.status_code == 200:
                print(f"   ✓ Ollama connection successful")
            else:
                print(f"   ⚠️  Ollama returned status code: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Could not connect to Ollama: {e}")
            
    elif GENERATOR_LLM_PROVIDER == "gemini":
        print(f"   Gemini Model: {GENERATOR_GEMINI_MODEL}")
        api_key_display = GENERATOR_GOOGLE_API_KEY[:10] + "..." if GENERATOR_GOOGLE_API_KEY else "NOT SET"
        print(f"   API Key: {api_key_display}")
        
        if not GENERATOR_GOOGLE_API_KEY:
            print("   ❌ ERROR: GENERATOR_GOOGLE_API_KEY is not set!")
            return False
        else:
            print("   ✓ API key is configured")
    else:
        print(f"   ❌ ERROR: Invalid provider '{GENERATOR_LLM_PROVIDER}'")
        return False
    
    # Check Validator LLM configuration
    print(f"\n3. Validator LLM Configuration:")
    print(f"   Provider: {VALIDATOR_LLM_PROVIDER.upper()}")
    
    if VALIDATOR_LLM_PROVIDER == "ollama":
        print(f"   Ollama Model: {VALIDATOR_OLLAMA_MODEL}")
        print(f"   Ollama URL: {VALIDATOR_OLLAMA_BASE_URL}")
        
        if not VALIDATOR_OLLAMA_MODEL:
            print("   ❌ ERROR: VALIDATOR_OLLAMA_MODEL is not set!")
            return False
        
        # Test Ollama connection
        try:
            import requests
            response = requests.get(f"{VALIDATOR_OLLAMA_BASE_URL}/api/version", timeout=2)
            if response.status_code == 200:
                print(f"   ✓ Ollama connection successful")
            else:
                print(f"   ⚠️  Ollama returned status code: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Could not connect to Ollama: {e}")
            
    elif VALIDATOR_LLM_PROVIDER == "gemini":
        print(f"   Gemini Model: {VALIDATOR_GEMINI_MODEL}")
        api_key_display = VALIDATOR_GOOGLE_API_KEY[:10] + "..." if VALIDATOR_GOOGLE_API_KEY else "NOT SET"
        print(f"   API Key: {api_key_display}")
        
        if not VALIDATOR_GOOGLE_API_KEY:
            print("   ❌ ERROR: VALIDATOR_GOOGLE_API_KEY is not set!")
            return False
        else:
            print("   ✓ API key is configured")
    else:
        print(f"   ❌ ERROR: Invalid provider '{VALIDATOR_LLM_PROVIDER}'")
        return False
    
    # Try to create LLM instances
    print(f"\n4. Testing LLM Instance Creation:")
    
    try:
        from app.llm.llm_factory import create_generator_llm
        generator = create_generator_llm()
        print("   ✓ Generator LLM instance created successfully")
    except Exception as e:
        print(f"   ❌ ERROR creating Generator LLM: {e}")
        return False
    
    try:
        from app.llm.llm_factory import create_validator_llm
        validator = create_validator_llm()
        print("   ✓ Validator LLM instance created successfully")
    except Exception as e:
        print(f"   ❌ ERROR creating Validator LLM: {e}")
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ CONFIGURATION TEST PASSED")
    print("=" * 60)
    print("\nYour dual-LLM system is properly configured!")
    print(f"\nConfiguration Summary:")
    print(f"  - Generator: {GENERATOR_LLM_PROVIDER}")
    print(f"  - Validator: {VALIDATOR_LLM_PROVIDER}")
    print(f"  - Max Iterations: {MAX_LLM_ITERATIONS}")
    print("\nYou can now start the backend server:")
    print("  python -m app.main")
    print("\n")
    
    return True


if __name__ == "__main__":
    try:
        success = test_configuration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
