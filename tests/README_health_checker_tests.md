# HealthChecker Test Suite Documentation

This document describes the comprehensive test suite for the `HealthChecker` service in the lets-talk pipeline system.

## Overview

The HealthChecker service provides comprehensive health monitoring for the entire incremental indexing system, including vector store, metadata, configuration, and system resources. The test suite ensures all functionality works correctly across various scenarios and edge cases.

## Test Files

### 1. `test_health_checker_pytest.py`
**Full pytest-based test suite with mocking and comprehensive coverage**

Features:
- Uses pytest framework with fixtures and parameterization
- Comprehensive mocking of dependencies (VectorStoreManager, PerformanceMonitor)
- Tests all public and private methods
- Covers error scenarios and exception handling
- Tests configuration validation with invalid settings
- Validates backup file management logic
- Tests health analysis and recommendation generation

Test Coverage:
- ✅ HealthChecker initialization
- ✅ Comprehensive health checks (healthy/unhealthy scenarios)
- ✅ Quick health checks
- ✅ Vector store health validation
- ✅ Metadata integrity checking (valid/corrupted/missing files)
- ✅ System resource monitoring (healthy/warning/critical levels)
- ✅ Configuration validation (valid/invalid settings)
- ✅ Backup file management (normal/too many/old files)
- ✅ Health analysis and recommendations
- ✅ Exception handling and error scenarios
- ✅ Convenience function testing
- ✅ Edge cases and boundary conditions

### 2. `test_health_checker_comprehensive_pytest.py`
**Standalone comprehensive test suite without pytest dependencies**

Features:
- Self-contained test runner with detailed logging
- Real file system operations for integration testing
- Comprehensive test scenarios with mock patches
- Detailed test output and progress reporting
- Automated setup and cleanup of test environment

Test Coverage:
- ✅ Complete HealthChecker lifecycle testing
- ✅ Real metadata file operations
- ✅ Integration testing with temporary directories
- ✅ Mock-based vector store and performance monitoring
- ✅ Comprehensive error handling verification
- ✅ Test environment management

### 3. `test_health_checker_simple_pytest.py`
**Simple test runner for basic functionality verification**

Features:
- Minimal dependencies and setup
- Basic functionality verification
- Simple pass/fail reporting
- Quick validation of core features
- Easy to run and understand

Test Coverage:
- ✅ Basic initialization testing
- ✅ Core method functionality
- ✅ Simple health check operations
- ✅ Basic error handling

### 4. `run_health_checker_tests.py`
**Test runner script for executing pytest-based tests**

Features:
- Uses `uv run pytest` following project conventions
- Verbose output with detailed error reporting
- Automatic test discovery and execution
- Exit code reporting for CI/CD integration

## Running the Tests

### Using pytest (Recommended)
```bash
# Run the main pytest suite
uv run python tests/run_health_checker_tests.py

# Or run pytest directly
uv run pytest tests/test_health_checker_pytest.py -v

# Run with coverage
uv run pytest tests/test_health_checker_pytest.py -v --cov=lets_talk.core.pipeline.services.health_checker
```

### Using the Comprehensive Test Suite
```bash
# Run the standalone comprehensive test
uv run python tests/test_health_checker_comprehensive_pytest.py
```

### Using the Simple Test Runner
```bash
# Run basic functionality tests
uv run python tests/test_health_checker_simple_pytest.py
```

## Test Scenarios Covered

### 1. Initialization and Configuration
- ✅ Valid HealthChecker initialization with all parameters
- ✅ Initialization with None values (local storage mode)
- ✅ Configuration parameter validation
- ✅ Invalid configuration detection and reporting

### 2. Metadata Integrity
- ✅ Valid metadata file with correct schema
- ✅ Missing metadata file detection
- ✅ Corrupted metadata file handling
- ✅ Missing required columns detection
- ✅ Empty metadata file handling

### 3. Vector Store Health
- ✅ Healthy vector store connectivity
- ✅ Unhealthy vector store detection
- ✅ Vector store connection exceptions
- ✅ Both Qdrant and local storage modes

### 4. System Resource Monitoring
- ✅ Healthy system resource levels
- ✅ Warning-level resource usage
- ✅ Critical resource usage detection
- ✅ Partial system stats handling
- ✅ Memory, disk, and CPU monitoring

### 5. Backup File Management
- ✅ No backup files scenario
- ✅ Normal backup file count
- ✅ Excessive backup file detection
- ✅ Old backup file identification
- ✅ Backup cleanup recommendations

### 6. Health Analysis
- ✅ Overall status determination (healthy/warning/unhealthy/error)
- ✅ Recommendation generation based on issues
- ✅ Error aggregation and reporting
- ✅ Priority-based recommendation ordering

### 7. Error Handling
- ✅ Exception handling in all major methods
- ✅ Graceful degradation on component failures
- ✅ Error reporting without system crashes
- ✅ Partial functionality when components unavailable

### 8. Integration Testing
- ✅ End-to-end health check workflows
- ✅ Real file system operations
- ✅ Component interaction testing
- ✅ Configuration loading and validation

## Test Data and Fixtures

### Sample Metadata Structure
```csv
source,content_checksum,indexed_timestamp
doc1.md,abc123,1640995200
doc2.md,def456,1640995300
doc3.md,ghi789,1640995400
```

### Mock System Stats
```python
{
    "memory_percent": 50.0,
    "disk_percent": 60.0,
    "cpu_percent": 30.0
}
```

### Health Check Response Structure
```python
{
    "overall_status": "healthy|warning|unhealthy|error",
    "timestamp": 1640995200.0,
    "checks": {
        "vector_store": {"status": "healthy", "details": "..."},
        "metadata": {"status": "healthy", "exists": True, "readable": True},
        "system_resources": {"status": "healthy", "memory_ok": True},
        "configuration": {"status": "healthy", "issues": []},
        "backups": {"status": "healthy", "backup_count": 0}
    },
    "recommendations": [],
    "errors": []
}
```

## Dependencies

### Required Packages
- `pandas`: For metadata file operations
- `unittest.mock`: For mocking dependencies (standard library)
- `tempfile`: For test environment setup (standard library)
- `os`, `sys`, `time`: Standard library modules

### Optional Packages
- `pytest`: For advanced test features (fixtures, parameterization)
- `pytest-cov`: For coverage reporting

## Test Environment

### Temporary Directory Structure
```
/tmp/health_checker_test_XXXXXX/
├── test_metadata.csv
├── corrupted_metadata.csv
├── bad_metadata.csv
├── test_metadata.csv.backup.0
├── test_metadata.csv.backup.1
├── test_metadata.csv.backup.old
└── vector_store/
```

### Cleanup
All test files and directories are automatically cleaned up after test execution, ensuring no interference between test runs.

## Performance Considerations

### Test Execution Time
- Simple tests: < 1 second
- Comprehensive tests: 10-30 seconds
- Full pytest suite: 30-60 seconds

### Resource Usage
- Minimal memory footprint
- Temporary file system usage only
- No network dependencies (mocked)
- No persistent state changes

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure backend path is in PYTHONPATH
   - Check that all dependencies are installed
   - Verify the lets_talk package structure

2. **File Permission Errors**
   - Ensure write permissions in test directory
   - Check that temporary directory creation is allowed

3. **Mock Failures**
   - Verify mock patches are applied correctly
   - Check that method signatures match actual implementation

### Debug Mode
Enable verbose logging by setting environment variable:
```bash
export PYTHONPATH=/path/to/backend
export LOG_LEVEL=DEBUG
uv run python tests/test_health_checker_simple_pytest.py
```

## Contributing

When adding new tests:

1. Follow the existing naming convention: `test_health_checker_*_pytest.py`
2. Use descriptive test method names
3. Include both positive and negative test cases
4. Add appropriate error handling tests
5. Update this documentation with new test scenarios
6. Ensure cleanup of any created resources

## Integration with CI/CD

The test suite is designed to work with continuous integration:

```yaml
# Example GitHub Actions step
- name: Run HealthChecker Tests
  run: |
    uv run pytest tests/test_health_checker_pytest.py -v --tb=short
    if [ $? -eq 0 ]; then
      echo "✅ HealthChecker tests passed"
    else
      echo "❌ HealthChecker tests failed"
      exit 1
    fi
```

## Future Enhancements

Planned test improvements:
- [ ] Performance benchmarking tests
- [ ] Load testing for large metadata files
- [ ] Network failure simulation
- [ ] Database connection testing
- [ ] Multi-threading safety tests
- [ ] Configuration hot-reload testing
