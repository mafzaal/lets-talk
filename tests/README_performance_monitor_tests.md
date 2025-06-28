# Performance Monitor Tests

This directory contains comprehensive tests for the Performance Monitor service in the lets-talk pipeline.

## Test Files

### `test_performance_monitor_pytest.py`
Main test suite for the PerformanceMonitor and OptimizationService classes.

### `test_performance_monitor_comprehensive_pytest.py`
Comprehensive integration-style tests that verify end-to-end functionality.

### `run_performance_monitor_tests.py`
Test runner script for easy execution of performance monitor tests.

#### Test Classes:

1. **TestPerformanceMonitor** - Tests for the PerformanceMonitor class
2. **TestOptimizationService** - Tests for the OptimizationService class

#### Key Test Coverage:

**PerformanceMonitor Tests:**
- ✅ Instance creation and initialization
- ✅ System stats collection (with/without psutil)
- ✅ Operation monitoring and metrics tracking
- ✅ Metrics history management
- ✅ Performance summaries and filtering
- ✅ Error handling and edge cases
- ✅ Global convenience functions

**OptimizationService Tests:**
- ✅ Instance creation and configuration
- ✅ Batch size optimization
- ✅ Chunking parameter optimization
- ✅ Performance optimizations application
- ✅ Adaptive chunking algorithms
- ✅ Processing efficiency analysis
- ✅ Integration with PerformanceMonitor

## Running the Tests

### Run All Performance Monitor Tests
```bash
# Using the project's uv package manager (recommended)
uv run pytest tests/test_performance_monitor_pytest.py -v

# Run comprehensive tests
uv run pytest tests/test_performance_monitor_comprehensive_pytest.py -v

# Run both test suites
uv run pytest tests/test_performance_monitor*pytest.py -v

# Using the test runner script
python tests/run_performance_monitor_tests.py

# Run comprehensive tests directly
uv run python tests/test_performance_monitor_comprehensive_pytest.py
```

### Run Specific Test Class
```bash
# Test only PerformanceMonitor
uv run pytest tests/test_performance_monitor_pytest.py::TestPerformanceMonitor -v

# Test only OptimizationService
uv run pytest tests/test_performance_monitor_pytest.py::TestOptimizationService -v
```

### Run Specific Test Function
```bash
# Example: Test system stats collection
uv run pytest tests/test_performance_monitor_pytest.py::TestPerformanceMonitor::test_get_system_stats_with_psutil -v

# Example: Test batch size optimization
uv run pytest tests/test_performance_monitor_pytest.py::TestOptimizationService::test_optimize_batch_size_basic -v
```

### Run Tests with Different Markers
```bash
# Run only unit tests (if marked)
uv run pytest tests/test_performance_monitor_pytest.py -m unit -v

# Skip slow tests
uv run pytest tests/test_performance_monitor_pytest.py -m "not slow" -v
```

## Test Structure

The tests follow the project's established patterns:

1. **Setup and Teardown**: Uses pytest fixtures for clean test environments
2. **Mocking**: Extensive use of `unittest.mock` for external dependencies
3. **Error Handling**: Tests both success and failure scenarios
4. **Edge Cases**: Comprehensive coverage of boundary conditions
5. **Integration**: Tests interaction between components

## Test Fixtures

### `performance_monitor`
Creates a PerformanceMonitor instance with monitoring enabled for testing.

### `optimization_service`
Creates an OptimizationService instance with default configuration.

### `sample_documents`
Provides a set of test documents with varying lengths for chunking optimization tests.

## Dependencies

The tests mock external dependencies where possible to ensure isolation:

- **psutil**: Mocked for system resource monitoring tests
- **time.time()**: Used for actual timing in performance tests
- **langchain Document**: Used for document processing tests

## Performance Considerations

Some tests include actual timing operations but use minimal delays (0.01-0.1 seconds) to avoid slow test execution while still validating timing logic.

## Error Scenarios Tested

1. **Missing Dependencies**: psutil not available
2. **System Errors**: Exceptions during system stats collection
3. **Empty Data**: No documents or metrics to process
4. **Invalid Parameters**: Out-of-bounds or invalid configuration values
5. **Resource Constraints**: Memory-limited optimization scenarios

## Expected Test Results

All tests should pass when run in a properly configured environment. The tests are designed to be:

- **Fast**: Complete execution in under 30 seconds
- **Reliable**: Deterministic results across different environments
- **Comprehensive**: High code coverage of the performance monitor module
- **Maintainable**: Clear test names and good documentation

## Troubleshooting

### Import Errors
If you encounter import errors, ensure:
1. You're running from the project root directory
2. The backend directory is in the Python path
3. All required dependencies are installed

### Timing Test Failures
Timing-based tests may occasionally fail on heavily loaded systems. This is expected behavior for performance monitoring tests.

### Missing psutil
Tests will skip psutil-dependent functionality gracefully if the library is not installed, but will still test the fallback behavior.

## Contributing

When adding new tests:

1. Follow the existing naming convention: `test_<feature>_<scenario>`
2. Use descriptive docstrings for test functions
3. Include both positive and negative test cases
4. Mock external dependencies appropriately
5. Add appropriate pytest markers for test categorization

## Future Enhancements

Potential areas for additional test coverage:

1. **Load Testing**: High-volume document processing
2. **Memory Profiling**: Actual memory usage validation
3. **Concurrent Operations**: Multi-threaded performance monitoring
4. **Real System Integration**: Tests with actual system resources
5. **Performance Regression**: Benchmarking against previous versions
