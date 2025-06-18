"""Blog processing utilities."""
import hashlib
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from langchain_community.document_loaders.text import TextLoader
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain.embeddings import init_embeddings

from lets_talk.shared.config import (
    BASE_URL, DATA_DIR, INDEX_ONLY_PUBLISHED_POSTS, OLLAMA_BASE_URL,
    QDRANT_URL, VECTOR_STORAGE_PATH, EMBEDDING_MODEL, QDRANT_COLLECTION,
    BLOG_BASE_URL, CHUNK_SIZE, CHUNK_OVERLAP, METADATA_CSV_FILE,
    CHECKSUM_ALGORITHM, BATCH_SIZE, ENABLE_BATCH_PROCESSING,
    ENABLE_PERFORMANCE_MONITORING, ADAPTIVE_CHUNKING, MAX_BACKUP_FILES,
    BATCH_PAUSE_SECONDS, MAX_CONCURRENT_OPERATIONS
)

logger = logging.getLogger(__name__)


def calculate_content_checksum(content: str, algorithm: str = CHECKSUM_ALGORITHM) -> str:
    """Calculate checksum of document content."""
    try:
        if algorithm.lower() == "md5":
            return hashlib.md5(content.encode('utf-8')).hexdigest()
        elif algorithm.lower() == "sha256":
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        elif algorithm.lower() == "sha1":
            return hashlib.sha1(content.encode('utf-8')).hexdigest()
        else:
            logger.warning(f"Unknown checksum algorithm: {algorithm}. Using SHA256.")
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
    except Exception as e:
        logger.error(f"Error calculating checksum: {e}")
        return ""


def load_blog_posts(
    data_dir: str = DATA_DIR, 
    glob_pattern: str = "*.md"
) -> List[Document]:
    """Load blog posts from the specified directory."""
    logger.info(f"Loading blog posts from {data_dir} with pattern {glob_pattern}")
    
    try:
        loader = DirectoryLoader(
            data_dir,
            glob=glob_pattern,
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
            show_progress=True
        )
        docs = loader.load()
        logger.info(f"Loaded {len(docs)} documents from {data_dir}")
        return docs
    except Exception as e:
        logger.error(f"Error loading blog posts: {e}")
        return []


def update_document_metadata(
    docs: List[Document],
    data_dir_prefix: str = "",
    base_url: str = BASE_URL,
    blog_base_url: str = BLOG_BASE_URL,
    remove_suffix: str = "*.md"
) -> List[Document]:
    """Update document metadata with URLs and other information."""
    logger.info(f"Updating metadata for {len(docs)} documents")
    
    updated_docs = []
    for doc in docs:
        try:
            # Get the source path and clean it
            source_path = doc.metadata.get("source", "")
            if data_dir_prefix and source_path.startswith(data_dir_prefix):
                relative_path = source_path[len(data_dir_prefix):]
            else:
                relative_path = source_path
            
            # Remove file extension
            clean_path = relative_path
            if remove_suffix and remove_suffix != "*.md":
                # Remove specific suffix
                if clean_path.endswith(remove_suffix.replace("*", "")):
                    clean_path = clean_path[:-len(remove_suffix.replace("*", ""))]
            else:
                # Remove .md extension
                if clean_path.endswith(".md"):
                    clean_path = clean_path[:-3]
            
            # Create URLs
            blog_url = f"{blog_base_url.rstrip('/')}/{clean_path.lstrip('/')}"
            absolute_url = f"{base_url.rstrip('/')}/{clean_path.lstrip('/')}"
            
            # Update metadata
            doc.metadata.update({
                "url": blog_url,
                "absolute_url": absolute_url,
                "relative_path": clean_path,
                "source_file": source_path,
                "checksum": calculate_content_checksum(doc.page_content),
                "processed_timestamp": pd.Timestamp.now().isoformat()
            })
            
            updated_docs.append(doc)
            
        except Exception as e:
            logger.error(f"Error updating metadata for document {doc.metadata.get('source', 'unknown')}: {e}")
            updated_docs.append(doc)  # Add original doc even if metadata update fails
    
    logger.info(f"Successfully updated metadata for {len(updated_docs)} documents")
    return updated_docs


def chunk_documents(
    docs: List[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    adaptive: bool = ADAPTIVE_CHUNKING
) -> List[Document]:
    """Split documents into chunks for better retrieval."""
    logger.info(f"Chunking {len(docs)} documents with size={chunk_size}, overlap={chunk_overlap}")
    
    try:
        if adaptive:
            # Adaptive chunking based on document length
            chunked_docs = []
            for doc in docs:
                doc_length = len(doc.page_content)
                if doc_length <= chunk_size:
                    # Document is small enough, don't chunk
                    chunked_docs.append(doc)
                else:
                    # Use smaller chunks for very long documents
                    adaptive_chunk_size = min(chunk_size, max(500, doc_length // 10))
                    adaptive_overlap = min(chunk_overlap, adaptive_chunk_size // 4)
                    
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=adaptive_chunk_size,
                        chunk_overlap=adaptive_overlap,
                        length_function=len,
                        is_separator_regex=False,
                    )
                    chunks = splitter.split_documents([doc])
                    chunked_docs.extend(chunks)
        else:
            # Standard chunking
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                is_separator_regex=False,
            )
            chunked_docs = text_splitter.split_documents(docs)
        
        logger.info(f"Created {len(chunked_docs)} chunks from {len(docs)} documents")
        return chunked_docs
        
    except Exception as e:
        logger.error(f"Error chunking documents: {e}")
        return docs  # Return original docs if chunking fails


def create_vector_store(
    docs: List[Document],
    collection_name: str = QDRANT_COLLECTION,
    embedding_model: str = EMBEDDING_MODEL,
    qdrant_url: str = QDRANT_URL,
    force_recreate: bool = False
) -> Optional[QdrantVectorStore]:
    """Create or update vector store with documents."""
    logger.info(f"Creating vector store with {len(docs)} documents")
    
    try:
        # Initialize embeddings
        embeddings = init_embeddings(embedding_model)
        
        if embedding_model.startswith("ollama:"):
            base_url = OLLAMA_BASE_URL
            logger.info(f"Using Ollama embeddings with base_url: {base_url}")
            embeddings = init_embeddings(embedding_model, base_url=base_url)
        
        # Create vector store
        if force_recreate:
            logger.info("Force recreating vector store")
            vector_store = QdrantVectorStore.from_documents(
                docs,
                embeddings,
                url=qdrant_url,
                prefer_grpc=True,
                collection_name=collection_name,
                force_recreate=True
            )
        else:
            try:
                # Try to load existing vector store
                vector_store = QdrantVectorStore.from_existing_collection(
                    embedding=embeddings,
                    collection_name=collection_name,
                    url=qdrant_url,
                    prefer_grpc=True,
                )
                logger.info("Using existing vector store")
            except Exception:
                # Create new vector store if existing one doesn't exist
                logger.info("Creating new vector store")
                vector_store = QdrantVectorStore.from_documents(
                    docs,
                    embeddings,
                    url=qdrant_url,
                    prefer_grpc=True,
                    collection_name=collection_name
                )
        
        logger.info("Vector store created successfully")
        return vector_store
        
    except Exception as e:
        logger.error(f"Error creating vector store: {e}")
        return None


def save_document_stats(
    docs: List[Document],
    output_dir: str,
    filename: Optional[str] = None
) -> str:
    """Save document statistics to a JSON file."""
    import json
    from datetime import datetime
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"blog_stats_{timestamp}.json"
    
    stats = {
        "total_documents": len(docs),
        "timestamp": datetime.now().isoformat(),
        "documents": []
    }
    
    for doc in docs:
        doc_stats = {
            "source": doc.metadata.get("source", "unknown"),
            "url": doc.metadata.get("url", ""),
            "content_length": len(doc.page_content),
            "checksum": doc.metadata.get("checksum", ""),
            "chunk_count": 1  # Will be updated if document is chunked
        }
        stats["documents"].append(doc_stats)
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Save stats
    output_path = Path(output_dir) / filename
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Document statistics saved to: {output_path}")
    return str(output_path)
