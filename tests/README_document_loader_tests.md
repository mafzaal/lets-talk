# Document Loader Tests

This directory contains comprehensive test suites for the DocumentLoader service, which is responsible for loading and processing blog posts from markdown files.

## Test Files

### 1. `test_document_loader_simple.py`
A simple, standalone test script that verifies basic functionality without complex dependencies. This test:
- Tests imports and module loading
- Verifies DocumentLoader instantiation
- Processes real data from the workspace
- Validates statistics calculation

### 2. `test_document_loader_comprehensive.py`
A comprehensive unittest-based test suite that covers all aspects of the DocumentLoader service:

#### Test Coverage:
- **Document Loading**: Basic document loading from directories
- **URL Generation**: Conversion of file paths to web URLs
- **Frontmatter Parsing**: 
  - Complete frontmatter with all fields
  - Mixed data types (strings, booleans, lists, numbers)
  - Boolean published fields
  - Default title generation for missing frontmatter
- **Metadata Processing**: 
  - Media URL processing (images, videos)
  - YouTube video ID conversion to embed URLs
  - Category list handling
- **Filtering**: Published vs unpublished document filtering
- **Statistics**: Document statistics calculation and display
- **Error Handling**: Graceful handling of malformed content
- **Real Data Integration**: Testing with actual workspace data

### 3. `run_document_loader_tests.py`
A test runner that executes all document loader tests and provides a comprehensive summary.

## Running the Tests

### Quick Test
```bash
# Run the simple test suite
uv run python tests/test_document_loader_simple.py
```

### Comprehensive Tests
```bash
# Run the full test suite
uv run python tests/test_document_loader_comprehensive.py
```

### All Tests
```bash
# Run all document loader tests with summary
uv run python tests/run_document_loader_tests.py
```

### Using unittest
```bash
# Run tests using standard unittest discovery
uv run python -m unittest discover tests -p "*document_loader*" -v
```

## Test Data

The tests use a combination of:
1. **Generated test data**: Created dynamically in temporary directories
2. **Real workspace data**: Actual markdown files from the `data/` directory
3. **Mock data**: Predefined Document objects for specific test scenarios

## Features Tested

### Core Functionality
- ✅ Document loading from markdown files
- ✅ Recursive directory scanning
- ✅ File pattern matching (*.md)
- ✅ Content length calculation

### Frontmatter Processing
- ✅ YAML frontmatter parsing
- ✅ String field extraction (title, date, description)
- ✅ List field processing (categories)
- ✅ Boolean field handling (published)
- ✅ Mixed data type support
- ✅ Error handling for malformed frontmatter

### URL and Media Processing
- ✅ URL generation from file paths
- ✅ Blog base URL integration
- ✅ Cover image URL processing
- ✅ YouTube video ID to embed URL conversion
- ✅ Relative to absolute URL conversion

### Metadata Enhancement
- ✅ Post slug extraction from directory names
- ✅ Default title generation
- ✅ Content length tracking
- ✅ Published status handling

### Statistics and Reporting
- ✅ Document count and character statistics
- ✅ Min/max/average length calculation
- ✅ Detailed document information compilation
- ✅ Statistics display formatting

### Filtering and Configuration
- ✅ Published/unpublished document filtering
- ✅ Configurable indexing options
- ✅ Custom URL base configuration

## Test Structure

Each test class focuses on a specific aspect:

- **TestDocumentLoaderCore**: Core loading and processing functionality
- **TestDocumentStats**: Statistics calculation and display
- **TestConvenienceFunctions**: Wrapper functions and utilities
- **TestDocumentLoaderWithRealData**: Integration with actual workspace data

## Dependencies

The tests require:
- `langchain` - For Document objects
- `python-frontmatter` - For YAML frontmatter parsing
- Standard library modules: `unittest`, `tempfile`, `pathlib`

## Error Handling

The tests verify that the DocumentLoader:
- Gracefully handles missing frontmatter
- Processes malformed YAML without crashing
- Provides default values for missing fields
- Logs warnings for processing errors
- Continues processing even with individual document errors

## Integration

These tests ensure the DocumentLoader service integrates properly with:
- The RAG pipeline for document indexing
- Vector store operations
- Blog post statistics generation
- Content management workflows

## Maintenance

When modifying the DocumentLoader service:
1. Run the simple tests first for quick feedback
2. Run comprehensive tests for full validation
3. Update tests if adding new features
4. Ensure all tests pass before committing changes

The test suite is designed to catch regressions and validate new functionality while being maintainable and fast to execute.
