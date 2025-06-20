#!/bin/bash

echo "Setting up Ollama for RAG Chatbot..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Ollama is not installed. Please install it first:"
    echo ""
    echo "For macOS:"
    echo "  brew install ollama"
    echo ""
    echo "For Linux:"
    echo "  curl -fsSL https://ollama.ai/install.sh | sh"
    echo ""
    echo "For Windows:"
    echo "  Download from https://ollama.ai/download"
    echo ""
    exit 1
fi

echo "Ollama is installed. Starting Ollama service..."

# Start Ollama service (if not already running)
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama service..."
    ollama serve &
    sleep 5
else
    echo "Ollama service is already running."
fi

echo "Pulling required models..."

# Pull Llama 2 7B model
echo "Pulling llama2:7b model (this may take a while)..."
ollama pull llama2:7b

# Pull embedding model
echo "Pulling nomic-embed-text model..."
ollama pull nomic-embed-text

echo "Verifying models..."
ollama list

echo "Setup complete! Models are ready to use."
echo ""
echo "To test the models:"
echo "  ollama run llama2:7b"
echo ""
echo "To check if Ollama is running:"
echo "  curl http://localhost:11434/api/tags"