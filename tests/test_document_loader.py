#!/usr/bin/env python3
"""
Test script for the DocumentLoader service.

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
import tempfile
import unittest
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

class TestDocumentLoader(unittest.TestCase):
    """Test cases for DocumentLoader class."""
    
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
        
        # Test document 1: Complete frontmatter
        test_post_1_dir = Path(self.test_dir) / "test-post-1"
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
        test_post_2_dir = Path(self.test_dir) / "test-post-2"
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
        test_post_3_dir = Path(self.test_dir) / "test-post-3"
        test_post_3_dir.mkdir(parents=True, exist_ok=True)
        
        test_post_3_content = """# Test Post 3

This is a test post without any frontmatter to test default behavior.

## Some Content

Testing content without frontmatter parsing.
"""
        
        with open(test_post_3_dir / "index.md", "w") as f:
            f.write(test_post_3_content)
        
        # Test document 4: Invalid frontmatter
        test_post_4_dir = Path(self.test_dir) / "test-post-4"
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
    
    def test_load_documents_basic(self):
        """Test basic document loading functionality."""
        documents = self.loader.load_documents(recursive=True, show_progress=False)
        
        # Should load all 4 test documents
        self.assertEqual(len(documents), 4)
        
        # Check that all documents are Document instances
        for doc in documents:
            self.assertIsInstance(doc, Document)
            self.assertIsInstance(doc.page_content, str)
            self.assertIsInstance(doc.metadata, dict)
    
    def test_url_generation(self):
        """Test URL generation from source paths."""
        documents = self.loader.load_documents(recursive=True, show_progress=False)
        
        for doc in documents:
            # Should have a URL in metadata
            self.assertIn("url", doc.metadata)
            
            # URL should start with blog base URL
            self.assertTrue(doc.metadata["url"].startswith(self.blog_base_url))
            
            # URL should not end with index.md or .md
            self.assertFalse(doc.metadata["url"].endswith("index.md"))
            self.assertFalse(doc.metadata["url"].endswith(".md"))
    
    def test_metadata_extraction(self):
        """Test metadata extraction and processing."""
        documents = self.loader.load_documents(recursive=True, show_progress=False)
        
        # Find the complete frontmatter document
        complete_doc = None
        for doc in documents:
            if "test-post-1" in doc.metadata.get("source", ""):
                complete_doc = doc
                break
        
        self.assertIsNotNone(complete_doc)
        assert complete_doc is not None  # Type hint for static analysis
        
        # Check basic metadata
        self.assertIn("post_slug", complete_doc.metadata)
        self.assertEqual(complete_doc.metadata["post_slug"], "test-post-1")
        
        self.assertIn("content_length", complete_doc.metadata)
        self.assertGreater(complete_doc.metadata["content_length"], 0)
        
        # Check frontmatter parsing
        self.assertEqual(complete_doc.metadata["post_title"], "Test Post 1: Complete Frontmatter")
        self.assertEqual(complete_doc.metadata["date"], "2025-06-23T10:00:00-06:00")
        self.assertEqual(complete_doc.metadata["description"], "A test post with complete frontmatter")
        self.assertEqual(complete_doc.metadata["categories"], ["AI", "Testing", "Documentation"])
        self.assertTrue(complete_doc.metadata["published"])
        self.assertEqual(complete_doc.metadata["reading_time"], "5 min")
    
    def test_media_url_processing(self):
        """Test media URL processing (cover images and videos)."""
        documents = self.loader.load_documents(recursive=True, show_progress=False)
        
        # Find the complete frontmatter document
        complete_doc = None
        for doc in documents:
            if "test-post-1" in doc.metadata.get("source", ""):
                complete_doc = doc
                break
        
        self.assertIsNotNone(complete_doc)
        assert complete_doc is not None  # Type hint for static analysis
        
        # Check cover image URL processing
        self.assertIn("cover_image", complete_doc.metadata)
        expected_image_url = f"{self.base_url.rstrip('/')}/images/test-cover.jpg"
        self.assertEqual(complete_doc.metadata["cover_image"], expected_image_url)
        
        # Check YouTube video URL processing
        self.assertIn("cover_video", complete_doc.metadata)
        expected_video_url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        self.assertEqual(complete_doc.metadata["cover_video"], expected_video_url)
    
    def test_default_title_generation(self):
        """Test default title generation for documents without titles."""
        documents = self.loader.load_documents(recursive=True, show_progress=False)
        
        # Find the no-frontmatter document
        no_frontmatter_doc = None
        for doc in documents:
            if "test-post-3" in doc.metadata.get("source", ""):
                no_frontmatter_doc = doc
                break
        
        self.assertIsNotNone(no_frontmatter_doc)
        assert no_frontmatter_doc is not None  # Type hint for static analysis
        
        # Should have a default title based on directory name
        self.assertEqual(no_frontmatter_doc.metadata["post_title"], "Test Post 3")
    
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
        
        published_docs = published_loader.load_documents(recursive=True, show_progress=False)
        
        # Should have fewer documents (test-post-2 is unpublished)
        self.assertLess(len(published_docs), 4)
        
        # All returned documents should be published
        for doc in published_docs:
            # Default to True if not specified, so check explicit False
            if "published" in doc.metadata:
                self.assertNotEqual(doc.metadata["published"], False)
    
    def test_error_handling(self):
        """Test error handling for invalid frontmatter."""
        documents = self.loader.load_documents(recursive=True, show_progress=False)
        
        # Should still load all documents even with invalid frontmatter
        self.assertEqual(len(documents), 4)
        
        # Find the invalid frontmatter document
        invalid_doc = None
        for doc in documents:
            if "test-post-4" in doc.metadata.get("source", ""):
                invalid_doc = doc
                break
        
        self.assertIsNotNone(invalid_doc)
        assert invalid_doc is not None  # Type hint for static analysis
        
        # Should have default title even with invalid frontmatter
        self.assertEqual(invalid_doc.metadata["post_title"], "Test Post 4")


class TestDocumentStats(unittest.TestCase):
    """Test cases for DocumentStats class."""
    
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
    
    def test_calculate_stats_basic(self):
        """Test basic statistics calculation."""
        stats = DocumentStats.calculate_stats(self.documents)
        
        self.assertEqual(stats["total_documents"], 2)
        self.assertEqual(stats["total_characters"], 55)  # 13 + 42
        self.assertEqual(stats["min_length"], 13)
        self.assertEqual(stats["max_length"], 42)
        self.assertEqual(stats["avg_length"], 27.5)
        
        # Check document info
        self.assertEqual(len(stats["documents"]), 2)
        self.assertEqual(stats["documents"][0]["title"], "Test Post 1")
        self.assertEqual(stats["documents"][1]["title"], "Test Post 2")
    
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
    
    def test_load_blog_posts_integration(self):
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
            self.assertIsInstance(documents, list)
            
            if documents:  # Only test if documents were loaded
                self.assertIsInstance(documents[0], Document)
    
    def test_get_document_stats_function(self):
        """Test the get_document_stats convenience function."""
        document = Document(
            page_content="Test content",
            metadata={"post_title": "Test", "content_length": 12}
        )
        
        stats = get_document_stats([document])
        
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats["total_documents"], 1)
        self.assertEqual(stats["total_characters"], 12)
    
    def test_display_document_stats_function(self):
        """Test the display_document_stats convenience function."""
        stats = {"total_documents": 1, "total_characters": 10, "min_length": 10, 
                "max_length": 10, "avg_length": 10.0, "documents": []}
        
        # Should not raise any exceptions
        try:
            display_document_stats(stats)
        except Exception as e:
            self.fail(f"display_document_stats raised an exception: {e}")


def run_tests():
    """Run all tests and display results."""
    print("=" * 60)
    print("DOCUMENT LOADER TEST SUITE")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDocumentLoader))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDocumentStats))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestConvenienceFunctions))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 All tests passed!")
        return True
    else:
        print("\n❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
