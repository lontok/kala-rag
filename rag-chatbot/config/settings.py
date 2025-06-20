import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Ollama Configuration
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    ollama_model: str = Field(default="llama2:7b", env="OLLAMA_MODEL")
    embedding_model: str = Field(default="nomic-embed-text", env="EMBEDDING_MODEL")
    
    # ChromaDB Configuration
    chroma_persist_directory: str = Field(default="./data/chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    chroma_collection_name: str = Field(default="rag_documents", env="CHROMA_COLLECTION_NAME")
    
    # Document Processing
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    max_chunks_per_doc: int = Field(default=1000, env="MAX_CHUNKS_PER_DOC")
    
    # Retrieval Configuration
    top_k_results: int = Field(default=5, env="TOP_K_RESULTS")
    similarity_threshold: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    
    # Streamlit Configuration
    streamlit_port: int = Field(default=8501, env="STREAMLIT_PORT")
    streamlit_server_headless: bool = Field(default=True, env="STREAMLIT_SERVER_HEADLESS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default="./logs/app.log", env="LOG_FILE")
    
    # Paths
    upload_directory: str = Field(default="./data/documents", env="UPLOAD_DIRECTORY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        Path(self.chroma_persist_directory).mkdir(parents=True, exist_ok=True)
        Path(self.upload_directory).mkdir(parents=True, exist_ok=True)
        if self.log_file:
            Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()