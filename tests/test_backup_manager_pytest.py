#!/usr/bin/env python3
"""
Pytest test suite for the MetadataManager and BackupManager classes.

This test script covers:
- MetadataManager functionality including checksums, CSV operations, and change detection
- BackupManager functionality including backup creation, restoration, and cleanup
- Convenience functions for backward compatibility
- Error handling and edge cases
"""

import os
import sys
import shutil
import tempfile
import pytest
import time
import glob
from pathlib import Path
from typing import Dict, List
from unittest.mock import patch, MagicMock

import pandas as pd
from langchain.schema.document import Document

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

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


class TestBackupManager:
    """Test suite for BackupManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def backup_manager(self):
        """Create a BackupManager instance for testing."""
        return BackupManager(max_backup_files=3)
    
    @pytest.fixture
    def test_file(self, temp_dir):
        """Create a test file for backup operations."""
        file_path = os.path.join(temp_dir, "test_file.txt")
        with open(file_path, 'w') as f:
            f.write("This is test content for backup operations.")
        return file_path
    
    def test_backup_manager_initialization(self):
        """Test BackupManager initialization with different parameters."""
        # Test default initialization
        manager = BackupManager()
        assert manager.max_backup_files == 3  # Default from config
        
        # Test custom initialization
        manager = BackupManager(max_backup_files=5)
        assert manager.max_backup_files == 5
    
    def test_create_backup_success(self, backup_manager, test_file):
        """Test successful backup creation."""
        backup_path = backup_manager.create_backup(test_file)
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
        assert backup_path.startswith(test_file + ".backup.")
        
        # Verify backup content matches original
        with open(test_file, 'r') as original:
            original_content = original.read()
        with open(backup_path, 'r') as backup:
            backup_content = backup.read()
        
        assert original_content == backup_content
    
    def test_create_backup_nonexistent_file(self, backup_manager, temp_dir):
        """Test backup creation for non-existent file."""
        nonexistent_file = os.path.join(temp_dir, "nonexistent.txt")
        backup_path = backup_manager.create_backup(nonexistent_file)
        
        assert backup_path is None
    
    def test_create_backup_permission_error(self, backup_manager, test_file):
        """Test backup creation with permission error."""
        with patch('shutil.copy2', side_effect=PermissionError("Permission denied")):
            backup_path = backup_manager.create_backup(test_file)
            assert backup_path is None
    
    def test_restore_backup_success(self, backup_manager, test_file, temp_dir):
        """Test successful backup restoration."""
        # Create a backup
        backup_path = backup_manager.create_backup(test_file)
        assert backup_path is not None
        
        # Modify the original file
        with open(test_file, 'w') as f:
            f.write("Modified content")
        
        # Create a new target file path
        restore_path = os.path.join(temp_dir, "restored_file.txt")
        
        # Restore from backup
        success = backup_manager.restore_backup(backup_path, restore_path)
        
        assert success is True
        assert os.path.exists(restore_path)
        
        # Verify restored content matches original backup
        with open(restore_path, 'r') as restored:
            restored_content = restored.read()
        assert restored_content == "This is test content for backup operations."
    
    def test_restore_backup_failure(self, backup_manager, temp_dir):
        """Test backup restoration failure scenarios."""
        backup_path = os.path.join(temp_dir, "nonexistent_backup.txt")
        restore_path = os.path.join(temp_dir, "restore_target.txt")
        
        success = backup_manager.restore_backup(backup_path, restore_path)
        assert success is False
    
    def test_restore_backup_permission_error(self, backup_manager, test_file, temp_dir):
        """Test backup restoration with permission error."""
        backup_path = backup_manager.create_backup(test_file)
        restore_path = os.path.join(temp_dir, "restore_target.txt")
        
        with patch('shutil.copy2', side_effect=PermissionError("Permission denied")):
            success = backup_manager.restore_backup(backup_path, restore_path)
            assert success is False
    
    def test_cleanup_old_backups_no_cleanup_needed(self, backup_manager, test_file):
        """Test cleanup when number of backups is within limit."""
        # Create 2 backups (less than max_backup_files=3)
        backup1 = backup_manager.create_backup(test_file)
        time.sleep(0.1)  # Ensure different timestamps
        backup2 = backup_manager.create_backup(test_file)
        
        assert backup1 is not None
        assert backup2 is not None
        
        # Run cleanup
        backup_manager.cleanup_old_backups(test_file)
        
        # Both backups should still exist
        assert os.path.exists(backup1)
        assert os.path.exists(backup2)
    
    def test_cleanup_old_backups_with_cleanup(self, backup_manager, test_file):
        """Test cleanup when number of backups exceeds limit."""
        backups = []
        
        # Create 5 backups (exceeds max_backup_files=3)
        # Use longer delays to ensure different timestamps
        for i in range(5):
            backup_path = backup_manager.create_backup(test_file)
            backups.append(backup_path)
            time.sleep(1.1)  # Ensure different timestamps (1+ second)
        
        # Verify all backups exist initially and are unique
        unique_backups = set(backup for backup in backups if backup is not None)
        assert len(unique_backups) == 5, f"Expected 5 unique backups, got {len(unique_backups)}: {unique_backups}"
        
        for backup in backups:
            assert backup is not None
            assert os.path.exists(backup)
        
        # Run cleanup
        backup_manager.cleanup_old_backups(test_file)
        
        # Check which backups still exist after cleanup
        import glob
        backup_pattern = f"{test_file}.backup.*"
        remaining_backups = glob.glob(backup_pattern)
        
        # Should keep only 3 most recent backups
        assert len(remaining_backups) == 3
        
        # Verify the remaining backups are the newest ones
        # Sort by modification time (newest first)
        remaining_backups.sort(key=os.path.getmtime, reverse=True)
        for backup in remaining_backups:
            assert os.path.exists(backup)
    
    def test_cleanup_old_backups_no_backups(self, backup_manager, test_file):
        """Test cleanup when no backup files exist."""
        # This should not raise any errors
        backup_manager.cleanup_old_backups(test_file)
    
    def test_cleanup_old_backups_glob_error(self, backup_manager, test_file):
        """Test cleanup with glob pattern errors."""
        with patch('glob.glob', side_effect=Exception("Glob error")):
            # Should not raise exception, just log warning
            backup_manager.cleanup_old_backups(test_file)
    
    def test_cleanup_old_backups_remove_error(self, backup_manager, test_file):
        """Test cleanup when file removal fails."""
        # Create backups that exceed limit
        backups = []
        for i in range(5):
            backup_path = backup_manager.create_backup(test_file)
            backups.append(backup_path)
            time.sleep(0.1)
        
        # Mock os.remove to fail for some files
        original_remove = os.remove
        def mock_remove(path):
            if path == backups[0]:  # Make first backup removal fail
                raise OSError("Permission denied")
            else:
                original_remove(path)
        
        with patch('os.remove', side_effect=mock_remove):
            # Should not raise exception, just ignore failed removals
            backup_manager.cleanup_old_backups(test_file)
    
    def test_multiple_backup_and_restore_cycle(self, backup_manager, test_file, temp_dir):
        """Test multiple backup and restore operations."""
        # Read original content from test_file fixture (before any modifications)
        with open(test_file, 'r') as f:
            original_content = f.read()
        
        # Create initial backup of original content
        backup1 = backup_manager.create_backup(test_file)
        assert backup1 is not None
        
        # Wait to ensure different timestamp for next backup
        time.sleep(1.1)
        
        # Now modify the file and create second backup
        modified_content_v1 = "Modified content v1"
        with open(test_file, 'w') as f:
            f.write(modified_content_v1)
        backup2 = backup_manager.create_backup(test_file)
        assert backup2 is not None
        
        # Verify backups have different names (different timestamps)
        assert backup1 != backup2, f"Backups should have different names: {backup1} vs {backup2}"
        
        # Restore from first backup (should have original content)
        restore_path1 = os.path.join(temp_dir, "restore1.txt")
        success1 = backup_manager.restore_backup(backup1, restore_path1)
        assert success1 is True
        
        # Restore from second backup (should have first modification)
        restore_path2 = os.path.join(temp_dir, "restore2.txt")
        success2 = backup_manager.restore_backup(backup2, restore_path2)
        assert success2 is True
        
        # Verify content in restored files
        with open(restore_path1, 'r') as f:
            content1 = f.read()
        with open(restore_path2, 'r') as f:
            content2 = f.read()
        
        assert content1 == original_content  # First backup should have original content
        assert content2 == modified_content_v1  # Second backup should have first modification
        assert content1 != content2
    
    def test_backup_preserves_file_metadata(self, backup_manager, test_file):
        """Test that backup preserves file metadata (timestamps, permissions)."""
        # Get original file stats
        original_stat = os.stat(test_file)
        
        # Create backup
        backup_path = backup_manager.create_backup(test_file)
        assert backup_path is not None
        
        # Get backup file stats
        backup_stat = os.stat(backup_path)
        
        # Verify that shutil.copy2 preserved timestamps
        assert abs(original_stat.st_mtime - backup_stat.st_mtime) < 1.0
        assert original_stat.st_mode == backup_stat.st_mode
    
    def test_concurrent_backup_operations(self, backup_manager, test_file):
        """Test multiple backup operations with timestamps."""
        backups = []
        
        # Create multiple backups with longer delays to ensure different timestamps
        for i in range(3):
            backup_path = backup_manager.create_backup(test_file)
            backups.append(backup_path)
            # Longer delay to ensure different timestamps
            time.sleep(1.1)
        
        # Verify all backups were created successfully
        for backup in backups:
            assert backup is not None
            assert os.path.exists(backup)
        
        # Verify backups have different timestamps in their names
        timestamps = []
        for backup in backups:
            timestamp_str = backup.split('.backup.')[1]
            timestamps.append(int(timestamp_str))
        
        # All timestamps should be different due to 1+ second delays
        assert len(set(timestamps)) == 3  # All should be different
        
        # Verify timestamps are in ascending order (later backups have higher timestamps)
        for i in range(1, len(timestamps)):
            assert timestamps[i] > timestamps[i-1]


class TestBackupManagerConvenienceFunctions:
    """Test convenience functions for BackupManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def test_file(self, temp_dir):
        """Create a test file for backup operations."""
        file_path = os.path.join(temp_dir, "test_metadata.csv")
        content = "source,content_checksum,file_modified_time\n"
        content += "file1.txt,abc123,1234567890\n"
        content += "file2.txt,def456,1234567891\n"
        
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def test_backup_metadata_csv_success(self, test_file):
        """Test successful metadata CSV backup using convenience function."""
        backup_path = backup_metadata_csv(test_file)
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
        assert backup_path.startswith(test_file + ".backup.")
    
    def test_backup_metadata_csv_nonexistent_file(self, temp_dir):
        """Test metadata CSV backup for non-existent file."""
        nonexistent_file = os.path.join(temp_dir, "nonexistent.csv")
        backup_path = backup_metadata_csv(nonexistent_file)
        
        assert backup_path is None
    
    def test_restore_metadata_backup_success(self, test_file, temp_dir):
        """Test successful metadata backup restoration using convenience function."""
        # Create backup
        backup_path = backup_metadata_csv(test_file)
        assert backup_path is not None
        
        # Create target file for restoration
        restore_path = os.path.join(temp_dir, "restored_metadata.csv")
        
        # Restore backup
        success = restore_metadata_backup(backup_path, restore_path)
        
        assert success is True
        assert os.path.exists(restore_path)
        
        # Verify content matches
        with open(test_file, 'r') as original:
            original_content = original.read()
        with open(restore_path, 'r') as restored:
            restored_content = restored.read()
        
        assert original_content == restored_content
    
    def test_restore_metadata_backup_failure(self, temp_dir):
        """Test metadata backup restoration failure."""
        backup_path = os.path.join(temp_dir, "nonexistent_backup.csv")
        restore_path = os.path.join(temp_dir, "restore_target.csv")
        
        success = restore_metadata_backup(backup_path, restore_path)
        assert success is False


class TestBackupManagerIntegration:
    """Integration tests for BackupManager with real file operations."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_full_backup_workflow(self, temp_dir):
        """Test complete backup workflow with CSV metadata files."""
        manager = BackupManager(max_backup_files=2)
        
        # Create a metadata CSV file
        csv_file = os.path.join(temp_dir, "blog_metadata.csv")
        original_data = {
            'source': ['file1.md', 'file2.md'],
            'content_checksum': ['hash1', 'hash2'],
            'file_modified_time': [1234567890, 1234567891],
            'indexed_timestamp': [1234567892, 1234567893],
            'index_status': ['indexed', 'indexed'],
            'chunk_count': [3, 5]
        }
        df = pd.DataFrame(original_data)
        df.to_csv(csv_file, index=False)
        
        # Create first backup
        backup1 = manager.create_backup(csv_file)
        assert backup1 is not None
        
        # Wait to ensure different timestamp
        time.sleep(1.1)
        
        # Modify the CSV file
        modified_data = original_data.copy()
        modified_data['source'].append('file3.md')
        modified_data['content_checksum'].append('hash3')
        modified_data['file_modified_time'].append(1234567894)
        modified_data['indexed_timestamp'].append(1234567895)
        modified_data['index_status'].append('indexed')
        modified_data['chunk_count'].append(2)
        
        df_modified = pd.DataFrame(modified_data)
        df_modified.to_csv(csv_file, index=False)
        
        # Create second backup
        backup2 = manager.create_backup(csv_file)
        assert backup2 is not None
        
        # Wait to ensure different timestamp
        time.sleep(1.1)
        
        # Add another row to the dataframe
        new_row = {
            'source': 'file4.md',
            'content_checksum': 'hash4',
            'file_modified_time': 1234567896,
            'indexed_timestamp': 1234567897,
            'index_status': 'pending',
            'chunk_count': 1
        }
        df_modified = pd.concat([df_modified, pd.DataFrame([new_row])], ignore_index=True)
        
        df_modified.to_csv(csv_file, index=False)
        backup3 = manager.create_backup(csv_file)
        assert backup3 is not None
        
        # Trigger cleanup
        manager.cleanup_old_backups(csv_file)
        
        # Check that only 2 backups remain
        backup_pattern = f"{csv_file}.backup.*"
        remaining_backups = glob.glob(backup_pattern)
        assert len(remaining_backups) == 2
        
        # Restore from one of the remaining backups
        restore_path = os.path.join(temp_dir, "restored_metadata.csv")
        success = manager.restore_backup(backup2, restore_path)
        assert success is True
        
        # Verify restored content
        restored_df = pd.read_csv(restore_path)
        assert len(restored_df) == 3  # Should have 3 rows (original 2 + 1 added)
        assert 'file3.md' in restored_df['source'].values
    
    def test_backup_manager_error_handling(self, temp_dir):
        """Test BackupManager error handling in various scenarios."""
        manager = BackupManager()
        
        # Test with invalid directory
        invalid_file = "/invalid/path/that/does/not/exist.csv"
        backup_path = manager.create_backup(invalid_file)
        assert backup_path is None
        
        # Test cleanup with invalid file
        manager.cleanup_old_backups(invalid_file)  # Should not raise exception
        
        # Test restore with invalid paths
        success = manager.restore_backup("/invalid/backup.csv", "/invalid/restore.csv")
        assert success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
