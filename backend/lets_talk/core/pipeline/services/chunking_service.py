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
    ChunkingStrategy,
    EMBEDDING_MODEL,
    ADAPTIVE_CHUNKING
)
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
        adaptive_chunking: bool = ADAPTIVE_CHUNKING
    ):
        """
        Initialize the chunking service.
        
        Args:
            chunk_size: Default chunk size in characters
            chunk_overlap: Default overlap between chunks
            chunking_strategy: Strategy to use for chunking
            embedding_model: Embedding model for semantic chunking
            adaptive_chunking: Whether to use adaptive chunking
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunking_strategy = chunking_strategy
        self.embedding_model = embedding_model
        self.adaptive_chunking = adaptive_chunking
    
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
        
        # Apply adaptive chunking if enabled
        if self.adaptive_chunking:
            chunk_size, chunk_overlap = self._optimize_chunking_parameters(
                documents, chunk_size, chunk_overlap
            )
        
        logger.info(f"Splitting {len(documents)} documents using {strategy} strategy "
                   f"(chunk_size={chunk_size}, overlap={chunk_overlap})")
        
        if strategy == ChunkingStrategy.SEMANTIC:
            split_docs = self._semantic_chunking(documents)
        else:
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
            from langchain.embeddings import init_embeddings
            
            # Initialize embeddings for semantic chunking
            embeddings = init_embeddings(self.embedding_model)
            
            semantic_chunker = SemanticChunker(
                embeddings, # type: ignore
                breakpoint_threshold_type="percentile"
            )
            split_docs = semantic_chunker.split_documents(documents)
            
            logger.info("Successfully applied semantic chunking")
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


# Convenience functions for backward compatibility
def split_documents(
    documents: List[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    chunking_strategy: ChunkingStrategy = CHUNKING_STRATEGY
) -> List[Document]:
    """
    Split documents into chunks for better embedding and retrieval.
    
    Args:
        documents: List of Document objects to split
        chunk_size: Size of each chunk in characters
        chunk_overlap: Overlap between chunks in characters
        chunking_strategy: Strategy to use for chunking
        
    Returns:
        List of split Document objects
    """
    service = ChunkingService(chunk_size, chunk_overlap, chunking_strategy)
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
