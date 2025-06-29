"""
Document chunking service module.

This module handles different strategies for splitting documents into chunks
for better embedding and retrieval.
"""

import logging
from typing import List, Tuple, Optional

from langchain.schema.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from lets_talk.shared.config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    CHUNKING_STRATEGY,
    USE_CHUNKING,
    ChunkingStrategy,
    EMBEDDING_MODEL,
    ADAPTIVE_CHUNKING,
    SemanticChunkerBreakpointType,
    SEMANTIC_CHUNKER_BREAKPOINT_TYPE,
    SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT,
    SEMANTIC_CHUNKER_MIN_CHUNK_SIZE,
)
from lets_talk.utils.wrapper import init_embeddings_wrapper
from ..utils.common_utils import handle_exceptions, log_execution_time

logger = logging.getLogger(__name__)


class ChunkingService:
    """
    Handles document chunking with different strategies.
    """
    
    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
        chunking_strategy: ChunkingStrategy = CHUNKING_STRATEGY,
        embedding_model: str = EMBEDDING_MODEL,
        adaptive_chunking: bool = ADAPTIVE_CHUNKING,
        semantic_breakpoint_type: SemanticChunkerBreakpointType = SEMANTIC_CHUNKER_BREAKPOINT_TYPE,
        semantic_breakpoint_threshold_amount: float = SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT,
        semantic_min_chunk_size: int = SEMANTIC_CHUNKER_MIN_CHUNK_SIZE,
    ):
        """
        Initialize the chunking service.
        
        Args:
            chunk_size: Default chunk size in characters
            chunk_overlap: Default overlap between chunks
            chunking_strategy: Strategy to use for chunking
            embedding_model: Embedding model for semantic chunking
            adaptive_chunking: Whether to use adaptive chunking
            semantic_breakpoint_type: Breakpoint threshold type for semantic chunking
            semantic_breakpoint_threshold_amount: Threshold amount for semantic chunking breakpoints
            semantic_min_chunk_size: Minimum chunk size for semantic chunking
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunking_strategy = chunking_strategy
        self.embedding_model = embedding_model
        self.adaptive_chunking = adaptive_chunking
        self.semantic_breakpoint_type = semantic_breakpoint_type
        self.semantic_breakpoint_threshold_amount = semantic_breakpoint_threshold_amount
        self.semantic_min_chunk_size = semantic_min_chunk_size
    
    @handle_exceptions(default_return=[])
    @log_execution_time()
    def split_documents(
        self,
        documents: List[Document],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        strategy: Optional[ChunkingStrategy] = None
    ) -> List[Document]:
        """
        Split documents into chunks using the specified strategy.
        
        Args:
            documents: List of Document objects to split
            chunk_size: Override chunk size
            chunk_overlap: Override chunk overlap
            strategy: Override chunking strategy
            
        Returns:
            List of split Document objects
        """
        if not documents:
            return []
        
        # Use provided parameters or defaults
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap
        strategy = strategy or self.chunking_strategy
        
       
        
        # Log parameters based on chunking strategy
        if strategy == ChunkingStrategy.SEMANTIC:
            logger.info(f"Splitting {len(documents)} documents using {strategy} strategy "
                   f"(breakpoint_type={self.semantic_breakpoint_type.value}, "
                   f"threshold={self.semantic_breakpoint_threshold_amount}, "
                   f"min_chunk_size={self.semantic_min_chunk_size})")
        else:
            logger.info(f"Splitting {len(documents)} documents using {strategy} strategy "
                   f"(chunk_size={chunk_size}, overlap={chunk_overlap}, "
                   f"adaptive={self.adaptive_chunking})")
            
        if strategy == ChunkingStrategy.SEMANTIC:
            split_docs = self._semantic_chunking(documents)
        else:
             # Apply adaptive chunking if enabled
            if self.adaptive_chunking:
                chunk_size, chunk_overlap = self._optimize_chunking_parameters(
                    documents, chunk_size, chunk_overlap
                )
            split_docs = self._text_splitter_chunking(documents, chunk_size, chunk_overlap)
        
        # Update chunk count metadata
        self._update_chunk_metadata(documents, split_docs)
        
        logger.info(f"Split {len(documents)} documents into {len(split_docs)} chunks")
        return split_docs
    
    def _semantic_chunking(self, documents: List[Document]) -> List[Document]:
        """
        Split documents using semantic chunking.
        
        Args:
            documents: Documents to split
            
        Returns:
            List of split documents
        """
        try:
            from langchain_experimental.text_splitter import SemanticChunker
            
            # Initialize embeddings for semantic chunking
            embeddings = init_embeddings_wrapper(self.embedding_model)
            
            # Create semantic chunker with configured parameters
            semantic_chunker = SemanticChunker(
                embeddings,  # type: ignore
                breakpoint_threshold_type=self.semantic_breakpoint_type.value,
                breakpoint_threshold_amount=self.semantic_breakpoint_threshold_amount,
                # Note: min_chunk_size parameter may not be available in all versions
                # Remove this line if it causes issues with your langchain_experimental version
                # min_chunk_size=self.semantic_min_chunk_size,
            )
            
            split_docs = semantic_chunker.split_documents(documents)
            
            logger.info(f"Successfully applied semantic chunking with breakpoint_type={self.semantic_breakpoint_type.value}, "
                       f"threshold_amount={self.semantic_breakpoint_threshold_amount}")
            return split_docs
            
        except ImportError:
            logger.warning("langchain_experimental not available, falling back to text splitter")
            return self._text_splitter_chunking(documents, self.chunk_size, self.chunk_overlap)
        except Exception as e:
            logger.error(f"Error with semantic chunking: {e}, falling back to text splitter")
            return self._text_splitter_chunking(documents, self.chunk_size, self.chunk_overlap)
    
    def _text_splitter_chunking(
        self,
        documents: List[Document],
        chunk_size: int,
        chunk_overlap: int
    ) -> List[Document]:
        """
        Split documents using recursive character text splitter.
        
        Args:
            documents: Documents to split
            chunk_size: Size of chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of split documents
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        
        split_docs = text_splitter.split_documents(documents)
        logger.info(f"Applied text splitter chunking with size={chunk_size}, overlap={chunk_overlap}")
        return split_docs
    
    def _update_chunk_metadata(
        self,
        original_docs: List[Document],
        split_docs: List[Document]
    ) -> None:
        """
        Update chunk count metadata in both original and split documents.
        
        Args:
            original_docs: Original documents before splitting
            split_docs: Documents after splitting
        """
        # Count chunks per source document
        source_to_chunk_count = {}
        for doc in split_docs:
            source = doc.metadata.get("source", "")
            source_to_chunk_count[source] = source_to_chunk_count.get(source, 0) + 1
        
        # Update chunk_count in the original documents' metadata
        for doc in original_docs:
            source = doc.metadata.get("source", "")
            doc.metadata["chunk_count"] = source_to_chunk_count.get(source, 1)
        
        # Also update chunk_count in split documents
        for doc in split_docs:
            source = doc.metadata.get("source", "")
            doc.metadata["chunk_count"] = source_to_chunk_count.get(source, 1)
    
    def _optimize_chunking_parameters(
        self,
        documents: List[Document],
        target_chunk_size: int,
        target_overlap: int
    ) -> Tuple[int, int]:
        """
        Optimize chunking parameters based on document characteristics.
        
        Args:
            documents: Documents to analyze
            target_chunk_size: Target chunk size
            target_overlap: Target overlap
            
        Returns:
            Tuple of (optimized_chunk_size, optimized_overlap)
        """
        if not documents:
            return target_chunk_size, target_overlap
        
        # Analyze document lengths
        lengths = [len(doc.page_content) for doc in documents]
        avg_length = sum(lengths) / len(lengths)
        min_length = min(lengths)
        max_length = max(lengths)
        
        logger.info(f"Document analysis: avg={avg_length:.0f}, min={min_length}, max={max_length}")
        
        # Optimize chunk size based on document characteristics
        max_chunk_size = 2000  # Maximum allowed chunk size
        
        if avg_length < target_chunk_size:
            # Documents are small, use smaller chunks to avoid over-chunking
            optimized_chunk_size = max(int(avg_length * 0.7), 500)
            optimized_overlap = max(int(optimized_chunk_size * 0.05), 50)
        elif avg_length > max_chunk_size:
            # Documents are large, use larger chunks
            optimized_chunk_size = max_chunk_size
            optimized_overlap = max(int(optimized_chunk_size * 0.1), 100)
        else:
            # Documents are medium-sized, use target size
            optimized_chunk_size = target_chunk_size
            optimized_overlap = max(int(optimized_chunk_size * 0.1), target_overlap)
        
        logger.info(f"Optimized chunking: size={optimized_chunk_size}, overlap={optimized_overlap}")
        return optimized_chunk_size, optimized_overlap
    
    def estimate_chunks(self, documents: List[Document]) -> int:
        """
        Estimate the number of chunks that will be created.
        
        Args:
            documents: Documents to analyze
            
        Returns:
            Estimated number of chunks
        """
        if not documents:
            return 0
        
        total_chars = sum(len(doc.page_content) for doc in documents)
        effective_chunk_size = self.chunk_size - self.chunk_overlap
        
        # Simple estimation
        estimated_chunks = max(1, total_chars // effective_chunk_size)
        
        logger.debug(f"Estimated {estimated_chunks} chunks from {len(documents)} documents "
                    f"({total_chars} total characters)")
        
        return estimated_chunks
    
    def analyze_chunking_efficiency(
        self,
        original_docs: List[Document],
        split_docs: List[Document]
    ) -> dict:
        """
        Analyze the efficiency of the chunking process.
        
        Args:
            original_docs: Original documents before chunking
            split_docs: Documents after chunking
            
        Returns:
            Dictionary with efficiency metrics
        """
        if not original_docs or not split_docs:
            return {}
        
        total_original_chars = sum(len(doc.page_content) for doc in original_docs)
        total_split_chars = sum(len(doc.page_content) for doc in split_docs)
        
        # Calculate statistics
        split_lengths = [len(doc.page_content) for doc in split_docs]
        avg_chunk_size = sum(split_lengths) / len(split_lengths) if split_lengths else 0
        
        efficiency_metrics = {
            "original_documents": len(original_docs),
            "resulting_chunks": len(split_docs),
            "chunks_per_document": len(split_docs) / len(original_docs),
            "total_original_chars": total_original_chars,
            "total_split_chars": total_split_chars,
            "character_expansion_ratio": total_split_chars / total_original_chars if total_original_chars > 0 else 0,
            "average_chunk_size": avg_chunk_size,
            "min_chunk_size": min(split_lengths) if split_lengths else 0,
            "max_chunk_size": max(split_lengths) if split_lengths else 0,
            "target_chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }
        
        logger.info(f"Chunking efficiency: {efficiency_metrics['chunks_per_document']:.1f} chunks/doc, "
                   f"avg size: {avg_chunk_size:.0f} chars")
        
        return efficiency_metrics
    
    @staticmethod
    def get_available_breakpoint_types() -> List[str]:
        """
        Get all available breakpoint threshold types for semantic chunking.
        
        Returns:
            List of available breakpoint threshold type strings
        """
        return [bp_type.value for bp_type in SemanticChunkerBreakpointType]
    
    def validate_semantic_chunker_config(self) -> bool:
        """
        Validate the semantic chunker configuration parameters.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        # Validate breakpoint threshold amount based on type
        if self.semantic_breakpoint_type in [SemanticChunkerBreakpointType.PERCENTILE, SemanticChunkerBreakpointType.GRADIENT]:
            # Percentile and gradient should be between 0.0 and 100.0
            if not (0.0 <= self.semantic_breakpoint_threshold_amount <= 100.0):
                logger.warning(f"Invalid threshold amount {self.semantic_breakpoint_threshold_amount} for {self.semantic_breakpoint_type}. "
                              "Should be between 0.0 and 100.0")
                return False
        elif self.semantic_breakpoint_type == SemanticChunkerBreakpointType.STANDARD_DEVIATION:
            # Standard deviation should be positive
            if self.semantic_breakpoint_threshold_amount <= 0.0:
                logger.warning(f"Invalid threshold amount {self.semantic_breakpoint_threshold_amount} for standard_deviation. "
                              "Should be positive")
                return False
        elif self.semantic_breakpoint_type == SemanticChunkerBreakpointType.INTERQUARTILE:
            # Interquartile should be positive
            if self.semantic_breakpoint_threshold_amount <= 0.0:
                logger.warning(f"Invalid threshold amount {self.semantic_breakpoint_threshold_amount} for interquartile. "
                              "Should be positive")
                return False
        
        # Validate minimum chunk size
        if self.semantic_min_chunk_size <= 0:
            logger.warning(f"Invalid min_chunk_size {self.semantic_min_chunk_size}. Should be positive")
            return False
        
        return True
    
    def get_semantic_chunker_config_info(self) -> dict:
        """
        Get information about the current semantic chunker configuration.
        
        Returns:
            Dictionary with configuration details and recommendations
        """
        config_info = {
            "breakpoint_type": self.semantic_breakpoint_type.value,
            "breakpoint_threshold_amount": self.semantic_breakpoint_threshold_amount,
            "min_chunk_size": self.semantic_min_chunk_size,
            "is_valid": self.validate_semantic_chunker_config(),
        }
        
        # Add recommendations based on breakpoint type
        recommendations = {
            SemanticChunkerBreakpointType.PERCENTILE: 
                "Good for general use. Default 95.0 works well for most documents. "
                "Lower values (85-90) create smaller chunks, higher values (95-99) create larger chunks.",
            SemanticChunkerBreakpointType.STANDARD_DEVIATION:
                "Good for documents with consistent structure. Default 3.0 is conservative. "
                "Lower values (1.5-2.5) create more chunks, higher values (3.5-5.0) create fewer chunks.",
            SemanticChunkerBreakpointType.INTERQUARTILE:
                "Good for outlier detection. Default 1.5 works well. "
                "Lower values (1.0-1.2) are more sensitive, higher values (2.0-3.0) are less sensitive.",
            SemanticChunkerBreakpointType.GRADIENT:
                "Good for highly correlated or domain-specific content (legal, medical). "
                "Uses anomaly detection on gradient. Default 95.0 percentile threshold."
        }
        
        config_info["recommendation"] = recommendations.get(self.semantic_breakpoint_type, "Unknown breakpoint type")
        config_info["available_types"] = self.get_available_breakpoint_types()
        
        return config_info

# Convenience functions for backward compatibility
def split_documents(
    documents: List[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    chunking_strategy: ChunkingStrategy = CHUNKING_STRATEGY,
    semantic_breakpoint_type: Optional[SemanticChunkerBreakpointType] = None,
    semantic_breakpoint_threshold_amount: Optional[float] = None,
) -> List[Document]:
    """
    Split documents into chunks for better embedding and retrieval.
    
    Args:
        documents: List of Document objects to split
        chunk_size: Size of each chunk in characters
        chunk_overlap: Overlap between chunks in characters
        chunking_strategy: Strategy to use for chunking
        semantic_breakpoint_type: Breakpoint threshold type for semantic chunking
        semantic_breakpoint_threshold_amount: Threshold amount for semantic chunking
        
    Returns:
        List of split Document objects
    """
    service = ChunkingService(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunking_strategy=chunking_strategy,
        semantic_breakpoint_type=semantic_breakpoint_type or SEMANTIC_CHUNKER_BREAKPOINT_TYPE,
        semantic_breakpoint_threshold_amount=semantic_breakpoint_threshold_amount or SEMANTIC_CHUNKER_BREAKPOINT_THRESHOLD_AMOUNT,
    )
    return service.split_documents(documents)


def optimize_chunking_strategy(
    documents: List[Document],
    target_chunk_size: int = 1000,
    max_chunk_size: int = 2000
) -> Tuple[int, int]:
    """
    Optimize chunking parameters based on document characteristics.
    
    Args:
        documents: List of documents to analyze
        target_chunk_size: Target chunk size
        max_chunk_size: Maximum allowed chunk size
        
    Returns:
        Tuple of (optimized_chunk_size, optimized_overlap)
    """
    service = ChunkingService(adaptive_chunking=True)
    return service._optimize_chunking_parameters(documents, target_chunk_size, 100)
