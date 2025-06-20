#!/usr/bin/env python3
"""Test script to verify Ollama setup."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ollama_client import OllamaClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ollama_setup():
    """Test Ollama connection and model availability."""
    client = OllamaClient()
    
    # Test connection
    print("Testing Ollama connection...")
    if not client.check_connection():
        print("❌ Failed to connect to Ollama. Please ensure Ollama is running.")
        print("   Run: ollama serve")
        return False
    print("✅ Successfully connected to Ollama")
    
    # Check models
    print(f"\nChecking for {client.model}...")
    if not client.check_model_available(client.model):
        print(f"❌ Model {client.model} not found.")
        print(f"   Run: ollama pull {client.model}")
        return False
    print(f"✅ Model {client.model} is available")
    
    print(f"\nChecking for {client.embedding_model}...")
    if not client.check_model_available(client.embedding_model):
        print(f"❌ Model {client.embedding_model} not found.")
        print(f"   Run: ollama pull {client.embedding_model}")
        return False
    print(f"✅ Model {client.embedding_model} is available")
    
    # Test generation
    print("\nTesting text generation...")
    try:
        response = client.generate("Hello! Please respond with a brief greeting.", temperature=0.5)
        print(f"✅ Generation test successful: {response[:100]}...")
    except Exception as e:
        print(f"❌ Generation test failed: {e}")
        return False
    
    # Test embeddings
    print("\nTesting embedding generation...")
    try:
        embeddings = client.generate_embeddings(["Test text for embedding"])
        print(f"✅ Embedding test successful: Generated {len(embeddings[0])}-dimensional embedding")
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Ollama is properly configured.")
    return True


if __name__ == "__main__":
    test_ollama_setup()