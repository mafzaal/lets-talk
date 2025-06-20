"""
Refactored processors module - Main entry point for pipeline operations.

This module provides a simplified interface to the refactored pipeline services
while maintaining backward compatibility with the original processors.py API.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from langchain.schema.document import Document
from langchain_qdrant import QdrantVectorStore

from lets_talk.shared.config import (
    BASE_URL,
    BATCH_SIZE,
    BLOG_BASE_URL,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHUNKING_STRATEGY,
    DATA_DIR,
    EMBEDDING_MODEL,
    ENABLE_BATCH_PROCESSING,
    INDEX_ONLY_PUBLISHED_POSTS,
    METADATA_CSV_FILE,
    QDRANT_COLLECTION,
    QDRANT_URL,
    VECTOR_STORAGE_PATH,
    ChunkingStrategy
)

# Import from refactored services
from .services.chunking_service import ChunkingService
from .services.document_loader import DocumentLoader, DocumentStats
from .services.health_checker import HealthChecker
from .services.metadata_manager import BackupManager, MetadataManager
from .services.performance_monitor import OptimizationService, PerformanceMonitor
from .services.vector_store_manager import VectorStoreManager
from .utils.batch_processor import BatchProcessor

logger = logging.getLogger(__name__)


class PipelineProcessor:
    """
    Main pipeline processor that orchestrates all document processing operations.
    """
    
    def __init__(
        self,
        data_dir: str = DATA_DIR,
        storage_path: str = VECTOR_STORAGE_PATH,
        collection_name: str = QDRANT_COLLECTION,
        qdrant_url: str = QDRANT_URL,
        embedding_model: str = EMBEDDING_MODEL,
        metadata_csv_path: str = METADATA_CSV_FILE
    ):
        """
        Initialize the pipeline processor.
        
        Args:
            data_dir: Directory containing blog posts
            storage_path: Path to vector store
            collection_name: Qdrant collection name
            qdrant_url: Qdrant server URL
            embedding_model: Embedding model name
            metadata_csv_path: Path to metadata CSV file
        """
        self.data_dir = data_dir
        self.storage_path = storage_path
        self.collection_name = collection_name
        self.qdrant_url = qdrant_url
        self.embedding_model = embedding_model
        self.metadata_csv_path = metadata_csv_path
        
        # Initialize services
        self.document_loader = DocumentLoader(data_dir=data_dir)
        self.metadata_manager = MetadataManager(metadata_csv_path=metadata_csv_path)
        self.vector_store_manager = VectorStoreManager(
            storage_path, collection_name, qdrant_url, embedding_model
        )
        self.chunking_service = ChunkingService()
        self.performance_monitor = PerformanceMonitor()
        self.optimization_service = OptimizationService()
        self.backup_manager = BackupManager()
        self.health_checker = HealthChecker(
            storage_path, collection_name, qdrant_url, embedding_model, metadata_csv_path
        )
    
    def process_documents_full(
        self,
        force_recreate: bool = False,
        show_progress: bool = True
    ) -> bool:
        """
        Process all documents and create/recreate the vector store.
        
        Args:
            force_recreate: Whether to force recreation of vector store
            show_progress: Whether to show progress
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        try:
            logger.info("Starting full document processing pipeline")
            
            # Step 1: Load documents
            documents = self.document_loader.load_documents(show_progress=show_progress)
            if not documents:
                logger.warning("No documents loaded")
                return False
            
            # Step 2: Add metadata including checksums
            documents = self.metadata_manager.add_checksum_metadata(documents)
            
            # Step 3: Split documents
            split_docs = self.chunking_service.split_documents(documents)
            
            # Step 4: Create vector store
            vector_store = self.vector_store_manager.create_vector_store(
                split_docs, force_recreate=force_recreate
            )
            if vector_store is None:
                logger.error("Failed to create vector store")
                return False
            
            # Step 5: Save metadata
            self.metadata_manager.save_metadata_csv(documents)
            
            # Step 6: Update indexed status
            document_sources = [doc.metadata.get("source", "") for doc in documents]
            self.metadata_manager.update_indexed_status(document_sources, "indexed")
            
            # Monitor performance
            self.performance_monitor.monitor_operation(
                "full_processing", start_time, len(documents), len(split_docs)
            )
            
            logger.info(f"Successfully processed {len(documents)} documents into {len(split_docs)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error in full document processing: {e}")
            return False
    
    def process_documents_incremental(
        self,
        use_batch_processing: bool = ENABLE_BATCH_PROCESSING,
        batch_size: int = BATCH_SIZE
    ) -> bool:
        """
        Process documents incrementally, updating only what has changed.
        
        Args:
            use_batch_processing: Whether to use batch processing
            batch_size: Batch size for processing
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        try:
            logger.info("Starting incremental document processing")
            
            # Create backup
            backup_path = self.backup_manager.create_backup(self.metadata_csv_path)
            
            # Load current documents
            current_docs = self.document_loader.load_documents(show_progress=False)
            if not current_docs:
                logger.warning("No current documents found")
                return True
            
            # Add checksums to current documents
            current_docs = self.metadata_manager.add_checksum_metadata(current_docs)
            
            # Detect changes
            changes = self.metadata_manager.detect_document_changes(current_docs)
            
            # Process only changed documents
            new_docs = changes["new"]
            modified_docs = changes["modified"]
            deleted_sources = changes["deleted_sources"]
            
            if not (new_docs or modified_docs or deleted_sources):
                logger.info("No changes detected, skipping processing")
                return True
            
            # Split changed documents
            docs_to_split = new_docs + modified_docs
            if docs_to_split:
                split_docs = self.chunking_service.split_documents(docs_to_split)
            else:
                split_docs = []
            
            # Separate split docs by type
            split_new_docs = []
            split_modified_docs = []
            
            if split_docs:
                new_sources = {doc.metadata.get("source", "") for doc in new_docs}
                for doc in split_docs:
                    if doc.metadata.get("source", "") in new_sources:
                        split_new_docs.append(doc)
                    else:
                        split_modified_docs.append(doc)
            
            # Update vector store incrementally
            success = self.vector_store_manager.update_incrementally(
                split_new_docs, split_modified_docs, deleted_sources,
                use_batch_processing, batch_size
            )
            
            if not success:
                logger.error("Failed to update vector store incrementally")
                if backup_path:
                    logger.info("Restoring metadata backup")
                    self.backup_manager.restore_backup(backup_path, self.metadata_csv_path)
                return False
            
            # Save updated metadata
            all_current_docs = current_docs  # Include all current docs in metadata
            self.metadata_manager.save_metadata_csv(all_current_docs)
            
            # Update indexed status for processed documents
            processed_sources = [doc.metadata.get("source", "") for doc in docs_to_split]
            self.metadata_manager.update_indexed_status(processed_sources, "indexed")
            
            # Monitor performance
            total_processed = len(new_docs) + len(modified_docs)
            self.performance_monitor.monitor_operation(
                "incremental_processing", start_time, total_processed, len(split_docs)
            )
            
            logger.info(f"Incremental processing completed: {len(new_docs)} new, "
                       f"{len(modified_docs)} modified, {len(deleted_sources)} deleted")
            return True
            
        except Exception as e:
            logger.error(f"Error in incremental processing: {e}")
            return False
    
    def health_check(self, comprehensive: bool = True) -> Dict[str, Any]:
        """
        Perform health check of the pipeline system.
        
        Args:
            comprehensive: Whether to perform comprehensive or quick check
            
        Returns:
            Health check results
        """
        if comprehensive:
            return self.health_checker.comprehensive_health_check()
        else:
            return self.health_checker.quick_health_check()


# Global processor instance for backward compatibility
_global_processor = None


def get_processor() -> PipelineProcessor:
    """Get or create the global processor instance."""
    global _global_processor
    if _global_processor is None:
        _global_processor = PipelineProcessor()
    return _global_processor


# Backward compatibility functions - these maintain the original API
def load_blog_posts(
    data_dir: str = DATA_DIR,
    glob_pattern: str = "*.md",
    recursive: bool = True,
    show_progress: bool = True
) -> List[Document]:
    """Load blog posts from the specified directory."""
    loader = DocumentLoader(data_dir=data_dir)
    return loader.load_documents(glob_pattern, recursive, show_progress)


def update_document_metadata(
    documents: List[Document],
    data_dir_prefix: str = DATA_DIR,
    blog_base_url: str = BLOG_BASE_URL,
    base_url: str = BASE_URL,
    remove_suffix: str = "index.md",
    index_only_published_posts: bool = INDEX_ONLY_PUBLISHED_POSTS
) -> List[Document]:
    """Update document metadata - now handled in DocumentLoader."""
    # This is now handled automatically in DocumentLoader
    # For backward compatibility, we just add checksums
    manager = MetadataManager()
    return manager.add_checksum_metadata(documents)


def get_document_stats(documents: List[Document]) -> Dict[str, Any]:
    """Get statistics about the documents."""
    return DocumentStats.calculate_stats(documents)


def display_document_stats(stats: Dict[str, Any]) -> None:
    """Display document statistics in a readable format."""
    DocumentStats.display_stats(stats)


def split_documents(
    documents: List[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    chunking_strategy: ChunkingStrategy = CHUNKING_STRATEGY
) -> List[Document]:
    """Split documents into chunks for better embedding and retrieval."""
    service = ChunkingService(chunk_size, chunk_overlap, chunking_strategy)
    return service.split_documents(documents)


def create_vector_store(
    documents: List[Document],
    storage_path: str = VECTOR_STORAGE_PATH,
    collection_name: str = QDRANT_COLLECTION,
    qdrant_url: str = QDRANT_URL,
    embedding_model: str = EMBEDDING_MODEL,
    force_recreate: bool = False
) -> Optional[QdrantVectorStore]:
    """Create a vector store from the documents using Qdrant."""
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
    manager = VectorStoreManager()
    return manager.add_documents(vector_store, documents)


def remove_documents_from_vector_store(
    vector_store: QdrantVectorStore,
    document_sources: List[str]
) -> bool:
    """Remove documents from the vector store based on their source paths."""
    manager = VectorStoreManager()
    return manager.remove_documents_by_source(vector_store, document_sources)


def update_vector_store_incrementally(
    storage_path: str,
    collection_name: str,
    embedding_model: str,
    qdrant_url: str,
    new_docs: List[Document],
    modified_docs: List[Document],
    deleted_sources: List[str],
    use_enhanced_mode: bool = ENABLE_BATCH_PROCESSING,
    batch_size: int = BATCH_SIZE
) -> bool:
    """Update vector store incrementally by adding new/modified docs and removing deleted ones."""
    manager = VectorStoreManager(storage_path, collection_name, qdrant_url, embedding_model)
    return manager.update_incrementally(
        new_docs, modified_docs, deleted_sources, use_enhanced_mode, batch_size
    )


def update_vector_store_incrementally_with_rollback(
    storage_path: str,
    collection_name: str,
    embedding_model: str,
    qdrant_url: str,
    new_docs: List[Document],
    modified_docs: List[Document],
    deleted_sources: List[str],
    metadata_csv_path: str,
    all_documents: List[Document]
) -> Tuple[bool, str]:
    """Update vector store incrementally with comprehensive error handling and rollback."""
    processor = PipelineProcessor(
        storage_path=storage_path,
        collection_name=collection_name,
        qdrant_url=qdrant_url,
        embedding_model=embedding_model,
        metadata_csv_path=metadata_csv_path
    )
    
    try:
        success = processor.process_documents_incremental()
        return success, "Success" if success else "Failed"
    except Exception as e:
        return False, str(e)


# Import commonly used functions to maintain compatibility
from .services.metadata_manager import (
    add_checksum_metadata,
    backup_metadata_csv,
    calculate_content_checksum,
    detect_document_changes,
    get_file_modification_time,
    load_existing_metadata,
    restore_metadata_backup,
    save_document_metadata_csv,
    should_process_document
)
from .services.performance_monitor import (
    apply_performance_optimizations,
    get_processing_stats,
    monitor_incremental_performance
)
from .services.health_checker import comprehensive_system_health_check
from .services.vector_store_manager import validate_vector_store_health
from .utils.batch_processor import (
    batch_process_items,
    chunk_list,
    estimate_batch_size
)
from .utils.common_utils import (
    format_file_size,
    format_duration,
    safe_int,
    safe_float
)

# Export all backward compatibility functions
__all__ = [
    # Main classes
    "PipelineProcessor",
    
    # Backward compatibility functions
    "load_blog_posts",
    "update_document_metadata", 
    "get_document_stats",
    "display_document_stats",
    "split_documents",
    "create_vector_store",
    "load_vector_store",
    "add_documents_to_vector_store",
    "remove_documents_from_vector_store",
    "update_vector_store_incrementally",
    "update_vector_store_incrementally_with_rollback",
    
    # Metadata functions
    "add_checksum_metadata",
    "backup_metadata_csv",
    "calculate_content_checksum",
    "detect_document_changes",
    "get_file_modification_time",
    "load_existing_metadata",
    "restore_metadata_backup",
    "save_document_metadata_csv",
    "should_process_document",
    
    # Performance functions
    "apply_performance_optimizations",
    "get_processing_stats",
    "monitor_incremental_performance",
    
    # Health and utility functions
    "comprehensive_system_health_check",
    "validate_vector_store_health",
    "batch_process_items",
    "chunk_list",
    "estimate_batch_size",
    "format_file_size",
    "format_duration",
    "safe_int",
    "safe_float",
]
