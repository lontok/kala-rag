import ollama
from typing import List, Dict, Any, Optional
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self):
        self.host = settings.ollama_host
        self.model = settings.ollama_model
        self.embedding_model = settings.embedding_model
        self.client = ollama.Client(host=self.host)
        
    def check_connection(self) -> bool:
        """Check if Ollama service is accessible."""
        try:
            self.client.list()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    def check_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available."""
        try:
            models = self.client.list()
            return any(model.get('name', '').startswith(model_name) for model in models.get('models', []))
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a model if not already available."""
        try:
            if not self.check_model_available(model_name):
                logger.info(f"Pulling model: {model_name}")
                self.client.pull(model_name)
                logger.info(f"Successfully pulled model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    def generate(self, prompt: str, context: Optional[str] = None, 
                 temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text using the LLM."""
        try:
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer:"
            
            response = self.client.generate(
                model=self.model,
                prompt=full_prompt,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            )
            
            return response['response']
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        embeddings = []
        try:
            for text in texts:
                response = self.client.embeddings(
                    model=self.embedding_model,
                    prompt=text
                )
                embeddings.append(response['embedding'])
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def stream_generate(self, prompt: str, context: Optional[str] = None,
                       temperature: float = 0.7, max_tokens: int = 1000):
        """Generate text using the LLM with streaming."""
        try:
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer:"
            
            stream = self.client.generate(
                model=self.model,
                prompt=full_prompt,
                stream=True,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            )
            
            for chunk in stream:
                yield chunk['response']
        except Exception as e:
            logger.error(f"Failed to generate streaming response: {e}")
            raise