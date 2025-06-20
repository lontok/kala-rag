#!/usr/bin/env python3
"""Test script to verify ChromaDB setup."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.vector_store import VectorStore
from src.document_processor import DocumentProcessorFactory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_chromadb_setup():
    """Test ChromaDB and vector storage functionality."""
    print("Testing ChromaDB setup...")
    
    # Initialize vector store
    try:
        vector_store = VectorStore()
        print("✅ Successfully initialized ChromaDB")
    except Exception as e:
        print(f"❌ Failed to initialize ChromaDB: {e}")
        return False
    
    # Get collection stats
    try:
        stats = vector_store.get_collection_stats()
        print(f"\n📊 Collection Statistics:")
        print(f"   Collection: {stats['collection_name']}")
        print(f"   Total chunks: {stats['total_chunks']}")
        print(f"   Unique documents: {stats['unique_documents']}")
    except Exception as e:
        print(f"❌ Failed to get collection stats: {e}")
    
    # Test with sample document
    if os.path.exists("test_document.txt"):
        print("\n📄 Testing document processing and storage...")
        try:
            # Process document
            processed_doc = DocumentProcessorFactory.process_document("test_document.txt")
            print(f"   Processed {processed_doc.total_chunks} chunks")
            
            # Add to vector store
            success, message = vector_store.add_document(processed_doc)
            if success:
                print(f"✅ {message}")
            else:
                print(f"⚠️  {message}")
            
            # Test search
            print("\n🔍 Testing search functionality...")
            results = vector_store.search("What is RAG?", n_results=3)
            print(f"   Found {len(results)} results")
            
            if results:
                print("\n   Top result:")
                print(f"   Text: {results[0]['text'][:100]}...")
                print(f"   Similarity: {results[0].get('similarity', 'N/A')}")
                
        except Exception as e:
            print(f"❌ Error during document testing: {e}")
    
    print("\n✅ ChromaDB test completed!")
    return True


if __name__ == "__main__":
    test_chromadb_setup()