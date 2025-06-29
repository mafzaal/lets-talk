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
    INCREMENTAL_FALLBACK_THRESHOLD,
    INCREMENTAL_MODE,
    INDEX_ONLY_PUBLISHED_POSTS,
    MAX_BACKUP_FILES,
    MAX_CONCURRENT_OPERATIONS,
    METADATA_CSV_FILE,
    OUTPUT_DIR,
    QDRANT_COLLECTION,
    QDRANT_URL,
    SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT,
    SEMANTIC_CHUNKER_BREAKPOINT_TYPE,
    SEMANTIC_CHUNKER_MIN_CHUNK_SIZE,
    STATS_OUTPUT_DIR,
    USE_CHUNKING,
    VECTOR_STORAGE_PATH,
    WEB_URLS,
    ChunkingStrategy,
    SemanticChunkerBreakpointType
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
        semantic_breakpoint_type: SemanticChunkerBreakpointType = SEMANTIC_CHUNKER_BREAKPOINT_TYPE,
        semantic_breakpoint_threshold_amount: float = SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT,
        semantic_min_chunk_size: int = SEMANTIC_CHUNKER_MIN_CHUNK_SIZE,
        vector_storage_path: str = VECTOR_STORAGE_PATH,
        qdrant_url: str = QDRANT_URL,
        collection_name: str = QDRANT_COLLECTION,
        force_recreate: bool = FORCE_RECREATE,
        embedding_model: str = EMBEDDING_MODEL,
        incremental_mode: str = INCREMENTAL_MODE,
        checksum_algorithm: str = CHECKSUM_ALGORITHM,
        auto_detect_changes:bool=  AUTO_DETECT_CHANGES,
        incremental_fallback_threshold: float = INCREMENTAL_FALLBACK_THRESHOLD,
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
            data_dir_pattern: Glob pattern for matching files in data directory
            web_urls: List of web URLs to process
            base_url: Base URL for generating absolute URLs
            blog_base_url: Base URL for blog posts
            index_only_published_posts: Whether to index only published posts
            output_dir: Directory for output files
            stats_output_dir: Directory for statistics and metadata files
            use_chunking: Whether to enable document chunking
            chunking_strategy: Strategy for document chunking
            adaptive_chunking: Whether to use adaptive chunking
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between consecutive chunks
            semantic_breakpoint_type: Type of semantic breakpoint for chunking
            semantic_breakpoint_threshold_amount: Threshold amount for semantic chunking
            semantic_min_chunk_size: Minimum size for semantic chunks
            vector_storage_path: Path to vector store storage
            qdrant_url: Qdrant server URL
            collection_name: Qdrant collection name
            force_recreate: Whether to force recreation of vector store
            embedding_model: Name of the embedding model to use
            incremental_mode: Mode for incremental processing
            checksum_algorithm: Algorithm for calculating checksums
            auto_detect_changes: Whether to automatically detect document changes
            incremental_fallback_threshold: Threshold for falling back to full indexing when too many changes detected
            enable_batch_processing: Whether to enable batch processing
            batch_size: Size of processing batches
            enbable_performance_monitoring: Whether to enable performance monitoring
            batch_pause_seconds: Pause duration between batches in seconds
            max_concurrent_operations: Maximum number of concurrent operations
            max_backup_files: Maximum number of backup files to retain
            metadata_csv: Name of the metadata CSV file
            blog_stats_filename: Name of the blog statistics file
            blog_docs_filename: Name of the blog documents file
            health_report_filename: Name of the health report file
            ci_summary_filename: Name of the CI summary file
            build_info_filename: Name of the build information file
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
        self.incremental_fallback_threshold = incremental_fallback_threshold

    

        # Chunking parameters
        self.use_chunking = use_chunking
        self.chunking_strategy = chunking_strategy
        self.adaptive_chunking = adaptive_chunking
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.semantic_breakpoint_type = semantic_breakpoint_type
        self.semantic_breakpoint_threshold_amount = semantic_breakpoint_threshold_amount
        self.semantic_min_chunk_size = semantic_min_chunk_size

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
        self.logger.info(f"  - Semantic breakpoint type: {self.semantic_breakpoint_type}")
        self.logger.info(f"  - Semantic breakpoint threshold amount: {self.semantic_breakpoint_threshold_amount}")
        self.logger.info(f"  - Semantic minimum chunk size: {self.semantic_min_chunk_size}")
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
            self.chunking_service = ChunkingService(chunk_size=chunk_size,
                                                    chunk_overlap=chunk_overlap,
                                                    chunking_strategy=chunking_strategy,
                                                    adaptive_chunking=adaptive_chunking,
                                                    semantic_breakpoint_type=semantic_breakpoint_type,
                                                    semantic_breakpoint_threshold_amount=semantic_breakpoint_threshold_amount,
                                                    semantic_min_chunk_size=semantic_min_chunk_size
                                                    )
            
            self.logger.debug("Initializing performance monitor service")
            self.performance_monitor = PerformanceMonitor(enable_monitoring=enbable_performance_monitoring)
            
            self.logger.debug("Initializing optimization service")
            self.optimization_service = OptimizationService(adaptive_chunking= adaptive_chunking,
                                                             chunk_size=chunk_size,
                                                             chunk_overlap=chunk_overlap
                                                             )
            
            self.logger.debug("Initializing backup manager service")
            self.backup_manager = BackupManager(max_backup_files=max_backup_files)
            
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
            if self.use_chunking:
                self.logger.info("Step 3: Splitting documents into chunks")
                split_docs = self.chunking_service.split_documents(documents)
                self.logger.info(f"Split {len(documents)} documents into {len(split_docs)} chunks")
            else:
                self.logger.info("Chunking is disabled, using original documents as chunks")
                split_docs = documents
                
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

    def _vector_store_exists(self) -> bool:
        """Check if vector store exists and is accessible."""
        try:
            # Check if collection exists and vector store can be loaded
            if not self.vector_store_manager.collection_exists():
                return False
            
            # Try to load the vector store to ensure it's accessible
            vector_store = self.vector_store_manager.load_vector_store()
            return vector_store is not None
        except Exception as e:
            self.logger.debug(f"Vector store existence check failed: {e}")
            return False
    
    def _metadata_exists(self) -> bool:
        """Check if metadata file exists and is readable."""
        try:
            return os.path.exists(self.metadata_csv_path) and os.path.isfile(self.metadata_csv_path)
        except Exception as e:
            self.logger.debug(f"Metadata file existence check failed: {e}")
            return False
    
    def _check_vector_store_compatibility(self) -> Tuple[bool, List[str]]:
        """
        Check if current configuration is compatible with existing vector store.
        
        Returns:
            Tuple of (is_compatible, list_of_issues)
        """
        issues = []
        
        try:
            # Load existing vector store to check compatibility
            existing_store = self.vector_store_manager.load_vector_store()
            if existing_store is None:
                issues.append("Cannot load existing vector store")
                return False, issues
            
            # Check embedding model compatibility
            # Note: This would require storing metadata about the vector store configuration
            # For now, we'll rely on vector store manager's internal checks
            
            # Check if collection exists and is accessible
            try:
                # Try to get collection info
                collection_info = existing_store.client.get_collection(self.collection_name)
                if collection_info is None:
                    issues.append(f"Collection '{self.collection_name}' does not exist")
                    return False, issues
            except Exception as e:
                issues.append(f"Cannot access collection '{self.collection_name}': {e}")
                return False, issues
            
            # Additional compatibility checks could be added here:
            # - Check if embedding dimensions match
            # - Check if chunking strategy metadata matches
            # - Check if document schema is compatible
            
            self.logger.debug("Vector store compatibility check passed")
            return True, issues
            
        except Exception as e:
            issues.append(f"Vector store compatibility check failed: {e}")
            self.logger.debug(f"Vector store compatibility check error: {e}")
            return False, issues
    
    def _should_fallback_to_full(self) -> bool:
        """
        Determine if we should fallback to full indexing based on change threshold.
        
        Returns:
            True if should fallback to full indexing, False otherwise
        """
        try:
            # Load current documents for change detection
            current_docs = self.document_loader.load_documents(show_progress=False)
            if not current_docs:
                self.logger.debug("No current documents found, recommending full indexing")
                return True
            
            # Add checksums to current documents
            current_docs = self.metadata_manager.add_checksum_metadata(current_docs)
            
            # Detect changes
            changes = self.metadata_manager.detect_document_changes(current_docs)
            
            # Calculate change ratio
            total_docs = len(current_docs)
            changed_docs = len(changes["new"]) + len(changes["modified"])
            
            if total_docs == 0:
                return True
            
            change_ratio = changed_docs / total_docs
            
            self.logger.debug(f"Change detection: {changed_docs}/{total_docs} documents changed ({change_ratio:.2%})")
            
            # Use threshold from instance configuration
            fallback_threshold = self.incremental_fallback_threshold
            if change_ratio > fallback_threshold:
                self.logger.info(f"Change ratio {change_ratio:.2%} exceeds threshold {fallback_threshold:.2%}, recommending full indexing")
                return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Error during change threshold check: {e}")
            # If we can't determine changes, be conservative and do full indexing
            return True
    
    def determine_indexing_strategy(self) -> str:
        """
        Determine whether to perform full or incremental indexing based on parameters.
        
        Returns:
            "full" or "incremental"
        """
        self.logger.info("Determining optimal indexing strategy")
        
        # 1. FORCE_RECREATE overrides everything
        if self.force_recreate:
            self.logger.info("Strategy decision: FULL (force_recreate=True)")
            return "full"
        
        # 2. Explicit incremental_mode setting
        if self.incremental_mode == "full":
            self.logger.info("Strategy decision: FULL (incremental_mode='full')")
            return "full"
        elif self.incremental_mode == "incremental":
            self.logger.info("Strategy decision: INCREMENTAL (incremental_mode='incremental')")
            return "incremental"
        
        # 3. Auto mode - check prerequisites
        if self.incremental_mode == "auto":
            self.logger.debug("Auto mode - checking prerequisites for incremental processing")
            
            # Check if vector store exists
            if not self._vector_store_exists():
                self.logger.info("Strategy decision: FULL (vector store does not exist)")
                return "full"
            
            # Check if metadata exists
            if not self._metadata_exists():
                self.logger.info("Strategy decision: FULL (metadata file does not exist)")
                return "full"
            
            # Check if auto_detect_changes is enabled
            if not self.auto_detect_changes:
                self.logger.info("Strategy decision: FULL (auto_detect_changes=False)")
                return "full"
            
            # Check vector store compatibility
            is_compatible, compatibility_issues = self._check_vector_store_compatibility()
            if not is_compatible:
                self.logger.info(f"Strategy decision: FULL (vector store compatibility issues: {', '.join(compatibility_issues)})")
                return "full"
            
            # Check change threshold (if we can detect changes)
            if self._should_fallback_to_full():
                self.logger.info("Strategy decision: FULL (change threshold exceeded)")
                return "full"
            
            self.logger.info("Strategy decision: INCREMENTAL (all prerequisites met)")
            return "incremental"
        
        # Default case
        self.logger.warning(f"Unknown incremental_mode '{self.incremental_mode}', defaulting to full processing")
        return "full"
    
    def process_documents(
        self,
        show_progress: bool = True
    ) -> Tuple[bool, str]:
        """
        Process documents using intelligent strategy determination.
        
        Args:
            show_progress: Whether to show progress during processing
            
        Returns:
            Tuple of (success, process_mode)
        """
        start_time = time.time()
        self.logger.info("Starting intelligent document processing")
        
        try:
            # Determine the optimal strategy
            strategy = self.determine_indexing_strategy()
            
            # Execute based on determined strategy
            if strategy == "full":
                self.logger.info("Executing full document processing")
                success = self.process_documents_full(
                    force_recreate=self.force_recreate, 
                    show_progress=show_progress
                )
            else:  # strategy == "incremental"
                self.logger.info("Executing incremental document processing")
                success = self.process_documents_incremental(
                    use_batch_processing=self.enable_batch_processing,
                    batch_size=self.batch_size
                )
            
            elapsed_time = time.time() - start_time
            
            if success:
                self.logger.info(f"Document processing completed successfully in {strategy} mode ({elapsed_time:.2f}s)")
            else:
                self.logger.error(f"Document processing failed in {strategy} mode ({elapsed_time:.2f}s)")
            
            return success, strategy
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"Error in intelligent document processing after {elapsed_time:.2f} seconds: {e}")
            self.logger.exception("Full stack trace:")
            return False, "unknown"


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


# Export all backward compatibility functions
__all__ = [
    # Main classes
    "PipelineProcessor",
    "get_processor",
]
