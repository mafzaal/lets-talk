"""
Blog Data Utilities Module

This module contains utility functions for loading, processing, and storing blog posts
for the RAG system. It includes functions for loading blog posts from the data directory,
processing their metadata, and creating vector embeddings.
"""

import hashlib
import os
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

from lets_talk.config import (
    BASE_URL,
    DATA_DIR,
    INDEX_ONLY_PUBLISHED_POSTS,
    OLLAMA_BASE_URL,
    QDRANT_URL,
    VECTOR_STORAGE_PATH,
    EMBEDDING_MODEL,
    QDRANT_COLLECTION,
    BLOG_BASE_URL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    METADATA_CSV_FILE,
    CHECKSUM_ALGORITHM,
    BATCH_SIZE,
    ENABLE_BATCH_PROCESSING,
    ENABLE_PERFORMANCE_MONITORING,
    ADAPTIVE_CHUNKING,
    MAX_BACKUP_FILES,
    BATCH_PAUSE_SECONDS,
    MAX_CONCURRENT_OPERATIONS
)

# Checksum and metadata management functions

def calculate_content_checksum(content: str, algorithm: str = CHECKSUM_ALGORITHM) -> str:
    """
    Calculate checksum of document content.
    
    Args:
        content: The text content to hash
        algorithm: Hash algorithm to use (sha256, md5)
        
    Returns:
        Hexadecimal string representation of the hash
    """
    if algorithm.lower() == "md5":
        hash_obj = hashlib.md5()
    elif algorithm.lower() == "sha256":
        hash_obj = hashlib.sha256()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    hash_obj.update(content.encode('utf-8'))
    return hash_obj.hexdigest()


def get_file_modification_time(file_path: str) -> float:
    """
    Get file modification timestamp.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File modification time as timestamp
    """
    try:
        return os.path.getmtime(file_path)
    except OSError:
        return 0.0


def add_checksum_metadata(documents: List[Document]) -> List[Document]:
    """
    Add checksum and timing metadata to documents.
    
    Args:
        documents: List of Document objects to process
        
    Returns:
        Updated list of Document objects with checksum metadata
    """
    for doc in documents:
        # Calculate content checksum
        doc.metadata["content_checksum"] = calculate_content_checksum(doc.page_content)
        
        # Get file modification time
        source_path = doc.metadata.get("source", "")
        doc.metadata["file_modified_time"] = get_file_modification_time(source_path)
        
        # Add indexing timestamp (will be updated when actually indexed)
        doc.metadata["indexed_timestamp"] = 0.0
        
        # Initialize indexing status
        doc.metadata["index_status"] = "pending"
        
        # Placeholder for chunk count (will be updated after chunking)
        doc.metadata["chunk_count"] = 1
    
    return documents


def load_existing_metadata(metadata_csv_path: str) -> Dict[str, Dict]:
    """
    Load existing metadata from CSV into a lookup dictionary.
    
    Args:
        metadata_csv_path: Path to the metadata CSV file
        
    Returns:
        Dictionary with source paths as keys and metadata as values
    """
    if not os.path.exists(metadata_csv_path):
        return {}
    
    try:
        df = pd.read_csv(metadata_csv_path)
        metadata_dict = {}
        
        for _, row in df.iterrows():
            source = row.get('source', '')
            if source:
                metadata_dict[source] = row.to_dict()
        
        return metadata_dict
    except Exception as e:
        print(f"Error loading metadata CSV: {e}")
        return {}


def detect_document_changes(current_docs: List[Document], 
                          existing_metadata: Dict[str, Dict]) -> Dict[str, Any]:
    """
    Categorize documents based on changes compared to existing metadata.
    
    Args:
        current_docs: List of current Document objects
        existing_metadata: Dictionary of existing document metadata
        
    Returns:
        Dictionary with categories: new, modified, unchanged (List[Document]), deleted_sources (List[str])
    """
    new_docs = []
    modified_docs = []
    unchanged_docs = []
    current_sources = set()
    
    for doc in current_docs:
        source = doc.metadata.get("source", "")
        current_sources.add(source)
        
        if source not in existing_metadata:
            # New document
            new_docs.append(doc)
        else:
            existing_doc = existing_metadata[source]
            current_checksum = doc.metadata.get("content_checksum", "")
            existing_checksum = existing_doc.get("content_checksum", "")
            
            if current_checksum != existing_checksum:
                # Modified document
                modified_docs.append(doc)
            else:
                # Unchanged document
                unchanged_docs.append(doc)
    
    # Find deleted documents (in metadata but not in current docs)
    existing_sources = set(existing_metadata.keys())
    deleted_sources = list(existing_sources - current_sources)
    
    return {
        "new": new_docs,
        "modified": modified_docs,
        "unchanged": unchanged_docs,
        "deleted_sources": deleted_sources
    }


def should_process_document(doc: Document, existing_metadata: Dict[str, Dict]) -> bool:
    """
    Determine if a document needs processing based on checksum comparison.
    
    Args:
        doc: Document object to check
        existing_metadata: Dictionary of existing document metadata
        
    Returns:
        True if document should be processed, False otherwise
    """
    source = doc.metadata.get("source", "")
    
    if source not in existing_metadata:
        return True  # New document
    
    current_checksum = doc.metadata.get("content_checksum", "")
    existing_checksum = existing_metadata[source].get("content_checksum", "")
    
    return current_checksum != existing_checksum


def load_blog_posts(data_dir: str = DATA_DIR, 
                   glob_pattern: str = "*.md", 
                   recursive: bool = True, 
                   show_progress: bool = True) -> List[Document]:
    """
    Load blog posts from the specified directory.
    
    Args:
        data_dir: Directory containing the blog posts
        glob_pattern: Pattern to match files
        recursive: Whether to search subdirectories
        show_progress: Whether to show a progress bar
        
    Returns:
        List of Document objects containing the blog posts
    """
    text_loader = DirectoryLoader(
        data_dir, 
        glob=glob_pattern, 
        show_progress=show_progress,
        recursive=recursive,
        loader_cls=TextLoader,
        # loader_cls=UnstructuredMarkdownLoader,
        # loader_kwargs={
        #     "encoding": "utf-8",
        #     "mode": "elements",  # Load as elements for better processing
        #     "markdown_extensions": ["fenced_code", "tables", "attr_list"]
        # }

        
    )
    
    documents = text_loader.load()
    print(f"Loaded {len(documents)} documents from {data_dir}")
    return documents


def update_document_metadata(documents: List[Document], 
                           data_dir_prefix: str = DATA_DIR,
                           blog_base_url: str = BLOG_BASE_URL,
                           base_url: str = BASE_URL,
                           remove_suffix: str = "index.md",
                           index_only_published_posts : bool= INDEX_ONLY_PUBLISHED_POSTS) -> List[Document]:
    """
    Update the metadata of documents to include URL and other information.
    
    Args:
        documents: List of Document objects to update
        data_dir_prefix: Prefix to replace in source paths
        blog_base_url: Base URL for the blog posts (default: BLOG_BASE_URL)
        base_url: Base URL for absolute media links (default: BASE_URL)
        remove_suffix: Suffix to remove from paths (like index.md)
        
    Returns:
        Updated list of Document objects
    """

    # add / at the end of blog_base_url if not present
    if not blog_base_url.endswith('/'):
        blog_base_url += '/'
        
    for doc in documents:
        # Create URL from source path
        doc.metadata["url"] = doc.metadata["source"].replace(data_dir_prefix, blog_base_url)
        
        

        # Remove index.md or other suffix if present
        if remove_suffix and doc.metadata["url"].endswith(remove_suffix):
            doc.metadata["url"] = doc.metadata["url"][:-len(remove_suffix)]

        # Remove .md suffix if present
        if doc.metadata["url"].endswith(".md"):
            doc.metadata["url"] = doc.metadata["url"][:-3]

        # Extract post title from the directory structure
        path_parts = Path(doc.metadata["source"]).parts
        if len(path_parts) > 1:
            # Use the directory name as post_slug
            doc.metadata["post_slug"] = path_parts[-2]
            try:
                #extract title from `doc.page_content`'s front matter like `title:`
                # Extract frontmatter data
                frontmatter_data = {}
                content_parts = doc.page_content.split('---', 2)
                
                if len(content_parts) >= 3:  # Valid frontmatter found
                    frontmatter_text = content_parts[1]
                    for line in frontmatter_text.strip().split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"')
                            frontmatter_data[key] = value
                
                # Set metadata fields from frontmatter
                doc.metadata["post_title"] = frontmatter_data.get("title", 
                                            path_parts[-2].replace("-", " ").title())
                
                #Handle URL and other metadata fields
                if not base_url:
                    base_url = blog_base_url
                
                def make_absolute_url(url, base_url=base_url):
                    """Helper function to convert relative URLs to absolute ones."""
                    if url and not (url.startswith("http://") or url.startswith("https://")):
                        return f"{base_url.rstrip('/')}/{url.lstrip('/')}"
                    return url
                
                # Handle cover image and video with the same logic
                for media_type in ["coverImage", "coverVideo"]:
                    metadata_key = media_type.replace("cover", "cover_").lower()
                    if media_type in frontmatter_data:
                        doc.metadata[metadata_key] = make_absolute_url(frontmatter_data[media_type])

                # Add additional metadata fields if available
                if "date" in frontmatter_data:
                    doc.metadata["date"] = frontmatter_data["date"]
                if "categories" in frontmatter_data:
                    categories = frontmatter_data["categories"].strip('[]').replace('"', '')
                    doc.metadata["categories"] = [c.strip() for c in categories.split(',')]
                if "description" in frontmatter_data:
                    doc.metadata["description"] = frontmatter_data["description"]
                if "readingTime" in frontmatter_data:
                    doc.metadata["reading_time"] = frontmatter_data["readingTime"]
                if "published" in frontmatter_data:
                    doc.metadata["published"] = frontmatter_data["published"].lower() == "true"

            except Exception as e:
                doc.metadata["post_title"] = path_parts[-2].replace("-", " ").title()

        # Add document length as metadata
        doc.metadata["content_length"] = len(doc.page_content)

    # Filter out documents with doc.metadata["published"] == False if index_only_published_posts is True
    filtered_documents = []
    for doc in documents:
        if index_only_published_posts and "published" in doc.metadata and not doc.metadata["published"]:
            print(f"Skipping unpublished document: {doc.metadata['post_title']}")
        else:
            filtered_documents.append(doc)
    
    # Add checksum metadata to all filtered documents
    filtered_documents = add_checksum_metadata(filtered_documents)
        
    return filtered_documents


def get_document_stats(documents: List[Document]) -> Dict[str, Any]:
    """
    Get statistics about the documents.
    
    Args:
        documents: List of Document objects
        
    Returns:
        Dictionary with statistics
    """
    stats = {
        "total_documents": len(documents),
        "total_characters": sum(len(doc.page_content) for doc in documents),
        "min_length": min(len(doc.page_content) for doc in documents) if documents else 0,
        "max_length": max(len(doc.page_content) for doc in documents) if documents else 0,
        "avg_length": sum(len(doc.page_content) for doc in documents) / len(documents) if documents else 0,
    }
    
    # Create a list of document info for analysis
    doc_info = []
    for doc in documents:
        doc_info.append({
            "url": doc.metadata.get("url", ""),
            "source": doc.metadata.get("source", ""),
            "title": doc.metadata.get("post_title", ""),
            "text_length": doc.metadata.get("content_length", 0),
            "date": doc.metadata.get("date", ""),
            "categories": doc.metadata.get("categories", []),
            "description": doc.metadata.get("description", ""),
            "cover_image": doc.metadata.get("cover_image", ""),
            "cover_video": doc.metadata.get("cover_video", ""),
            "reading_time": doc.metadata.get("reading_time", ""),
            "published": doc.metadata.get("published", ""),
            "post_slug": doc.metadata.get("post_slug", ""),
            "content_checksum": doc.metadata.get("content_checksum", ""),
            "file_modified_time": doc.metadata.get("file_modified_time", 0.0),
            "indexed_timestamp": doc.metadata.get("indexed_timestamp", 0.0),
            "chunk_count": doc.metadata.get("chunk_count", 1),
            "index_status": doc.metadata.get("index_status", "pending"),
        })
    
    stats["documents"] = doc_info
    return stats


def display_document_stats(stats: Dict[str, Any]):
    """
    Display document statistics in a readable format.
    
    Args:
        stats: Dictionary with statistics from get_document_stats
    """
    print(f"Total Documents: {stats['total_documents']}")
    print(f"Total Characters: {stats['total_characters']}")
    print(f"Min Length: {stats['min_length']} characters")
    print(f"Max Length: {stats['max_length']} characters")
    print(f"Average Length: {stats['avg_length']:.2f} characters")
    print("\nDocument Details:")
    for doc in stats["documents"]:
        print(f"Title: {doc['title']}")
        print(f"URL: {doc['url']}")
        print(f"Date: {doc['date']}")
        print(f"Categories: {', '.join(doc['categories']) if doc['categories'] else 'N/A'}")
        print(f"Description: {doc['description']}")
        print(f"Cover Image: {doc['cover_image']}")
        print(f"Cover Video: {doc['cover_video']}")
        print(f"Reading Time: {doc['reading_time']}")
        print(f"Published: {doc['published']}")
        print(f"Content Checksum: {doc['content_checksum'][:16]}...")  # Show first 16 chars
        print(f"Index Status: {doc['index_status']}")
        print("-" * 40)


def split_documents(documents: List[Document], 
                   chunk_size: int = CHUNK_SIZE, 
                   chunk_overlap: int = CHUNK_OVERLAP) -> List[Document]:
    """
    Split documents into chunks for better embedding and retrieval.
    
    Args:
        documents: List of Document objects to split
        chunk_size: Size of each chunk in characters
        chunk_overlap: Overlap between chunks in characters
        
    Returns:
        List of split Document objects
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    
    # Track original documents and their chunk counts
    source_to_chunk_count = {}
    
    split_docs = text_splitter.split_documents(documents)
    
    # Count chunks per source document
    for doc in split_docs:
        source = doc.metadata.get("source", "")
        source_to_chunk_count[source] = source_to_chunk_count.get(source, 0) + 1
    
    # Update chunk_count in the original documents' metadata
    for doc in documents:
        source = doc.metadata.get("source", "")
        doc.metadata["chunk_count"] = source_to_chunk_count.get(source, 1)
    
    # Also update chunk_count in split documents
    for doc in split_docs:
        source = doc.metadata.get("source", "")
        doc.metadata["chunk_count"] = source_to_chunk_count.get(source, 1)
    
    print(f"Split {len(documents)} documents into {len(split_docs)} chunks")
    return split_docs


def create_vector_store(documents: List[Document], 
                       storage_path: str = VECTOR_STORAGE_PATH,
                       collection_name: str = QDRANT_COLLECTION,
                       qdrant_url: str = QDRANT_URL,
                       embedding_model: str = EMBEDDING_MODEL,
                       force_recreate: bool = False) -> Optional[QdrantVectorStore]:
    
    """
    Create a vector store from the documents using Qdrant.
    Args:
        documents: List of Document objects to embed
        storage_path: Path to the vector store
        collection_name: Name of the collection
        embedding_model: Name of the embedding model
        force_recreate: Whether to force recreation of the vector store
    Returns:
        QdrantVectorStore vector store or None if creation fails
    """

    embeddings = init_embeddings(embedding_model,base_url=OLLAMA_BASE_URL)

    if qdrant_url:
        vector_store = QdrantVectorStore.from_documents(
            documents,
            embedding=embeddings,  # type: ignore
            collection_name=collection_name,
            url=qdrant_url,
        )
        return vector_store

    vector_store = QdrantVectorStore.from_documents(
        documents,
        embedding=embeddings,  # type: ignore
        collection_name=collection_name,
        path=storage_path,
        force_recreate=force_recreate,
    )
    
    return vector_store


def load_vector_store(storage_path: str = VECTOR_STORAGE_PATH,
                     collection_name: str = QDRANT_COLLECTION,
                     qdrant_url: str = QDRANT_URL,
                     embedding_model: str = EMBEDDING_MODEL) -> Optional[QdrantVectorStore]:
    """
    Load an existing vector store.
    
    Args:
        storage_path: Path to the vector store
        collection_name: Name of the collection
        embedding_model: Name of the embedding model
        
    Returns:
        QdrantVectorStore vector store or None if it doesn't exist
    """
    # Initialize the embedding model
    embeddings = init_embeddings(embedding_model,base_url=OLLAMA_BASE_URL)
    

    if qdrant_url:
        vector_store = QdrantVectorStore.from_existing_collection(
            collection_name=collection_name,
            url=qdrant_url,
            embedding=embeddings,  # type: ignore
            prefer_grpc= True,  # Use gRPC for better performance
        )
        return vector_store


    # Check if vector store exists
    if not Path(storage_path).exists():
        print(f"Vector store not found at {storage_path}")
        return None
    
    try:
        # Initialize Qdrant client
        client = QdrantClient(path=storage_path)
        
        # Create vector store with the client
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=collection_name,
            embedding=embeddings, # type: ignore
        )
        print(f"Loaded vector store from {storage_path}")
        return vector_store
    except Exception as e:
        print(f"Error loading vector store: {e}")
        return None


def process_blog_posts(data_dir: str = DATA_DIR,
                      create_embeddings: bool = True,
                      force_recreate_embeddings: bool = False,
                      storage_path: str = VECTOR_STORAGE_PATH,
                      split_docs: bool = True,
                      display_stats:bool = False) -> Dict[str, Any]:
    """
    Complete pipeline to process blog posts and optionally create vector embeddings.
    
    Args:
        data_dir: Directory containing the blog posts
        create_embeddings: Whether to create vector embeddings
        force_recreate_embeddings: Whether to force recreation of embeddings
        storage_path: Path to the vector store (not used with in-memory approach)
        
    Returns:
        Dictionary with data and vector store (if created)
    """
    # Load documents
    documents = load_blog_posts(data_dir)
    
    # Update metadata
    documents = update_document_metadata(documents)

    if split_docs:
        # Split documents into smaller chunks
        documents = split_documents(documents)
    

    # Get and display stats
    stats = get_document_stats(documents)

    if display_stats:
        display_document_stats(stats)
    
    result = {
        "documents": documents,
        "stats": stats,
        "vector_store": None
    }
    
    # Create vector store if requested
    if create_embeddings:
        # Using in-memory vector store to avoid pickling issues
        vector_store = create_vector_store(
            documents, 
            force_recreate=force_recreate_embeddings,
            storage_path=storage_path
        )
        result["vector_store"] = vector_store
    
    return result


def add_documents_to_vector_store(vector_store: QdrantVectorStore, 
                                   documents: List[Document]) -> bool:
    """
    Add new documents to an existing vector store.
    
    Args:
        vector_store: Existing QdrantVectorStore instance
        documents: List of Document objects to add
        
    Returns:
        True if successful, False otherwise
    """
    if not documents:
        return True
    
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        # Add documents to the vector store
        vector_store.add_documents(documents)
        logger.info(f"Successfully added {len(documents)} documents to vector store")
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error adding documents to vector store: {e}")
        return False


def remove_documents_from_vector_store(vector_store: QdrantVectorStore, 
                                       document_sources: List[str]) -> bool:
    """
    Remove documents from the vector store based on their source paths.
    
    Args:
        vector_store: Existing QdrantVectorStore instance
        document_sources: List of source paths to remove
        
    Returns:
        True if successful, False otherwise
    """
    if not document_sources:
        return True
    
    try:
        # Import logger and models here to avoid circular imports
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from qdrant_client import models
        except ImportError:
            logger.warning("Could not import qdrant models for document removal")
            return False
        
        # Delete by metadata filter (source field)
        for source in document_sources:
            # Create a filter to find documents with this source
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.source",
                        match=models.MatchValue(value=source)
                    )
                ]
            )
            
            # Delete documents matching the filter
            vector_store.client.delete(
                collection_name=vector_store.collection_name,
                points_selector=models.FilterSelector(filter=filter_condition)
            )
        
        logger.info(f"Successfully removed documents for {len(document_sources)} sources from vector store")
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error removing documents from vector store: {e}")
        return False


def update_vector_store_incrementally(storage_path: str,
                                     collection_name: str,
                                     embedding_model: str,
                                     qdrant_url: str,
                                     new_docs: List[Document],
                                     modified_docs: List[Document],
                                     deleted_sources: List[str],
                                     use_enhanced_mode: bool = ENABLE_BATCH_PROCESSING,
                                     batch_size: int = BATCH_SIZE) -> bool:
    """
    Update vector store incrementally by adding new/modified docs and removing deleted ones.
    
    Args:
        storage_path: Path to the vector store
        collection_name: Name of the collection
        embedding_model: Name of the embedding model
        qdrant_url: Qdrant server URL (if using remote)
        new_docs: List of new documents to add
        modified_docs: List of modified documents to update
        deleted_sources: List of source paths to remove
        use_enhanced_mode: Whether to use enhanced mode with performance optimization
        batch_size: Batch size for processing documents
        
    Returns:
        True if successful, False otherwise
    """
    import time
    start_time = time.time()
    
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        # Load existing vector store
        vector_store = load_vector_store(
            storage_path=storage_path,
            collection_name=collection_name,
            qdrant_url=qdrant_url,
            embedding_model=embedding_model
        )
        
        if vector_store is None:
            logger.error("Could not load existing vector store for incremental update")
            return False
        
        # Remove deleted documents first
        if deleted_sources:
            logger.info(f"Removing {len(deleted_sources)} deleted documents from vector store")
            if use_enhanced_mode and len(deleted_sources) > batch_size:
                success = remove_documents_from_vector_store_batch(vector_store, deleted_sources, batch_size)
            else:
                success = remove_documents_from_vector_store(vector_store, deleted_sources)
            if not success:
                logger.error("Failed to remove deleted documents")
                return False
        
        # Remove old versions of modified documents
        if modified_docs:
            modified_sources = [doc.metadata.get("source", "") for doc in modified_docs]
            logger.info(f"Removing old versions of {len(modified_sources)} modified documents")
            if use_enhanced_mode and len(modified_sources) > batch_size:
                success = remove_documents_from_vector_store_batch(vector_store, modified_sources, batch_size)
            else:
                success = remove_documents_from_vector_store(vector_store, modified_sources)
            if not success:
                logger.error("Failed to remove old versions of modified documents")
                return False
        
        # Add new and modified documents
        all_docs_to_add = new_docs + modified_docs
        if all_docs_to_add:
            logger.info(f"Adding {len(all_docs_to_add)} documents to vector store ({len(new_docs)} new, {len(modified_docs)} modified)")
            if use_enhanced_mode and len(all_docs_to_add) > batch_size:
                success = add_documents_to_vector_store_batch(vector_store, all_docs_to_add, batch_size)
            else:
                success = add_documents_to_vector_store(vector_store, all_docs_to_add)
            if not success:
                logger.error("Failed to add new/modified documents")
                return False
        
        # Close the vector store connection
        if hasattr(vector_store, 'client') and vector_store.client:
            vector_store.client.close()
        
        # Log performance metrics
        total_docs = len(new_docs) + len(modified_docs)
        total_chunks = len(all_docs_to_add) if all_docs_to_add else 0
        metrics = monitor_incremental_performance(
            "incremental_update", start_time, total_docs, total_chunks
        )
        
        logger.info("Incremental vector store update completed successfully")
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error during incremental vector store update: {e}")
        return False


def save_document_metadata_csv(documents: List[Document], 
                              metadata_csv_path: str,
                              include_unchanged: bool = True) -> bool:
    """
    Save document metadata to CSV file.
    
    Args:
        documents: List of Document objects
        metadata_csv_path: Path to save the CSV file
        include_unchanged: Whether to include unchanged documents in the CSV
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        # Extract metadata for CSV
        metadata_records = []
        
        for doc in documents:
            metadata = doc.metadata.copy()
            
            # Ensure required fields exist
            metadata.setdefault("content_checksum", "")
            metadata.setdefault("file_modified_time", 0.0)
            metadata.setdefault("indexed_timestamp", 0.0)
            metadata.setdefault("index_status", "pending")
            metadata.setdefault("chunk_count", 1)
            
            metadata_records.append(metadata)
        
        # Convert to DataFrame and save
        df = pd.DataFrame(metadata_records)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(metadata_csv_path), exist_ok=True)
        
        # Save to CSV
        df.to_csv(metadata_csv_path, index=False)
        logger.info(f"Saved metadata for {len(documents)} documents to {metadata_csv_path}")
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error saving metadata CSV: {e}")
        return False


def backup_metadata_csv(metadata_csv_path: str) -> Optional[str]:
    """
    Create a backup of the metadata CSV file before making changes.
    
    Args:
        metadata_csv_path: Path to the metadata CSV file
        
    Returns:
        Path to the backup file if successful, None otherwise
    """
    if not os.path.exists(metadata_csv_path):
        return None
    
    try:
        import time
        timestamp = int(time.time())
        backup_path = f"{metadata_csv_path}.backup.{timestamp}"
        
        import shutil
        shutil.copy2(metadata_csv_path, backup_path)
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Created metadata backup at {backup_path}")
        return backup_path
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create metadata backup: {e}")
        return None


def restore_metadata_backup(backup_path: str, original_path: str) -> bool:
    """
    Restore metadata from backup file.
    
    Args:
        backup_path: Path to the backup file
        original_path: Path to restore to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import shutil
        shutil.copy2(backup_path, original_path)
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Restored metadata from backup {backup_path}")
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to restore metadata backup: {e}")
        return False


def validate_vector_store_health(storage_path: str, collection_name: str, 
                                qdrant_url: str, embedding_model: str) -> bool:
    """
    Validate that the vector store is healthy and accessible.
    
    Args:
        storage_path: Path to the vector store
        collection_name: Name of the collection
        qdrant_url: Qdrant server URL (if using remote)
        embedding_model: Name of the embedding model
        
    Returns:
        True if healthy, False otherwise
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        vector_store = load_vector_store(
            storage_path=storage_path,
            collection_name=collection_name,
            qdrant_url=qdrant_url,
            embedding_model=embedding_model
        )
        
        if vector_store is None:
            logger.warning("Vector store could not be loaded")
            return False
        
        # Test basic operations
        try:
            # Try to perform a basic similarity search to validate the store works
            test_results = vector_store.similarity_search("test query", k=1)
            logger.info("Vector store health check passed")
            return True
        except Exception as e:
            logger.warning(f"Vector store similarity search failed: {e}")
            return False
        finally:
            if hasattr(vector_store, 'client') and vector_store.client:
                vector_store.client.close()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Vector store health check failed: {e}")
        return False


def update_vector_store_incrementally_with_rollback(storage_path: str,
                                                   collection_name: str,
                                                   embedding_model: str,
                                                   qdrant_url: str,
                                                   new_docs: List[Document],
                                                   modified_docs: List[Document],
                                                   deleted_sources: List[str],
                                                   metadata_csv_path: str,
                                                   all_documents: List[Document]) -> Tuple[bool, str]:
    """
    Update vector store incrementally with comprehensive error handling and rollback.
    
    Args:
        storage_path: Path to the vector store
        collection_name: Name of the collection
        embedding_model: Name of the embedding model
        qdrant_url: Qdrant server URL (if using remote)
        new_docs: List of new documents to add
        modified_docs: List of modified documents to update
        deleted_sources: List of source paths to remove
        metadata_csv_path: Path to metadata CSV file
        all_documents: All documents for metadata backup
        
    Returns:
        Tuple of (success, error_message)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Create backup of metadata before starting
    backup_path = backup_metadata_csv(metadata_csv_path)
    
    # Pre-flight checks
    logger.info("Performing pre-flight health checks...")
    if not validate_vector_store_health(storage_path, collection_name, qdrant_url, embedding_model):
        error_msg = "Vector store failed pre-flight health check"
        logger.error(error_msg)
        return False, error_msg
    
    try:
        # Load existing vector store
        vector_store = load_vector_store(
            storage_path=storage_path,
            collection_name=collection_name,
            qdrant_url=qdrant_url,
            embedding_model=embedding_model
        )
        
        if vector_store is None:
            error_msg = "Could not load existing vector store for incremental update"
            logger.error(error_msg)
            return False, error_msg
        
        # Step 1: Remove deleted documents
        if deleted_sources:
            logger.info(f"Step 1/3: Removing {len(deleted_sources)} deleted documents from vector store")
            success = remove_documents_from_vector_store(vector_store, deleted_sources)
            if not success:
                error_msg = "Failed to remove deleted documents"
                logger.error(error_msg)
                return False, error_msg
        
        # Step 2: Remove old versions of modified documents
        if modified_docs:
            modified_sources = [doc.metadata.get("source", "") for doc in modified_docs]
            logger.info(f"Step 2/3: Removing old versions of {len(modified_sources)} modified documents")
            success = remove_documents_from_vector_store(vector_store, modified_sources)
            if not success:
                error_msg = "Failed to remove old versions of modified documents"
                logger.error(error_msg)
                return False, error_msg
        
        # Step 3: Add new and modified documents
        all_docs_to_add = new_docs + modified_docs
        if all_docs_to_add:
            logger.info(f"Step 3/3: Adding {len(all_docs_to_add)} documents to vector store ({len(new_docs)} new, {len(modified_docs)} modified)")
            success = add_documents_to_vector_store(vector_store, all_docs_to_add)
            if not success:
                error_msg = "Failed to add new/modified documents"
                logger.error(error_msg)
                return False, error_msg
        
        # Post-flight health check
        logger.info("Performing post-flight health checks...")
        if hasattr(vector_store, 'client') and vector_store.client:
            vector_store.client.close()
        
        if not validate_vector_store_health(storage_path, collection_name, qdrant_url, embedding_model):
            error_msg = "Vector store failed post-flight health check"
            logger.error(error_msg)
            # Attempt to restore backup if available
            if backup_path:
                logger.info("Attempting to restore metadata backup due to health check failure")
                restore_metadata_backup(backup_path, metadata_csv_path)
            return False, error_msg
        
        # Update and save metadata
        import time
        current_time = time.time()
        
        # Update metadata for processed documents
        processed_sources = set()
        for doc in new_docs + modified_docs:
            source = doc.metadata.get("source", "")
            processed_sources.add(source)
        
        for doc in all_documents:
            source = doc.metadata.get("source", "")
            if source in processed_sources:
                doc.metadata["indexed_timestamp"] = current_time
                doc.metadata["index_status"] = "indexed"
        
        # Save updated metadata
        success_metadata = save_document_metadata_csv(all_documents, metadata_csv_path)
        if not success_metadata:
            logger.warning("Failed to save updated metadata CSV, but vector store update succeeded")
        
        # Clean up old backup (keep only the most recent one)
        cleanup_old_backups(metadata_csv_path, keep_count=1)
        
        logger.info("Incremental vector store update completed successfully with full validation")
        return True, "Success"
        
    except Exception as e:
        error_msg = f"Unexpected error during incremental vector store update: {e}"
        logger.error(error_msg, exc_info=True)
        
        # Attempt to restore backup if available
        if backup_path:
            logger.info("Attempting to restore metadata backup due to error")
            restore_metadata_backup(backup_path, metadata_csv_path)
        
        return False, error_msg


def cleanup_old_backups(metadata_csv_path: str, keep_count: int = MAX_BACKUP_FILES) -> None:
    """
    Clean up old backup files, keeping only the most recent ones.
    
    Args:
        metadata_csv_path: Path to the metadata CSV file
        keep_count: Number of backup files to keep
    """
    try:
        import glob
        import os
        
        backup_pattern = f"{metadata_csv_path}.backup.*"
        backup_files = glob.glob(backup_pattern)
        
        if len(backup_files) <= keep_count:
            return
        
        # Sort by modification time (newest first)
        backup_files.sort(key=os.path.getmtime, reverse=True)
        
        # Remove oldest backups
        files_to_remove = backup_files[keep_count:]
        for backup_file in files_to_remove:
            try:
                os.remove(backup_file)
            except OSError:
                pass  # Ignore errors removing backup files
                
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Cleaned up {len(files_to_remove)} old backup files")
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Error cleaning up old backups: {e}")


def batch_process_documents(documents: List[Document], 
                          batch_size: int = 50,
                          operation: str = "add") -> List[List[Document]]:
    """
    Split documents into batches for efficient processing.
    
    Args:
        documents: List of documents to batch
        batch_size: Number of documents per batch
        operation: Type of operation (add, remove) for logging
        
    Returns:
        List of document batches
    """
    if not documents:
        return []
    
    batches = []
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        batches.append(batch)
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Split {len(documents)} documents into {len(batches)} batches of max {batch_size} for {operation}")
    
    return batches


def add_documents_to_vector_store_batch(vector_store: QdrantVectorStore, 
                                       documents: List[Document],
                                       batch_size: int = BATCH_SIZE) -> bool:
    """
    Add new documents to an existing vector store in batches for better performance.
    
    Args:
        vector_store: Existing QdrantVectorStore instance
        documents: List of Document objects to add
        batch_size: Number of documents to process per batch
        
    Returns:
        True if successful, False otherwise
    """
    if not documents:
        return True
    
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        # Process documents in batches
        batches = batch_process_documents(documents, batch_size, "add")
        
        for i, batch in enumerate(batches):
            logger.info(f"Processing batch {i+1}/{len(batches)} ({len(batch)} documents)")
            
            # Add batch to the vector store
            vector_store.add_documents(batch)
            
            # Optional: Brief pause between batches to avoid overwhelming the system
            if len(batches) > 1 and i < len(batches) - 1:
                import time
                time.sleep(BATCH_PAUSE_SECONDS)  # Configurable pause between batches
        
        logger.info(f"Successfully added {len(documents)} documents to vector store in {len(batches)} batches")
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error adding documents to vector store in batches: {e}")
        return False


def remove_documents_from_vector_store_batch(vector_store: QdrantVectorStore, 
                                            document_sources: List[str],
                                            batch_size: int = BATCH_SIZE) -> bool:
    """
    Remove documents from the vector store in batches for better performance.
    
    Args:
        vector_store: Existing QdrantVectorStore instance
        document_sources: List of source paths to remove
        batch_size: Number of sources to process per batch
        
    Returns:
        True if successful, False otherwise
    """
    if not document_sources:
        return True
    
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from qdrant_client import models
        except ImportError:
            logger.warning("Could not import qdrant models for batch document removal")
            return False
        
        # Process sources in batches
        batches = []
        for i in range(0, len(document_sources), batch_size):
            batch = document_sources[i:i + batch_size]
            batches.append(batch)
        
        logger.info(f"Split {len(document_sources)} sources into {len(batches)} batches for removal")
        
        for i, batch in enumerate(batches):
            logger.info(f"Removing batch {i+1}/{len(batches)} ({len(batch)} sources)")
            
            # Process each source in the batch individually for better compatibility
            for source in batch:
                filter_condition = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.source",
                            match=models.MatchValue(value=source)
                        )
                    ]
                )
                
                # Delete documents matching the filter
                vector_store.client.delete(
                    collection_name=vector_store.collection_name,
                    points_selector=models.FilterSelector(filter=filter_condition)
                )
            
            # Optional: Brief pause between batches
            if len(batches) > 1 and i < len(batches) - 1:
                import time
                time.sleep(BATCH_PAUSE_SECONDS)  # Configurable pause between batches
        
        logger.info(f"Successfully removed documents for {len(document_sources)} sources in {len(batches)} batches")
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error removing documents from vector store in batches: {e}")
        return False


def get_processing_stats() -> Dict[str, Any]:
    """
    Get system resource usage statistics for performance monitoring.
    
    Returns:
        Dictionary with system stats
    """
    stats = {}
    
    try:
        import psutil
        
        # Memory usage
        memory = psutil.virtual_memory()
        stats["memory_total_gb"] = round(memory.total / (1024**3), 2)
        stats["memory_available_gb"] = round(memory.available / (1024**3), 2)
        stats["memory_percent"] = memory.percent
        
        # CPU usage
        stats["cpu_percent"] = psutil.cpu_percent(interval=1)
        stats["cpu_count"] = psutil.cpu_count()
        
        # Disk usage for current directory
        disk = psutil.disk_usage('.')
        stats["disk_total_gb"] = round(disk.total / (1024**3), 2)
        stats["disk_free_gb"] = round(disk.free / (1024**3), 2)
        stats["disk_percent"] = round((disk.used / disk.total) * 100, 2)
        
    except ImportError:
        # psutil not available, provide basic stats
        stats["memory_info"] = "psutil not available"
    except Exception as e:
        stats["error"] = str(e)
    
    return stats


def optimize_chunking_strategy(documents: List[Document], 
                              target_chunk_size: int = 1000,
                              max_chunk_size: int = 2000) -> Tuple[int, int]:
    """
    Optimize chunking parameters based on document characteristics.
    
    Args:
        documents: List of documents to analyze
        target_chunk_size: Target chunk size
        max_chunk_size: Maximum allowed chunk size
        
    Returns:
        Tuple of (optimized_chunk_size, optimized_overlap)
    """
    if not documents:
        return target_chunk_size, 100
    
    # Analyze document lengths
    lengths = [len(doc.page_content) for doc in documents]
    avg_length = sum(lengths) / len(lengths)
    min_length = min(lengths)
    max_length = max(lengths)
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Document analysis: avg={avg_length:.0f}, min={min_length}, max={max_length}")
    
    # Optimize chunk size based on document characteristics
    if avg_length < target_chunk_size:
        # Documents are small, use smaller chunks to avoid over-chunking
        optimized_chunk_size = max(int(avg_length * 0.7), 500)
        optimized_overlap = max(int(optimized_chunk_size * 0.05), 50)
    elif avg_length > max_chunk_size:
        # Documents are large, use larger chunks
        optimized_chunk_size = max_chunk_size
        optimized_overlap = max(int(optimized_chunk_size * 0.1), 100)
    else:
        # Documents are medium-sized, use target size
        optimized_chunk_size = target_chunk_size
        optimized_overlap = max(int(optimized_chunk_size * 0.1), 100)
    
    logger.info(f"Optimized chunking: size={optimized_chunk_size}, overlap={optimized_overlap}")
    return optimized_chunk_size, optimized_overlap


def monitor_incremental_performance(operation: str, 
                                   start_time: float,
                                   document_count: int,
                                   chunk_count: int = 0) -> Dict[str, Any]:
    """
    Monitor and log performance metrics for incremental operations.
    
    Args:
        operation: Name of the operation
        start_time: Operation start time (from time.time())
        document_count: Number of documents processed
        chunk_count: Number of chunks processed
        
    Returns:
        Performance metrics dictionary
    """
    import time
    end_time = time.time()
    duration = end_time - start_time
    
    metrics = {
        "operation": operation,
        "duration_seconds": round(duration, 2),
        "document_count": document_count,
        "chunk_count": chunk_count,
        "documents_per_second": round(document_count / duration, 2) if duration > 0 else 0,
        "system_stats": get_processing_stats()
    }
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Performance: {operation} completed in {duration:.2f}s "
               f"({document_count} docs, {metrics['documents_per_second']:.1f} docs/sec)")
    
    return metrics


def apply_performance_optimizations(documents: List[Document], 
                                   target_chunk_size: int = CHUNK_SIZE,
                                   enable_monitoring: bool = ENABLE_PERFORMANCE_MONITORING) -> Tuple[List[Document], Dict[str, Any]]:
    """
    Apply comprehensive performance optimizations to documents.
    
    Args:
        documents: List of documents to optimize
        target_chunk_size: Target chunk size for optimization
        enable_monitoring: Whether to enable performance monitoring
        
    Returns:
        Tuple of (optimized_documents, performance_metrics)
    """
    import time
    start_time = time.time()
    
    performance_metrics = {
        "input_document_count": len(documents),
        "optimizations_applied": [],
        "performance_stats": {}
    }
    
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        # Apply adaptive chunking if enabled
        if ADAPTIVE_CHUNKING and documents:
            logger.info("Applying adaptive chunking optimization...")
            optimized_chunk_size, optimized_overlap = optimize_chunking_strategy(
                documents, target_chunk_size
            )
            performance_metrics["optimizations_applied"].append("adaptive_chunking")
            performance_metrics["chunk_size"] = optimized_chunk_size
            performance_metrics["chunk_overlap"] = optimized_overlap
        else:
            optimized_chunk_size = target_chunk_size
            optimized_overlap = CHUNK_OVERLAP
        
        # Monitor system resources if enabled
        if enable_monitoring:
            performance_metrics["performance_stats"] = get_processing_stats()
            performance_metrics["optimizations_applied"].append("resource_monitoring")
        
        # Apply document-level optimizations
        optimized_documents = documents.copy()
        
        # Add performance metadata to documents
        for doc in optimized_documents:
            doc.metadata["optimization_applied"] = True
            doc.metadata["optimized_chunk_size"] = optimized_chunk_size
            doc.metadata["optimized_chunk_overlap"] = optimized_overlap
        
        # Calculate performance metrics
        end_time = time.time()
        performance_metrics["optimization_duration"] = round(end_time - start_time, 3)
        performance_metrics["documents_per_second"] = round(
            len(documents) / (end_time - start_time), 2
        ) if end_time > start_time else 0
        
        logger.info(f"Performance optimizations completed in {performance_metrics['optimization_duration']}s")
        logger.info(f"Applied optimizations: {', '.join(performance_metrics['optimizations_applied'])}")
        
        return optimized_documents, performance_metrics
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error applying performance optimizations: {e}")
        performance_metrics["error"] = str(e)
        return documents, performance_metrics


def comprehensive_system_health_check(storage_path: str,
                                     collection_name: str,
                                     qdrant_url: str,
                                     embedding_model: str,
                                     metadata_csv_path: str) -> Dict[str, Any]:
    """
    Perform a comprehensive health check of the entire incremental indexing system.
    
    Args:
        storage_path: Path to the vector store
        collection_name: Name of the collection
        qdrant_url: Qdrant server URL
        embedding_model: Embedding model name
        metadata_csv_path: Path to metadata CSV file
        
    Returns:
        Dictionary with detailed health check results
    """
    import logging
    import time
    logger = logging.getLogger(__name__)
    
    health_report = {
        "overall_status": "unknown",
        "timestamp": time.time(),
        "checks": {},
        "recommendations": [],
        "errors": []
    }
    
    try:
        # Check 1: Vector store health
        logger.info("Checking vector store health...")
        vector_store_healthy = validate_vector_store_health(
            storage_path, collection_name, qdrant_url, embedding_model
        )
        health_report["checks"]["vector_store"] = {
            "status": "healthy" if vector_store_healthy else "unhealthy",
            "details": "Vector store is accessible and responsive" if vector_store_healthy else "Vector store is not accessible"
        }
        
        # Check 2: Metadata file integrity
        logger.info("Checking metadata file integrity...")
        metadata_exists = os.path.exists(metadata_csv_path)
        metadata_readable = False
        metadata_record_count = 0
        
        if metadata_exists:
            try:
                df = pd.read_csv(metadata_csv_path)
                metadata_readable = True
                metadata_record_count = len(df)
            except Exception as e:
                health_report["errors"].append(f"Metadata file read error: {e}")
        
        health_report["checks"]["metadata"] = {
            "status": "healthy" if (metadata_exists and metadata_readable) else "unhealthy",
            "exists": metadata_exists,
            "readable": metadata_readable,
            "record_count": metadata_record_count
        }
        
        # Check 3: System resources
        logger.info("Checking system resources...")
        system_stats = get_processing_stats()
        memory_ok = True
        disk_ok = True
        
        if "memory_percent" in system_stats:
            memory_ok = system_stats["memory_percent"] < 85  # Less than 85% memory usage
        if "disk_percent" in system_stats:
            disk_ok = system_stats["disk_percent"] < 90  # Less than 90% disk usage
            
        health_report["checks"]["system_resources"] = {
            "status": "healthy" if (memory_ok and disk_ok) else "warning",
            "memory_ok": memory_ok,
            "disk_ok": disk_ok,
            "details": system_stats
        }
        
        # Check 4: Configuration validation
        logger.info("Checking configuration...")
        config_valid = True
        config_issues = []
        
        if BATCH_SIZE <= 0:
            config_valid = False
            config_issues.append("Invalid batch size")
        if CHUNK_SIZE <= 0:
            config_valid = False
            config_issues.append("Invalid chunk size")
        if not CHECKSUM_ALGORITHM in ["sha256", "md5"]:
            config_valid = False
            config_issues.append("Invalid checksum algorithm")
            
        health_report["checks"]["configuration"] = {
            "status": "healthy" if config_valid else "unhealthy",
            "issues": config_issues
        }
        
        # Check 5: Backup file management
        logger.info("Checking backup files...")
        backup_files = []
        if os.path.exists(metadata_csv_path):
            import glob
            backup_pattern = f"{metadata_csv_path}.backup.*"
            backup_files = glob.glob(backup_pattern)
        
        backup_count_ok = len(backup_files) <= MAX_BACKUP_FILES * 2  # Allow some buffer
        
        health_report["checks"]["backups"] = {
            "status": "healthy" if backup_count_ok else "warning",
            "backup_count": len(backup_files),
            "max_allowed": MAX_BACKUP_FILES
        }
        
        # Generate overall status
        check_statuses = [check["status"] for check in health_report["checks"].values()]
        if all(status == "healthy" for status in check_statuses):
            health_report["overall_status"] = "healthy"
        elif any(status == "unhealthy" for status in check_statuses):
            health_report["overall_status"] = "unhealthy"
        else:
            health_report["overall_status"] = "warning"
        
        # Generate recommendations
        if not vector_store_healthy:
            health_report["recommendations"].append("Check vector store configuration and connectivity")
        if not metadata_exists or not metadata_readable:
            health_report["recommendations"].append("Recreate or repair metadata file")
        if not memory_ok:
            health_report["recommendations"].append("Reduce batch size or free up system memory")
        if not disk_ok:
            health_report["recommendations"].append("Free up disk space")
        if not config_valid:
            health_report["recommendations"].append("Review and fix configuration parameters")
        if not backup_count_ok:
            health_report["recommendations"].append("Clean up old backup files")
            
        logger.info(f"System health check completed: {health_report['overall_status']}")
        return health_report
        
    except Exception as e:
        health_report["overall_status"] = "error"
        health_report["errors"].append(f"Health check failed: {e}")
        logger.error(f"System health check failed: {e}")
        return health_report


