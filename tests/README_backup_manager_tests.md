# BackupManager Tests Documentation

This document describes the comprehensive test suite for the `BackupManager` class from the metadata manager module.

## Overview

The test suite `test_backup_manager_pytest.py` provides complete coverage of the `BackupManager` class functionality, including:

- **Backup creation and validation**
- **Backup restoration operations**
- **Automatic cleanup of old backups**
- **Error handling and edge cases**
- **Integration with real CSV metadata files**
- **Convenience function testing**

## Test Classes

### TestBackupManager

Core functionality tests for the BackupManager class:

#### Initialization Tests
- ✅ **test_backup_manager_initialization**: Tests proper initialization with default and custom parameters

#### Backup Creation Tests
- ✅ **test_create_backup_success**: Validates successful backup creation and content preservation
- ✅ **test_create_backup_nonexistent_file**: Tests handling of non-existent source files
- ✅ **test_create_backup_permission_error**: Validates error handling for permission issues

#### Backup Restoration Tests
- ✅ **test_restore_backup_success**: Tests successful backup restoration to new location
- ✅ **test_restore_backup_failure**: Validates handling of missing backup files
- ✅ **test_restore_backup_permission_error**: Tests error handling during restoration

#### Cleanup Operations Tests
- ✅ **test_cleanup_old_backups_no_cleanup_needed**: Tests cleanup when within backup limits
- ✅ **test_cleanup_old_backups_with_cleanup**: Validates proper cleanup of excess backups
- ✅ **test_cleanup_old_backups_no_backups**: Tests cleanup operation on non-existent backups
- ✅ **test_cleanup_old_backups_glob_error**: Tests error handling in glob operations
- ✅ **test_cleanup_old_backups_remove_error**: Validates graceful handling of file removal failures

#### Advanced Workflow Tests
- ✅ **test_multiple_backup_and_restore_cycle**: Tests complete backup/modify/restore workflow
- ✅ **test_backup_preserves_file_metadata**: Validates preservation of file timestamps and permissions
- ✅ **test_concurrent_backup_operations**: Tests timestamp uniqueness in multiple backups

### TestBackupManagerConvenienceFunctions

Tests for standalone convenience functions:

- ✅ **test_backup_metadata_csv_success**: Tests `backup_metadata_csv()` function
- ✅ **test_backup_metadata_csv_nonexistent_file**: Tests error handling in convenience function
- ✅ **test_restore_metadata_backup_success**: Tests `restore_metadata_backup()` function
- ✅ **test_restore_metadata_backup_failure**: Tests error handling in restore function

### TestBackupManagerIntegration

Integration tests with real CSV metadata files:

- ✅ **test_full_backup_workflow**: Complete workflow with CSV metadata files, including:
  - Multiple backup creation
  - CSV modifications between backups
  - Automatic cleanup triggering
  - Backup restoration and validation
- ✅ **test_backup_manager_error_handling**: Tests error scenarios with invalid paths

## Key Testing Insights

### Timestamp Collision Issue

During testing, we discovered that the `BackupManager` uses `int(time.time())` for backup timestamps, which can cause collisions when multiple backups are created within the same second. Our tests account for this by:

- Adding 1+ second delays between backup operations in tests
- Validating that backups have unique filenames when created with sufficient time gaps
- Testing the cleanup mechanism properly handles this timestamp-based naming

### Test Patterns

The tests follow these important patterns:

1. **Fixture Usage**: Temporary directories and test files are properly created and cleaned up
2. **Error Simulation**: Using `unittest.mock.patch` to simulate permission errors and other failures
3. **Content Validation**: All tests verify that backup content matches original content exactly
4. **Timing Considerations**: Tests account for timestamp resolution limitations

## Running the Tests

### Individual Test Classes
```bash
# Run all BackupManager tests
uv run pytest tests/test_backup_manager_pytest.py::TestBackupManager -v

# Run convenience function tests
uv run pytest tests/test_backup_manager_pytest.py::TestBackupManagerConvenienceFunctions -v

# Run integration tests
uv run pytest tests/test_backup_manager_pytest.py::TestBackupManagerIntegration -v
```

### All BackupManager Tests
```bash
# Run all backup-related tests
uv run pytest tests/test_backup_manager_pytest.py -v

# Run with coverage
uv run pytest tests/test_backup_manager_pytest.py --cov=lets_talk.core.pipeline.services.metadata_manager
```

### Specific Test Methods
```bash
# Test cleanup functionality
uv run pytest tests/test_backup_manager_pytest.py::TestBackupManager::test_cleanup_old_backups_with_cleanup -v

# Test backup creation
uv run pytest tests/test_backup_manager_pytest.py::TestBackupManager::test_create_backup_success -v
```

## Test Results Summary

- **Total Tests**: 21
- **Passing**: 21 ✅
- **Coverage**: Complete coverage of all BackupManager public methods
- **Edge Cases**: Comprehensive error handling and edge case testing
- **Integration**: Real-world scenarios with CSV metadata files

## Dependencies

The tests require:
- `pytest` - Testing framework
- `pandas` - For CSV file operations in integration tests
- `unittest.mock` - For error simulation
- `tempfile` - For temporary test directories
- `time` - For timestamp testing
- `glob` - For backup file pattern matching

## Best Practices Demonstrated

1. **Proper Resource Cleanup**: All temporary files and directories are cleaned up
2. **Error Handling Testing**: Comprehensive testing of error scenarios
3. **Content Validation**: Verification that backups preserve file content exactly
4. **Timing Awareness**: Tests account for system timestamp limitations
5. **Integration Testing**: Real-world scenarios with actual file operations
