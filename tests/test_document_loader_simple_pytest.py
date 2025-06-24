#!/usr/bin/env python3
"""
Simple pytest test suite for the DocumentLoader service.

This test script verifies basic functionality of the document loader
without complex imports or circular dependencies.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

def test_document_loader_imports():
    """Test that we can import the document loader module."""
    print("Testing document loader imports...")
    
    # Add the backend directory to the path
    backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    # Test basic langchain import
    from langchain.schema.document import Document
    print("✓ Langchain Document import successful")
    
    # Test document loader service import
    from lets_talk.core.pipeline.services.document_loader import DocumentLoader
    print("✓ DocumentLoader class import successful")
    
    from lets_talk.core.pipeline.services.document_loader import DocumentStats
    print("✓ DocumentStats class import successful")
    
    from lets_talk.core.pipeline.services.document_loader import load_blog_posts
    print("✓ load_blog_posts function import successful")
    
    assert True  # All imports successful


def test_document_loader_creation():
    """Test creating a DocumentLoader instance."""
    print("Testing DocumentLoader instantiation...")
    
    # Add the backend directory to the path
    backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    from lets_talk.core.pipeline.services.document_loader import DocumentLoader
    
    # Create a temporary directory for testing
    test_dir = tempfile.mkdtemp()
    
    try:
        # Create DocumentLoader instance
        loader = DocumentLoader(
            data_dir=test_dir,
            data_dir_pattern="*.md",
            blog_base_url="https://example.com/blog/",
            base_url="https://example.com",
            index_only_published_posts=False
        )
        
        print("✓ DocumentLoader instance created successfully")
        print(f"  - data_dir: {loader.data_dir}")
        print(f"  - blog_base_url: {loader.blog_base_url}")
        print(f"  - base_url: {loader.base_url}")
        
        assert loader.data_dir == test_dir
        assert loader.blog_base_url == "https://example.com/blog/"
        assert loader.base_url == "https://example.com"
        
    finally:
        # Clean up
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)


def test_document_processing_with_real_data():
    """Test document processing with actual data from the workspace."""
    print("Testing document processing with real data...")
    
    # Add the backend directory to the path
    backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    from lets_talk.core.pipeline.services.document_loader import load_blog_posts
    
    # Use the actual data directory from the workspace
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    if os.path.exists(data_dir):
        print(f"Found data directory: {data_dir}")
        
        # Load documents
        documents = load_blog_posts(
            data_dir=data_dir,
            data_dir_pattern="*.md",
            blog_base_url="https://example.com/blog/",
            base_url="https://example.com",
            recursive=True,
            show_progress=False
        )
        
        print(f"✓ Loaded {len(documents)} documents")
        
        assert isinstance(documents, list)
        
        if documents:
            print("Document details:")
            for i, doc in enumerate(documents[:3]):  # Show first 3 documents
                print(f"  Document {i+1}:")
                print(f"    - Title: {doc.metadata.get('post_title', 'N/A')}")
                print(f"    - URL: {doc.metadata.get('url', 'N/A')}")
                print(f"    - Content length: {len(doc.page_content)}")
                print(f"    - Published: {doc.metadata.get('published', 'N/A')}")
            if len(documents) > 3:
                print(f"    ... and {len(documents) - 3} more documents")
        
            # Validate first document
            assert hasattr(documents[0], 'page_content')
            assert hasattr(documents[0], 'metadata')
            assert isinstance(documents[0].metadata, dict)
    else:
        pytest.skip(f"Data directory not found: {data_dir}")


def test_document_stats():
    """Test document statistics calculation."""
    print("Testing document statistics...")
    
    # Add the backend directory to the path
    backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    from langchain.schema.document import Document
    from lets_talk.core.pipeline.services.document_loader import DocumentStats
    
    # Create test documents
    test_docs = [
        Document(
            page_content="Short test content",
            metadata={
                "post_title": "Test Post 1",
                "url": "https://example.com/post1",
                "content_length": 18,
                "published": True
            }
        ),
        Document(
            page_content="This is a longer test content with more text to test statistics",
            metadata={
                "post_title": "Test Post 2",
                "url": "https://example.com/post2",
                "content_length": 63,  # Actual length
                "published": False
            }
        )
    ]
    
    # Calculate statistics
    stats = DocumentStats.calculate_stats(test_docs)
    
    print("✓ Statistics calculated successfully")
    print(f"  - Total documents: {stats['total_documents']}")
    print(f"  - Total characters: {stats['total_characters']}")
    print(f"  - Min length: {stats['min_length']}")
    print(f"  - Max length: {stats['max_length']}")
    print(f"  - Average length: {stats['avg_length']:.2f}")
    
    assert stats['total_documents'] == 2
    assert stats['total_characters'] == 81  # 18 + 63
    assert stats['min_length'] == 18
    assert stats['max_length'] == 63
    assert stats['avg_length'] == 40.5
    
    # Test empty list
    empty_stats = DocumentStats.calculate_stats([])
    print(f"✓ Empty stats handling: {empty_stats['total_documents']} documents")
    
    assert empty_stats['total_documents'] == 0


if __name__ == "__main__":
    # Run with pytest when executed directly
    pytest.main([__file__, "-v"])
