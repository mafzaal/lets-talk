"""
Refactored processors module - Main entry point for pipeline operations.

This module provides a simplified interface to the refactored pipeline services
while maintaining backward compatibility with the original processors.py API.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from langchain.schema.document import Document
from langchain_qdrant import QdrantVectorStore

from lets_talk.shared.config import (
    ADAPTIVE_CHUNKING,
    AUTO_DETECT_CHANGES,
    BASE_URL,
    BATCH_PAUSE_SECONDS,
    BATCH_SIZE,
    BLOG_BASE_URL,
    BLOG_DOCS_FILENAME,
    BLOG_STATS_FILENAME,
    BUILD_INFO_FILENAME,
    CHECKSUM_ALGORITHM,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHUNKING_STRATEGY,
    CI_SUMMARY_FILENAME,
    DATA_DIR,
    DATA_DIR_PATTERN,
    EMBEDDING_MODEL,
    ENABLE_BATCH_PROCESSING,
    ENABLE_PERFORMANCE_MONITORING,
    FORCE_RECREATE,
    HEALTH_REPORT_FILENAME,
    INCREMENTAL_MODE,
    INDEX_ONLY_PUBLISHED_POSTS,
    MAX_BACKUP_FILES,
    MAX_CONCURRENT_OPERATIONS,
    METADATA_CSV_FILE,
    OUTPUT_DIR,
    QDRANT_COLLECTION,
    QDRANT_URL,
    STATS_OUTPUT_DIR,
    USE_CHUNKING,
    VECTOR_STORAGE_PATH,
    WEB_URLS,
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
        data_dir_pattern: str = DATA_DIR_PATTERN,
        web_urls: List[str] = WEB_URLS,
        base_url: str = BASE_URL,
        blog_base_url: str = BLOG_BASE_URL,
        index_only_published_posts: bool = INDEX_ONLY_PUBLISHED_POSTS,
        output_dir: str = OUTPUT_DIR,
        stats_output_dir: str = STATS_OUTPUT_DIR,
        use_chunking: bool = USE_CHUNKING,
        chunking_strategy: ChunkingStrategy = CHUNKING_STRATEGY,
        adaptive_chunking:bool= ADAPTIVE_CHUNKING,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
        vector_storage_path: str = VECTOR_STORAGE_PATH,
        qdrant_url: str = QDRANT_URL,
        collection_name: str = QDRANT_COLLECTION,
        force_recreate: bool = FORCE_RECREATE,
        embedding_model: str = EMBEDDING_MODEL,
        incremental_mode: str = INCREMENTAL_MODE,
        checksum_algorithm: str = CHECKSUM_ALGORITHM,
        auto_detect_changes:bool=  AUTO_DETECT_CHANGES,
        enable_batch_processing: bool = ENABLE_BATCH_PROCESSING,
        batch_size: int = BATCH_SIZE,
        enbable_performance_monitoring: bool = ENABLE_PERFORMANCE_MONITORING,
        batch_pause_seconds:float = BATCH_PAUSE_SECONDS,
        max_concurrent_operations:int = MAX_CONCURRENT_OPERATIONS,
        max_backup_files:int= MAX_BACKUP_FILES,
        metadata_csv: str = METADATA_CSV_FILE,
        blog_stats_filename: str = BLOG_STATS_FILENAME,
        blog_docs_filename: str = BLOG_DOCS_FILENAME,
        health_report_filename: str = HEALTH_REPORT_FILENAME,
        ci_summary_filename: str = CI_SUMMARY_FILENAME,
        build_info_filename: str = BUILD_INFO_FILENAME,


        
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
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize configuration parameters
        # Data parameters
        self.data_dir = data_dir
        self.data_dir_pattern = data_dir_pattern
        self.web_urls = web_urls
        self.base_url = base_url
        self.blog_base_url = blog_base_url
        self.index_only_published_posts = index_only_published_posts

        # Checksum and incremental indexing parameters
        self.incremental_mode = incremental_mode
        self.checksum_algorithm = checksum_algorithm
        self.auto_detect_changes = auto_detect_changes

    

        # Chunking parameters
        self.use_chunking = use_chunking
        self.chunking_strategy = chunking_strategy
        self.adaptive_chunking = adaptive_chunking
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Vector store parameters
        self.vector_storage_path = vector_storage_path
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.force_recreate = force_recreate


    
        
        # Batch processing and performance monitoring parameters
        self.enable_batch_processing = enable_batch_processing
        self.batch_size = batch_size
        self.enbable_performance_monitoring = enbable_performance_monitoring
        self.batch_pause_seconds = batch_pause_seconds
        self.max_concurrent_operations = max_concurrent_operations

        # Backup and metadata parameters
        self.max_backup_files = max_backup_files

   

        # Output and storage parameters
        self.output_dir = output_dir
        self.stats_output_dir = stats_output_dir
        self.metadata_csv = metadata_csv        
        self.blog_stats_filename = blog_stats_filename
        self.blog_docs_filename = blog_docs_filename
        self.health_report_filename = health_report_filename
        self.ci_summary_filename = ci_summary_filename
        self.build_info_filename = build_info_filename
        
        # Set paths for metadata CSV and stats output directory
        
        # Ensure output directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(stats_output_dir, exist_ok=True)
        
        

        self.metadata_csv_path = os.path.join(stats_output_dir,metadata_csv)
        self.blog_stats_path = os.path.join(stats_output_dir, blog_stats_filename)
        self.blog_docs_path = os.path.join(stats_output_dir, blog_docs_filename)
        self.health_report_path = os.path.join(stats_output_dir, health_report_filename)
        self.ci_summary_path = os.path.join(stats_output_dir, ci_summary_filename)
        self.build_info_path = os.path.join(stats_output_dir, build_info_filename)
        
        # Log initialization details
        self.logger.info(f"Initializing PipelineProcessor with configuration:")
        self.logger.info(f"  - Data directory: {self.data_dir}")
        self.logger.info(f"  - Data pattern: {self.data_dir_pattern}")
        self.logger.info(f"  - Web URLs: {len(self.web_urls)} configured")
        self.logger.info(f"  - Base URL: {self.base_url}")
        self.logger.info(f"  - Blog base URL: {self.blog_base_url}")
        self.logger.info(f"  - Index only published: {self.index_only_published_posts}")
        self.logger.info(f"  - Output directory: {self.output_dir}")
        self.logger.info(f"  - Stats output directory: {self.stats_output_dir}")
        self.logger.info(f"  - Use chunking: {self.use_chunking}")
        self.logger.info(f"  - Chunking strategy: {self.chunking_strategy}")
        self.logger.info(f"  - Adaptive chunking: {self.adaptive_chunking}")
        self.logger.info(f"  - Chunk size: {self.chunk_size}")
        self.logger.info(f"  - Chunk overlap: {self.chunk_overlap}")
        self.logger.info(f"  - Vector storage path: {self.vector_storage_path}")
        self.logger.info(f"  - Qdrant URL: {self.qdrant_url}")
        self.logger.info(f"  - Collection name: {self.collection_name}")
        self.logger.info(f"  - Embedding model: {self.embedding_model}")
        self.logger.info(f"  - Force recreate: {self.force_recreate}")
        self.logger.info(f"  - Incremental mode: {self.incremental_mode}")
        self.logger.info(f"  - Checksum algorithm: {self.checksum_algorithm}")
        self.logger.info(f"  - Auto detect changes: {self.auto_detect_changes}")
        self.logger.info(f"  - Enable batch processing: {self.enable_batch_processing}")
        self.logger.info(f"  - Batch size: {self.batch_size}")
        self.logger.info(f"  - Performance monitoring: {self.enbable_performance_monitoring}")
        self.logger.info(f"  - Batch pause seconds: {self.batch_pause_seconds}")
        self.logger.info(f"  - Max concurrent operations: {self.max_concurrent_operations}")
        self.logger.info(f"  - Max backup files: {self.max_backup_files}")
        self.logger.info(f"  - Metadata CSV path: {self.metadata_csv_path}")
        self.logger.info(f"  - Blog stats path: {self.blog_stats_path}")
        self.logger.info(f"  - Blog docs path: {self.blog_docs_path}")
        self.logger.info(f"  - Health report path: {self.health_report_path}")
        self.logger.info(f"  - CI summary path: {self.ci_summary_path}")
        self.logger.info(f"  - Build info path: {self.build_info_path}")
        
        try:
            # Initialize services
            self.logger.debug("Initializing document loader service")
            self.document_loader = DocumentLoader(data_dir=data_dir,base_url=base_url,
                                                  blog_base_url=blog_base_url,
                                                  index_only_published_posts=index_only_published_posts,
                                                  data_dir_pattern=data_dir_pattern,
                                                  web_urls=web_urls)
            
            self.logger.debug("Initializing metadata manager service")
            self.metadata_manager = MetadataManager(metadata_csv_path=self.metadata_csv_path, checksum_algorithm=checksum_algorithm, max_backup_files= max_backup_files)
            
            self.logger.debug("Initializing vector store manager service")
            self.vector_store_manager = VectorStoreManager(
                vector_storage_path, collection_name, qdrant_url, embedding_model
            )
            
            self.logger.debug("Initializing chunking service")
            self.chunking_service = ChunkingService()
            
            self.logger.debug("Initializing performance monitor service")
            self.performance_monitor = PerformanceMonitor()
            
            self.logger.debug("Initializing optimization service")
            self.optimization_service = OptimizationService()
            
            self.logger.debug("Initializing backup manager service")
            self.backup_manager = BackupManager()
            
            self.logger.debug("Initializing health checker service")
            self.health_checker = HealthChecker(
                vector_storage_path, collection_name, qdrant_url, embedding_model, metadata_csv_path=self.metadata_csv_path
            )
            
            self.logger.info("PipelineProcessor initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PipelineProcessor: {e}")
            raise
    
    
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
        self.logger.info(f"Starting full document processing pipeline (force_recreate={force_recreate}, show_progress={show_progress})")
        
        try:
            # Step 1: Load documents
            self.logger.info("Step 1: Loading documents from data directory")
            documents = self.document_loader.load_documents(show_progress=show_progress)
            if not documents:
                self.logger.warning("No documents loaded from data directory")
                return False
            
            self.logger.info(f"Successfully loaded {len(documents)} documents")
            
            # Step 2: Add metadata including checksums
            self.logger.info("Step 2: Adding checksum metadata to documents")
            documents = self.metadata_manager.add_checksum_metadata(documents)
            self.logger.debug(f"Added checksum metadata to {len(documents)} documents")
            
            # Step 3: Split documents
            self.logger.info("Step 3: Splitting documents into chunks")
            split_docs = self.chunking_service.split_documents(documents)
            self.logger.info(f"Split {len(documents)} documents into {len(split_docs)} chunks")
            
            # Step 4: Create vector store
            self.logger.info(f"Step 4: Creating vector store (force_recreate={force_recreate})")
            vector_store = self.vector_store_manager.create_vector_store(
                split_docs, force_recreate=force_recreate
            )
            if vector_store is None:
                self.logger.error("Failed to create vector store")
                return False
            
            self.logger.info("Vector store created successfully")
            
            # Step 5: Save metadata
            self.logger.info("Step 5: Saving metadata to CSV file")
            self.metadata_manager.save_metadata_csv(documents)
            self.logger.debug(f"Metadata saved to {self.metadata_csv_path}")
            
            # Step 6: Update indexed status
            self.logger.info("Step 6: Updating indexed status for documents")
            document_sources = [doc.metadata.get("source", "") for doc in documents]
            self.metadata_manager.update_indexed_status(document_sources, "indexed")
            self.logger.debug(f"Updated indexed status for {len(document_sources)} documents")
            
            # Monitor performance
            self.performance_monitor.monitor_operation(
                "full_processing", start_time, len(documents), len(split_docs)
            )
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Full document processing completed successfully in {elapsed_time:.2f} seconds")
            self.logger.info(f"Processing summary: {len(documents)} documents → {len(split_docs)} chunks")
            return True
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"Error in full document processing after {elapsed_time:.2f} seconds: {e}")
            self.logger.exception("Full stack trace:")
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
        self.logger.info(f"Starting incremental document processing (batch_processing={use_batch_processing}, batch_size={batch_size})")
        
        try:
            # Create backup
            self.logger.info("Creating metadata backup before incremental processing")
            backup_path = self.backup_manager.create_backup(self.metadata_csv_path)
            if backup_path:
                self.logger.debug(f"Backup created at: {backup_path}")
            else:
                self.logger.warning("Failed to create metadata backup")
            
            # Load current documents
            self.logger.info("Loading current documents for change detection")
            current_docs = self.document_loader.load_documents(show_progress=False)
            if not current_docs:
                self.logger.warning("No current documents found, skipping incremental processing")
                return True
            
            self.logger.debug(f"Loaded {len(current_docs)} current documents")
            
            # Add checksums to current documents
            self.logger.debug("Adding checksum metadata to current documents")
            current_docs = self.metadata_manager.add_checksum_metadata(current_docs)
            
            # Detect changes
            self.logger.info("Detecting document changes")
            changes = self.metadata_manager.detect_document_changes(current_docs)
            
            # Process only changed documents
            new_docs = changes["new"]
            modified_docs = changes["modified"]
            deleted_sources = changes["deleted_sources"]
            
            self.logger.info(f"Change detection results:")
            self.logger.info(f"  - New documents: {len(new_docs)}")
            self.logger.info(f"  - Modified documents: {len(modified_docs)}")
            self.logger.info(f"  - Deleted documents: {len(deleted_sources)}")
            
            if not (new_docs or modified_docs or deleted_sources):
                self.logger.info("No changes detected, skipping processing")
                return True
            
            # Split changed documents
            docs_to_split = new_docs + modified_docs
            if docs_to_split:
                self.logger.info(f"Splitting {len(docs_to_split)} changed documents into chunks")
                split_docs = self.chunking_service.split_documents(docs_to_split)
                self.logger.info(f"Split into {len(split_docs)} chunks")
            else:
                split_docs = []
                self.logger.debug("No documents to split")
            
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
                
                self.logger.debug(f"Separated chunks: {len(split_new_docs)} new, {len(split_modified_docs)} modified")
            
            # Update vector store incrementally
            self.logger.info("Updating vector store incrementally")
            success = self.vector_store_manager.update_incrementally(
                split_new_docs, split_modified_docs, deleted_sources,
                use_batch_processing, batch_size
            )
            
            if not success:
                self.logger.error("Failed to update vector store incrementally")
                if backup_path:
                    self.logger.warning("Restoring metadata backup due to failure")
                    self.backup_manager.restore_backup(backup_path, self.metadata_csv_path)
                return False
            
            self.logger.info("Vector store updated successfully")
            
            # Save updated metadata
            self.logger.info("Saving updated metadata to CSV")
            all_current_docs = current_docs  # Include all current docs in metadata
            self.metadata_manager.save_metadata_csv(all_current_docs)
            
            # Update indexed status for processed documents
            processed_sources = [doc.metadata.get("source", "") for doc in docs_to_split]
            if processed_sources:
                self.logger.debug(f"Updating indexed status for {len(processed_sources)} processed documents")
                self.metadata_manager.update_indexed_status(processed_sources, "indexed")
            
            # Monitor performance
            total_processed = len(new_docs) + len(modified_docs)
            self.performance_monitor.monitor_operation(
                "incremental_processing", start_time, total_processed, len(split_docs)
            )
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Incremental processing completed successfully in {elapsed_time:.2f} seconds")
            self.logger.info(f"Processing summary: {len(new_docs)} new, {len(modified_docs)} modified, {len(deleted_sources)} deleted")
            return True
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"Error in incremental processing after {elapsed_time:.2f} seconds: {e}")
            self.logger.exception("Full stack trace:")
            return False
    
    def health_check(self, comprehensive: bool = True) -> Dict[str, Any]:
        """
        Perform health check of the pipeline system.
        
        Args:
            comprehensive: Whether to perform comprehensive or quick check
            
        Returns:
            Health check results
        """
        self.logger.info(f"Starting {'comprehensive' if comprehensive else 'quick'} health check")
        
        try:
            if comprehensive:
                self.logger.debug("Performing comprehensive health check")
                results = self.health_checker.comprehensive_health_check()
            else:
                self.logger.debug("Performing quick health check")
                results = self.health_checker.quick_health_check()
            
            # Log health check summary
            overall_status = results.get("overall_status", "unknown")
            self.logger.info(f"Health check completed with overall status: {overall_status}")
            
            if overall_status == "healthy":
                self.logger.info("All systems are functioning normally")
            elif overall_status == "warning":
                self.logger.warning("Some systems have warnings - check detailed results")
            elif overall_status == "critical":
                self.logger.error("Critical issues detected - immediate attention required")
            
            # Log component statuses
            for component, status in results.items():
                if isinstance(status, dict) and "status" in status:
                    component_status = status["status"]
                    if component_status != "healthy":
                        self.logger.warning(f"Component '{component}' status: {component_status}")
                    else:
                        self.logger.debug(f"Component '{component}' status: {component_status}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error during health check: {e}")
            self.logger.exception("Health check exception details:")
            return {"overall_status": "error", "error": str(e)}


# Global processor instance for backward compatibility
_global_processor = None


def get_processor() -> PipelineProcessor:
    """Get or create the global processor instance."""
    global _global_processor
    if _global_processor is None:
        logger.info("Creating global PipelineProcessor instance")
        _global_processor = PipelineProcessor()
        logger.debug("Global PipelineProcessor instance created successfully")
    return _global_processor


# # Backward compatibility functions - these maintain the original API
# def load_blog_posts(
#     data_dir: str = DATA_DIR,
#     glob_pattern: str = "*.md",
#     recursive: bool = True,
#     show_progress: bool = True
# ) -> List[Document]:
#     """Load blog posts from the specified directory."""
#     loader = DocumentLoader(data_dir=data_dir)
#     return loader.load_documents(glob_pattern, recursive, show_progress)


# def update_document_metadata(
#     documents: List[Document],
#     data_dir_prefix: str = DATA_DIR,
#     blog_base_url: str = BLOG_BASE_URL,
#     base_url: str = BASE_URL,
#     remove_suffix: str = "index.md",
#     index_only_published_posts: bool = INDEX_ONLY_PUBLISHED_POSTS
# ) -> List[Document]:
#     """Update document metadata - now handled in DocumentLoader."""
#     # This is now handled automatically in DocumentLoader
#     # For backward compatibility, we just add checksums
#     manager = MetadataManager()
#     return manager.add_checksum_metadata(documents)


# def get_document_stats(documents: List[Document]) -> Dict[str, Any]:
#     """Get statistics about the documents."""
#     return DocumentStats.calculate_stats(documents)


# def display_document_stats(stats: Dict[str, Any]) -> None:
#     """Display document statistics in a readable format."""
#     DocumentStats.display_stats(stats)


# def split_documents(
#     documents: List[Document],
#     chunk_size: int = CHUNK_SIZE,
#     chunk_overlap: int = CHUNK_OVERLAP,
#     chunking_strategy: ChunkingStrategy = CHUNKING_STRATEGY
# ) -> List[Document]:
#     """Split documents into chunks for better embedding and retrieval."""
#     service = ChunkingService(chunk_size, chunk_overlap, chunking_strategy)
#     return service.split_documents(documents)


# def create_vector_store(
#     documents: List[Document],
#     storage_path: str = VECTOR_STORAGE_PATH,
#     collection_name: str = QDRANT_COLLECTION,
#     qdrant_url: str = QDRANT_URL,
#     embedding_model: str = EMBEDDING_MODEL,
#     force_recreate: bool = False
# ) -> Optional[QdrantVectorStore]:
#     """Create a vector store from the documents using Qdrant."""
#     manager = VectorStoreManager(storage_path, collection_name, qdrant_url, embedding_model)
#     return manager.create_vector_store(documents, force_recreate)


# def load_vector_store(
#     storage_path: str = VECTOR_STORAGE_PATH,
#     collection_name: str = QDRANT_COLLECTION,
#     qdrant_url: str = QDRANT_URL,
#     embedding_model: str = EMBEDDING_MODEL
# ) -> Optional[QdrantVectorStore]:
#     """Load an existing vector store."""
#     manager = VectorStoreManager(storage_path, collection_name, qdrant_url, embedding_model)
#     return manager.load_vector_store()


# def add_documents_to_vector_store(
#     vector_store: QdrantVectorStore,
#     documents: List[Document]
# ) -> bool:
#     """Add new documents to an existing vector store."""
#     manager = VectorStoreManager()
#     return manager.add_documents(vector_store, documents)


# def remove_documents_from_vector_store(
#     vector_store: QdrantVectorStore,
#     document_sources: List[str]
# ) -> bool:
#     """Remove documents from the vector store based on their source paths."""
#     manager = VectorStoreManager()
#     return manager.remove_documents_by_source(vector_store, document_sources)


# def update_vector_store_incrementally(
#     storage_path: str,
#     collection_name: str,
#     embedding_model: str,
#     qdrant_url: str,
#     new_docs: List[Document],
#     modified_docs: List[Document],
#     deleted_sources: List[str],
#     use_enhanced_mode: bool = ENABLE_BATCH_PROCESSING,
#     batch_size: int = BATCH_SIZE
# ) -> bool:
#     """Update vector store incrementally by adding new/modified docs and removing deleted ones."""
#     manager = VectorStoreManager(storage_path, collection_name, qdrant_url, embedding_model)
#     return manager.update_incrementally(
#         new_docs, modified_docs, deleted_sources, use_enhanced_mode, batch_size
#     )


# def update_vector_store_incrementally_with_rollback(
#     storage_path: str,
#     collection_name: str,
#     embedding_model: str,
#     qdrant_url: str,
#     new_docs: List[Document],
#     modified_docs: List[Document],
#     deleted_sources: List[str],
#     metadata_csv_path: str,
#     all_documents: List[Document]
# ) -> Tuple[bool, str]:
#     """Update vector store incrementally with comprehensive error handling and rollback."""
#     logger.info(f"Starting incremental update with rollback for collection '{collection_name}'")
#     logger.debug(f"Processing: {len(new_docs)} new, {len(modified_docs)} modified, {len(deleted_sources)} deleted documents")
    
#     processor = PipelineProcessor(
#         storage_path=storage_path,
#         collection_name=collection_name,
#         qdrant_url=qdrant_url,
#         embedding_model=embedding_model,
#         metadata_csv=metadata_csv_path
#     )
    
#     try:
#         success = processor.process_documents_incremental()
#         message = "Success" if success else "Failed"
        
#         if success:
#             logger.info("Incremental update with rollback completed successfully")
#         else:
#             logger.error("Incremental update with rollback failed")
            
#         return success, message
        
#     except Exception as e:
#         error_msg = str(e)
#         logger.error(f"Exception during incremental update with rollback: {error_msg}")
#         logger.exception("Full exception details:")
#         return False, error_msg


# # Import commonly used functions to maintain compatibility
# from .services.metadata_manager import (
#     add_checksum_metadata,
#     backup_metadata_csv,
#     calculate_content_checksum,
#     detect_document_changes,
#     get_file_modification_time,
#     load_existing_metadata,
#     restore_metadata_backup,
#     save_document_metadata_csv,
#     should_process_document
# )
# from .services.performance_monitor import (
#     apply_performance_optimizations,
#     get_processing_stats,
#     monitor_incremental_performance
# )
# from .services.health_checker import comprehensive_system_health_check
# from .services.vector_store_manager import validate_vector_store_health
# from .utils.batch_processor import (
#     batch_process_items,
#     chunk_list,
#     estimate_batch_size
# )
# from .utils.common_utils import (
#     format_file_size,
#     format_duration,
#     safe_int,
#     safe_float
# )

# Export all backward compatibility functions
__all__ = [
    # Main classes
    "PipelineProcessor",
    "get_processor",
    
    # Backward compatibility functions
    # "load_blog_posts",
    # "update_document_metadata", 
    # "get_document_stats",
    # "display_document_stats",
    # "split_documents",
    # "create_vector_store",
    # "load_vector_store",
    # "add_documents_to_vector_store",
    # "remove_documents_from_vector_store",
    # "update_vector_store_incrementally",
    # "update_vector_store_incrementally_with_rollback",
    
    # # Metadata functions
    # "add_checksum_metadata",
    # "backup_metadata_csv",
    # "calculate_content_checksum",
    # "detect_document_changes",
    # "get_file_modification_time",
    # "load_existing_metadata",
    # "restore_metadata_backup",
    # "save_document_metadata_csv",
    # "should_process_document",
    
    # # Performance functions
    # "apply_performance_optimizations",
    # "get_processing_stats",
    # "monitor_incremental_performance",
    
    # # Health and utility functions
    # "comprehensive_system_health_check",
    # "validate_vector_store_health",
    # "batch_process_items",
    # "chunk_list",
    # "estimate_batch_size",
    # "format_file_size",
    # "format_duration",
    # "safe_int",
    # "safe_float",
]
