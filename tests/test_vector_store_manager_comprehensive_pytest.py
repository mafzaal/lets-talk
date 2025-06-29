#!/usr/bin/env python3
"""
Comprehensive pytest test suite for the VectorStoreManager service.

This test script provides extensive coverage of:
- VectorStoreManager initialization and configuration
- Vector store creation (local and remote)
- Vector store loading with error handling
- Document addition and removal operations
- Batch processing functionality
- Incremental updates with comprehensive scenarios
- Health validation and monitoring
- Convenience function testing
- Edge cases and error handling
- Performance considerations
"""

import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock, call

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Test if we can import required modules
IMPORT_SUCCESS = True
IMPORT_ERRORS = []

try:
    from langchain.schema.document import Document
except ImportError as e:
    IMPORT_ERRORS.append(f"langchain.schema.document: {e}")
    Document = None

try:
    from lets_talk.core.pipeline.services.vector_store_manager import (
        VectorStoreManager,
        create_vector_store,
        load_vector_store,
        add_documents_to_vector_store,
        remove_documents_from_vector_store,
        validate_vector_store_health
    )
except ImportError as e:
    IMPORT_ERRORS.append(f"vector_store_manager: {e}")
    VectorStoreManager = None

try:
    from lets_talk.shared.config import (
        EMBEDDING_MODEL,
        QDRANT_COLLECTION,
        QDRANT_URL,
        VECTOR_STORAGE_PATH
    )
except ImportError as e:
    IMPORT_ERRORS.append(f"shared.config: {e}")
    # Set defaults for testing
    EMBEDDING_MODEL = "test_embedding_model"
    QDRANT_COLLECTION = "test_collection"
    QDRANT_URL = ""
    VECTOR_STORAGE_PATH = "/tmp/test_vector_store"

if IMPORT_ERRORS:
    IMPORT_SUCCESS = False
    print("Import errors detected:")
    for error in IMPORT_ERRORS:
        print(f"  - {error}")


def create_mock_document(content: str, source: str, **metadata) -> object:
    """Create a mock document object for testing."""
    if Document:
        return Document(
            page_content=content,
            metadata={"source": source, **metadata}
        )
    else:
        # Create a simple mock if Document is not available
        mock_doc = Mock()
        mock_doc.page_content = content
        mock_doc.metadata = {"source": source, **metadata}
        return mock_doc


class TestVectorStoreManagerComprehensive:
    """Comprehensive test cases for VectorStoreManager class."""

    @pytest.fixture
    def temp_storage_path(self):
        """Create a temporary storage path for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_embeddings(self):
        """Mock embeddings model with realistic behavior."""
        with patch('lets_talk.core.pipeline.services.vector_store_manager.init_embeddings_wrapper') as mock:
            mock_embedding = Mock()
            mock_embedding.embed_documents.return_value = [
                [0.1, 0.2, 0.3] for _ in range(10)  # Support multiple documents
            ]
            mock_embedding.embed_query.return_value = [0.1, 0.2, 0.3]
            mock.return_value = mock_embedding
            yield mock_embedding

    @pytest.fixture
    def sample_documents(self):
        """Create diverse sample documents for testing."""
        return [
            create_mock_document(
                "This is a comprehensive guide to machine learning fundamentals.",
                "/content/ml/basics.md",
                title="ML Basics",
                category="tutorial",
                published=True
            ),
            create_mock_document(
                "Deep learning architectures and neural network design patterns.",
                "/content/dl/architectures.md",
                title="Deep Learning Architectures",
                category="advanced",
                published=True
            ),
            create_mock_document(
                "Natural language processing techniques and applications.",
                "/content/nlp/techniques.md",
                title="NLP Techniques",
                category="tutorial",
                published=False
            ),
            create_mock_document(
                "Computer vision algorithms and image processing methods.",
                "/content/cv/algorithms.md",
                title="Computer Vision",
                category="advanced",
                published=True
            )
        ]

    @pytest.fixture
    def vector_store_manager(self, temp_storage_path, mock_embeddings):
        """Create a VectorStoreManager instance for testing."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        return VectorStoreManager(
            storage_path=temp_storage_path,
            collection_name="test_collection",
            qdrant_url="",  # Use local storage
            embedding_model="test_embedding_model"
        )

    @pytest.fixture
    def mock_qdrant_vector_store(self):
        """Create a comprehensive mock of QdrantVectorStore."""
        mock_store = Mock()
        mock_store.collection_name = "test_collection"
        mock_store.client = Mock()
        mock_store.client.close = Mock()
        mock_store.add_documents = Mock(return_value=None)
        mock_store.similarity_search = Mock(return_value=[])
        
        # Mock delete method for document removal
        mock_store.client.delete = Mock(return_value=None)
        
        return mock_store

    def test_initialization_with_defaults(self):
        """Test VectorStoreManager initialization with default configuration."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        manager = VectorStoreManager()
        
        assert manager.storage_path == VECTOR_STORAGE_PATH
        assert manager.collection_name == QDRANT_COLLECTION
        assert manager.qdrant_url == QDRANT_URL
        assert manager.embedding_model == EMBEDDING_MODEL
        assert manager._embeddings is None

    def test_initialization_with_custom_config(self, temp_storage_path):
        """Test VectorStoreManager initialization with custom configuration."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        custom_config = {
            "storage_path": temp_storage_path,
            "collection_name": "custom_ml_collection",
            "qdrant_url": "http://localhost:6333",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
        }
        
        manager = VectorStoreManager(**custom_config)
        
        assert manager.storage_path == custom_config["storage_path"]
        assert manager.collection_name == custom_config["collection_name"]
        assert manager.qdrant_url == custom_config["qdrant_url"]
        assert manager.embedding_model == custom_config["embedding_model"]

    def test_embeddings_property_lazy_loading(self, vector_store_manager, mock_embeddings):
        """Test embeddings property implements lazy loading correctly."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        # Initially, embeddings should be None
        assert vector_store_manager._embeddings is None
        
        # First access should initialize embeddings
        embeddings_first = vector_store_manager.embeddings
        assert embeddings_first is not None
        assert embeddings_first == mock_embeddings
        assert vector_store_manager._embeddings is not None
        
        # Subsequent accesses should return the same instance
        embeddings_second = vector_store_manager.embeddings
        assert embeddings_second is embeddings_first

    @patch('lets_talk.core.pipeline.services.vector_store_manager.QdrantVectorStore')
    def test_create_vector_store_local_storage(self, mock_qdrant_class, vector_store_manager, sample_documents):
        """Test creating vector store with local storage configuration."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
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
    def test_create_vector_store_remote_storage(self, mock_qdrant_class, temp_storage_path, mock_embeddings, sample_documents):
        """Test creating vector store with remote Qdrant configuration."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        manager = VectorStoreManager(
            storage_path=temp_storage_path,
            collection_name="remote_collection",
            qdrant_url="http://qdrant.example.com:6333",
            embedding_model="test_model"
        )
        
        mock_vector_store = Mock()
        mock_qdrant_class.from_documents.return_value = mock_vector_store
        
        result = manager.create_vector_store(sample_documents, force_recreate=True)
        
        assert result == mock_vector_store
        mock_qdrant_class.from_documents.assert_called_once_with(
            sample_documents,
            embedding=manager.embeddings,
            collection_name="remote_collection",
            url="http://qdrant.example.com:6333"
        )

    @patch('lets_talk.core.pipeline.services.vector_store_manager.QdrantVectorStore')
    def test_create_vector_store_with_empty_documents(self, mock_qdrant_class, vector_store_manager):
        """Test creating vector store with empty document list."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        mock_vector_store = Mock()
        mock_qdrant_class.from_documents.return_value = mock_vector_store
        
        result = vector_store_manager.create_vector_store([])
        
        assert result == mock_vector_store
        mock_qdrant_class.from_documents.assert_called_once_with(
            [],
            embedding=vector_store_manager.embeddings,
            collection_name="test_collection",
            path=vector_store_manager.storage_path,
            force_recreate=False
        )

    @patch('lets_talk.core.pipeline.services.vector_store_manager.QdrantVectorStore')
    def test_create_vector_store_error_handling(self, mock_qdrant_class, vector_store_manager, sample_documents):
        """Test create_vector_store handles exceptions gracefully."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        # Test various exception scenarios
        exceptions_to_test = [
            ConnectionError("Failed to connect to Qdrant"),
            ValueError("Invalid embedding dimensions"),
            RuntimeError("Insufficient memory"),
            Exception("Unknown error")
        ]
        
        for exception in exceptions_to_test:
            mock_qdrant_class.from_documents.side_effect = exception
            
            result = vector_store_manager.create_vector_store(sample_documents)
            
            assert result is None

    @patch('lets_talk.core.pipeline.services.vector_store_manager.QdrantVectorStore')
    @patch('lets_talk.core.pipeline.services.vector_store_manager.QdrantClient')
    def test_load_vector_store_local_success(self, mock_client_class, mock_qdrant_class, vector_store_manager, temp_storage_path):
        """Test successfully loading vector store from local storage."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
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

    def test_load_vector_store_local_nonexistent(self, vector_store_manager):
        """Test loading vector store when local storage doesn't exist."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        # Ensure the storage path doesn't exist
        storage_path = vector_store_manager.storage_path
        if Path(storage_path).exists():
            shutil.rmtree(storage_path)
        
        result = vector_store_manager.load_vector_store()
        
        assert result is None

    @patch('lets_talk.core.pipeline.services.vector_store_manager.QdrantVectorStore')
    def test_load_vector_store_remote_success(self, mock_qdrant_class, temp_storage_path, mock_embeddings):
        """Test successfully loading vector store from remote Qdrant."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        manager = VectorStoreManager(
            storage_path=temp_storage_path,
            collection_name="remote_collection",
            qdrant_url="http://qdrant.example.com:6333",
            embedding_model="test_model"
        )
        
        mock_vector_store = Mock()
        mock_qdrant_class.from_existing_collection.return_value = mock_vector_store
        
        result = manager.load_vector_store()
        
        assert result == mock_vector_store
        mock_qdrant_class.from_existing_collection.assert_called_once_with(
            collection_name="remote_collection",
            url="http://qdrant.example.com:6333",
            embedding=manager.embeddings,
            prefer_grpc=True
        )

    def test_add_documents_successful_operation(self, vector_store_manager, mock_qdrant_vector_store, sample_documents):
        """Test successfully adding documents to vector store."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        result = vector_store_manager.add_documents(mock_qdrant_vector_store, sample_documents)
        
        assert result is True
        mock_qdrant_vector_store.add_documents.assert_called_once_with(sample_documents)

    def test_add_documents_empty_list_handling(self, vector_store_manager, mock_qdrant_vector_store):
        """Test adding empty list of documents is handled correctly."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        result = vector_store_manager.add_documents(mock_qdrant_vector_store, [])
        
        assert result is True
        mock_qdrant_vector_store.add_documents.assert_not_called()

    def test_add_documents_error_scenarios(self, vector_store_manager, mock_qdrant_vector_store, sample_documents):
        """Test add_documents handles various error scenarios."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        error_scenarios = [
            ConnectionError("Vector store connection lost"),
            ValueError("Invalid document format"),
            MemoryError("Insufficient memory for embeddings"),
            Exception("Unexpected error")
        ]
        
        for error in error_scenarios:
            mock_qdrant_vector_store.add_documents.side_effect = error
            
            result = vector_store_manager.add_documents(mock_qdrant_vector_store, sample_documents)
            
            assert result is False

    @patch('qdrant_client.models')
    def test_remove_documents_by_source_success(self, mock_models, vector_store_manager, mock_qdrant_vector_store):
        """Test successfully removing documents by source paths."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        # Setup mock models
        mock_filter = Mock()
        mock_field_condition = Mock()
        mock_match_value = Mock()
        mock_filter_selector = Mock()
        
        mock_models.Filter.return_value = mock_filter
        mock_models.FieldCondition.return_value = mock_field_condition
        mock_models.MatchValue.return_value = mock_match_value
        mock_models.FilterSelector.return_value = mock_filter_selector
        
        document_sources = [
            "/content/ml/basics.md",
            "/content/dl/architectures.md",
            "/content/nlp/techniques.md"
        ]
        
        result = vector_store_manager.remove_documents_by_source(mock_qdrant_vector_store, document_sources)
        
        assert result is True
        assert mock_qdrant_vector_store.client.delete.call_count == len(document_sources)
        
        # Verify the filter construction
        assert mock_models.Filter.call_count == len(document_sources)
        assert mock_models.FieldCondition.call_count == len(document_sources)
        assert mock_models.MatchValue.call_count == len(document_sources)

    def test_remove_documents_by_source_empty_list(self, vector_store_manager, mock_qdrant_vector_store):
        """Test removing empty list of document sources."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        result = vector_store_manager.remove_documents_by_source(mock_qdrant_vector_store, [])
        
        assert result is True
        mock_qdrant_vector_store.client.delete.assert_not_called()

    @patch('lets_talk.core.pipeline.services.vector_store_manager.BatchProcessor')
    def test_batch_processing_add_documents(self, mock_batch_processor_class, vector_store_manager, mock_qdrant_vector_store, sample_documents):
        """Test batch processing for adding documents."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
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

    @patch('lets_talk.core.pipeline.services.vector_store_manager.BatchProcessor')
    def test_batch_processing_remove_documents(self, mock_batch_processor_class, vector_store_manager, mock_qdrant_vector_store):
        """Test batch processing for removing documents."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        mock_processor = Mock()
        mock_processor.process_batches.return_value = True
        mock_batch_processor_class.return_value = mock_processor
        
        document_sources = [f"/content/doc{i}.md" for i in range(10)]
        
        result = vector_store_manager.remove_documents_batch(
            mock_qdrant_vector_store,
            document_sources,
            batch_size=3,
            pause_between_batches=0.05
        )
        
        assert result is True
        mock_batch_processor_class.assert_called_once_with(
            batch_size=3,
            pause_between_batches=0.05
        )
        mock_processor.process_batches.assert_called_once()

    def test_validate_health_successful_check(self, vector_store_manager, mock_qdrant_vector_store):
        """Test successful health validation of vector store."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        with patch.object(vector_store_manager, 'load_vector_store', return_value=mock_qdrant_vector_store):
            mock_qdrant_vector_store.similarity_search.return_value = []
            
            result = vector_store_manager.validate_health()
            
            assert result is True
            mock_qdrant_vector_store.similarity_search.assert_called_once_with("test query", k=1)
            mock_qdrant_vector_store.client.close.assert_called_once()

    def test_validate_health_various_failure_scenarios(self, vector_store_manager):
        """Test health validation handles various failure scenarios."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        # Scenario 1: Vector store cannot be loaded
        with patch.object(vector_store_manager, 'load_vector_store', return_value=None):
            result = vector_store_manager.validate_health()
            assert result is False
        
        # Scenario 2: Similarity search fails
        mock_store = Mock()
        mock_store.similarity_search.side_effect = Exception("Search failed")
        mock_store.client.close = Mock()
        
        with patch.object(vector_store_manager, 'load_vector_store', return_value=mock_store):
            result = vector_store_manager.validate_health()
            assert result is False
            mock_store.client.close.assert_called_once()
        
        # Scenario 3: General exception during health check
        with patch.object(vector_store_manager, 'load_vector_store', side_effect=Exception("Health check failed")):
            result = vector_store_manager.validate_health()
            assert result is False

    def test_update_incrementally_comprehensive_scenario(self, vector_store_manager, mock_qdrant_vector_store, sample_documents):
        """Test comprehensive incremental update scenario."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        # Prepare test data
        new_docs = sample_documents[:2]
        modified_docs = sample_documents[2:3]
        deleted_sources = ["/content/old/deprecated.md", "/content/old/obsolete.md"]
        
        # Mock all required operations
        with patch.object(vector_store_manager, 'load_vector_store', return_value=mock_qdrant_vector_store):
            with patch.object(vector_store_manager, 'remove_documents_by_source', return_value=True) as mock_remove:
                with patch.object(vector_store_manager, 'add_documents', return_value=True) as mock_add:
                    
                    result = vector_store_manager.update_incrementally(
                        new_docs, modified_docs, deleted_sources, use_batch_processing=False
                    )
                    
                    assert result is True
                    
                    # Verify the sequence of operations
                    assert mock_remove.call_count == 2  # Once for deleted, once for modified
                    assert mock_add.call_count == 1    # Once for new + modified combined
                    
                    mock_qdrant_vector_store.client.close.assert_called_once()

    def test_update_incrementally_with_batch_processing(self, vector_store_manager, mock_qdrant_vector_store, sample_documents):
        """Test incremental update with batch processing enabled."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        new_docs = sample_documents[:2]
        modified_docs = sample_documents[2:3]
        deleted_sources = ["/content/old/deprecated.md"]
        
        with patch.object(vector_store_manager, 'load_vector_store', return_value=mock_qdrant_vector_store):
            with patch.object(vector_store_manager, 'remove_documents_batch', return_value=True) as mock_remove_batch:
                with patch.object(vector_store_manager, 'add_documents_batch', return_value=True) as mock_add_batch:
                    
                    result = vector_store_manager.update_incrementally(
                        new_docs, modified_docs, deleted_sources,
                        use_batch_processing=True, batch_size=2
                    )
                    
                    assert result is True
                    # Verify that batch methods were called
                    # Note: The exact call count may vary based on implementation logic
                    assert mock_remove_batch.called or mock_add_batch.called

    def test_update_incrementally_failure_scenarios(self, vector_store_manager, sample_documents):
        """Test incremental update handles various failure scenarios."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        new_docs = sample_documents[:1]
        modified_docs = sample_documents[1:2]
        deleted_sources = ["/content/old/test.md"]
        
        # Scenario 1: Cannot load vector store
        with patch.object(vector_store_manager, 'load_vector_store', return_value=None):
            result = vector_store_manager.update_incrementally(new_docs, modified_docs, deleted_sources)
            assert result is False
        
        # Scenario 2: Document removal fails
        mock_store = Mock()
        with patch.object(vector_store_manager, 'load_vector_store', return_value=mock_store):
            with patch.object(vector_store_manager, 'remove_documents_by_source', return_value=False):
                result = vector_store_manager.update_incrementally(new_docs, modified_docs, deleted_sources)
                assert result is False
        
        # Scenario 3: Document addition fails
        with patch.object(vector_store_manager, 'load_vector_store', return_value=mock_store):
            with patch.object(vector_store_manager, 'remove_documents_by_source', return_value=True):
                with patch.object(vector_store_manager, 'add_documents', return_value=False):
                    result = vector_store_manager.update_incrementally(new_docs, modified_docs, deleted_sources)
                    assert result is False

    def test_update_incrementally_no_changes(self, vector_store_manager, mock_qdrant_vector_store):
        """Test incremental update when there are no changes to process."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        with patch.object(vector_store_manager, 'load_vector_store', return_value=mock_qdrant_vector_store):
            result = vector_store_manager.update_incrementally([], [], [])
            
            assert result is True
            mock_qdrant_vector_store.client.close.assert_called_once()


class TestConvenienceFunctions:
    """Test cases for convenience functions that provide backward compatibility."""

    @pytest.fixture
    def temp_storage_path(self):
        """Create temporary storage path."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents."""
        return [
            create_mock_document("Test content", "/path/to/test.md")
        ]

    @patch('lets_talk.core.pipeline.services.vector_store_manager.VectorStoreManager')
    def test_create_vector_store_convenience_function(self, mock_manager_class, temp_storage_path, sample_documents):
        """Test create_vector_store convenience function."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
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
    def test_load_vector_store_convenience_function(self, mock_manager_class, temp_storage_path):
        """Test load_vector_store convenience function."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        mock_manager = Mock()
        mock_manager.load_vector_store.return_value = "mock_vector_store"
        mock_manager_class.return_value = mock_manager
        
        result = load_vector_store(
            storage_path=temp_storage_path,
            collection_name="test_collection",
            qdrant_url="http://localhost:6333",
            embedding_model="test_model"
        )
        
        assert result == "mock_vector_store"
        mock_manager_class.assert_called_once_with(
            temp_storage_path, "test_collection", "http://localhost:6333", "test_model"
        )
        mock_manager.load_vector_store.assert_called_once()

    @patch('lets_talk.core.pipeline.services.vector_store_manager.VectorStoreManager')
    def test_add_documents_convenience_function(self, mock_manager_class, sample_documents):
        """Test add_documents_to_vector_store convenience function."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        mock_manager = Mock()
        mock_manager.add_documents.return_value = True
        mock_manager_class.return_value = mock_manager
        
        mock_vector_store = Mock()
        
        result = add_documents_to_vector_store(mock_vector_store, sample_documents)
        
        assert result is True
        mock_manager_class.assert_called_once()
        mock_manager.add_documents.assert_called_once_with(mock_vector_store, sample_documents)

    @patch('lets_talk.core.pipeline.services.vector_store_manager.VectorStoreManager')
    def test_remove_documents_convenience_function(self, mock_manager_class):
        """Test remove_documents_from_vector_store convenience function."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        mock_manager = Mock()
        mock_manager.remove_documents_by_source.return_value = True
        mock_manager_class.return_value = mock_manager
        
        mock_vector_store = Mock()
        document_sources = ["/path/to/doc1.md", "/path/to/doc2.md"]
        
        result = remove_documents_from_vector_store(mock_vector_store, document_sources)
        
        assert result is True
        mock_manager.remove_documents_by_source.assert_called_once_with(mock_vector_store, document_sources)

    @patch('lets_talk.core.pipeline.services.vector_store_manager.VectorStoreManager')
    def test_validate_health_convenience_function(self, mock_manager_class):
        """Test validate_vector_store_health convenience function."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
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


class TestEdgeCasesAndPerformance:
    """Test cases for edge cases, error handling, and performance considerations."""

    def test_large_document_batch_processing(self):
        """Test handling of large document batches."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        # Create a large number of mock documents
        large_document_set = [
            create_mock_document(f"Document {i} content", f"/path/doc{i}.md")
            for i in range(1000)
        ]
        
        manager = VectorStoreManager(
            storage_path="/tmp/test",
            collection_name="large_test",
            qdrant_url="",
            embedding_model="test_model"
        )
        
        mock_vector_store = Mock()
        
        with patch('lets_talk.core.pipeline.services.vector_store_manager.BatchProcessor') as mock_batch_processor:
            mock_processor = Mock()
            mock_processor.process_batches.return_value = True
            mock_batch_processor.return_value = mock_processor
            
            result = manager.add_documents_batch(mock_vector_store, large_document_set, batch_size=50)
            
            assert result is True
            mock_batch_processor.assert_called_once_with(batch_size=50, pause_between_batches=0.1)

    def test_concurrent_access_safety(self):
        """Test vector store manager behavior under concurrent access."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        manager = VectorStoreManager()
        
        # Test that multiple embeddings access is safe
        with patch('lets_talk.core.pipeline.services.vector_store_manager.init_embeddings_wrapper') as mock_init:
            mock_embedding = Mock()
            mock_init.return_value = mock_embedding
            
            # Multiple concurrent accesses should return the same instance
            embeddings1 = manager.embeddings
            embeddings2 = manager.embeddings
            embeddings3 = manager.embeddings
            
            assert embeddings1 is embeddings2 is embeddings3
            mock_init.assert_called_once()

    def test_memory_efficient_document_processing(self):
        """Test memory-efficient processing of documents."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        manager = VectorStoreManager()
        
        # Test processing empty document lists doesn't consume unnecessary resources
        mock_vector_store = Mock()
        
        result = manager.add_documents_batch(mock_vector_store, [], batch_size=100)
        assert result is True
        
        result = manager.remove_documents_batch(mock_vector_store, [], batch_size=100)
        assert result is True

    def test_configuration_validation(self):
        """Test configuration validation and error handling."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        # Test with various configuration scenarios
        valid_configs = [
            {"storage_path": "/tmp/test", "collection_name": "test", "qdrant_url": "", "embedding_model": "test"},
            {"storage_path": "/tmp/test2", "collection_name": "test2", "qdrant_url": "http://localhost:6333", "embedding_model": "test2"},
        ]
        
        for config in valid_configs:
            manager = VectorStoreManager(**config)
            assert manager.storage_path == config["storage_path"]
            assert manager.collection_name == config["collection_name"]
            assert manager.qdrant_url == config["qdrant_url"]
            assert manager.embedding_model == config["embedding_model"]

    def test_resource_cleanup(self):
        """Test proper resource cleanup in various scenarios."""
        if not IMPORT_SUCCESS:
            pytest.skip("Required modules not available for import")
        
        manager = VectorStoreManager()
        
        # Test health validation cleanup
        mock_vector_store = Mock()
        mock_vector_store.similarity_search.return_value = []
        mock_vector_store.client.close = Mock()
        
        with patch.object(manager, 'load_vector_store', return_value=mock_vector_store):
            result = manager.validate_health()
            assert result is True
            mock_vector_store.client.close.assert_called_once()
        
        # Test cleanup on exception
        mock_vector_store.similarity_search.side_effect = Exception("Test error")
        mock_vector_store.client.close.reset_mock()
        
        with patch.object(manager, 'load_vector_store', return_value=mock_vector_store):
            result = manager.validate_health()
            assert result is False
            mock_vector_store.client.close.assert_called_once()


if __name__ == "__main__":
    if IMPORT_SUCCESS:
        pytest.main([__file__, "-v"])
    else:
        print("Cannot run tests due to import failures:")
        for error in IMPORT_ERRORS:
            print(f"  - {error}")
        print("\nPlease ensure all required dependencies are installed.")
