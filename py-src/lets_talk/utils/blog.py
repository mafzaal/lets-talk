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
    CHECKSUM_ALGORITHM
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


