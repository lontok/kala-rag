# RAG Chatbot

A Retrieval-Augmented Generation chatbot using Streamlit, Ollama, ChromaDB, and LangChain.

## Quick Start

### 1. Set up Python environment
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set up Ollama
```bash
# Make sure Ollama is installed and running
# If not installed, see: https://ollama.ai

# Run the setup script to download required models
./setup_ollama.sh
```

### 3. Run the application
```bash
streamlit run app.py
```

The app will open in your browser at http://localhost:8501

## Testing Document Upload

1. Navigate to the web interface
2. Click "Browse files" or drag and drop a document
3. Supported formats: PDF, TXT, MD, DOCX, CSV
4. Click "Upload and Process" to process the document
5. View the processed chunks and metadata

## Project Structure

- `app.py` - Main Streamlit application
- `src/` - Core modules
  - `document_processor.py` - Document processing and chunking
  - `utils.py` - File handling utilities
  - `ollama_client.py` - Ollama API wrapper
- `config/` - Configuration files
- `data/` - Document storage
- `tests/` - Test files