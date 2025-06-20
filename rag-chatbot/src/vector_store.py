import logging
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import hashlib
from datetime import datetime

from config.settings import settings
from src.embeddings import EmbeddingGenerator
from src.document_processor import ProcessedDocument, DocumentChunk

logger = logging.getLogger(__name__)


class VectorStore:
    """Manage vector storage using ChromaDB."""
    
    def __init__(self):
        """Initialize ChromaDB client and collection."""
        # Initialize ChromaDB with persistent storage
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding generator
        self.embedding_generator = EmbeddingGenerator(use_ollama=True)
        
        # Get or create collection
        self.collection_name = settings.chroma_collection_name
        self._initialize_collection()
        
        logger.info(f"Initialized ChromaDB with collection: {self.collection_name}")
    
    def _initialize_collection(self):
        """Initialize or get the ChromaDB collection."""
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Using existing collection: {self.collection_name}")
        except Exception:
            # Create new collection if it doesn't exist
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "RAG document embeddings"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
    
    def add_document(self, processed_doc: ProcessedDocument) -> Tuple[bool, str]:
        """
        Add a processed document to the vector store.
        
        Args:
            processed_doc: ProcessedDocument object containing chunks and metadata
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if document already exists
            if self.document_exists(processed_doc.file_hash):
                return False, "Document already exists in vector store"
            
            # Extract texts from chunks
            texts = [chunk.text for chunk in processed_doc.chunks]
            if not texts:
                return False, "No text chunks to process"
            
            # Generate embeddings in batches
            logger.info(f"Generating embeddings for {len(texts)} chunks...")
            embeddings = self.embedding_generator.batch_generate_embeddings(texts)
            
            # Prepare data for ChromaDB
            ids = [chunk.chunk_id for chunk in processed_doc.chunks]
            metadatas = []
            
            for chunk in processed_doc.chunks:
                # Create metadata for each chunk
                metadata = {
                    "file_hash": processed_doc.file_hash,
                    "file_path": processed_doc.file_path,
                    "file_name": chunk.metadata.get("file_name", ""),
                    "chunk_index": chunk.metadata.get("chunk_index", 0),
                    "total_chunks": chunk.metadata.get("total_chunks", 1),
                    "chunk_token_count": chunk.metadata.get("chunk_token_count", 0),
                    "file_type": chunk.metadata.get("file_type", "unknown"),
                    "indexed_at": datetime.now().isoformat()
                }
                
                # Add additional metadata if available
                if "page_number" in chunk.metadata:
                    metadata["page_number"] = chunk.metadata["page_number"]
                
                metadatas.append(metadata)
            
            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            
            # Store document metadata
            self._store_document_metadata(processed_doc)
            
            logger.info(f"Successfully added document: {processed_doc.file_path}")
            return True, f"Added {len(texts)} chunks to vector store"
            
        except Exception as e:
            logger.error(f"Error adding document to vector store: {e}")
            return False, f"Error: {str(e)}"
    
    def search(self, query: str, n_results: int = None, 
               filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents using a query.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of search results with documents and metadata
        """
        if n_results is None:
            n_results = settings.top_k_results
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_query_embedding(query)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_dict
            )
            
            # Format results
            formatted_results = []
            if results and results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    }
                    
                    # Calculate similarity score (1 - distance for cosine)
                    if result['distance'] is not None:
                        result['similarity'] = 1 - result['distance']
                    
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} results for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def document_exists(self, file_hash: str) -> bool:
        """Check if a document already exists in the vector store."""
        try:
            results = self.collection.get(
                where={"file_hash": file_hash},
                limit=1
            )
            return len(results['ids']) > 0
        except Exception as e:
            logger.error(f"Error checking document existence: {e}")
            return False
    
    def delete_document(self, file_hash: str) -> Tuple[bool, str]:
        """
        Delete a document from the vector store.
        
        Args:
            file_hash: Hash of the document to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={"file_hash": file_hash}
            )
            
            if not results['ids']:
                return False, "Document not found in vector store"
            
            # Delete all chunks
            self.collection.delete(ids=results['ids'])
            
            logger.info(f"Deleted {len(results['ids'])} chunks for document: {file_hash}")
            return True, f"Deleted {len(results['ids'])} chunks"
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False, f"Error: {str(e)}"
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection."""
        try:
            # Get total count
            count = self.collection.count()
            
            # Get unique documents
            all_results = self.collection.get()
            unique_docs = set()
            
            if all_results['metadatas']:
                for metadata in all_results['metadatas']:
                    if metadata and 'file_hash' in metadata:
                        unique_docs.add(metadata['file_hash'])
            
            stats = {
                'total_chunks': count,
                'unique_documents': len(unique_docs),
                'collection_name': self.collection_name
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {
                'total_chunks': 0,
                'unique_documents': 0,
                'collection_name': self.collection_name,
                'error': str(e)
            }
    
    def _store_document_metadata(self, processed_doc: ProcessedDocument):
        """Store document-level metadata (could be extended to use a separate metadata store)."""
        # For now, metadata is stored with each chunk
        # In production, you might want a separate metadata collection
        pass
    
    def reset_collection(self) -> Tuple[bool, str]:
        """Reset the entire collection (delete all data)."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self._initialize_collection()
            logger.info("Collection reset successfully")
            return True, "Collection reset successfully"
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            return False, f"Error: {str(e)}"
    
    def get_similar_chunks(self, chunk_id: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Find chunks similar to a given chunk."""
        try:
            # Get the chunk
            result = self.collection.get(ids=[chunk_id], include=['embeddings', 'documents', 'metadatas'])
            
            if not result['ids']:
                return []
            
            # Use the chunk's embedding to find similar chunks
            embedding = result['embeddings'][0]
            
            # Search for similar chunks
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results + 1,  # +1 because it will include itself
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format and filter out the original chunk
            formatted_results = []
            if results and results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    if results['ids'][0][i] != chunk_id:  # Skip the original chunk
                        result = {
                            'id': results['ids'][0][i],
                            'text': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'similarity': 1 - results['distances'][0][i]
                        }
                        formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error finding similar chunks: {e}")
            return []