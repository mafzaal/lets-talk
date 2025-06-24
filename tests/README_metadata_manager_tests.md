# Metadata Manager Tests

This directory contains comprehensive test suites for the metadata manager module.

## Overview

The `test_metadata_manager.py` file contains unit tests for the metadata management functionality, including:

- **MetadataManager class**: Core metadata operations including checksums, CSV storage, and change detection
- **BackupManager class**: Backup and restore operations for metadata files
- **Convenience functions**: Standalone utility functions for backward compatibility

## Test Coverage

### MetadataManager Tests

- ✅ **Checksum calculation**: SHA256 and MD5 hash algorithms
- ✅ **File modification time**: File timestamp retrieval and error handling
- ✅ **Metadata enhancement**: Adding checksum and timing metadata to documents
- ✅ **CSV operations**: Loading and saving metadata to/from CSV files
- ✅ **Change detection**: Identifying new, modified, unchanged, and deleted documents
- ✅ **Processing decisions**: Determining whether documents need reprocessing
- ✅ **Status updates**: Updating indexed status and timestamps
- ✅ **Error handling**: Graceful handling of file and data errors

### BackupManager Tests

- ✅ **Backup creation**: Creating timestamped backup files
- ✅ **Backup restoration**: Restoring files from backup copies
- ✅ **Cleanup operations**: Managing backup file retention and cleanup
- ✅ **Error scenarios**: Handling missing files and operation failures

### Convenience Functions Tests

- ✅ **Standalone functions**: Testing all backward-compatibility functions
- ✅ **Function equivalence**: Ensuring standalone functions work identically to class methods

## Running the Tests

### Using pytest directly:
```bash
cd /home/mafzaal/source/lets-talk
uv run pytest tests/test_metadata_manager.py -v
```

### Using the test runner script:
```bash
cd /home/mafzaal/source/lets-talk
./tests/run_metadata_manager_tests.py
```

### Running with coverage (if needed):
```bash
cd /home/mafzaal/source/lets-talk
uv run pytest tests/test_metadata_manager.py --cov=lets_talk.core.pipeline.services.metadata_manager
```

## Test Structure

### Test Classes

1. **TestMetadataManager**: Tests for the main MetadataManager class
2. **TestBackupManager**: Tests for the BackupManager class  
3. **TestConvenienceFunctions**: Tests for standalone utility functions

### Test Fixtures

- `temp_dir`: Creates temporary directories for file operations
- `metadata_manager`: Creates MetadataManager instances with test configurations
- `backup_manager`: Creates BackupManager instances for testing
- `sample_documents`: Provides sample Document objects for testing

### Mocking and Testing Strategies

- **File system mocking**: Using temporary directories and file mocking
- **Time mocking**: Controlling timestamps for consistent testing
- **Error injection**: Testing error handling paths with mock exceptions
- **Data validation**: Verifying CSV content and metadata integrity

## Key Test Scenarios

### Happy Path Testing
- Document processing with valid data
- Successful CSV operations
- Proper backup creation and restoration
- Correct change detection logic

### Edge Case Testing
- Empty document sets
- Missing files and directories
- Invalid hash algorithms
- CSV parsing errors

### Error Handling Testing
- File permission errors
- Disk space issues
- Corrupted data handling
- Network interruption simulation

## Dependencies

The tests require the following packages (automatically installed with `uv`):
- `pytest`: Testing framework
- `pytest-mock`: Mocking utilities
- `pytest-asyncio`: Async testing support
- `pytest-cov`: Coverage reporting
- `pandas`: Data manipulation for CSV operations
- `langchain`: Document schema support

## Test Configuration

The test configuration is defined in `pyproject.toml`:
- Test discovery patterns
- Coverage settings
- Warning filters
- Marker definitions

## Contributing

When adding new functionality to the metadata manager:

1. **Add corresponding tests**: Each new method should have comprehensive tests
2. **Test error paths**: Ensure error conditions are tested
3. **Update fixtures**: Add new test data as needed
4. **Document test cases**: Include clear docstrings explaining test purposes
5. **Verify coverage**: Ensure new code is properly tested

## Test Examples

### Basic Usage Test
```python
def test_checksum_calculation(self, metadata_manager):
    content = "Test content"
    checksum = metadata_manager.calculate_content_checksum(content)
    assert len(checksum) == 64  # SHA256
```

### Error Handling Test
```python
@patch('pandas.read_csv')
def test_load_metadata_error(self, mock_read_csv, metadata_manager):
    mock_read_csv.side_effect = Exception("CSV read error")
    metadata = metadata_manager.load_existing_metadata()
    assert metadata == {}
```

### Integration Test
```python
def test_full_workflow(self, metadata_manager, sample_documents):
    # Add metadata, save to CSV, load back, verify integrity
    docs_with_metadata = metadata_manager.add_checksum_metadata(sample_documents)
    success = metadata_manager.save_metadata_csv(docs_with_metadata)
    assert success
    
    loaded_metadata = metadata_manager.load_existing_metadata()
    assert len(loaded_metadata) == len(sample_documents)
```
