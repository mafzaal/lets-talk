#!/usr/bin/env python3
"""
Pytest test suite for the DocumentLoader service.

This test script covers:
- Document loading functionality
- Frontmatter parsing
- Metadata extraction
- URL generation
- Statistics calculation
- Published/unpublished filtering
"""

import os
import sys
import shutil
import tempfile
import pytest
from pathlib import Path
from typing import Dict, List


# Import langchain Document first
from langchain.schema.document import Document


# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


# Then import document loader components
document_loader_module = None
try:
    from lets_talk.core.pipeline.services import document_loader as document_loader_module
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"Failed to import document_loader module: {e}")
    IMPORT_SUCCESS = False

from lets_talk.core.pipeline.services.document_loader import DocumentLoader, DocumentStats, display_document_stats, get_document_stats, load_blog_posts


@pytest.fixture
def test_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def blog_urls():
    """Provide test URLs."""
    return {
        "blog_base_url": "https://example.com/blog/",
        "base_url": "https://example.com"
    }


@pytest.fixture
def document_loader(test_dir, blog_urls):
    """Create a DocumentLoader instance for testing."""
    _create_test_documents(test_dir)
    
    return DocumentLoader(
        data_dir=test_dir,
        data_dir_pattern="*.md",
        blog_base_url=blog_urls["blog_base_url"],
        base_url=blog_urls["base_url"],
        index_only_published_posts=False
    )


def _create_test_documents(test_dir):
    """Create test markdown documents with various frontmatter configurations."""
    
    # Test document 1: Complete frontmatter
    test_post_1_dir = Path(test_dir) / "test-post-1"
    test_post_1_dir.mkdir(parents=True, exist_ok=True)
    
    test_post_1_content = """---
title: "Test Post 1: Complete Frontmatter"
date: 2025-06-23T10:00:00-06:00
description: "A test post with complete frontmatter"
categories: ["AI", "Testing", "Documentation"]
coverImage: "images/test-cover.jpg"
youTubeVideoId: "dQw4w9WgXcQ"
published: true
readingTime: "5 min"
---

# Test Post 1

This is a test post with complete frontmatter to test the document loader functionality.

## Content Section

Some meaningful content here to test content length calculation.
"""
    
    with open(test_post_1_dir / "index.md", "w") as f:
        f.write(test_post_1_content)
    
    # Test document 2: Minimal frontmatter
    test_post_2_dir = Path(test_dir) / "test-post-2"
    test_post_2_dir.mkdir(parents=True, exist_ok=True)
    
    test_post_2_content = """---
title: "Test Post 2: Minimal Frontmatter"
published: false
---

# Test Post 2

This is a test post with minimal frontmatter.
"""
    
    with open(test_post_2_dir / "index.md", "w") as f:
        f.write(test_post_2_content)
    
    # Test document 3: No frontmatter
    test_post_3_dir = Path(test_dir) / "test-post-3"
    test_post_3_dir.mkdir(parents=True, exist_ok=True)
    
    test_post_3_content = """# Test Post 3

This is a test post without any frontmatter to test default behavior.

## Some Content

Testing content without frontmatter parsing.
"""
    
    with open(test_post_3_dir / "index.md", "w") as f:
        f.write(test_post_3_content)
    
    # Test document 4: Invalid frontmatter
    test_post_4_dir = Path(test_dir) / "test-post-4"
    test_post_4_dir.mkdir(parents=True, exist_ok=True)
    
    test_post_4_content = """---
title: "Test Post 4: Invalid Frontmatter
description: Missing closing quote
categories: [AI, Testing
---

# Test Post 4

This post has invalid frontmatter to test error handling.
"""
    
    with open(test_post_4_dir / "index.md", "w") as f:
        f.write(test_post_4_content)


# DocumentLoader Tests

def test_load_documents_basic(document_loader):
    """Test basic document loading functionality."""
    documents = document_loader.load_documents(recursive=True, show_progress=False)
    
    # Should load all 4 test documents
    assert len(documents) == 4
    
    # Check that all documents are Document instances
    for doc in documents:
        assert isinstance(doc, Document)
        assert isinstance(doc.page_content, str)
        assert isinstance(doc.metadata, dict)


def test_url_generation(document_loader):
    """Test URL generation from source paths."""
    documents = document_loader.load_documents(recursive=True, show_progress=False)
    
    for doc in documents:
        # Should have a URL in metadata
        assert "url" in doc.metadata
        
        # URL should start with blog base URL
        assert doc.metadata["url"].startswith(document_loader.blog_base_url)
        
        # URL should not end with index.md or .md
        assert not doc.metadata["url"].endswith("index.md")
        assert not doc.metadata["url"].endswith(".md")


def test_metadata_extraction(document_loader):
    """Test metadata extraction and processing."""
    documents = document_loader.load_documents(recursive=True, show_progress=False)
    
    # Find the complete frontmatter document
    complete_doc = None
    for doc in documents:
        if "test-post-1" in doc.metadata.get("source", ""):
            complete_doc = doc
            break
    
    assert complete_doc is not None
    
    # Check basic metadata
    assert "post_slug" in complete_doc.metadata
    assert complete_doc.metadata["post_slug"] == "test-post-1"
    
    assert "content_length" in complete_doc.metadata
    assert complete_doc.metadata["content_length"] > 0
    
    # Check frontmatter parsing
    assert complete_doc.metadata["post_title"] == "Test Post 1: Complete Frontmatter"
    # The frontmatter parser may convert datetime format
    assert "2025-06-23" in complete_doc.metadata["date"]
    assert "10:00:00" in complete_doc.metadata["date"] 
    assert complete_doc.metadata["description"] == "A test post with complete frontmatter"
    assert complete_doc.metadata["categories"] == ["AI", "Testing", "Documentation"]
    assert complete_doc.metadata["published"] is True
    assert complete_doc.metadata["reading_time"] == "5 min"


def test_media_url_processing(document_loader, blog_urls):
    """Test media URL processing (cover images and videos)."""
    documents = document_loader.load_documents(recursive=True, show_progress=False)
    
    # Find the complete frontmatter document
    complete_doc = None
    for doc in documents:
        if "test-post-1" in doc.metadata.get("source", ""):
            complete_doc = doc
            break
    
    assert complete_doc is not None
    
    # Check cover image URL processing
    assert "cover_image" in complete_doc.metadata
    expected_image_url = f"{blog_urls['base_url'].rstrip('/')}/images/test-cover.jpg"
    assert complete_doc.metadata["cover_image"] == expected_image_url
    
    # Check YouTube video URL processing
    assert "cover_video" in complete_doc.metadata
    expected_video_url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
    assert complete_doc.metadata["cover_video"] == expected_video_url


def test_default_title_generation(document_loader):
    """Test default title generation for documents without titles."""
    documents = document_loader.load_documents(recursive=True, show_progress=False)
    
    # Find the no-frontmatter document
    no_frontmatter_doc = None
    for doc in documents:
        if "test-post-3" in doc.metadata.get("source", ""):
            no_frontmatter_doc = doc
            break
    
    assert no_frontmatter_doc is not None
    
    # Should have a default title based on directory name
    assert no_frontmatter_doc.metadata["post_title"] == "Test Post 3"


def test_published_filtering(test_dir, blog_urls):
    """Test filtering of published vs unpublished documents."""
    _create_test_documents(test_dir)
    
    # Test with published-only filtering enabled
    published_loader = DocumentLoader(
        data_dir=test_dir,
        data_dir_pattern="*.md",
        blog_base_url=blog_urls["blog_base_url"],
        base_url=blog_urls["base_url"],
        index_only_published_posts=True
    )
    
    published_docs = published_loader.load_documents(recursive=True, show_progress=False)
    
    # Should have fewer documents (test-post-2 is unpublished)
    assert len(published_docs) < 4
    
    # All returned documents should be published
    for doc in published_docs:
        # Default to True if not specified, so check explicit False
        if "published" in doc.metadata:
            assert doc.metadata["published"] is not False


def test_error_handling(document_loader):
    """Test error handling for invalid frontmatter."""
    documents = document_loader.load_documents(recursive=True, show_progress=False)
    
    # Should still load all documents even with invalid frontmatter
    assert len(documents) == 4
    
    # Find the invalid frontmatter document
    invalid_doc = None
    for doc in documents:
        if "test-post-4" in doc.metadata.get("source", ""):
            invalid_doc = doc
            break
    
    assert invalid_doc is not None
    
    # Should have default title even with invalid frontmatter
    assert invalid_doc.metadata["post_title"] == "Test Post 4"


# DocumentStats Tests

@pytest.fixture
def sample_documents():
    """Create sample documents for statistics testing."""
    return [
        Document(
            page_content="Short content",
            metadata={
                "url": "https://example.com/post1",
                "source": "/test/post1/index.md",
                "post_title": "Test Post 1",
                "content_length": 13,
                "date": "2025-06-23",
                "categories": ["AI"],
                "published": True
            }
        ),
        Document(
            page_content="This is much longer content with more text",
            metadata={
                "url": "https://example.com/post2",
                "source": "/test/post2/index.md",
                "post_title": "Test Post 2",
                "content_length": 42,
                "date": "2025-06-22",
                "categories": ["Testing", "Documentation"],
                "published": False
            }
        )
    ]


def test_calculate_stats_basic(sample_documents):
    """Test basic statistics calculation."""
    stats = DocumentStats.calculate_stats(sample_documents)
    
    assert stats["total_documents"] == 2
    assert stats["total_characters"] == 55  # 13 + 42
    assert stats["min_length"] == 13
    assert stats["max_length"] == 42
    assert stats["avg_length"] == 27.5
    
    # Check document info
    assert len(stats["documents"]) == 2
    assert stats["documents"][0]["title"] == "Test Post 1"
    assert stats["documents"][1]["title"] == "Test Post 2"


def test_calculate_stats_empty():
    """Test statistics calculation with empty document list."""
    stats = DocumentStats.calculate_stats([])
    
    assert stats["total_documents"] == 0
    assert stats["total_characters"] == 0
    assert stats["min_length"] == 0
    assert stats["max_length"] == 0
    assert stats["avg_length"] == 0
    assert len(stats["documents"]) == 0


def test_display_stats(sample_documents):
    """Test statistics display functionality."""
    stats = DocumentStats.calculate_stats(sample_documents)
    
    # This should not raise any exceptions
    DocumentStats.display_stats(stats)


# Convenience Functions Tests

def test_load_blog_posts_integration():
    """Test the load_blog_posts convenience function."""
    # Use the existing test data directory
    test_data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    if os.path.exists(test_data_dir):
        documents = load_blog_posts(
            data_dir=test_data_dir,
            data_dir_pattern="*.md",
            blog_base_url="https://example.com/blog/",
            base_url="https://example.com",
            recursive=True,
            show_progress=False
        )
        
        # Should load some documents
        assert isinstance(documents, list)
        
        if documents:  # Only test if documents were loaded
            assert isinstance(documents[0], Document)


def test_get_document_stats_function():
    """Test the get_document_stats convenience function."""
    document = Document(
        page_content="Test content",
        metadata={"post_title": "Test", "content_length": 12}
    )
    
    stats = get_document_stats([document])
    
    assert isinstance(stats, dict)
    assert stats["total_documents"] == 1
    assert stats["total_characters"] == 12


def test_display_document_stats_function():
    """Test the display_document_stats convenience function."""
    stats = {
        "total_documents": 1, 
        "total_characters": 10, 
        "min_length": 10,
        "max_length": 10, 
        "avg_length": 10.0, 
        "documents": []
    }
    
    # Should not raise any exceptions
    display_document_stats(stats)


if __name__ == "__main__":
    # Run with pytest when executed directly
    pytest.main([__file__, "-v"])
