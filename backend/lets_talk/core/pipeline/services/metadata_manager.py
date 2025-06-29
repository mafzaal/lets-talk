"""
Metadata management module.

This module handles document metadata operations including checksums,
CSV storage, change detection, and backup management.
"""

import hashlib
import logging
import os
import shutil
import time
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
from langchain.schema.document import Document

from lets_talk.shared.config import (
    CHECKSUM_ALGORITHM,
    METADATA_CSV_FILE,
    MAX_BACKUP_FILES
)
from ..utils.common_utils import handle_exceptions, log_execution_time

logger = logging.getLogger(__name__)


class MetadataManager:
    """
    Manages document metadata operations including checksums and CSV storage.
    """
    
    def __init__(
        self,
        metadata_csv_path: str = METADATA_CSV_FILE,
        checksum_algorithm: str = CHECKSUM_ALGORITHM,
        max_backup_files: int = MAX_BACKUP_FILES
    ):
        """
        Initialize the metadata manager.
        
        Args:
            metadata_csv_path: Path to metadata CSV file
            checksum_algorithm: Algorithm for content checksums
            max_backup_files: Maximum number of backup files to keep
        """
        self.metadata_csv_path = metadata_csv_path
        self.checksum_algorithm = checksum_algorithm
        self.max_backup_files = max_backup_files
    
    def calculate_content_checksum(self, content: str) -> str:
        """
        Calculate checksum of document content.
        
        Args:
            content: The text content to hash
            
        Returns:
            Hexadecimal string representation of the hash
        """
        if self.checksum_algorithm.lower() == "md5":
            hash_obj = hashlib.md5()
        elif self.checksum_algorithm.lower() == "sha256":
            hash_obj = hashlib.sha256()
        else:
            raise ValueError(f"Unsupported hash algorithm: {self.checksum_algorithm}")
        
        hash_obj.update(content.encode('utf-8'))
        return hash_obj.hexdigest()
    
    @staticmethod
    def get_file_modification_time(file_path: str) -> float:
        """
        Get file modification timestamp.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File modification time as timestamp
        """
        try:
            return os.path.getmtime(file_path)
        except OSError:
            return 0.0
    
    def add_checksum_metadata(self, documents: List[Document]) -> List[Document]:
        """
        Add checksum and timing metadata to documents.
        
        Args:
            documents: List of Document objects to process
            
        Returns:
            Updated list of Document objects with checksum metadata
        """
        for doc in documents:
            # Calculate content checksum
            doc.metadata["content_checksum"] = self.calculate_content_checksum(doc.page_content)
            
            # Get file modification time
            source_path = doc.metadata.get("source", "")
            doc.metadata["file_modified_time"] = self.get_file_modification_time(source_path)
            
            # Add indexing timestamp (will be updated when actually indexed)
            doc.metadata["indexed_timestamp"] = 0.0
            
            # Initialize indexing status
            doc.metadata["index_status"] = "pending"
            
            # Placeholder for chunk count (will be updated after chunking)
            doc.metadata["chunk_count"] = 1
        
        return documents
    
    @handle_exceptions(default_return={})
    def load_existing_metadata(self, metadata_csv_path: Optional[str] = None) -> Dict[str, Dict]:
        """
        Load existing metadata from CSV into a lookup dictionary.
        
        Args:
            metadata_csv_path: Path to the metadata CSV file (uses default if None)
            
        Returns:
            Dictionary with source paths as keys and metadata as values
        """
        csv_path = metadata_csv_path or self.metadata_csv_path
        
        if not os.path.exists(csv_path):
            logger.info(f"Metadata CSV file not found at {csv_path}")
            return {}
        
        try:
            df = pd.read_csv(csv_path)
            metadata_dict = {}
            
            for _, row in df.iterrows():
                source = row.get('source', '')
                if source:
                    metadata_dict[source] = row.to_dict()
            
            logger.info(f"Loaded metadata for {len(metadata_dict)} documents from {csv_path}")
            return metadata_dict
        except Exception as e:
            logger.error(f"Error loading metadata CSV: {e}")
            return {}
    
    def detect_document_changes(
        self,
        current_docs: List[Document],
        existing_metadata: Optional[Dict[str, Dict]] = None
    ) -> Dict[str, Any]:
        """
        Categorize documents based on changes compared to existing metadata.
        
        Args:
            current_docs: List of current Document objects
            existing_metadata: Dictionary of existing document metadata (loads from CSV if None)
            
        Returns:
            Dictionary with categories: new, modified, unchanged (List[Document]), deleted_sources (List[str])
        """
        if existing_metadata is None:
            existing_metadata = self.load_existing_metadata()
        
        new_docs = []
        modified_docs = []
        unchanged_docs = []
        current_sources = set()
        
        for doc in current_docs:
            source = doc.metadata.get("source", "")
            current_sources.add(source)
            
            if source not in existing_metadata:
                # New document
                new_docs.append(doc)
            else:
                existing_doc = existing_metadata[source]
                current_checksum = doc.metadata.get("content_checksum", "")
                existing_checksum = existing_doc.get("content_checksum", "")
                
                if current_checksum != existing_checksum:
                    # Modified document
                    modified_docs.append(doc)
                else:
                    # Unchanged document
                    unchanged_docs.append(doc)
        
        # Find deleted documents (in metadata but not in current docs)
        existing_sources = set(existing_metadata.keys())
        deleted_sources = list(existing_sources - current_sources)
        
        logger.info(f"Change detection: {len(new_docs)} new, {len(modified_docs)} modified, "
                   f"{len(unchanged_docs)} unchanged, {len(deleted_sources)} deleted")
        
        return {
            "new": new_docs,
            "modified": modified_docs,
            "unchanged": unchanged_docs,
            "deleted_sources": deleted_sources
        }
    
    def should_process_document(
        self,
        doc: Document,
        existing_metadata: Optional[Dict[str, Dict]] = None
    ) -> bool:
        """
        Determine if a document needs processing based on checksum comparison.
        
        Args:
            doc: Document object to check
            existing_metadata: Dictionary of existing document metadata
            
        Returns:
            True if document should be processed, False otherwise
        """
        if existing_metadata is None:
            existing_metadata = self.load_existing_metadata()
        
        source = doc.metadata.get("source", "")
        
        if source not in existing_metadata:
            return True  # New document
        
        current_checksum = doc.metadata.get("content_checksum", "")
        existing_checksum = existing_metadata[source].get("content_checksum", "")
        
        return current_checksum != existing_checksum
    
    @handle_exceptions(default_return=False)
    @log_execution_time()
    def save_metadata_csv(
        self,
        documents: List[Document],
        metadata_csv_path: Optional[str] = None
    ) -> bool:
        """
        Save document metadata to CSV file.
        
        Args:
            documents: List of Document objects
            metadata_csv_path: Path to save the CSV file (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        csv_path = metadata_csv_path or self.metadata_csv_path
        
        try:
            # Extract metadata for CSV
            metadata_records = []
            
            for doc in documents:
                metadata = doc.metadata.copy()
                
                # Ensure required fields exist
                metadata.setdefault("content_checksum", "")
                metadata.setdefault("file_modified_time", 0.0)
                metadata.setdefault("indexed_timestamp", 0.0)
                metadata.setdefault("index_status", "pending")
                metadata.setdefault("chunk_count", 1)
                
                metadata_records.append(metadata)
            
            # Convert to DataFrame and save
            df = pd.DataFrame(metadata_records)
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            
            # Save to CSV
            df.to_csv(csv_path, index=False)
            logger.info(f"Saved metadata for {len(documents)} documents to {csv_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving metadata CSV: {e}")
            return False
    
    def update_indexed_status(
        self,
        document_sources: List[str],
        status: str = "indexed",
        timestamp: Optional[float] = None
    ) -> bool:
        """
        Update the indexed status and timestamp for specific documents.
        
        Args:
            document_sources: List of document source paths to update
            status: New status to set
            timestamp: Timestamp to set (current time if None)
            
        Returns:
            True if successful, False otherwise
        """
        if timestamp is None:
            timestamp = time.time()
        
        try:
            # Load existing metadata
            existing_metadata = self.load_existing_metadata()
            
            # Update status for specified documents
            updated_count = 0
            for source in document_sources:
                if source in existing_metadata:
                    existing_metadata[source]["indexed_timestamp"] = timestamp
                    existing_metadata[source]["index_status"] = status
                    updated_count += 1
            
            # Convert back to documents for saving
            # This is a bit of a hack, but maintains compatibility
            if updated_count > 0:
                # Create dummy documents with updated metadata
                dummy_docs = []
                for source, metadata in existing_metadata.items():
                    doc = Document(page_content="", metadata=metadata)
                    dummy_docs.append(doc)
                
                self.save_metadata_csv(dummy_docs)
                logger.info(f"Updated indexed status for {updated_count} documents")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating indexed status: {e}")
            return False


class BackupManager:
    """
    Manages backup operations for metadata files.
    """
    
    def __init__(self, max_backup_files: int = MAX_BACKUP_FILES):
        """
        Initialize the backup manager.
        
        Args:
            max_backup_files: Maximum number of backup files to keep
        """
        self.max_backup_files = max_backup_files
    
    @handle_exceptions(default_return=None)
    def create_backup(self, file_path: str) -> Optional[str]:
        """
        Create a backup of a file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to the backup file if successful, None otherwise
        """
        if not os.path.exists(file_path):
            logger.warning(f"File not found for backup: {file_path}")
            return None
        
        try:
            timestamp = int(time.time())
            backup_path = f"{file_path}.backup.{timestamp}"
            
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup at {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    @handle_exceptions(default_return=False)
    def restore_backup(self, backup_path: str, original_path: str) -> bool:
        """
        Restore a file from backup.
        
        Args:
            backup_path: Path to the backup file
            original_path: Path to restore to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            shutil.copy2(backup_path, original_path)
            logger.info(f"Restored file from backup {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    @handle_exceptions()
    def cleanup_old_backups(self, file_path: str) -> None:
        """
        Clean up old backup files, keeping only the most recent ones.
        
        Args:
            file_path: Path to the original file
        """
        try:
            import glob
            
            backup_pattern = f"{file_path}.backup.*"
            backup_files = glob.glob(backup_pattern)
            
            if len(backup_files) <= self.max_backup_files:
                return
            
            # Sort by modification time (newest first)
            backup_files.sort(key=os.path.getmtime, reverse=True)
            
            # Remove oldest backups
            files_to_remove = backup_files[self.max_backup_files:]
            for backup_file in files_to_remove:
                try:
                    os.remove(backup_file)
                except OSError:
                    pass  # Ignore errors removing backup files
            
            logger.info(f"Cleaned up {len(files_to_remove)} old backup files")
            
        except Exception as e:
            logger.warning(f"Error cleaning up old backups: {e}")


# Convenience functions for backward compatibility
def calculate_content_checksum(content: str, algorithm: str = CHECKSUM_ALGORITHM) -> str:
    """Calculate checksum of document content."""
    manager = MetadataManager(checksum_algorithm=algorithm)
    return manager.calculate_content_checksum(content)


def get_file_modification_time(file_path: str) -> float:
    """Get file modification timestamp."""
    return MetadataManager.get_file_modification_time(file_path)


def add_checksum_metadata(documents: List[Document]) -> List[Document]:
    """Add checksum and timing metadata to documents."""
    manager = MetadataManager()
    return manager.add_checksum_metadata(documents)


def load_existing_metadata(metadata_csv_path: str) -> Dict[str, Dict]:
    """Load existing metadata from CSV into a lookup dictionary."""
    manager = MetadataManager(metadata_csv_path=metadata_csv_path)
    return manager.load_existing_metadata()


def detect_document_changes(current_docs: List[Document], 
                          existing_metadata: Dict[str, Dict]) -> Dict[str, Any]:
    """Categorize documents based on changes compared to existing metadata."""
    manager = MetadataManager()
    return manager.detect_document_changes(current_docs, existing_metadata)


def should_process_document(doc: Document, existing_metadata: Dict[str, Dict]) -> bool:
    """Determine if a document needs processing based on checksum comparison."""
    manager = MetadataManager()
    return manager.should_process_document(doc, existing_metadata)


def save_document_metadata_csv(documents: List[Document], 
                              metadata_csv_path: str) -> bool:
    """Save document metadata to CSV file."""
    manager = MetadataManager(metadata_csv_path=metadata_csv_path)
    return manager.save_metadata_csv(documents)


def backup_metadata_csv(metadata_csv_path: str) -> Optional[str]:
    """Create a backup of the metadata CSV file."""
    backup_manager = BackupManager()
    return backup_manager.create_backup(metadata_csv_path)


def restore_metadata_backup(backup_path: str, original_path: str) -> bool:
    """Restore metadata from backup file."""
    backup_manager = BackupManager()
    return backup_manager.restore_backup(backup_path, original_path)
