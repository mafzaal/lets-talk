# VectorStoreManager Tests

This directory contains comprehensive pytest test suites for the VectorStoreManager service, which handles all vector store operations including creation, loading, updating, and document management with Qdrant.

## Test Files

### 1. `test_vector_store_manager_simple_pytest.py`
A simplified test suite focusing on core functionality:
- Basic initialization testing
- Embeddings lazy loading
- Vector store creation and loading
- Document addition operations
- Basic error handling

### 2. `test_vector_store_manager_comprehensive_pytest.py`
A comprehensive test suite covering:
- **Initialization & Configuration**: Default and custom configurations
- **Vector Store Operations**: Creation with local/remote storage, loading with error handling
- **Document Management**: Adding, removing, batch processing
- **Incremental Updates**: Complex scenarios with new/modified/deleted documents
- **Health Validation**: Comprehensive health checks and monitoring
- **Convenience Functions**: Backward compatibility functions
- **Edge Cases**: Large batches, concurrent access, memory efficiency
- **Error Handling**: Various failure scenarios and exception handling

### 3. `run_vector_store_manager_tests.py`
Test runner script that:
- Checks for required dependencies
- Sets up the environment
- Runs both test suites
- Provides detailed output and error reporting

## Test Coverage

The test suites cover the following VectorStoreManager methods:

### Core Methods
- `__init__()` - Initialization with various configurations
- `embeddings` (property) - Lazy loading of embeddings
- `create_vector_store()` - Vector store creation
- `load_vector_store()` - Vector store loading
- `add_documents()` - Document addition
- `remove_documents_by_source()` - Document removal
- `validate_health()` - Health validation
- `update_incrementally()` - Incremental updates

### Batch Processing Methods
- `add_documents_batch()` - Batch document addition
- `remove_documents_batch()` - Batch document removal

### Convenience Functions
- `create_vector_store()` - Global convenience function
- `load_vector_store()` - Global convenience function
- `add_documents_to_vector_store()` - Global convenience function
- `remove_documents_from_vector_store()` - Global convenience function
- `validate_vector_store_health()` - Global convenience function

## Test Scenarios

### 1. Configuration Testing
- Default configuration values
- Custom configuration parameters
- Local vs. remote Qdrant setup
- Invalid configuration handling

### 2. Vector Store Operations
- Creating new vector stores
- Loading existing vector stores
- Force recreation scenarios
- Connection failure handling

### 3. Document Management
- Adding single and multiple documents
- Removing documents by source paths
- Empty document list handling
- Large document batch processing

### 4. Incremental Updates
- New document addition
- Modified document updates
- Document deletion
- Complex multi-operation scenarios
- Batch vs. non-batch processing

### 5. Error Handling
- Connection failures
- Invalid parameters
- Memory errors
- Unexpected exceptions
- Resource cleanup

### 6. Performance & Scalability
- Large document sets (1000+ documents)
- Batch size optimization
- Memory efficiency
- Concurrent access safety

## Running the Tests

### Prerequisites
Ensure you have the required dependencies installed:
```bash
uv add pytest
uv add langchain
# Other project-specific dependencies should already be installed
```

### Running All Tests
```bash
# Using the test runner (recommended)
uv run python tests/run_vector_store_manager_tests.py

# Using pytest directly
uv run pytest tests/test_vector_store_manager_simple_pytest.py -v
uv run pytest tests/test_vector_store_manager_comprehensive_pytest.py -v
```

### Running Specific Test Categories
```bash
# Run only simple tests
uv run pytest tests/test_vector_store_manager_simple_pytest.py -v

# Run comprehensive tests
uv run pytest tests/test_vector_store_manager_comprehensive_pytest.py -v

# Run specific test classes
uv run pytest tests/test_vector_store_manager_comprehensive_pytest.py::TestVectorStoreManagerComprehensive -v

# Run specific test methods
uv run pytest tests/test_vector_store_manager_comprehensive_pytest.py::TestVectorStoreManagerComprehensive::test_initialization_with_defaults -v
```

### Test Output
The tests provide detailed output including:
- Test results (pass/fail)
- Import error handling
- Mocking verification
- Performance considerations
- Resource cleanup verification

## Mocking Strategy

The tests use comprehensive mocking to isolate the VectorStoreManager from external dependencies:

### 1. Embeddings Mocking
- `init_embeddings_wrapper` is mocked to return a test embedding model
- Embedding operations return predictable test vectors

### 2. Qdrant Mocking
- `QdrantVectorStore` class is mocked for vector store operations
- `QdrantClient` is mocked for direct client operations
- `qdrant_client.models` is mocked for filter operations

### 3. File System Mocking
- Temporary directories are used for storage path testing
- Path existence checks are mocked as needed

### 4. Batch Processing Mocking
- `BatchProcessor` is mocked to verify batch operations
- Processing functions are mocked to return predictable results

## Error Handling

The tests include comprehensive error handling:

### 1. Import Error Handling
- Tests skip gracefully if required modules are not available
- Detailed error messages are provided for missing dependencies

### 2. Exception Testing
- Various exception types are tested (ConnectionError, ValueError, etc.)
- Resource cleanup is verified even during exceptions

### 3. Edge Case Testing
- Empty document lists
- Non-existent storage paths
- Invalid configurations
- Memory limitations

## Best Practices

The test suite follows these best practices:

### 1. Test Isolation
- Each test is independent and can run in any order
- Fixtures provide clean test environments
- Mocking prevents side effects

### 2. Comprehensive Coverage
- All public methods are tested
- Both success and failure scenarios are covered
- Edge cases and error conditions are included

### 3. Maintainability
- Clear test names describe what is being tested
- Fixtures reduce code duplication
- Comments explain complex test scenarios

### 4. Performance Considerations
- Large-scale tests verify scalability
- Resource usage is monitored
- Cleanup is verified

## Contributing

When adding new tests:

1. **Follow Naming Conventions**: Use descriptive test method names
2. **Use Appropriate Fixtures**: Leverage existing fixtures where possible
3. **Include Error Cases**: Test both success and failure scenarios
4. **Mock Dependencies**: Isolate the component under test
5. **Document Complex Tests**: Add comments for complex test logic
6. **Verify Cleanup**: Ensure resources are properly cleaned up

## Known Issues

1. **Import Dependencies**: Tests require specific dependencies to be installed
2. **Environment Setup**: Backend path must be correctly configured
3. **Mock Complexity**: Some tests require complex mocking setups

## Future Improvements

1. **Performance Benchmarking**: Add performance measurement tests
2. **Integration Testing**: Add tests with real Qdrant instances
3. **Stress Testing**: Add tests for extreme load conditions
4. **Monitoring Integration**: Add tests for monitoring and observability features
