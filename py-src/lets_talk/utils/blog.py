"""
Blog Data Utilities Module

This module contains utility functions for loading, processing, and storing blog posts
for the RAG system. It includes functions for loading blog posts from the data directory,
processing their metadata, and creating vector embeddings.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_community.document_loaders.text import TextLoader
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient


from lets_talk.config import (
    DATA_DIR,
    VECTOR_STORAGE_PATH,
    EMBEDDING_MODEL,
    QDRANT_COLLECTION,
    BLOG_BASE_URL,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)

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
        loader_cls=TextLoader
        
    )
    
    documents = text_loader.load()
    print(f"Loaded {len(documents)} documents from {data_dir}")
    return documents


def update_document_metadata(documents: List[Document], 
                           data_dir_prefix: str = DATA_DIR,
                           blog_base_url: str = BLOG_BASE_URL,
                           remove_suffix: str = "index.md") -> List[Document]:
    """
    Update the metadata of documents to include URL and other information.
    
    Args:
        documents: List of Document objects to update
        data_dir_prefix: Prefix to replace in source paths
        blog_base_url: Base URL for the blog posts
        remove_suffix: Suffix to remove from paths (like index.md)
        
    Returns:
        Updated list of Document objects
    """
    for doc in documents:
        # Create URL from source path
        doc.metadata["url"] = doc.metadata["source"].replace(data_dir_prefix, blog_base_url)
        
        # Remove index.md or other suffix if present
        if remove_suffix and doc.metadata["url"].endswith(remove_suffix):
            doc.metadata["url"] = doc.metadata["url"][:-len(remove_suffix)]
            
        # Extract post title from the directory structure
        path_parts = Path(doc.metadata["source"]).parts
        if len(path_parts) > 1:
            # Use the directory name as post_slug
            doc.metadata["post_slug"] = path_parts[-2]
            try:
                #extract title from `doc.page_content`'s front matter like `title:`
                doc.metadata["post_title"] = doc.page_content.split("title:")[1].split("\n")[0].strip()
            except Exception as e:
                doc.metadata["post_title"] = path_parts[-2].replace("-", " ").title()

        # Add document length as metadata
        doc.metadata["content_length"] = len(doc.page_content)
    
    return documents


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
    
    # For use in notebooks where pandas and display are available:
    try:
        import pandas as pd
        from IPython.display import display
        if stats["documents"]:
            df = pd.DataFrame(stats["documents"])
            display(df)
    except (ImportError, NameError):
        # Just print the first 5 documents if not in a notebook environment
        if stats["documents"]:
            print("\nFirst 5 documents:")
            for i, doc in enumerate(stats["documents"][:5]):
                print(f"{i+1}. {doc['title']} ({doc['url']})")


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
    
    split_docs = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(split_docs)} chunks")
    return split_docs


def create_vector_store(documents: List[Document], 
                       storage_path: str = VECTOR_STORAGE_PATH,
                       collection_name: str = QDRANT_COLLECTION,
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

    vector_store = QdrantVectorStore.from_documents(
        documents,
        embedding=HuggingFaceEmbeddings(model_name=embedding_model),
        collection_name=collection_name,
        path=storage_path,
        force_recreate=force_recreate,
    )
    
    return vector_store


def load_vector_store(storage_path: str = VECTOR_STORAGE_PATH,
                     collection_name: str = QDRANT_COLLECTION,
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
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
    
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
            embedding=embeddings,
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


# Allow script to be run directly if needed
if __name__ == "__main__":
    print("Blog Data Utilities Module")
    print("Available functions:")
    print("- load_blog_posts()")
    print("- update_document_metadata()")
    print("- get_document_stats()")
    print("- display_document_stats()")
    print("- split_documents()")
    print("- create_vector_store()")
    print("- load_vector_store()")
    print("- process_blog_posts()")
