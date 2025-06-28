"""
Vector store management module.

This module handles all vector store operations including creation, loading,
updating, and document management with Qdrant.
"""

import logging
from pathlib import Path
from typing import List, Optional


from langchain.schema.document import Document
from langchain_qdrant import QdrantVectorStore
from lets_talk.utils.wrapper import init_embeddings_wrapper
from qdrant_client import QdrantClient, models

from lets_talk.shared.config import (
    EMBEDDING_MODEL,
    QDRANT_COLLECTION,
    QDRANT_URL,
    VECTOR_STORAGE_PATH
)
from ..utils.common_utils import handle_exceptions, log_execution_time
from ..utils.batch_processor import BatchProcessor

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    Manages vector store operations with Qdrant.
    """
    
    def __init__(
        self,
        storage_path: str = VECTOR_STORAGE_PATH,
        collection_name: str = QDRANT_COLLECTION,
        qdrant_url: str = QDRANT_URL,
        embedding_model: str = EMBEDDING_MODEL
    ):
        """
        Initialize the vector store manager.
        
        Args:
            storage_path: Path to local vector store
            collection_name: Name of the Qdrant collection
            qdrant_url: URL for remote Qdrant instance
            embedding_model: Name of the embedding model
        """
        self.storage_path = storage_path
        self.collection_name = collection_name
        self.qdrant_url = qdrant_url
        self.embedding_model = embedding_model
        self._embeddings = None
    
    @property
    def embeddings(self):
        """Lazy initialization of embeddings."""
        if self._embeddings is None:
            self._embeddings = init_embeddings_wrapper(self.embedding_model)
        return self._embeddings
    
    @handle_exceptions(default_return=None)
    @log_execution_time()
    def create_vector_store(
        self,
        documents: List[Document],
        force_recreate: bool = False
    ) -> Optional[QdrantVectorStore]:
        """
        Create a vector store from documents.
        
        Args:
            documents: List of Document objects to embed
            force_recreate: Whether to force recreation of the vector store
            
        Returns:
            QdrantVectorStore instance or None if creation fails
        """
        logger.info(f"Creating vector store with {len(documents)} documents")
        
        try:
            if self.qdrant_url:
                # Use remote Qdrant
                vector_store = QdrantVectorStore.from_documents(
                    documents,
                    embedding=self.embeddings, # type: ignore
                    collection_name=self.collection_name,
                    url=self.qdrant_url,
                )
            else:
                # Use local Qdrant
                vector_store = QdrantVectorStore.from_documents(
                    documents,
                    embedding=self.embeddings, # type: ignore
                    collection_name=self.collection_name,
                    path=self.storage_path,
                    force_recreate=force_recreate,
                )
            
            logger.info(f"Successfully created vector store at {self.qdrant_url or self.storage_path}")
            return vector_store
            
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            return None
    
    @handle_exceptions(default_return=None)
    def load_vector_store(self) -> Optional[QdrantVectorStore]:
        """
        Load an existing vector store.
        
        Returns:
            QdrantVectorStore instance or None if it doesn't exist
        """
        try:
            if self.qdrant_url:
                # Use remote Qdrant - check if collection exists first
                if not self.collection_exists():
                    logger.info(f"Collection '{self.collection_name}' does not exist, creating it...")
                    if not self.create_collection():
                        logger.error("Failed to create collection")
                        return None
                
                # Use remote Qdrant
                vector_store = QdrantVectorStore.from_existing_collection(
                    collection_name=self.collection_name,
                    url=self.qdrant_url,
                    embedding=self.embeddings, # type: ignore
                    prefer_grpc=True,  # Use gRPC for better performance
                )
                logger.info(f"Loaded vector store from remote Qdrant: {self.qdrant_url}")
                return vector_store
            else:
                # Use local Qdrant
                if not Path(self.storage_path).exists():
                    logger.info(f"Vector store not found at {self.storage_path}")
                    return None
                
                # Check if collection exists in local Qdrant
                if not self.collection_exists():
                    logger.info(f"Collection '{self.collection_name}' does not exist, creating it...")
                    if not self.create_collection():
                        logger.error("Failed to create collection")
                        return None
                
                # Initialize Qdrant client
                client = QdrantClient(path=self.storage_path)
                
                # Create vector store with the client
                vector_store = QdrantVectorStore(
                    client=client,
                    collection_name=self.collection_name,
                    embedding=self.embeddings, # type: ignore
                )
                logger.info(f"Loaded vector store from {self.storage_path}")
                return vector_store
                
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            return None
    
    @handle_exceptions(default_return=False)
    def add_documents(
        self,
        vector_store: QdrantVectorStore,
        documents: List[Document]
    ) -> bool:
        """
        Add new documents to an existing vector store.
        
        Args:
            vector_store: Existing QdrantVectorStore instance
            documents: List of Document objects to add
            
        Returns:
            True if successful, False otherwise
        """
        if not documents:
            return True
        
        try:
            vector_store.add_documents(documents)
            logger.info(f"Successfully added {len(documents)} documents to vector store")
            return True
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            return False
    
    @handle_exceptions(default_return=False)
    def remove_documents_by_source(
        self,
        vector_store: QdrantVectorStore,
        document_sources: List[str]
    ) -> bool:
        """
        Remove documents from the vector store based on their source paths.
        
        Args:
            vector_store: Existing QdrantVectorStore instance
            document_sources: List of source paths to remove
            
        Returns:
            True if successful, False otherwise
        """
        if not document_sources:
            return True
        
        try:
            # Delete by metadata filter (source field)
            for source in document_sources:
                # Create a filter to find documents with this source
                filter_condition = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.source",
                            match=models.MatchValue(value=source)
                        )
                    ]
                )
                
                # Delete documents matching the filter
                vector_store.client.delete(
                    collection_name=vector_store.collection_name,
                    points_selector=models.FilterSelector(filter=filter_condition)
                )
            
            logger.info(f"Successfully removed documents for {len(document_sources)} sources")
            return True
        except ImportError:
            logger.warning("Could not import qdrant models for document removal")
            return False
        except Exception as e:
            logger.error(f"Error removing documents from vector store: {e}")
            return False
    
    def add_documents_batch(
        self,
        vector_store: QdrantVectorStore,
        documents: List[Document],
        batch_size: int = 50,
        pause_between_batches: float = 0.1
    ) -> bool:
        """
        Add documents to vector store in batches for better performance.
        
        Args:
            vector_store: Existing QdrantVectorStore instance
            documents: List of Document objects to add
            batch_size: Number of documents per batch
            pause_between_batches: Seconds to pause between batches
            
        Returns:
            True if successful, False otherwise
        """
        if not documents:
            return True
        
        def process_batch(batch: List[Document]) -> bool:
            return self.add_documents(vector_store, batch)
        
        processor = BatchProcessor(
            batch_size=batch_size,
            pause_between_batches=pause_between_batches
        )
        
        return processor.process_batches(
            documents,
            process_batch,
            "Adding documents to vector store"
        )
    
    def remove_documents_batch(
        self,
        vector_store: QdrantVectorStore,
        document_sources: List[str],
        batch_size: int = 50,
        pause_between_batches: float = 0.1
    ) -> bool:
        """
        Remove documents from vector store in batches for better performance.
        
        Args:
            vector_store: Existing QdrantVectorStore instance
            document_sources: List of source paths to remove
            batch_size: Number of sources per batch
            pause_between_batches: Seconds to pause between batches
            
        Returns:
            True if successful, False otherwise
        """
        if not document_sources:
            return True
        
        def process_batch(batch: List[str]) -> bool:
            return self.remove_documents_by_source(vector_store, batch)
        
        processor = BatchProcessor(
            batch_size=batch_size,
            pause_between_batches=pause_between_batches
        )
        
        return processor.process_batches(
            document_sources,
            process_batch,
            "Removing documents from vector store"
        )
    
    @handle_exceptions(default_return=False)
    def validate_health(self) -> bool:
        """
        Validate that the vector store is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            vector_store = self.load_vector_store()
            
            if vector_store is None:
                logger.warning("Vector store could not be loaded")
                return False
            
            # Test basic operations
            try:
                # Try to perform a basic similarity search to validate the store works
                test_results = vector_store.similarity_search("test query", k=1)
                logger.info("Vector store health check passed")
                return True
            except Exception as e:
                logger.warning(f"Vector store similarity search failed: {e}")
                return False
            finally:
                # Clean up connection
                if hasattr(vector_store, 'client') and vector_store.client:
                    vector_store.client.close()
                    
        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            return False
    
    @log_execution_time()
    def update_incrementally(
        self,
        new_docs: List[Document],
        modified_docs: List[Document],
        deleted_sources: List[str],
        use_batch_processing: bool = True,
        batch_size: int = 50
    ) -> bool:
        """
        Update vector store incrementally by adding new/modified docs and removing deleted ones.
        
        Args:
            new_docs: List of new documents to add
            modified_docs: List of modified documents to update
            deleted_sources: List of source paths to remove
            use_batch_processing: Whether to use batch processing
            batch_size: Batch size for processing
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing vector store
            vector_store = self.load_vector_store()
            
            if vector_store is None:
                logger.error("Could not load existing vector store for incremental update")
                return False
            
            # Step 1: Remove deleted documents
            if deleted_sources:
                logger.info(f"Removing {len(deleted_sources)} deleted documents")
                if use_batch_processing and len(deleted_sources) > batch_size:
                    success = self.remove_documents_batch(vector_store, deleted_sources, batch_size)
                else:
                    success = self.remove_documents_by_source(vector_store, deleted_sources)
                if not success:
                    logger.error("Failed to remove deleted documents")
                    return False
            
            # Step 2: Remove old versions of modified documents
            if modified_docs:
                modified_sources = [doc.metadata.get("source", "") for doc in modified_docs]
                logger.info(f"Removing old versions of {len(modified_sources)} modified documents")
                if use_batch_processing and len(modified_sources) > batch_size:
                    success = self.remove_documents_batch(vector_store, modified_sources, batch_size)
                else:
                    success = self.remove_documents_by_source(vector_store, modified_sources)
                if not success:
                    logger.error("Failed to remove old versions of modified documents")
                    return False
            
            # Step 3: Add new and modified documents
            all_docs_to_add = new_docs + modified_docs
            if all_docs_to_add:
                logger.info(f"Adding {len(all_docs_to_add)} documents ({len(new_docs)} new, {len(modified_docs)} modified)")
                if use_batch_processing and len(all_docs_to_add) > batch_size:
                    success = self.add_documents_batch(vector_store, all_docs_to_add, batch_size)
                else:
                    success = self.add_documents(vector_store, all_docs_to_add)
                if not success:
                    logger.error("Failed to add new/modified documents")
                    return False
            
            # Close the vector store connection
            if hasattr(vector_store, 'client') and vector_store.client:
                vector_store.client.close()
            
            logger.info("Incremental vector store update completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during incremental vector store update: {e}")
            return False
    
    @handle_exceptions(default_return=False)
    def collection_exists(self) -> bool:
        """
        Check if the Qdrant collection exists.
        
        Returns:
            True if collection exists, False otherwise
        """
        client = None
        try:
            if self.qdrant_url:
                # Use remote Qdrant
                client = QdrantClient(url=self.qdrant_url, prefer_grpc=True)
            else:
                # Use local Qdrant
                client = QdrantClient(path=self.storage_path)
            
            # Get collection info to check if it exists
            try:
                client.get_collection(self.collection_name)
                logger.info(f"Collection '{self.collection_name}' exists")
                return True
            except Exception:
                logger.info(f"Collection '{self.collection_name}' does not exist")
                return False
                
        except Exception as e:
            logger.error(f"Error checking if collection exists: {e}")
            return False
        finally:
            if client is not None:
                client.close()
    
    @handle_exceptions(default_return=False)
    def create_collection(self) -> bool:
        """
        Create an empty Qdrant collection with proper configuration.
        
        Returns:
            True if collection created successfully, False otherwise
        """
        client = None
        try:
            if self.qdrant_url:
                # Use remote Qdrant
                client = QdrantClient(url=self.qdrant_url, prefer_grpc=True)
            else:
                # Use local Qdrant
                client = QdrantClient(path=self.storage_path)
            
            # Get embedding dimension from the model
            # Create a dummy embedding to get the dimension
            dummy_text = "test"
            dummy_embedding = self.embeddings.embed_query(dummy_text)
            vector_size = len(dummy_embedding)
            
            # Create collection with proper vector configuration
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )
            
            logger.info(f"Successfully created collection '{self.collection_name}' with vector size {vector_size}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False
        finally:
            if client is not None:
                client.close()
                

# Convenience functions for backward compatibility
def create_vector_store(
    documents: List[Document],
    storage_path: str = VECTOR_STORAGE_PATH,
    collection_name: str = QDRANT_COLLECTION,
    qdrant_url: str = QDRANT_URL,
    embedding_model: str = EMBEDDING_MODEL,
    force_recreate: bool = False
) -> Optional[QdrantVectorStore]:
    """Create a vector store from documents."""
    manager = VectorStoreManager(storage_path, collection_name, qdrant_url, embedding_model)
    return manager.create_vector_store(documents, force_recreate)


def load_vector_store(
    storage_path: str = VECTOR_STORAGE_PATH,
    collection_name: str = QDRANT_COLLECTION,
    qdrant_url: str = QDRANT_URL,
    embedding_model: str = EMBEDDING_MODEL
) -> Optional[QdrantVectorStore]:
    """Load an existing vector store."""
    manager = VectorStoreManager(storage_path, collection_name, qdrant_url, embedding_model)
    return manager.load_vector_store()


def add_documents_to_vector_store(
    vector_store: QdrantVectorStore,
    documents: List[Document]
) -> bool:
    """Add new documents to an existing vector store."""
    # Use default manager for this operation
    manager = VectorStoreManager()
    return manager.add_documents(vector_store, documents)


def remove_documents_from_vector_store(
    vector_store: QdrantVectorStore,
    document_sources: List[str]
) -> bool:
    """Remove documents from the vector store based on their source paths."""
    manager = VectorStoreManager()
    return manager.remove_documents_by_source(vector_store, document_sources)


def validate_vector_store_health(
    storage_path: str,
    collection_name: str,
    qdrant_url: str,
    embedding_model: str
) -> bool:
    """Validate that the vector store is healthy and accessible."""
    manager = VectorStoreManager(storage_path, collection_name, qdrant_url, embedding_model)
    return manager.validate_health()


def check_collection_exists(
    storage_path: str = VECTOR_STORAGE_PATH,
    collection_name: str = QDRANT_COLLECTION,
    qdrant_url: str = QDRANT_URL,
    embedding_model: str = EMBEDDING_MODEL
) -> bool:
    """Check if the Qdrant collection exists."""
    manager = VectorStoreManager(storage_path, collection_name, qdrant_url, embedding_model)
    return manager.collection_exists()


def create_collection_if_not_exists(
    storage_path: str = VECTOR_STORAGE_PATH,
    collection_name: str = QDRANT_COLLECTION,
    qdrant_url: str = QDRANT_URL,
    embedding_model: str = EMBEDDING_MODEL
) -> bool:
    """Create Qdrant collection if it doesn't exist."""
    manager = VectorStoreManager(storage_path, collection_name, qdrant_url, embedding_model)
    if not manager.collection_exists():
        return manager.create_collection()
    return True
