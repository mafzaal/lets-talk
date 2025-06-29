#!/usr/bin/env python3
"""
Comprehensive pytest test suite for the DocumentLoader service.

This test suite uses pytest and covers:
- Document loading functionality
- Frontmatter parsing with various data types
- Metadata extraction and URL generation
- Statistics calculation
- Published/unpublished filtering
- Error handling for malformed content
"""

import os
import sys
import shutil
import tempfile
import pytest
from pathlib import Path
from typing import Dict, List

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import required modules
from langchain.schema.document import Document
from lets_talk.core.pipeline.services.document_loader import (
    DocumentLoader,
    DocumentStats,
    load_blog_posts,
    get_document_stats,
    display_document_stats
)


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
def comprehensive_loader(test_dir, blog_urls):
    """Create a DocumentLoader instance with comprehensive test documents."""
    _create_comprehensive_test_documents(test_dir)
    
    return DocumentLoader(
        data_dir=test_dir,
        data_dir_pattern="*.md",
        blog_base_url=blog_urls["blog_base_url"],
        base_url=blog_urls["base_url"],
        index_only_published_posts=False
    )


def _create_comprehensive_test_documents(test_dir):
    """Create comprehensive test markdown documents with various frontmatter configurations."""
    
    # Test document 1: Complete frontmatter with all data types
    test_post_1_dir = Path(test_dir) / "complete-frontmatter"
    test_post_1_dir.mkdir(parents=True, exist_ok=True)
    
    test_post_1_content = """---
title: "Complete Frontmatter Test"
date: 2025-06-23T10:00:00-06:00
description: "A test post with complete frontmatter"
categories: ["AI", "Testing", "Documentation"]
coverImage: "images/test-cover.jpg"
youTubeVideoId: "dQw4w9WgXcQ"
published: true
readingTime: "5 min"
---

# Complete Frontmatter Test

This test document has complete frontmatter with all supported fields.

## Content

Some meaningful content to test processing.
"""
    
    with open(test_post_1_dir / "index.md", "w") as f:
        f.write(test_post_1_content)
    
    # Test document 2: Boolean published field
    test_post_2_dir = Path(test_dir) / "boolean-published"
    test_post_2_dir.mkdir(parents=True, exist_ok=True)
    
    test_post_2_content = """---
title: "Boolean Published Test"
published: false
categories:
  - Testing
  - Validation
---

# Boolean Published Test

This document has a boolean published field set to false.
"""
    
    with open(test_post_2_dir / "index.md", "w") as f:
        f.write(test_post_2_content)
    
    # Test document 3: No frontmatter
    test_post_3_dir = Path(test_dir) / "no-frontmatter"
    test_post_3_dir.mkdir(parents=True, exist_ok=True)
    
    test_post_3_content = """# No Frontmatter Test

This document has no frontmatter to test default behavior.
"""
    
    with open(test_post_3_dir / "index.md", "w") as f:
        f.write(test_post_3_content)
    
    # Test document 4: Mixed data types
    test_post_4_dir = Path(test_dir) / "mixed-types"
    test_post_4_dir.mkdir(parents=True, exist_ok=True)
    
    test_post_4_content = """---
title: "Mixed Data Types Test"
date: 2025-06-23
description: "Testing mixed data types in frontmatter"
categories: "AI, Machine Learning, Testing"
published: "true"
readingTime: 3
coverVideo: "https://example.com/video.mp4"
---

# Mixed Data Types Test

This document tests handling of mixed data types in frontmatter.
"""
    
    with open(test_post_4_dir / "index.md", "w") as f:
        f.write(test_post_4_content)


# Comprehensive DocumentLoader Core Tests

def test_document_loading_basic(comprehensive_loader):
    """Test basic document loading functionality."""
    documents = comprehensive_loader.load_documents(recursive=True, show_progress=False)
    
    # Should load all 4 test documents
    assert len(documents) == 4
    
    # Check that all documents are Document instances
    for doc in documents:
        assert isinstance(doc, Document)


def test_url_generation(comprehensive_loader):
    """Test URL generation from source paths."""
    documents = comprehensive_loader.load_documents(recursive=True, show_progress=False)
    
    for doc in documents:
        assert "url" in doc.metadata
        assert doc.metadata["url"].startswith(comprehensive_loader.blog_base_url)


def test_frontmatter_parsing_complete(comprehensive_loader, blog_urls):
    """Test parsing of complete frontmatter."""
    documents = comprehensive_loader.load_documents(recursive=True, show_progress=False)
    
    # Find the complete frontmatter document
    complete_doc = next(
        (doc for doc in documents if "complete-frontmatter" in doc.metadata.get("source", "")),
        None
    )
    
    assert complete_doc is not None
    
    # Check all frontmatter fields
    assert complete_doc.metadata["post_title"] == "Complete Frontmatter Test"
    # Note: The frontmatter parser may convert 'T' to space in datetime
    assert "2025-06-23" in complete_doc.metadata["date"]
    assert complete_doc.metadata["description"] == "A test post with complete frontmatter"
    assert complete_doc.metadata["categories"] == ["AI", "Testing", "Documentation"]
    assert complete_doc.metadata["published"] is True
    assert complete_doc.metadata["reading_time"] == "5 min"
    
    # Check media URL processing
    expected_image_url = f"{blog_urls['base_url'].rstrip('/')}/images/test-cover.jpg"
    assert complete_doc.metadata["cover_image"] == expected_image_url
    
    expected_video_url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
    assert complete_doc.metadata["cover_video"] == expected_video_url


def test_frontmatter_parsing_boolean_published(comprehensive_loader):
    """Test parsing of boolean published field."""
    documents = comprehensive_loader.load_documents(recursive=True, show_progress=False)
    
    # Find the boolean published document
    boolean_doc = next(
        (doc for doc in documents if "boolean-published" in doc.metadata.get("source", "")),
        None
    )
    
    assert boolean_doc is not None
    
    # Check boolean published field
    assert boolean_doc.metadata["published"] is False
    
    # Check list categories
    assert boolean_doc.metadata["categories"] == ["Testing", "Validation"]


def test_frontmatter_parsing_mixed_types(comprehensive_loader):
    """Test parsing of mixed data types in frontmatter."""
    documents = comprehensive_loader.load_documents(recursive=True, show_progress=False)
    
    # Find the mixed types document
    mixed_doc = next(
        (doc for doc in documents if "mixed-types" in doc.metadata.get("source", "")),
        None
    )
    
    assert mixed_doc is not None
    
    # Check string published field converted to boolean
    assert mixed_doc.metadata["published"] is True
    
    # Check string categories converted to list
    assert mixed_doc.metadata["categories"] == ["AI", "Machine Learning", "Testing"]
    
    # Check numeric reading time converted to string
    assert mixed_doc.metadata["reading_time"] == "3"


def test_default_title_generation(comprehensive_loader):
    """Test default title generation for documents without titles."""
    documents = comprehensive_loader.load_documents(recursive=True, show_progress=False)
    
    # Find the no frontmatter document
    no_frontmatter_doc = next(
        (doc for doc in documents if "no-frontmatter" in doc.metadata.get("source", "")),
        None
    )
    
    assert no_frontmatter_doc is not None
    # Should have a default title based on directory name
    assert "No Frontmatter" in no_frontmatter_doc.metadata["post_title"]


def test_published_filtering(test_dir, blog_urls):
    """Test filtering of published vs unpublished documents."""
    _create_comprehensive_test_documents(test_dir)
    
    # Test with published-only filtering enabled
    published_loader = DocumentLoader(
        data_dir=test_dir,
        data_dir_pattern="*.md",
        blog_base_url=blog_urls["blog_base_url"],
        base_url=blog_urls["base_url"],
        index_only_published_posts=True
    )
    
    published_docs = published_loader.load_documents(recursive=True, show_progress=False)
    
    # Should have fewer documents (boolean-published is unpublished)
    assert len(published_docs) < 4
    
    # All returned documents should be published
    for doc in published_docs:
        if "published" in doc.metadata:
            assert doc.metadata["published"] is not False


# DocumentStats Tests

@pytest.fixture
def test_documents():
    """Create test documents for statistics testing."""
    return [
        Document(
            page_content="Short test content",  # 18 characters
            metadata={
                "post_title": "Test Post 1",
                "url": "https://example.com/post1",
                "content_length": 18,
                "published": True
            }
        ),
        Document(
            page_content="This is a longer test content with more text to test statistics",  # 63 characters
            metadata={
                "post_title": "Test Post 2",
                "url": "https://example.com/post2",
                "content_length": 63,
                "published": False
            }
        )
    ]


def test_calculate_stats_basic(test_documents):
    """Test basic statistics calculation."""
    stats = DocumentStats.calculate_stats(test_documents)
    
    assert stats["total_documents"] == 2
    assert stats["total_characters"] == 81  # 18 + 63
    assert stats["min_length"] == 18
    assert stats["max_length"] == 63
    assert stats["avg_length"] == 40.5


def test_calculate_stats_empty():
    """Test statistics calculation with empty document list."""
    stats = DocumentStats.calculate_stats([])
    
    assert stats["total_documents"] == 0
    assert stats["total_characters"] == 0
    assert stats["min_length"] == 0
    assert stats["max_length"] == 0
    assert stats["avg_length"] == 0


def test_display_stats(test_documents):
    """Test statistics display functionality."""
    stats = DocumentStats.calculate_stats(test_documents)
    
    # This should not raise any exceptions
    DocumentStats.display_stats(stats)


# Convenience Functions Tests

def test_get_document_stats_function(test_documents):
    """Test the get_document_stats convenience function."""
    stats = get_document_stats(test_documents)
    
    assert isinstance(stats, dict)
    assert stats["total_documents"] == 2


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


def test_load_blog_posts_integration_with_real_data():
    """Test DocumentLoader with real data from the workspace."""
    # Use the actual data directory from the workspace
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    if os.path.exists(data_dir):
        documents = load_blog_posts(
            data_dir=data_dir,
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
            print(f"Loaded {len(documents)} real documents from workspace")


if __name__ == "__main__":
    # Run with pytest when executed directly
    pytest.main([__file__, "-v"])
