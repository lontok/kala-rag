#!/usr/bin/env python3
"""Test script for document processing functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.document_processor import DocumentProcessorFactory
from src.utils import SUPPORTED_EXTENSIONS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_files():
    """Create test files for processing."""
    test_dir = "test_documents"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create test text file
    with open(f"{test_dir}/test.txt", "w") as f:
        f.write("""This is a test document for the RAG system.
It contains multiple paragraphs to test chunking.

The chunking algorithm should split this text into smaller pieces
while maintaining context and overlap between chunks.

This is the third paragraph. It contains important information
that should be preserved during the chunking process.""")
    
    # Create test markdown file
    with open(f"{test_dir}/test.md", "w") as f:
        f.write("""# Test Markdown Document

## Introduction
This is a test markdown document with various formatting.

## Main Content
- Bullet point 1
- Bullet point 2
- Bullet point 3

### Subsection
This subsection contains additional details that should be 
extracted and processed correctly.

## Conclusion
The document processor should handle markdown formatting appropriately.""")
    
    return test_dir


def test_document_processing():
    """Test document processing functionality."""
    print("Setting up test documents...")
    test_dir = create_test_files()
    
    print("\nTesting document processors:")
    print("-" * 50)
    
    for ext in ['.txt', '.md']:
        test_file = f"{test_dir}/test{ext}"
        if os.path.exists(test_file):
            print(f"\nProcessing {ext} file...")
            try:
                processed_doc = DocumentProcessorFactory.process_document(test_file)
                
                print(f"✅ Successfully processed {ext} file")
                print(f"   File: {processed_doc.file_path}")
                print(f"   Total chunks: {processed_doc.total_chunks}")
                print(f"   Total tokens: {processed_doc.total_tokens}")
                print(f"   Metadata: {processed_doc.metadata}")
                
                # Show first chunk
                if processed_doc.chunks:
                    first_chunk = processed_doc.chunks[0]
                    print(f"\n   First chunk preview:")
                    print(f"   Text: {first_chunk.text[:100]}...")
                    print(f"   Chunk metadata: {first_chunk.metadata}")
                    
            except Exception as e:
                print(f"❌ Failed to process {ext} file: {e}")
    
    # Cleanup
    print("\nCleaning up test files...")
    import shutil
    shutil.rmtree(test_dir)
    
    print("\n✅ Document processing tests completed!")


if __name__ == "__main__":
    test_document_processing()