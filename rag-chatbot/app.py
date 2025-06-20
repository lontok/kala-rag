import streamlit as st
import os
from pathlib import Path
import logging
from datetime import datetime

from src.utils import save_uploaded_file, get_uploaded_files, delete_file, format_file_size, SUPPORTED_EXTENSIONS
from src.document_processor import DocumentProcessorFactory
from src.vector_store import VectorStore
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="RAG Chatbot - Document Upload",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = {}
if 'upload_status' not in st.session_state:
    st.session_state.upload_status = None
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = VectorStore()


def process_uploaded_file(file_path: str, add_to_vector_store: bool = True):
    """Process an uploaded file and store results in session state."""
    try:
        with st.spinner(f"Processing {os.path.basename(file_path)}..."):
            processed_doc = DocumentProcessorFactory.process_document(file_path)
            
            # Add to vector store if requested
            vector_status = None
            if add_to_vector_store:
                with st.spinner("Adding to vector store..."):
                    success, message = st.session_state.vector_store.add_document(processed_doc)
                    vector_status = {'success': success, 'message': message}
            
            st.session_state.processed_files[file_path] = {
                'processed_at': datetime.now(),
                'total_chunks': processed_doc.total_chunks,
                'total_tokens': processed_doc.total_tokens,
                'metadata': processed_doc.metadata,
                'file_hash': processed_doc.file_hash,
                'vector_status': vector_status
            }
            
            if vector_status and not vector_status['success']:
                return True, f"Processed {processed_doc.total_chunks} chunks. Vector store: {vector_status['message']}"
            else:
                return True, f"Successfully processed: {processed_doc.total_chunks} chunks, {processed_doc.total_tokens} tokens"
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return False, f"Error processing file: {str(e)}"


def main():
    st.title("📚 RAG Chatbot - Document Management")
    st.markdown("Upload and manage documents for the RAG system")
    
    # Sidebar
    with st.sidebar:
        st.header("📊 System Status")
        
        # Display settings
        st.subheader("Configuration")
        st.text(f"Chunk Size: {settings.chunk_size} tokens")
        st.text(f"Chunk Overlap: {settings.chunk_overlap} tokens")
        st.text(f"Upload Directory: {settings.upload_directory}")
        
        # File statistics
        uploaded_files = get_uploaded_files()
        st.subheader("Document Statistics")
        st.metric("Total Documents", len(uploaded_files))
        if uploaded_files:
            total_size = sum(f['size'] for f in uploaded_files)
            st.metric("Total Size", format_file_size(total_size))
        
        # Vector store statistics
        st.subheader("Vector Store")
        vector_stats = st.session_state.vector_store.get_collection_stats()
        st.metric("Indexed Chunks", vector_stats['total_chunks'])
        st.metric("Unique Documents", vector_stats['unique_documents'])
    
    # Main content area
    col1, col2 = st.columns([2, 3])
    
    # Upload section
    with col1:
        st.header("=� Upload Documents")
        
        # Display supported formats
        st.info(f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS.keys())}")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=list(SUPPORTED_EXTENSIONS.keys()),
            help="Select a document to upload and process"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.text(f"File: {uploaded_file.name}")
            st.text(f"Size: {format_file_size(uploaded_file.size)}")
            
            # Upload button
            if st.button("Upload and Process", type="primary"):
                # Save file
                success, file_path, error = save_uploaded_file(
                    uploaded_file.getvalue(),
                    uploaded_file.name
                )
                
                if success:
                    st.success(f"File uploaded: {os.path.basename(file_path)}")
                    
                    # Process file
                    proc_success, proc_message = process_uploaded_file(file_path)
                    if proc_success:
                        st.success(proc_message)
                        st.session_state.upload_status = ('success', proc_message)
                    else:
                        st.error(proc_message)
                        st.session_state.upload_status = ('error', proc_message)
                    
                    # Refresh the page to show new file
                    st.rerun()
                else:
                    st.error(f"Upload failed: {error}")
                    st.session_state.upload_status = ('error', error)
    
    # Document list section
    with col2:
        st.header("=� Uploaded Documents")
        
        uploaded_files = get_uploaded_files()
        
        if uploaded_files:
            # Create a table of files
            for file_info in uploaded_files:
                with st.container():
                    col_name, col_size, col_status, col_action = st.columns([3, 1, 2, 1])
                    
                    with col_name:
                        st.text(file_info['name'])
                    
                    with col_size:
                        st.text(f"{file_info['size_mb']} MB")
                    
                    with col_status:
                        if file_info['path'] in st.session_state.processed_files:
                            proc_info = st.session_state.processed_files[file_info['path']]
                            st.success(f" {proc_info['total_chunks']} chunks")
                        else:
                            if st.button("Process", key=f"proc_{file_info['path']}"):
                                proc_success, proc_message = process_uploaded_file(file_info['path'])
                                if proc_success:
                                    st.success(proc_message)
                                else:
                                    st.error(proc_message)
                                st.rerun()
                    
                    with col_action:
                        if st.button("=�", key=f"del_{file_info['path']}", help="Delete file"):
                            success, error = delete_file(file_info['path'])
                            if success:
                                st.success("File deleted")
                                if file_info['path'] in st.session_state.processed_files:
                                    del st.session_state.processed_files[file_info['path']]
                                st.rerun()
                            else:
                                st.error(error)
                    
                    # Show metadata if processed
                    if file_info['path'] in st.session_state.processed_files:
                        with st.expander("View Details"):
                            proc_info = st.session_state.processed_files[file_info['path']]
                            st.json(proc_info['metadata'])
            
        else:
            st.info("No documents uploaded yet. Upload a document to get started!")
    
    # Status messages
    if st.session_state.upload_status:
        status_type, message = st.session_state.upload_status
        if status_type == 'success':
            st.success(message)
        else:
            st.error(message)
        # Clear status after displaying
        st.session_state.upload_status = None


if __name__ == "__main__":
    main()