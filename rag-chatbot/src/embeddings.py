import logging
from typing import List, Union, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from src.ollama_client import OllamaClient
from config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings using either Ollama or Sentence Transformers."""
    
    def __init__(self, use_ollama: bool = True):
        """
        Initialize the embedding generator.
        
        Args:
            use_ollama: If True, use Ollama for embeddings. Otherwise, use Sentence Transformers.
        """
        self.use_ollama = use_ollama
        
        if use_ollama:
            self.client = OllamaClient()
            self.model_name = settings.embedding_model
            logger.info(f"Using Ollama embedding model: {self.model_name}")
        else:
            # Use Sentence Transformers as fallback
            self.model_name = "all-MiniLM-L6-v2"
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Using Sentence Transformers model: {self.model_name}")
    
    def generate_embeddings(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for one or more texts.
        
        Args:
            texts: Single text string or list of text strings
            
        Returns:
            List of embedding vectors
        """
        # Convert single text to list
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return []
        
        try:
            if self.use_ollama:
                # Use Ollama for embeddings
                embeddings = self.client.generate_embeddings(texts)
                logger.info(f"Generated {len(embeddings)} embeddings using Ollama")
                return embeddings
            else:
                # Use Sentence Transformers
                embeddings = self.model.encode(texts, convert_to_numpy=True)
                # Convert numpy arrays to lists for consistency
                embeddings_list = [emb.tolist() for emb in embeddings]
                logger.info(f"Generated {len(embeddings_list)} embeddings using Sentence Transformers")
                return embeddings_list
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            # If Ollama fails, fallback to Sentence Transformers
            if self.use_ollama:
                logger.warning("Falling back to Sentence Transformers")
                self.use_ollama = False
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                return self.generate_embeddings(texts)
            else:
                raise
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a single query.
        
        Args:
            query: Query text
            
        Returns:
            Embedding vector
        """
        embeddings = self.generate_embeddings(query)
        return embeddings[0] if embeddings else []
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Compute cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def batch_generate_embeddings(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings in batches for better performance.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once
            
        Returns:
            List of embedding vectors
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.generate_embeddings(batch)
            all_embeddings.extend(embeddings)
            
            # Log progress for large batches
            if len(texts) > batch_size:
                progress = min(i + batch_size, len(texts))
                logger.info(f"Embedding progress: {progress}/{len(texts)}")
        
        return all_embeddings