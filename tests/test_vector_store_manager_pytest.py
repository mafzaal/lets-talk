#!/usr/bin/env python3
"""
Pytest test suite for the VectorStoreManager service.

This test script covers:
- VectorStoreManager initialization
- Vector store creation and loading
- Document addition and removal
- Batch processing operations
- Incremental updates
- Health validation
- Error handling and edge cases
"""

import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock, call

# Import langchain Document first
from langchain.schema.document import Document

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import the modules to test
try:
    from lets_talk.core.pipeline.services.vector_store_manager import (
        VectorStoreManager,
        create_vector_store,
        load_vector_store,
        add_documents_to_vector_store,
        remove_documents_from_vector_store,
        validate_vector_store_health
    )
    from lets_talk.shared.config import (
        EMBEDDING_MODEL,
        QDRANT_COLLECTION,
        QDRANT_URL,
        VECTOR_STORAGE_PATH
    )
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"Failed to import vector_store_manager module: {e}")
    IMPORT_SUCCESS = False


class TestVectorStoreManager:
    """Test cases for VectorStoreManager class."""

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
            ),
            Document(
                page_content="An introduction to natural language processing.",
                metadata={"source": "/path/to/doc3.md", "title": "NLP Intro"}
            )
        ]

    @pytest.fixture
    def vector_store_manager(self, temp_storage_path, mock_embeddings):
        """Create a VectorStoreManager instance for testing."""
        return VectorStoreManager(
            storage_path=temp_storage_path,
            collection_name="test_collection",
            qdrant_url="",  # Use local storage
            embedding_model="test_embedding_model"
        )

    @pytest.fixture
    def mock_qdrant_vector_store(self):
        """Mock QdrantVectorStore."""
        mock_store = Mock()
        mock_store.collection_name = "test_collection"
        mock_store.client = Mock()
        mock_store.add_documents = Mock()
        mock_store.similarity_search = Mock(return_value=[])
        return mock_store

    def test_initialization_default_values(self):
        """Test VectorStoreManager initialization with default values."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        manager = VectorStoreManager()
        
        assert manager.storage_path == VECTOR_STORAGE_PATH
        assert manager.collection_name == QDRANT_COLLECTION
        assert manager.qdrant_url == QDRANT_URL
        assert manager.embedding_model == EMBEDDING_MODEL
        assert manager._embeddings is None

    def test_initialization_custom_values(self, temp_storage_path):
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
    def test_create_vector_store_remote(self, mock_qdrant_class, temp_storage_path, mock_embeddings, sample_documents):
        """Test creating a vector store with remote Qdrant."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        manager = VectorStoreManager(
            storage_path=temp_storage_path,
            collection_name="test_collection",
            qdrant_url="http://localhost:6333",
            embedding_model="test_model"
        )
        
        mock_vector_store = Mock()
        mock_qdrant_class.from_documents.return_value = mock_vector_store
        
        result = manager.create_vector_store(sample_documents)
        
        assert result == mock_vector_store
        mock_qdrant_class.from_documents.assert_called_once_with(
            sample_documents,
            embedding=manager.embeddings,
            collection_name="test_collection",
            url="http://localhost:6333"
        )

    @patch('lets_talk.core.pipeline.services.vector_store_manager.QdrantVectorStore')
    def test_create_vector_store_force_recreate(self, mock_qdrant_class, vector_store_manager, sample_documents):
        """Test creating a vector store with force_recreate=True."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_vector_store = Mock()
        mock_qdrant_class.from_documents.return_value = mock_vector_store
        
        result = vector_store_manager.create_vector_store(sample_documents, force_recreate=True)
        
        assert result == mock_vector_store
        mock_qdrant_class.from_documents.assert_called_once_with(
            sample_documents,
            embedding=vector_store_manager.embeddings,
            collection_name="test_collection",
            path=vector_store_manager.storage_path,
            force_recreate=True
        )

    @patch('lets_talk.core.pipeline.services.vector_store_manager.QdrantVectorStore')
    def test_create_vector_store_exception_handling(self, mock_qdrant_class, vector_store_manager, sample_documents):
        """Test create_vector_store exception handling."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_qdrant_class.from_documents.side_effect = Exception("Creation failed")
        
        result = vector_store_manager.create_vector_store(sample_documents)
        
        assert result is None

    @patch('lets_talk.core.pipeline.services.vector_store_manager.QdrantVectorStore')
    @patch('lets_talk.core.pipeline.services.vector_store_manager.QdrantClient')
    def test_load_vector_store_local_success(self, mock_client_class, mock_qdrant_class, vector_store_manager, temp_storage_path):
        """Test loading a vector store from local storage successfully."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        # Create the storage path to simulate existing vector store
        Path(temp_storage_path).mkdir(exist_ok=True)
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_vector_store = Mock()
        mock_qdrant_class.return_value = mock_vector_store
        
        result = vector_store_manager.load_vector_store()
        
        assert result == mock_vector_store
        mock_client_class.assert_called_once_with(path=temp_storage_path)
        mock_qdrant_class.assert_called_once_with(
            client=mock_client,
            collection_name="test_collection",
            embedding=vector_store_manager.embeddings
        )

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

    @patch('lets_talk.core.pipeline.services.vector_store_manager.QdrantVectorStore')
    def test_load_vector_store_remote(self, mock_qdrant_class, temp_storage_path, mock_embeddings):
        """Test loading a vector store from remote Qdrant."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        manager = VectorStoreManager(
            storage_path=temp_storage_path,
            collection_name="test_collection",
            qdrant_url="http://localhost:6333",
            embedding_model="test_model"
        )
        
        mock_vector_store = Mock()
        mock_qdrant_class.from_existing_collection.return_value = mock_vector_store
        
        result = manager.load_vector_store()
        
        assert result == mock_vector_store
        mock_qdrant_class.from_existing_collection.assert_called_once_with(
            collection_name="test_collection",
            url="http://localhost:6333",
            embedding=manager.embeddings,
            prefer_grpc=True
        )

    @patch('lets_talk.core.pipeline.services.vector_store_manager.QdrantVectorStore')
    def test_load_vector_store_exception_handling(self, mock_qdrant_class, vector_store_manager):
        """Test load_vector_store exception handling."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_qdrant_class.from_existing_collection.side_effect = Exception("Load failed")
        
        result = vector_store_manager.load_vector_store()
        
        assert result is None

    def test_add_documents_success(self, vector_store_manager, mock_qdrant_vector_store, sample_documents):
        """Test successfully adding documents to vector store."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        result = vector_store_manager.add_documents(mock_qdrant_vector_store, sample_documents)
        
        assert result is True
        mock_qdrant_vector_store.add_documents.assert_called_once_with(sample_documents)

    def test_add_documents_empty_list(self, vector_store_manager, mock_qdrant_vector_store):
        """Test adding empty list of documents."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        result = vector_store_manager.add_documents(mock_qdrant_vector_store, [])
        
        assert result is True
        mock_qdrant_vector_store.add_documents.assert_not_called()

    def test_add_documents_exception_handling(self, vector_store_manager, mock_qdrant_vector_store, sample_documents):
        """Test add_documents exception handling."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_qdrant_vector_store.add_documents.side_effect = Exception("Add failed")
        
        result = vector_store_manager.add_documents(mock_qdrant_vector_store, sample_documents)
        
        assert result is False

    @patch('lets_talk.core.pipeline.services.vector_store_manager.models')
    def test_remove_documents_by_source_success(self, mock_models, vector_store_manager, mock_qdrant_vector_store):
        """Test successfully removing documents by source."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        # Mock the qdrant models
        mock_filter = Mock()
        mock_field_condition = Mock()
        mock_match_value = Mock()
        mock_filter_selector = Mock()
        
        mock_models.Filter.return_value = mock_filter
        mock_models.FieldCondition.return_value = mock_field_condition
        mock_models.MatchValue.return_value = mock_match_value
        mock_models.FilterSelector.return_value = mock_filter_selector
        
        document_sources = ["/path/to/doc1.md", "/path/to/doc2.md"]
        
        result = vector_store_manager.remove_documents_by_source(mock_qdrant_vector_store, document_sources)
        
        assert result is True
        assert mock_qdrant_vector_store.client.delete.call_count == 2

    def test_remove_documents_by_source_empty_list(self, vector_store_manager, mock_qdrant_vector_store):
        """Test removing empty list of document sources."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        result = vector_store_manager.remove_documents_by_source(mock_qdrant_vector_store, [])
        
        assert result is True
        mock_qdrant_vector_store.client.delete.assert_not_called()

    def test_remove_documents_by_source_import_error(self, vector_store_manager, mock_qdrant_vector_store):
        """Test remove_documents_by_source with import error."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        with patch.dict('sys.modules', {'qdrant_client.models': None}):
            result = vector_store_manager.remove_documents_by_source(mock_qdrant_vector_store, ["/path/to/doc1.md"])
            
            assert result is False

    @patch('lets_talk.core.pipeline.services.vector_store_manager.BatchProcessor')
    def test_add_documents_batch_success(self, mock_batch_processor_class, vector_store_manager, mock_qdrant_vector_store, sample_documents):
        """Test successfully adding documents in batches."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_processor = Mock()
        mock_processor.process_batches.return_value = True
        mock_batch_processor_class.return_value = mock_processor
        
        result = vector_store_manager.add_documents_batch(
            mock_qdrant_vector_store, 
            sample_documents, 
            batch_size=2, 
            pause_between_batches=0.1
        )
        
        assert result is True
        mock_batch_processor_class.assert_called_once_with(
            batch_size=2,
            pause_between_batches=0.1
        )
        mock_processor.process_batches.assert_called_once()

    def test_add_documents_batch_empty_list(self, vector_store_manager, mock_qdrant_vector_store):
        """Test adding empty list of documents in batches."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        result = vector_store_manager.add_documents_batch(mock_qdrant_vector_store, [])
        
        assert result is True

    @patch('lets_talk.core.pipeline.services.vector_store_manager.BatchProcessor')
    def test_remove_documents_batch_success(self, mock_batch_processor_class, vector_store_manager, mock_qdrant_vector_store):
        """Test successfully removing documents in batches."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_processor = Mock()
        mock_processor.process_batches.return_value = True
        mock_batch_processor_class.return_value = mock_processor
        
        document_sources = ["/path/to/doc1.md", "/path/to/doc2.md"]
        
        result = vector_store_manager.remove_documents_batch(
            mock_qdrant_vector_store, 
            document_sources, 
            batch_size=1, 
            pause_between_batches=0.05
        )
        
        assert result is True
        mock_batch_processor_class.assert_called_once_with(
            batch_size=1,
            pause_between_batches=0.05
        )
        mock_processor.process_batches.assert_called_once()

    def test_remove_documents_batch_empty_list(self, vector_store_manager, mock_qdrant_vector_store):
        """Test removing empty list of document sources in batches."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        result = vector_store_manager.remove_documents_batch(mock_qdrant_vector_store, [])
        
        assert result is True

    def test_validate_health_success(self, vector_store_manager, mock_qdrant_vector_store):
        """Test successful health validation."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        with patch.object(vector_store_manager, 'load_vector_store', return_value=mock_qdrant_vector_store):
            mock_qdrant_vector_store.similarity_search.return_value = []
            
            result = vector_store_manager.validate_health()
            
            assert result is True
            mock_qdrant_vector_store.similarity_search.assert_called_once_with("test query", k=1)
            mock_qdrant_vector_store.client.close.assert_called_once()

    def test_validate_health_load_failure(self, vector_store_manager):
        """Test health validation when vector store cannot be loaded."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        with patch.object(vector_store_manager, 'load_vector_store', return_value=None):
            result = vector_store_manager.validate_health()
            
            assert result is False

    def test_validate_health_similarity_search_failure(self, vector_store_manager, mock_qdrant_vector_store):
        """Test health validation when similarity search fails."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        with patch.object(vector_store_manager, 'load_vector_store', return_value=mock_qdrant_vector_store):
            mock_qdrant_vector_store.similarity_search.side_effect = Exception("Search failed")
            
            result = vector_store_manager.validate_health()
            
            assert result is False
            mock_qdrant_vector_store.client.close.assert_called_once()

    def test_validate_health_exception_handling(self, vector_store_manager):
        """Test health validation exception handling."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        with patch.object(vector_store_manager, 'load_vector_store', side_effect=Exception("Load failed")):
            result = vector_store_manager.validate_health()
            
            assert result is False

    def test_update_incrementally_success(self, vector_store_manager, mock_qdrant_vector_store, sample_documents):
        """Test successful incremental update."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        new_docs = sample_documents[:1]
        modified_docs = sample_documents[1:2]
        deleted_sources = ["/path/to/old_doc.md"]
        
        with patch.object(vector_store_manager, 'load_vector_store', return_value=mock_qdrant_vector_store):
            with patch.object(vector_store_manager, 'remove_documents_by_source', return_value=True):
                with patch.object(vector_store_manager, 'add_documents', return_value=True):
                    
                    result = vector_store_manager.update_incrementally(
                        new_docs, modified_docs, deleted_sources, use_batch_processing=False
                    )
                    
                    assert result is True
                    mock_qdrant_vector_store.client.close.assert_called_once()

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

    def test_update_incrementally_remove_failure(self, vector_store_manager, mock_qdrant_vector_store, sample_documents):
        """Test incremental update when document removal fails."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        new_docs = sample_documents[:1]
        modified_docs = sample_documents[1:2]
        deleted_sources = ["/path/to/old_doc.md"]
        
        with patch.object(vector_store_manager, 'load_vector_store', return_value=mock_qdrant_vector_store):
            with patch.object(vector_store_manager, 'remove_documents_by_source', return_value=False):
                
                result = vector_store_manager.update_incrementally(
                    new_docs, modified_docs, deleted_sources
                )
                
                assert result is False

    def test_update_incrementally_add_failure(self, vector_store_manager, mock_qdrant_vector_store, sample_documents):
        """Test incremental update when document addition fails."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        new_docs = sample_documents[:1]
        modified_docs = sample_documents[1:2]
        deleted_sources = ["/path/to/old_doc.md"]
        
        with patch.object(vector_store_manager, 'load_vector_store', return_value=mock_qdrant_vector_store):
            with patch.object(vector_store_manager, 'remove_documents_by_source', return_value=True):
                with patch.object(vector_store_manager, 'add_documents', return_value=False):
                    
                    result = vector_store_manager.update_incrementally(
                        new_docs, modified_docs, deleted_sources
                    )
                    
                    assert result is False

    @patch('lets_talk.core.pipeline.services.vector_store_manager.BatchProcessor')
    def test_update_incrementally_with_batch_processing(self, mock_batch_processor_class, vector_store_manager, mock_qdrant_vector_store, sample_documents):
        """Test incremental update with batch processing enabled."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        new_docs = sample_documents[:1]
        modified_docs = sample_documents[1:2]
        deleted_sources = ["/path/to/old_doc.md"]
        
        with patch.object(vector_store_manager, 'load_vector_store', return_value=mock_qdrant_vector_store):
            with patch.object(vector_store_manager, 'remove_documents_batch', return_value=True):
                with patch.object(vector_store_manager, 'add_documents_batch', return_value=True):
                    
                    result = vector_store_manager.update_incrementally(
                        new_docs, modified_docs, deleted_sources, 
                        use_batch_processing=True, batch_size=1
                    )
                    
                    assert result is True

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


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    @pytest.fixture
    def temp_storage_path(self):
        """Create a temporary storage path for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(
                page_content="Test document content",
                metadata={"source": "/path/to/test.md"}
            )
        ]

    @patch('lets_talk.core.pipeline.services.vector_store_manager.VectorStoreManager')
    def test_create_vector_store_function(self, mock_manager_class, temp_storage_path, sample_documents):
        """Test create_vector_store convenience function."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_manager = Mock()
        mock_manager.create_vector_store.return_value = "mock_vector_store"
        mock_manager_class.return_value = mock_manager
        
        result = create_vector_store(
            sample_documents,
            storage_path=temp_storage_path,
            collection_name="test_collection",
            qdrant_url="",
            embedding_model="test_model",
            force_recreate=True
        )
        
        assert result == "mock_vector_store"
        mock_manager_class.assert_called_once_with(
            temp_storage_path, "test_collection", "", "test_model"
        )
        mock_manager.create_vector_store.assert_called_once_with(sample_documents, True)

    @patch('lets_talk.core.pipeline.services.vector_store_manager.VectorStoreManager')
    def test_load_vector_store_function(self, mock_manager_class, temp_storage_path):
        """Test load_vector_store convenience function."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_manager = Mock()
        mock_manager.load_vector_store.return_value = "mock_vector_store"
        mock_manager_class.return_value = mock_manager
        
        result = load_vector_store(
            storage_path=temp_storage_path,
            collection_name="test_collection",
            qdrant_url="",
            embedding_model="test_model"
        )
        
        assert result == "mock_vector_store"
        mock_manager_class.assert_called_once_with(
            temp_storage_path, "test_collection", "", "test_model"
        )
        mock_manager.load_vector_store.assert_called_once()

    @patch('lets_talk.core.pipeline.services.vector_store_manager.VectorStoreManager')
    def test_add_documents_to_vector_store_function(self, mock_manager_class, sample_documents):
        """Test add_documents_to_vector_store convenience function."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_manager = Mock()
        mock_manager.add_documents.return_value = True
        mock_manager_class.return_value = mock_manager
        
        mock_vector_store = Mock()
        
        result = add_documents_to_vector_store(mock_vector_store, sample_documents)
        
        assert result is True
        mock_manager_class.assert_called_once()
        mock_manager.add_documents.assert_called_once_with(mock_vector_store, sample_documents)

    @patch('lets_talk.core.pipeline.services.vector_store_manager.VectorStoreManager')
    def test_remove_documents_from_vector_store_function(self, mock_manager_class):
        """Test remove_documents_from_vector_store convenience function."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_manager = Mock()
        mock_manager.remove_documents_by_source.return_value = True
        mock_manager_class.return_value = mock_manager
        
        mock_vector_store = Mock()
        document_sources = ["/path/to/doc1.md", "/path/to/doc2.md"]
        
        result = remove_documents_from_vector_store(mock_vector_store, document_sources)
        
        assert result is True
        mock_manager_class.assert_called_once()
        mock_manager.remove_documents_by_source.assert_called_once_with(mock_vector_store, document_sources)

    @patch('lets_talk.core.pipeline.services.vector_store_manager.VectorStoreManager')
    def test_validate_vector_store_health_function(self, mock_manager_class):
        """Test validate_vector_store_health convenience function."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_manager = Mock()
        mock_manager.validate_health.return_value = True
        mock_manager_class.return_value = mock_manager
        
        result = validate_vector_store_health(
            storage_path="/test/path",
            collection_name="test_collection",
            qdrant_url="http://localhost:6333",
            embedding_model="test_model"
        )
        
        assert result is True
        mock_manager_class.assert_called_once_with(
            "/test/path", "test_collection", "http://localhost:6333", "test_model"
        )
        mock_manager.validate_health.assert_called_once()


class TestEdgeCasesAndErrorHandling:
    """Test cases for edge cases and error handling."""

    @pytest.fixture
    def vector_store_manager(self):
        """Create a VectorStoreManager instance for testing."""
        return VectorStoreManager(
            storage_path="/nonexistent/path",
            collection_name="test_collection",
            qdrant_url="",
            embedding_model="test_model"
        )

    def test_create_vector_store_empty_documents(self, vector_store_manager):
        """Test creating vector store with empty document list."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        with patch('lets_talk.core.pipeline.services.vector_store_manager.QdrantVectorStore') as mock_qdrant:
            mock_vector_store = Mock()
            mock_qdrant.from_documents.return_value = mock_vector_store
            
            result = vector_store_manager.create_vector_store([])
            
            assert result == mock_vector_store
            mock_qdrant.from_documents.assert_called_once_with(
                [],
                embedding=vector_store_manager.embeddings,
                collection_name="test_collection",
                path="/nonexistent/path",
                force_recreate=False
            )

    def test_embeddings_initialization_failure(self, vector_store_manager):
        """Test handling of embeddings initialization failure."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        with patch('lets_talk.core.pipeline.services.vector_store_manager.init_embeddings_wrapper', side_effect=Exception("Embedding init failed")):
            with pytest.raises(Exception, match="Embedding init failed"):
                _ = vector_store_manager.embeddings

    def test_update_incrementally_no_changes(self, vector_store_manager):
        """Test incremental update with no changes."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        mock_vector_store = Mock()
        
        with patch.object(vector_store_manager, 'load_vector_store', return_value=mock_vector_store):
            result = vector_store_manager.update_incrementally([], [], [])
            
            assert result is True
            mock_vector_store.client.close.assert_called_once()

    def test_batch_processing_with_small_batch_size(self, vector_store_manager):
        """Test batch processing with very small batch size."""
        if not IMPORT_SUCCESS:
            pytest.skip("Failed to import required modules")
        
        documents = [
            Document(page_content=f"Doc {i}", metadata={"source": f"/path/doc{i}.md"})
            for i in range(5)
        ]
        
        mock_vector_store = Mock()
        
        with patch('lets_talk.core.pipeline.services.vector_store_manager.BatchProcessor') as mock_batch_processor_class:
            mock_processor = Mock()
            mock_processor.process_batches.return_value = True
            mock_batch_processor_class.return_value = mock_processor
            
            result = vector_store_manager.add_documents_batch(
                mock_vector_store, documents, batch_size=1
            )
            
            assert result is True
            mock_batch_processor_class.assert_called_once_with(
                batch_size=1,
                pause_between_batches=0.1
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
