"""
Comprehensive tests for semantic chunking configuration and functionality.
"""

import pytest
from unittest.mock import Mock, patch
from langchain.schema.document import Document

from lets_talk.core.pipeline.services.chunking_service import ChunkingService, split_documents
from lets_talk.shared.config import (
    SemanticChunkerBreakpointType,
    ChunkingStrategy,
    SEMANTIC_CHUNKER_BREAKPOINT_TYPE,
    SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT,
    SEMANTIC_CHUNKER_MIN_CHUNK_SIZE,
)


class TestSemanticChunkerBreakpointType:
    """Test the SemanticChunkerBreakpointType enum."""
    
    def test_enum_values(self):
        """Test that all expected enum values are present."""
        expected_values = ["percentile", "standard_deviation", "interquartile", "gradient"]
        actual_values = [bp_type.value for bp_type in SemanticChunkerBreakpointType]
        assert set(actual_values) == set(expected_values)
    
    def test_enum_string_inheritance(self):
        """Test that enum inherits from string."""
        assert isinstance(SemanticChunkerBreakpointType.PERCENTILE, str)
        assert SemanticChunkerBreakpointType.PERCENTILE == "percentile"


class TestChunkingServiceConfiguration:
    """Test ChunkingService configuration and initialization."""
    
    def test_default_initialization(self):
        """Test default initialization with config values."""
        service = ChunkingService()
        assert service.semantic_breakpoint_type == SEMANTIC_CHUNKER_BREAKPOINT_TYPE
        assert service.semantic_breakpoint_threshold_amount == SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT
        assert service.semantic_min_chunk_size == SEMANTIC_CHUNKER_MIN_CHUNK_SIZE
    
    def test_custom_initialization(self):
        """Test initialization with custom values."""
        service = ChunkingService(
            semantic_breakpoint_type=SemanticChunkerBreakpointType.GRADIENT,
            semantic_breakpoint_threshold_amount=88.5,
            semantic_min_chunk_size=250
        )
        assert service.semantic_breakpoint_type == SemanticChunkerBreakpointType.GRADIENT
        assert service.semantic_breakpoint_threshold_amount == 88.5
        assert service.semantic_min_chunk_size == 250
    
    def test_get_available_breakpoint_types(self):
        """Test getting available breakpoint types."""
        available_types = ChunkingService.get_available_breakpoint_types()
        expected_types = ["percentile", "standard_deviation", "interquartile", "gradient"]
        assert set(available_types) == set(expected_types)


class TestSemanticChunkerValidation:
    """Test semantic chunker configuration validation."""
    
    def test_valid_percentile_configuration(self):
        """Test valid percentile configuration."""
        service = ChunkingService(
            semantic_breakpoint_type=SemanticChunkerBreakpointType.PERCENTILE,
            semantic_breakpoint_threshold_amount=95.0
        )
        assert service.validate_semantic_chunker_config() is True
    
    def test_invalid_percentile_too_high(self):
        """Test invalid percentile configuration (too high)."""
        service = ChunkingService(
            semantic_breakpoint_type=SemanticChunkerBreakpointType.PERCENTILE,
            semantic_breakpoint_threshold_amount=105.0
        )
        assert service.validate_semantic_chunker_config() is False
    
    def test_invalid_percentile_negative(self):
        """Test invalid percentile configuration (negative)."""
        service = ChunkingService(
            semantic_breakpoint_type=SemanticChunkerBreakpointType.PERCENTILE,
            semantic_breakpoint_threshold_amount=-5.0
        )
        assert service.validate_semantic_chunker_config() is False
    
    def test_valid_standard_deviation_configuration(self):
        """Test valid standard deviation configuration."""
        service = ChunkingService(
            semantic_breakpoint_type=SemanticChunkerBreakpointType.STANDARD_DEVIATION,
            semantic_breakpoint_threshold_amount=2.5
        )
        assert service.validate_semantic_chunker_config() is True
    
    def test_invalid_standard_deviation_negative(self):
        """Test invalid standard deviation configuration (negative)."""
        service = ChunkingService(
            semantic_breakpoint_type=SemanticChunkerBreakpointType.STANDARD_DEVIATION,
            semantic_breakpoint_threshold_amount=-1.0
        )
        assert service.validate_semantic_chunker_config() is False
    
    def test_valid_interquartile_configuration(self):
        """Test valid interquartile configuration."""
        service = ChunkingService(
            semantic_breakpoint_type=SemanticChunkerBreakpointType.INTERQUARTILE,
            semantic_breakpoint_threshold_amount=1.5
        )
        assert service.validate_semantic_chunker_config() is True
    
    def test_invalid_interquartile_zero(self):
        """Test invalid interquartile configuration (zero)."""
        service = ChunkingService(
            semantic_breakpoint_type=SemanticChunkerBreakpointType.INTERQUARTILE,
            semantic_breakpoint_threshold_amount=0.0
        )
        assert service.validate_semantic_chunker_config() is False
    
    def test_valid_gradient_configuration(self):
        """Test valid gradient configuration."""
        service = ChunkingService(
            semantic_breakpoint_type=SemanticChunkerBreakpointType.GRADIENT,
            semantic_breakpoint_threshold_amount=92.0
        )
        assert service.validate_semantic_chunker_config() is True
    
    def test_invalid_min_chunk_size(self):
        """Test invalid minimum chunk size."""
        service = ChunkingService(semantic_min_chunk_size=-10)
        assert service.validate_semantic_chunker_config() is False


class TestSemanticChunkerConfigInfo:
    """Test semantic chunker configuration information methods."""
    
    def test_config_info_structure(self):
        """Test that config info returns expected structure."""
        service = ChunkingService()
        config_info = service.get_semantic_chunker_config_info()
        
        required_keys = [
            "breakpoint_type", "breakpoint_threshold_amount", "min_chunk_size",
            "is_valid", "recommendation", "available_types"
        ]
        for key in required_keys:
            assert key in config_info
    
    def test_config_info_recommendations(self):
        """Test that each breakpoint type has a recommendation."""
        for bp_type in SemanticChunkerBreakpointType:
            service = ChunkingService(semantic_breakpoint_type=bp_type)
            config_info = service.get_semantic_chunker_config_info()
            assert len(config_info["recommendation"]) > 0
            assert isinstance(config_info["recommendation"], str)


class TestSemanticChunkingMethods:
    """Test semantic chunking methods."""
    
    def __init__(self):
        """Initialize test documents."""
        self.sample_docs = [
            Document(page_content="This is the first test document."),
            Document(page_content="This is the second test document with more content."),
            Document(page_content="This is the third test document with even more content to test chunking."),
        ]
    
    @patch('langchain_experimental.text_splitter.SemanticChunker')
    @patch('lets_talk.core.pipeline.services.chunking_service.init_embeddings_wrapper')
    def test_semantic_chunking_with_mock(self, mock_embeddings, mock_semantic_chunker):
        """Test semantic chunking with mocked dependencies."""
        # Mock the embeddings
        mock_embeddings.return_value = Mock()
        
        # Set up mock
        mock_splitter_instance = Mock()
        mock_splitter_instance.split_documents.return_value = self.sample_docs
        mock_semantic_chunker.return_value = mock_splitter_instance
        
        # Test the method
        service = ChunkingService()
        result = service._semantic_chunking(self.sample_docs)
        
        # Verify
        assert result == self.sample_docs
        mock_semantic_chunker.assert_called_once()
        mock_splitter_instance.split_documents.assert_called_once_with(self.sample_docs)
    
    def test_semantic_chunking_fallback_on_import_error(self):
        """Test that semantic chunking falls back to text splitter on import error."""
        # Patch at the place where it's imported (inside the method)
        with patch('lets_talk.core.pipeline.services.chunking_service.SemanticChunker', side_effect=ImportError):
            with patch('langchain_experimental.text_splitter.SemanticChunker', side_effect=ImportError):
                service = ChunkingService()
                
                # Mock the text splitter fallback
                with patch.object(service, '_text_splitter_chunking') as mock_text_chunking:
                    mock_text_chunking.return_value = self.sample_docs
                    
                    result = service._semantic_chunking(self.sample_docs)
                    
                    assert result == self.sample_docs
                    mock_text_chunking.assert_called_once()
    
    def test_semantic_chunking_fallback_on_runtime_error(self):
        """Test that semantic chunking falls back to text splitter on runtime error."""
        with patch('langchain_experimental.text_splitter.SemanticChunker', side_effect=RuntimeError("Test error")):
            service = ChunkingService()
            
            # Mock the text splitter fallback
            with patch.object(service, '_text_splitter_chunking') as mock_text_chunking:
                mock_text_chunking.return_value = self.sample_docs
                
                result = service._semantic_chunking(self.sample_docs)
                
                assert result == self.sample_docs
                mock_text_chunking.assert_called_once()


class TestSplitDocumentsMethod:
    """Test the main split_documents method with semantic chunking."""
    
    def __init__(self):
        """Initialize test documents."""
        self.sample_docs = [
            Document(page_content="Test document 1"),
            Document(page_content="Test document 2"),
        ]
    
    def test_split_documents_semantic_strategy(self):
        """Test split_documents with semantic strategy."""
        service = ChunkingService(chunking_strategy=ChunkingStrategy.SEMANTIC)
        
        with patch.object(service, '_semantic_chunking') as mock_semantic:
            mock_semantic.return_value = self.sample_docs
            
            result = service.split_documents(self.sample_docs)
            
            assert result == self.sample_docs
            mock_semantic.assert_called_once_with(self.sample_docs)
    
    def test_split_documents_text_splitter_strategy(self):
        """Test split_documents with text splitter strategy."""
        service = ChunkingService(chunking_strategy=ChunkingStrategy.TEXT_SPLITTER)
        
        with patch.object(service, '_text_splitter_chunking') as mock_text_chunking:
            mock_text_chunking.return_value = self.sample_docs
            
            result = service.split_documents(self.sample_docs)
            
            assert result == self.sample_docs
            mock_text_chunking.assert_called_once()


class TestConvenienceFunctions:
    """Test convenience functions with semantic chunking parameters."""
    
    def __init__(self):
        """Initialize test documents."""
        self.sample_docs = [
            Document(page_content="Test document for convenience function"),
        ]
    
    @patch('lets_talk.core.pipeline.services.chunking_service.ChunkingService')
    def test_split_documents_convenience_with_semantic_params(self, mock_chunking_service):
        """Test split_documents convenience function with semantic parameters."""
        # Mock service instance and its method
        mock_service_instance = Mock()
        mock_service_instance.split_documents.return_value = self.sample_docs
        mock_chunking_service.return_value = mock_service_instance
        
        # Call convenience function with semantic parameters
        result = split_documents(
            self.sample_docs,
            chunking_strategy=ChunkingStrategy.SEMANTIC,
            semantic_breakpoint_type=SemanticChunkerBreakpointType.GRADIENT,
            semantic_breakpoint_threshold_amount=88.0
        )
        
        # Verify service was created with correct parameters
        mock_chunking_service.assert_called_once_with(
            chunk_size=1000,  # default
            chunk_overlap=200,  # default
            chunking_strategy=ChunkingStrategy.SEMANTIC,
            semantic_breakpoint_type=SemanticChunkerBreakpointType.GRADIENT,
            semantic_breakpoint_threshold_amount=88.0,
        )
        
        # Verify service method was called
        mock_service_instance.split_documents.assert_called_once_with(self.sample_docs)
        assert result == self.sample_docs


class TestIntegrationWithRealDocuments:
    """Integration tests with real documents (no mocking)."""
    
    def test_chunking_service_with_real_documents(self):
        """Test ChunkingService with real documents."""
        documents = [
            Document(
                page_content="This is a test document about machine learning and artificial intelligence.",
                metadata={"source": "test1.md"}
            ),
            Document(
                page_content="This is another test document about deep learning and neural networks.",
                metadata={"source": "test2.md"}
            ),
        ]
        
        service = ChunkingService(
            chunking_strategy=ChunkingStrategy.SEMANTIC,
            semantic_breakpoint_type=SemanticChunkerBreakpointType.PERCENTILE,
            semantic_breakpoint_threshold_amount=95.0
        )
        
        # This should work even if it falls back to text splitter
        result = service.split_documents(documents)
        
        # Basic sanity checks
        assert isinstance(result, list)
        assert len(result) >= len(documents)  # Should have at least as many chunks as documents
        for chunk in result:
            assert isinstance(chunk, Document)
            assert len(chunk.page_content) > 0
    
    def test_efficiency_analysis(self):
        """Test chunking efficiency analysis."""
        original_docs = [
            Document(page_content="Short doc"),
            Document(page_content="This is a longer document with more content to analyze"),
        ]
        
        service = ChunkingService()
        split_docs = service.split_documents(original_docs)
        
        efficiency = service.analyze_chunking_efficiency(original_docs, split_docs)
        
        # Check that efficiency metrics are returned
        required_metrics = [
            "original_documents", "resulting_chunks", "chunks_per_document",
            "total_original_chars", "total_split_chars", "average_chunk_size",
            "min_chunk_size", "max_chunk_size"
        ]
        
        for metric in required_metrics:
            assert metric in efficiency
            assert isinstance(efficiency[metric], (int, float))
    
    def test_chunk_estimation(self):
        """Test chunk estimation functionality."""
        documents = [
            Document(page_content="x" * 1000),  # 1000 characters
            Document(page_content="y" * 500),   # 500 characters
        ]
        
        service = ChunkingService(chunk_size=500, chunk_overlap=50)
        estimated_chunks = service.estimate_chunks(documents)
        
        assert isinstance(estimated_chunks, int)
        assert estimated_chunks > 0


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
