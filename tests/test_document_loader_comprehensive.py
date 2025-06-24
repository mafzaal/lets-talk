#!/usr/bin/env python3
"""
Comprehensive unit tests for the DocumentLoader service.

This test suite uses the standard unittest framework and covers:
- Document loading functionality
- Frontmatter parsing with various data types
- Metadata extraction and URL generation
- Statistics calculation
- Published/unpublished filtering
- Error handling for malformed content
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import required modules
from langchain.schema.document import Document
from lets_talk.core.pipeline.services.document_loader import (
    DocumentLoader,
    DocumentStats,
    load_blog_posts,
    get_document_stats,
    display_document_stats
)


class TestDocumentLoaderCore(unittest.TestCase):
    """Test core DocumentLoader functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.blog_base_url = "https://example.com/blog/"
        self.base_url = "https://example.com"
        
        # Create test documents with different scenarios
        self._create_test_documents()
        
        self.loader = DocumentLoader(
            data_dir=self.test_dir,
            data_dir_pattern="*.md",
            blog_base_url=self.blog_base_url,
            base_url=self.base_url,
            index_only_published_posts=False
        )
    
    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_documents(self):
        """Create test markdown documents with various frontmatter configurations."""
        
        # Test document 1: Complete frontmatter with all data types
        test_post_1_dir = Path(self.test_dir) / "complete-frontmatter"
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
        test_post_2_dir = Path(self.test_dir) / "boolean-published"
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
        test_post_3_dir = Path(self.test_dir) / "no-frontmatter"
        test_post_3_dir.mkdir(parents=True, exist_ok=True)
        
        test_post_3_content = """# No Frontmatter Test

This document has no frontmatter to test default behavior.
"""
        
        with open(test_post_3_dir / "index.md", "w") as f:
            f.write(test_post_3_content)
        
        # Test document 4: Mixed data types
        test_post_4_dir = Path(self.test_dir) / "mixed-types"
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
    
    def test_document_loading_basic(self):
        """Test basic document loading functionality."""
        documents = self.loader.load_documents(recursive=True, show_progress=False)
        
        # Should load all 4 test documents
        self.assertEqual(len(documents), 4)
        
        # Check that all documents are Document instances
        for doc in documents:
            self.assertIsInstance(doc, Document)
            self.assertIsInstance(doc.page_content, str)
            self.assertIsInstance(doc.metadata, dict)
            
            # All documents should have basic metadata
            self.assertIn("url", doc.metadata)
            self.assertIn("post_title", doc.metadata)
            self.assertIn("content_length", doc.metadata)
            self.assertIn("post_slug", doc.metadata)
    
    def test_url_generation(self):
        """Test URL generation from source paths."""
        documents = self.loader.load_documents(recursive=True, show_progress=False)
        
        for doc in documents:
            url = doc.metadata["url"]
            
            # URL should start with blog base URL
            self.assertTrue(url.startswith(self.blog_base_url))
            
            # URL should not end with index.md or .md
            self.assertFalse(url.endswith("index.md"))
            self.assertFalse(url.endswith(".md"))
            
            # URL should contain the post slug
            post_slug = doc.metadata["post_slug"]
            self.assertIn(post_slug, url)
    
    def test_frontmatter_parsing_complete(self):
        """Test parsing of complete frontmatter."""
        documents = self.loader.load_documents(recursive=True, show_progress=False)
        
        # Find the complete frontmatter document
        complete_doc = next(
            (doc for doc in documents if "complete-frontmatter" in doc.metadata.get("source", "")),
            None
        )
        
        self.assertIsNotNone(complete_doc)
        assert complete_doc is not None  # Type hint for mypy
        
        # Check all frontmatter fields
        self.assertEqual(complete_doc.metadata["post_title"], "Complete Frontmatter Test")
        # Note: The frontmatter parser may convert 'T' to space in datetime
        self.assertIn("2025-06-23", complete_doc.metadata["date"])
        self.assertEqual(complete_doc.metadata["description"], "A test post with complete frontmatter")
        self.assertEqual(complete_doc.metadata["categories"], ["AI", "Testing", "Documentation"])
        self.assertTrue(complete_doc.metadata["published"])
        self.assertEqual(complete_doc.metadata["reading_time"], "5 min")
        
        # Check media URL processing
        expected_image_url = f"{self.base_url.rstrip('/')}/images/test-cover.jpg"
        self.assertEqual(complete_doc.metadata["cover_image"], expected_image_url)
        
        expected_video_url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        self.assertEqual(complete_doc.metadata["cover_video"], expected_video_url)
    
    def test_frontmatter_parsing_boolean_published(self):
        """Test parsing of boolean published field."""
        documents = self.loader.load_documents(recursive=True, show_progress=False)
        
        # Find the boolean published document
        boolean_doc = next(
            (doc for doc in documents if "boolean-published" in doc.metadata.get("source", "")),
            None
        )
        
        self.assertIsNotNone(boolean_doc)
        assert boolean_doc is not None  # Type hint for mypy
        
        # Check boolean published field
        self.assertFalse(boolean_doc.metadata["published"])
        
        # Check list categories
        self.assertEqual(boolean_doc.metadata["categories"], ["Testing", "Validation"])
    
    def test_frontmatter_parsing_mixed_types(self):
        """Test parsing of mixed data types in frontmatter."""
        documents = self.loader.load_documents(recursive=True, show_progress=False)
        
        # Find the mixed types document
        mixed_doc = next(
            (doc for doc in documents if "mixed-types" in doc.metadata.get("source", "")),
            None
        )
        
        self.assertIsNotNone(mixed_doc)
        assert mixed_doc is not None  # Type hint for mypy
        
        # Check string published field converted to boolean
        self.assertTrue(mixed_doc.metadata["published"])
        
        # Check string categories converted to list
        self.assertEqual(mixed_doc.metadata["categories"], ["AI", "Machine Learning", "Testing"])
        
        # Check numeric reading time converted to string
        self.assertEqual(mixed_doc.metadata["reading_time"], "3")
    
    def test_default_title_generation(self):
        """Test default title generation for documents without titles."""
        documents = self.loader.load_documents(recursive=True, show_progress=False)
        
        # Find the no frontmatter document
        no_frontmatter_doc = next(
            (doc for doc in documents if "no-frontmatter" in doc.metadata.get("source", "")),
            None
        )
        
        self.assertIsNotNone(no_frontmatter_doc)
        assert no_frontmatter_doc is not None  # Type hint for mypy
        
        # Should have a default title based on directory name
        self.assertEqual(no_frontmatter_doc.metadata["post_title"], "No Frontmatter")
    
    def test_published_filtering(self):
        """Test filtering of published vs unpublished documents."""
        # Test with published-only filtering enabled
        published_loader = DocumentLoader(
            data_dir=self.test_dir,
            data_dir_pattern="*.md",
            blog_base_url=self.blog_base_url,
            base_url=self.base_url,
            index_only_published_posts=True
        )
        
        all_docs = self.loader.load_documents(recursive=True, show_progress=False)
        published_docs = published_loader.load_documents(recursive=True, show_progress=False)
        
        # Should have fewer published documents
        self.assertLess(len(published_docs), len(all_docs))
        
        # All returned documents should be published
        for doc in published_docs:
            self.assertTrue(doc.metadata.get("published", True))


class TestDocumentStats(unittest.TestCase):
    """Test cases for DocumentStats functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock documents
        self.documents = [
            Document(
                page_content="Short content",
                metadata={
                    "url": "https://example.com/post1",
                    "source": "/test/post1/index.md",
                    "post_title": "Test Post 1",
                    "content_length": 13,
                    "date": "2025-06-23",
                    "categories": ["AI"],
                    "published": True,
                    "post_slug": "post1"
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
                    "published": False,
                    "post_slug": "post2"
                }
            )
        ]
    
    def test_calculate_stats_basic(self):
        """Test basic statistics calculation."""
        stats = DocumentStats.calculate_stats(self.documents)
        
        self.assertEqual(stats["total_documents"], 2)
        self.assertEqual(stats["total_characters"], 55)  # 13 + 42
        self.assertEqual(stats["min_length"], 13)
        self.assertEqual(stats["max_length"], 42)
        self.assertEqual(stats["avg_length"], 27.5)
        
        # Check document info structure
        self.assertEqual(len(stats["documents"]), 2)
        self.assertIsInstance(stats["documents"], list)
        
        # Check first document info
        doc1_info = stats["documents"][0]
        self.assertEqual(doc1_info["title"], "Test Post 1")
        self.assertEqual(doc1_info["url"], "https://example.com/post1")
        self.assertEqual(doc1_info["text_length"], 13)
        self.assertTrue(doc1_info["published"])
    
    def test_calculate_stats_empty(self):
        """Test statistics calculation with empty document list."""
        stats = DocumentStats.calculate_stats([])
        
        self.assertEqual(stats["total_documents"], 0)
        self.assertEqual(stats["total_characters"], 0)
        self.assertEqual(stats["min_length"], 0)
        self.assertEqual(stats["max_length"], 0)
        self.assertEqual(stats["avg_length"], 0)
        self.assertEqual(len(stats["documents"]), 0)
    
    def test_display_stats(self):
        """Test statistics display functionality."""
        stats = DocumentStats.calculate_stats(self.documents)
        
        # This should not raise any exceptions
        try:
            DocumentStats.display_stats(stats)
        except Exception as e:
            self.fail(f"display_stats raised an exception: {e}")


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""
    
    def test_get_document_stats_function(self):
        """Test the get_document_stats convenience function."""
        document = Document(
            page_content="Test content",
            metadata={
                "post_title": "Test",
                "content_length": 12,
                "url": "https://example.com/test",
                "published": True
            }
        )
        
        stats = get_document_stats([document])
        
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats["total_documents"], 1)
        self.assertEqual(stats["total_characters"], 12)
    
    def test_display_document_stats_function(self):
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
        try:
            display_document_stats(stats)
        except Exception as e:
            self.fail(f"display_document_stats raised an exception: {e}")


class TestDocumentLoaderWithRealData(unittest.TestCase):
    """Test DocumentLoader with real data from the workspace."""
    
    def test_load_blog_posts_integration(self):
        """Test the load_blog_posts function with real data."""
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
            self.assertIsInstance(documents, list)
            
            if documents:  # Only test if documents were loaded
                # Each document should be a Document instance
                for doc in documents:
                    self.assertIsInstance(doc, Document)
                    self.assertIsInstance(doc.page_content, str)
                    self.assertIsInstance(doc.metadata, dict)
                    
                    # Should have required metadata
                    self.assertIn("url", doc.metadata)
                    self.assertIn("post_title", doc.metadata)
                    self.assertIn("content_length", doc.metadata)
                    
                    # Content length should match actual content
                    self.assertEqual(
                        doc.metadata["content_length"],
                        len(doc.page_content)
                    )


def main():
    """Run all tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDocumentLoaderCore))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDocumentStats))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestConvenienceFunctions))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDocumentLoaderWithRealData))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
