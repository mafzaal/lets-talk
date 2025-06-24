"""
Test suite for the MetadataManager module.

This test suite covers:
- MetadataManager class functionality
- BackupManager class functionality
- Checksum calculation
- Metadata persistence (CSV)
- Document change detection
- Status updates
- Backup operations
- Error handling
"""

import os
import tempfile
import shutil
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest
import pandas as pd
from langchain.schema.document import Document

# Add the backend directory to sys.path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from lets_talk.core.pipeline.services.metadata_manager import (
    MetadataManager,
    BackupManager,
    calculate_content_checksum,
    get_file_modification_time,
    add_checksum_metadata,
    load_existing_metadata,
    detect_document_changes,
    should_process_document,
    save_document_metadata_csv,
    backup_metadata_csv,
    restore_metadata_backup
)


class TestMetadataManager:
    """Test cases for MetadataManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def metadata_manager(self, temp_dir):
        """Create a MetadataManager instance for testing."""
        csv_path = os.path.join(temp_dir, "test_metadata.csv")
        return MetadataManager(metadata_csv_path=csv_path)
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample Document objects for testing."""
        return [
            Document(
                page_content="This is the first document content.",
                metadata={
                    "source": "/path/to/doc1.md",
                    "title": "Document 1",
                    "author": "Test Author"
                }
            ),
            Document(
                page_content="This is the second document content.",
                metadata={
                    "source": "/path/to/doc2.md", 
                    "title": "Document 2",
                    "author": "Test Author"
                }
            )
        ]
    
    def test_calculate_content_checksum_sha256(self, metadata_manager):
        """Test SHA256 checksum calculation."""
        content = "Test content for checksum"
        checksum = metadata_manager.calculate_content_checksum(content)
        
        # SHA256 should produce a 64-character hex string
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)
        
        # Same content should produce same checksum
        checksum2 = metadata_manager.calculate_content_checksum(content)
        assert checksum == checksum2
    
    def test_calculate_content_checksum_md5(self, temp_dir):
        """Test MD5 checksum calculation."""
        csv_path = os.path.join(temp_dir, "test_metadata.csv")
        manager = MetadataManager(metadata_csv_path=csv_path, checksum_algorithm="md5")
        
        content = "Test content for checksum"
        checksum = manager.calculate_content_checksum(content)
        
        # MD5 should produce a 32-character hex string
        assert len(checksum) == 32
        assert all(c in "0123456789abcdef" for c in checksum)
    
    def test_calculate_content_checksum_invalid_algorithm(self, temp_dir):
        """Test invalid checksum algorithm raises ValueError."""
        csv_path = os.path.join(temp_dir, "test_metadata.csv")
        manager = MetadataManager(metadata_csv_path=csv_path, checksum_algorithm="invalid")
        
        with pytest.raises(ValueError, match="Unsupported hash algorithm"):
            manager.calculate_content_checksum("test content")
    
    @patch('os.path.getmtime')
    def test_get_file_modification_time(self, mock_getmtime):
        """Test file modification time retrieval."""
        mock_getmtime.return_value = 1234567890.0
        
        timestamp = MetadataManager.get_file_modification_time("/path/to/file.md")
        assert timestamp == 1234567890.0
        mock_getmtime.assert_called_once_with("/path/to/file.md")
    
    @patch('os.path.getmtime')
    def test_get_file_modification_time_file_not_found(self, mock_getmtime):
        """Test file modification time when file doesn't exist."""
        mock_getmtime.side_effect = OSError("File not found")
        
        timestamp = MetadataManager.get_file_modification_time("/nonexistent/file.md")
        assert timestamp == 0.0
    
    @patch('os.path.getmtime')
    def test_add_checksum_metadata(self, mock_getmtime, metadata_manager, sample_documents):
        """Test adding checksum metadata to documents."""
        mock_getmtime.return_value = 1234567890.0
        
        updated_docs = metadata_manager.add_checksum_metadata(sample_documents)
        
        assert len(updated_docs) == 2
        
        for doc in updated_docs:
            assert "content_checksum" in doc.metadata
            assert "file_modified_time" in doc.metadata
            assert "indexed_timestamp" in doc.metadata
            assert "index_status" in doc.metadata
            assert "chunk_count" in doc.metadata
            
            assert doc.metadata["file_modified_time"] == 1234567890.0
            assert doc.metadata["indexed_timestamp"] == 0.0
            assert doc.metadata["index_status"] == "pending"
            assert doc.metadata["chunk_count"] == 1
            
            # Verify checksum is calculated
            assert len(doc.metadata["content_checksum"]) == 64  # SHA256
    
    def test_load_existing_metadata_file_not_found(self, metadata_manager):
        """Test loading metadata when file doesn't exist."""
        metadata = metadata_manager.load_existing_metadata()
        assert metadata == {}
    
    def test_load_existing_metadata_success(self, metadata_manager, temp_dir):
        """Test successful loading of existing metadata."""
        # Create test CSV file
        csv_data = {
            'source': ['/path/to/doc1.md', '/path/to/doc2.md'],
            'content_checksum': ['abc123', 'def456'],
            'file_modified_time': [1234567890.0, 1234567891.0],
            'indexed_timestamp': [1234567892.0, 1234567893.0],
            'index_status': ['indexed', 'indexed'],
            'chunk_count': [1, 2]
        }
        df = pd.DataFrame(csv_data)
        df.to_csv(metadata_manager.metadata_csv_path, index=False)
        
        metadata = metadata_manager.load_existing_metadata()
        
        assert len(metadata) == 2
        assert '/path/to/doc1.md' in metadata
        assert '/path/to/doc2.md' in metadata
        assert metadata['/path/to/doc1.md']['content_checksum'] == 'abc123'
        assert metadata['/path/to/doc2.md']['content_checksum'] == 'def456'
    
    @patch('pandas.read_csv')
    def test_load_existing_metadata_error(self, mock_read_csv, metadata_manager):
        """Test error handling in load_existing_metadata."""
        mock_read_csv.side_effect = Exception("CSV read error")
        
        metadata = metadata_manager.load_existing_metadata()
        assert metadata == {}
    
    def test_detect_document_changes(self, metadata_manager, sample_documents):
        """Test document change detection."""
        # Add checksum metadata to documents
        docs_with_metadata = metadata_manager.add_checksum_metadata(sample_documents)
        
        # Create existing metadata (same content, so should be unchanged)
        existing_metadata = {
            '/path/to/doc1.md': {
                'source': '/path/to/doc1.md',
                'content_checksum': docs_with_metadata[0].metadata['content_checksum'],
                'file_modified_time': 1234567890.0
            },
            '/path/to/doc3.md': {
                'source': '/path/to/doc3.md', 
                'content_checksum': 'old_checksum',
                'file_modified_time': 1234567890.0
            }
        }
        
        changes = metadata_manager.detect_document_changes(docs_with_metadata, existing_metadata)
        
        assert len(changes['new']) == 1  # doc2 is new
        assert len(changes['modified']) == 0  # no modified docs
        assert len(changes['unchanged']) == 1  # doc1 is unchanged
        assert len(changes['deleted_sources']) == 1  # doc3 was deleted
        
        assert changes['new'][0].metadata['source'] == '/path/to/doc2.md'
        assert changes['unchanged'][0].metadata['source'] == '/path/to/doc1.md'
        assert '/path/to/doc3.md' in changes['deleted_sources']
    
    def test_detect_document_changes_with_modifications(self, metadata_manager):
        """Test detection of modified documents."""
        # Create document with different content
        doc = Document(
            page_content="Modified content",
            metadata={"source": "/path/to/doc1.md"}
        )
        doc_with_metadata = metadata_manager.add_checksum_metadata([doc])[0]
        
        # Create existing metadata with different checksum
        existing_metadata = {
            '/path/to/doc1.md': {
                'source': '/path/to/doc1.md',
                'content_checksum': 'different_checksum',
                'file_modified_time': 1234567890.0
            }
        }
        
        changes = metadata_manager.detect_document_changes([doc_with_metadata], existing_metadata)
        
        assert len(changes['modified']) == 1
        assert changes['modified'][0].metadata['source'] == '/path/to/doc1.md'
    
    def test_should_process_document_new(self, metadata_manager, sample_documents):
        """Test should_process_document for new document."""
        doc_with_metadata = metadata_manager.add_checksum_metadata(sample_documents)[0]
        
        should_process = metadata_manager.should_process_document(doc_with_metadata, {})
        assert should_process is True
    
    def test_should_process_document_unchanged(self, metadata_manager, sample_documents):
        """Test should_process_document for unchanged document."""
        doc_with_metadata = metadata_manager.add_checksum_metadata(sample_documents)[0]
        
        existing_metadata = {
            '/path/to/doc1.md': {
                'content_checksum': doc_with_metadata.metadata['content_checksum']
            }
        }
        
        should_process = metadata_manager.should_process_document(doc_with_metadata, existing_metadata)
        assert should_process is False
    
    def test_should_process_document_modified(self, metadata_manager, sample_documents):
        """Test should_process_document for modified document."""
        doc_with_metadata = metadata_manager.add_checksum_metadata(sample_documents)[0]
        
        existing_metadata = {
            '/path/to/doc1.md': {
                'content_checksum': 'different_checksum'
            }
        }
        
        should_process = metadata_manager.should_process_document(doc_with_metadata, existing_metadata)
        assert should_process is True
    
    def test_save_metadata_csv_success(self, metadata_manager, sample_documents, temp_dir):
        """Test successful saving of metadata to CSV."""
        docs_with_metadata = metadata_manager.add_checksum_metadata(sample_documents)
        
        success = metadata_manager.save_metadata_csv(docs_with_metadata)
        assert success is True
        
        # Verify file was created
        assert os.path.exists(metadata_manager.metadata_csv_path)
        
        # Verify content
        df = pd.read_csv(metadata_manager.metadata_csv_path)
        assert len(df) == 2
        assert 'source' in df.columns
        assert 'content_checksum' in df.columns
        assert 'file_modified_time' in df.columns
        assert 'indexed_timestamp' in df.columns
        assert 'index_status' in df.columns
        assert 'chunk_count' in df.columns
    
    @patch('pandas.DataFrame.to_csv')
    def test_save_metadata_csv_error(self, mock_to_csv, metadata_manager, sample_documents):
        """Test error handling in save_metadata_csv."""
        mock_to_csv.side_effect = Exception("CSV write error")
        
        docs_with_metadata = metadata_manager.add_checksum_metadata(sample_documents)
        success = metadata_manager.save_metadata_csv(docs_with_metadata)
        assert success is False
    
    def test_update_indexed_status(self, metadata_manager, temp_dir):
        """Test updating indexed status for documents."""
        # Create initial metadata CSV
        csv_data = {
            'source': ['/path/to/doc1.md', '/path/to/doc2.md'],
            'content_checksum': ['abc123', 'def456'],
            'file_modified_time': [1234567890.0, 1234567891.0],
            'indexed_timestamp': [0.0, 0.0],
            'index_status': ['pending', 'pending'],
            'chunk_count': [1, 2]
        }
        df = pd.DataFrame(csv_data)
        df.to_csv(metadata_manager.metadata_csv_path, index=False)
        
        # Update status
        timestamp = 1234567900.0  # Use fixed timestamp for consistent testing
        success = metadata_manager.update_indexed_status(
            ['/path/to/doc1.md'], 
            status='indexed',
            timestamp=timestamp
        )
        
        assert success is True
        
        # Verify update
        updated_metadata = metadata_manager.load_existing_metadata()
        assert updated_metadata['/path/to/doc1.md']['index_status'] == 'indexed'
        assert updated_metadata['/path/to/doc1.md']['indexed_timestamp'] == timestamp
        assert updated_metadata['/path/to/doc2.md']['index_status'] == 'pending'  # unchanged
    
    def test_update_indexed_status_nonexistent_source(self, metadata_manager):
        """Test updating status for non-existent document source."""
        success = metadata_manager.update_indexed_status(['/nonexistent/doc.md'])
        assert success is True  # Should succeed but not update anything


class TestBackupManager:
    """Test cases for BackupManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def backup_manager(self):
        """Create a BackupManager instance for testing."""
        return BackupManager(max_backup_files=3)
    
    def test_create_backup_success(self, backup_manager, temp_dir):
        """Test successful backup creation."""
        # Create a test file
        test_file = os.path.join(temp_dir, "test_file.csv")
        with open(test_file, 'w') as f:
            f.write("test,data\n1,2\n")
        
        backup_path = backup_manager.create_backup(test_file)
        
        assert backup_path is not None
        assert backup_path.startswith(test_file + ".backup.")
        assert os.path.exists(backup_path)
        
        # Verify backup content
        with open(backup_path, 'r') as f:
            content = f.read()
        assert content == "test,data\n1,2\n"
    
    def test_create_backup_file_not_found(self, backup_manager, temp_dir):
        """Test backup creation when file doesn't exist."""
        nonexistent_file = os.path.join(temp_dir, "nonexistent.csv")
        
        backup_path = backup_manager.create_backup(nonexistent_file)
        assert backup_path is None
    
    @patch('shutil.copy2')
    def test_create_backup_error(self, mock_copy2, backup_manager, temp_dir):
        """Test error handling in backup creation."""
        # Create a test file
        test_file = os.path.join(temp_dir, "test_file.csv")
        with open(test_file, 'w') as f:
            f.write("test data")
        
        mock_copy2.side_effect = Exception("Copy error")
        
        backup_path = backup_manager.create_backup(test_file)
        assert backup_path is None
    
    def test_restore_backup_success(self, backup_manager, temp_dir):
        """Test successful backup restoration."""
        # Create original and backup files
        original_file = os.path.join(temp_dir, "original.csv")
        backup_file = os.path.join(temp_dir, "backup.csv")
        
        with open(backup_file, 'w') as f:
            f.write("backup,data\n1,2\n")
        
        success = backup_manager.restore_backup(backup_file, original_file)
        assert success is True
        
        # Verify restoration
        assert os.path.exists(original_file)
        with open(original_file, 'r') as f:
            content = f.read()
        assert content == "backup,data\n1,2\n"
    
    @patch('shutil.copy2')
    def test_restore_backup_error(self, mock_copy2, backup_manager):
        """Test error handling in backup restoration."""
        mock_copy2.side_effect = Exception("Restore error")
        
        success = backup_manager.restore_backup("/backup/path", "/original/path")
        assert success is False
    
    def test_cleanup_old_backups(self, backup_manager, temp_dir):
        """Test cleanup of old backup files."""
        # Create original file
        original_file = os.path.join(temp_dir, "test_file.csv")
        with open(original_file, 'w') as f:
            f.write("test data")
        
        # Create multiple backup files with different timestamps
        backup_files = []
        base_time = int(time.time())
        for i in range(5):
            backup_path = f"{original_file}.backup.{base_time + i}"
            with open(backup_path, 'w') as f:
                f.write(f"backup {i}")
            backup_files.append(backup_path)
            # Set different modification times
            os.utime(backup_path, (base_time + i, base_time + i))
        
        # Run cleanup
        backup_manager.cleanup_old_backups(original_file)
        
        # Check that only max_backup_files (3) remain
        remaining_backups = [f for f in backup_files if os.path.exists(f)]
        assert len(remaining_backups) == 3
        
        # Verify that the oldest files were removed
        removed_count = len(backup_files) - len(remaining_backups)
        assert removed_count == 2
    
    def test_cleanup_old_backups_no_backups(self, backup_manager, temp_dir):
        """Test cleanup when no backup files exist."""
        original_file = os.path.join(temp_dir, "test_file.csv")
        
        # Should not raise an error
        backup_manager.cleanup_old_backups(original_file)
    
    def test_cleanup_old_backups_fewer_than_max(self, backup_manager, temp_dir):
        """Test cleanup when backup count is less than max."""
        # Create original file
        original_file = os.path.join(temp_dir, "test_file.csv")
        with open(original_file, 'w') as f:
            f.write("test data")
        
        # Create only 2 backup files (less than max of 3)
        backup_files = []
        for i in range(2):
            backup_path = f"{original_file}.backup.{int(time.time()) + i}"
            with open(backup_path, 'w') as f:
                f.write(f"backup {i}")
            backup_files.append(backup_path)
        
        # Run cleanup
        backup_manager.cleanup_old_backups(original_file)
        
        # All backups should remain
        for backup_file in backup_files:
            assert os.path.exists(backup_file)


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    def test_calculate_content_checksum_function(self):
        """Test the standalone calculate_content_checksum function."""
        content = "Test content"
        checksum = calculate_content_checksum(content)
        
        assert len(checksum) == 64  # SHA256 default
        assert all(c in "0123456789abcdef" for c in checksum)
    
    @patch('os.path.getmtime')
    def test_get_file_modification_time_function(self, mock_getmtime):
        """Test the standalone get_file_modification_time function."""
        mock_getmtime.return_value = 1234567890.0
        
        timestamp = get_file_modification_time("/path/to/file.md")
        assert timestamp == 1234567890.0
    
    def test_add_checksum_metadata_function(self):
        """Test the standalone add_checksum_metadata function."""
        docs = [
            Document(
                page_content="Test content",
                metadata={"source": "/path/to/doc.md"}
            )
        ]
        
        updated_docs = add_checksum_metadata(docs)
        
        assert len(updated_docs) == 1
        assert "content_checksum" in updated_docs[0].metadata
        assert "file_modified_time" in updated_docs[0].metadata
        assert "indexed_timestamp" in updated_docs[0].metadata
        assert "index_status" in updated_docs[0].metadata
        assert "chunk_count" in updated_docs[0].metadata
    
    def test_load_existing_metadata_function(self, tmp_path):
        """Test the standalone load_existing_metadata function."""
        csv_file = tmp_path / "test_metadata.csv"
        
        # Create test CSV
        csv_data = {
            'source': ['/path/to/doc1.md'],
            'content_checksum': ['abc123'],
            'file_modified_time': [1234567890.0]
        }
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_file, index=False)
        
        metadata = load_existing_metadata(str(csv_file))
        
        assert len(metadata) == 1
        assert '/path/to/doc1.md' in metadata
        assert metadata['/path/to/doc1.md']['content_checksum'] == 'abc123'
    
    def test_detect_document_changes_function(self):
        """Test the standalone detect_document_changes function."""
        docs = [
            Document(
                page_content="Test content",
                metadata={
                    "source": "/path/to/doc.md",
                    "content_checksum": "new_checksum"
                }
            )
        ]
        
        existing_metadata = {
            '/path/to/doc.md': {
                'content_checksum': 'old_checksum'
            }
        }
        
        changes = detect_document_changes(docs, existing_metadata)
        
        assert len(changes['modified']) == 1
        assert changes['modified'][0].metadata['source'] == '/path/to/doc.md'
    
    def test_should_process_document_function(self):
        """Test the standalone should_process_document function."""
        doc = Document(
            page_content="Test content",
            metadata={
                "source": "/path/to/doc.md",
                "content_checksum": "new_checksum"
            }
        )
        
        existing_metadata = {
            '/path/to/doc.md': {
                'content_checksum': 'old_checksum'
            }
        }
        
        should_process = should_process_document(doc, existing_metadata)
        assert should_process is True
    
    def test_save_document_metadata_csv_function(self, tmp_path):
        """Test the standalone save_document_metadata_csv function."""
        csv_file = tmp_path / "test_metadata.csv"
        
        docs = [
            Document(
                page_content="Test content",
                metadata={
                    "source": "/path/to/doc.md",
                    "content_checksum": "abc123",
                    "file_modified_time": 1234567890.0,
                    "indexed_timestamp": 0.0,
                    "index_status": "pending",
                    "chunk_count": 1
                }
            )
        ]
        
        success = save_document_metadata_csv(docs, str(csv_file))
        assert success is True
        assert csv_file.exists()
    
    def test_backup_metadata_csv_function(self, tmp_path):
        """Test the standalone backup_metadata_csv function."""
        csv_file = tmp_path / "test_metadata.csv"
        
        # Create test file
        with open(csv_file, 'w') as f:
            f.write("test,data\n1,2\n")
        
        backup_path = backup_metadata_csv(str(csv_file))
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
    
    def test_restore_metadata_backup_function(self, tmp_path):
        """Test the standalone restore_metadata_backup function."""
        backup_file = tmp_path / "backup.csv"
        original_file = tmp_path / "original.csv"
        
        # Create backup file
        with open(backup_file, 'w') as f:
            f.write("backup,data\n1,2\n")
        
        success = restore_metadata_backup(str(backup_file), str(original_file))
        assert success is True
        assert original_file.exists()


if __name__ == "__main__":
    pytest.main([__file__])
