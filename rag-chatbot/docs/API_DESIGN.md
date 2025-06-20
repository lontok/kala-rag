# API Design Document

## Core Modules API

### 1. Document Processor API

```python
class BaseDocumentProcessor:
    def extract_text(file_path: str) -> Tuple[str, Dict[str, Any]]
    def chunk_text(text: str, metadata: Dict) -> List[DocumentChunk]
    def process(file_path: str) -> ProcessedDocument

class DocumentProcessorFactory:
    def get_processor(file_path: str) -> BaseDocumentProcessor
    def process_document(file_path: str) -> ProcessedDocument
```

### 2. Embedding Generator API

```python
class EmbeddingGenerator:
    def generate_embeddings(texts: Union[str, List[str]]) -> List[List[float]]
    def generate_query_embedding(query: str) -> List[float]
    def compute_similarity(embedding1: List[float], embedding2: List[float]) -> float
    def batch_generate_embeddings(texts: List[str], batch_size: int) -> List[List[float]]
```

### 3. Vector Store API

```python
class VectorStore:
    def add_document(processed_doc: ProcessedDocument) -> Tuple[bool, str]
    def search(query: str, n_results: int, filter_dict: Dict) -> List[Dict[str, Any]]
    def document_exists(file_hash: str) -> bool
    def delete_document(file_hash: str) -> Tuple[bool, str]
    def get_collection_stats() -> Dict[str, Any]
    def reset_collection() -> Tuple[bool, str]
```

### 4. Retriever API (To Be Implemented)

```python
class Retriever:
    def retrieve(query: str, top_k: int) -> List[RetrievalResult]
    def retrieve_with_filter(query: str, filters: Dict, top_k: int) -> List[RetrievalResult]
    def rerank(results: List[RetrievalResult]) -> List[RetrievalResult]
    def get_context(results: List[RetrievalResult]) -> str
```

### 5. RAG Chain API (To Be Implemented)

```python
class RAGChain:
    def query(question: str, chat_history: List[Message]) -> Response
    def stream_query(question: str, chat_history: List[Message]) -> Iterator[str]
    def format_response(answer: str, sources: List[Source]) -> FormattedResponse
```

## Data Models

### Document Processing

```python
@dataclass
class DocumentChunk:
    text: str
    metadata: Dict[str, Any]
    chunk_id: str

@dataclass
class ProcessedDocument:
    file_path: str
    file_hash: str
    chunks: List[DocumentChunk]
    metadata: Dict[str, Any]
    total_chunks: int
    total_tokens: int
```

### Retrieval

```python
@dataclass
class RetrievalResult:
    chunk_id: str
    text: str
    score: float
    metadata: Dict[str, Any]

@dataclass
class Source:
    file_name: str
    page_number: Optional[int]
    chunk_index: int
    relevance_score: float
```

### Chat

```python
@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    sources: Optional[List[Source]]

@dataclass
class Response:
    answer: str
    sources: List[Source]
    confidence: float
    processing_time: float
```

## REST API Endpoints (Future)

### Document Management
- `POST /api/documents/upload` - Upload and process document
- `GET /api/documents` - List all documents
- `GET /api/documents/{doc_id}` - Get document details
- `DELETE /api/documents/{doc_id}` - Delete document

### Search & Query
- `POST /api/search` - Search documents
- `POST /api/query` - RAG query
- `POST /api/query/stream` - Streaming RAG query

### System
- `GET /api/health` - Health check
- `GET /api/stats` - System statistics
- `POST /api/reset` - Reset vector store

## Configuration API

```python
class Settings:
    # Ollama
    ollama_host: str
    ollama_model: str
    embedding_model: str
    
    # ChromaDB
    chroma_persist_directory: str
    chroma_collection_name: str
    
    # Processing
    chunk_size: int
    chunk_overlap: int
    max_chunks_per_doc: int
    
    # Retrieval
    top_k_results: int
    similarity_threshold: float
```

## Error Handling

```python
class RAGException(Exception):
    """Base exception for RAG system"""

class DocumentProcessingError(RAGException):
    """Raised when document processing fails"""

class EmbeddingError(RAGException):
    """Raised when embedding generation fails"""

class VectorStoreError(RAGException):
    """Raised when vector store operations fail"""

class RetrievalError(RAGException):
    """Raised when retrieval fails"""
```

## Event System (Future)

```python
class EventType(Enum):
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_PROCESSED = "document_processed"
    QUERY_RECEIVED = "query_received"
    RESPONSE_GENERATED = "response_generated"

class Event:
    type: EventType
    timestamp: datetime
    data: Dict[str, Any]
```