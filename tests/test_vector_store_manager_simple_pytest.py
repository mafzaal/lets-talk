#!/usr/bin/env python3
"""
Simple pytest test suite for the VectorStoreManager service.

This test script covers the core functionality of VectorStoreManager
with basic test cases for initialization and key methods.
"""

import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import test requirements
try:
    from langchain.schema.document import Document
    from lets_talk.core.pipeline.services.vector_store_manager import VectorStoreManager
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    IMPORT_SUCCESS = False


class TestVectorStoreManagerSimple:
    """Simple test cases for VectorStoreManager class."""

    @pytest.fixture
    def temp_storage_path(self):
        """Create a temporary storage path for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_embeddings(self):
        """Mock embeddings model."""
        with patch('lets_talk.core.pipeline.services.vector_store_manager.init_embeddings_wrapper') as mock:
            mock_embedding = Mock()
            mock_embedding.embed_documents.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
            mock_embedding.embed_query.return_value = [0.1, 0.2, 0.3]
            mock.return_value = mock_embedding
            yield mock_embedding

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(
                page_content="This is a test document about machine learning.",
                metadata={"source": "/path/to/doc1.md", "title": "ML Basics"}
            ),
            Document(
                page_content="This document covers deep learning concepts.",
                metadata={"source": "/path/to/doc2.md", "title": "Deep Learning"}
            )
        ]

    @pytest.fixture
    def vector_store_manager(self, temp_storage_path, mock_embeddings):
        """Create a VectorStoreManager instance for testing."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        return VectorStoreManager(
            storage_path=temp_storage_path,
            collection_name="test_collection",
            qdrant_url="",  # Use local storage
            embedding_model="test_embedding_model"
        )

    def test_initialization_with_custom_values(self, temp_storage_path):
        """Test VectorStoreManager initialization with custom values."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        manager = VectorStoreManager(
            storage_path=temp_storage_path,
            collection_name="custom_collection",
            qdrant_url="http://localhost:6333",
            embedding_model="custom_model"
        )
        
        assert manager.storage_path == temp_storage_path
        assert manager.collection_name == "custom_collection"
        assert manager.qdrant_url == "http://localhost:6333"
        assert manager.embedding_model == "custom_model"

    def test_embeddings_lazy_initialization(self, vector_store_manager, mock_embeddings):
        """Test that embeddings are lazily initialized."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        # Initially, embeddings should be None
        assert vector_store_manager._embeddings is None
        
        # Accessing embeddings property should initialize them
        embeddings = vector_store_manager.embeddings
        assert embeddings is not None
        assert embeddings == mock_embeddings

        # Second access should return the same instance
        embeddings2 = vector_store_manager.embeddings
        assert embeddings2 is embeddings

    @patch('lets_talk.core.pipeline.services.vector_store_manager.QdrantVectorStore')
    def test_create_vector_store_local(self, mock_qdrant_class, vector_store_manager, sample_documents):
        """Test creating a vector store with local storage."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_vector_store = Mock()
        mock_qdrant_class.from_documents.return_value = mock_vector_store
        
        result = vector_store_manager.create_vector_store(sample_documents)
        
        assert result == mock_vector_store
        mock_qdrant_class.from_documents.assert_called_once_with(
            sample_documents,
            embedding=vector_store_manager.embeddings,
            collection_name="test_collection",
            path=vector_store_manager.storage_path,
            force_recreate=False
        )

    @patch('lets_talk.core.pipeline.services.vector_store_manager.QdrantVectorStore')
    def test_create_vector_store_exception_handling(self, mock_qdrant_class, vector_store_manager, sample_documents):
        """Test create_vector_store exception handling."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_qdrant_class.from_documents.side_effect = Exception("Creation failed")
        
        result = vector_store_manager.create_vector_store(sample_documents)
        
        assert result is None

    def test_load_vector_store_local_not_exists(self, vector_store_manager):
        """Test loading a vector store when local storage doesn't exist."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        # Ensure the storage path doesn't exist
        storage_path = vector_store_manager.storage_path
        if Path(storage_path).exists():
            shutil.rmtree(storage_path)
        
        result = vector_store_manager.load_vector_store()
        
        assert result is None

    def test_load_vector_store_exception_handling(self, vector_store_manager):
        """Test load_vector_store exception handling."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        # Test by mocking the Path.exists to return True then causing an exception
        with patch('lets_talk.core.pipeline.services.vector_store_manager.Path') as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path.return_value = mock_path_instance
            
            with patch('lets_talk.core.pipeline.services.vector_store_manager.QdrantClient', side_effect=Exception("Load failed")):
                result = vector_store_manager.load_vector_store()
                assert result is None

    def test_add_documents_success(self, vector_store_manager, sample_documents):
        """Test successfully adding documents to vector store."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_vector_store = Mock()
        
        result = vector_store_manager.add_documents(mock_vector_store, sample_documents)
        
        assert result is True
        mock_vector_store.add_documents.assert_called_once_with(sample_documents)

    def test_add_documents_empty_list(self, vector_store_manager):
        """Test adding empty list of documents."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_vector_store = Mock()
        
        result = vector_store_manager.add_documents(mock_vector_store, [])
        
        assert result is True
        mock_vector_store.add_documents.assert_not_called()

    def test_add_documents_exception_handling(self, vector_store_manager, sample_documents):
        """Test add_documents exception handling."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_vector_store = Mock()
        mock_vector_store.add_documents.side_effect = Exception("Add failed")
        
        result = vector_store_manager.add_documents(mock_vector_store, sample_documents)
        
        assert result is False

    def test_validate_health_load_failure(self, vector_store_manager):
        """Test health validation when vector store cannot be loaded."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        with patch.object(vector_store_manager, 'load_vector_store', return_value=None):
            result = vector_store_manager.validate_health()
            
            assert result is False

    def test_validate_health_exception_handling(self, vector_store_manager):
        """Test health validation exception handling."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        with patch.object(vector_store_manager, 'load_vector_store', side_effect=Exception("Load failed")):
            result = vector_store_manager.validate_health()
            
            assert result is False

    def test_update_incrementally_load_failure(self, vector_store_manager, sample_documents):
        """Test incremental update when vector store cannot be loaded."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        new_docs = sample_documents[:1]
        modified_docs = sample_documents[1:2]
        deleted_sources = ["/path/to/old_doc.md"]
        
        with patch.object(vector_store_manager, 'load_vector_store', return_value=None):
            result = vector_store_manager.update_incrementally(
                new_docs, modified_docs, deleted_sources
            )
            
            assert result is False

    def test_update_incrementally_exception_handling(self, vector_store_manager, sample_documents):
        """Test incremental update exception handling."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        new_docs = sample_documents[:1]
        modified_docs = sample_documents[1:2]
        deleted_sources = ["/path/to/old_doc.md"]
        
        with patch.object(vector_store_manager, 'load_vector_store', side_effect=Exception("Load failed")):
            result = vector_store_manager.update_incrementally(
                new_docs, modified_docs, deleted_sources
            )
            
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
