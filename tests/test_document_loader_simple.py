#!/usr/bin/env python3
"""
Simple test script for the DocumentLoader service.

This test script verifies basic functionality of the document loader
without complex imports or circular dependencies.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

def test_document_loader_imports():
    """Test that we can import the document loader module."""
    print("Testing document loader imports...")
    
    # Add the backend directory to the path
    backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    try:
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
        
        return True, None
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False, str(e)


def test_document_loader_creation():
    """Test creating a DocumentLoader instance."""
    print("Testing DocumentLoader instantiation...")
    
    try:
        # Add the backend directory to the path
        backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        from lets_talk.core.pipeline.services.document_loader import DocumentLoader
        
        # Create a temporary directory for testing
        test_dir = tempfile.mkdtemp()
        
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
        
        # Clean up
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
        
        return True, None
        
    except Exception as e:
        print(f"✗ DocumentLoader creation failed: {e}")
        return False, str(e)


def test_document_processing_with_real_data():
    """Test document processing with actual data from the workspace."""
    print("Testing document processing with real data...")
    
    try:
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
            
            return True, None
        else:
            print(f"Data directory not found: {data_dir}")
            return False, "Data directory not found"
            
    except Exception as e:
        print(f"✗ Document processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


def test_document_stats():
    """Test document statistics calculation."""
    print("Testing document statistics...")
    
    try:
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
                    "content_length": 64,
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
        
        # Test empty list
        empty_stats = DocumentStats.calculate_stats([])
        print(f"✓ Empty stats handling: {empty_stats['total_documents']} documents")
        
        return True, None
        
    except Exception as e:
        print(f"✗ Statistics test failed: {e}")
        return False, str(e)


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("DOCUMENT LOADER SIMPLE TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_document_loader_imports),
        ("Creation Test", test_document_loader_creation),
        ("Real Data Test", test_document_processing_with_real_data),
        ("Statistics Test", test_document_stats),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        print("-" * 40)
        
        success, error = test_func()
        results.append((test_name, success, error))
        
        if success:
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED: {error}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed:")
        for test_name, success, error in results:
            if not success:
                print(f"  - {test_name}: {error}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
