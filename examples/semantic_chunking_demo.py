#!/usr/bin/env python3
"""
Example script demonstrating semantic chunking configuration and usage.
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from lets_talk.core.pipeline.services.chunking_service import ChunkingService, split_documents
from lets_talk.shared.config import (
    SemanticChunkerBreakpointType, 
    ChunkingStrategy
)
from langchain.schema.document import Document


def create_sample_documents():
    """Create sample documents for testing."""
    return [
        Document(
            page_content="""
            Machine learning is a subset of artificial intelligence that enables computers to learn 
            and improve from experience without being explicitly programmed. It focuses on the 
            development of computer programs that can access data and use it to learn for themselves.
            """,
            metadata={"source": "ml_intro.md", "topic": "machine_learning"}
        ),
        Document(
            page_content="""
            Deep learning is part of a broader family of machine learning methods based on artificial 
            neural networks with representation learning. Learning can be supervised, semi-supervised 
            or unsupervised. Deep learning architectures such as deep neural networks, deep belief 
            networks, recurrent neural networks and convolutional neural networks have been applied 
            to fields including computer vision, speech recognition, natural language processing.
            """,
            metadata={"source": "deep_learning.md", "topic": "deep_learning"}
        ),
        Document(
            page_content="""
            Natural language processing (NLP) is a subfield of linguistics, computer science, and 
            artificial intelligence concerned with the interactions between computers and human language, 
            in particular how to program computers to process and analyze large amounts of natural 
            language data. The goal is a computer capable of understanding the contents of documents, 
            including the contextual nuances of the language within them.
            """,
            metadata={"source": "nlp_basics.md", "topic": "nlp"}
        ),
        Document(
            page_content="""
            Python is a high-level, interpreted, general-purpose programming language. Its design 
            philosophy emphasizes code readability with the use of significant indentation. Python 
            is dynamically-typed and garbage-collected. It supports multiple programming paradigms, 
            including structured, object-oriented and functional programming.
            """,
            metadata={"source": "python_intro.md", "topic": "programming"}
        ),
    ]


def demonstrate_semantic_chunking_types():
    """Demonstrate different semantic chunking types."""
    print("🧩 Semantic Chunking Types Demonstration")
    print("=" * 60)
    
    documents = create_sample_documents()
    print(f"📄 Processing {len(documents)} sample documents")
    
    # Test each breakpoint type
    breakpoint_types = [
        (SemanticChunkerBreakpointType.PERCENTILE, 90.0),
        (SemanticChunkerBreakpointType.STANDARD_DEVIATION, 2.5),
        (SemanticChunkerBreakpointType.INTERQUARTILE, 1.5),
        (SemanticChunkerBreakpointType.GRADIENT, 92.0),
    ]
    
    results = {}
    
    for breakpoint_type, threshold in breakpoint_types:
        print(f"\n🔄 Testing {breakpoint_type.value} (threshold: {threshold})")
        
        try:
            service = ChunkingService(
                chunking_strategy=ChunkingStrategy.SEMANTIC,
                semantic_breakpoint_type=breakpoint_type,
                semantic_breakpoint_threshold_amount=threshold,
                semantic_min_chunk_size=50
            )
            
            # Get configuration info
            config_info = service.get_semantic_chunker_config_info()
            print(f"   📋 Configuration valid: {config_info['is_valid']}")
            
            if config_info['is_valid']:
                # Split documents
                chunks = service.split_documents(documents)
                results[breakpoint_type.value] = len(chunks)
                
                print(f"   ✅ Created {len(chunks)} chunks")
                
                # Analyze efficiency
                efficiency = service.analyze_chunking_efficiency(documents, chunks)
                print(f"   📊 Avg chunk size: {efficiency.get('average_chunk_size', 0):.0f} chars")
                print(f"   📊 Chunks per document: {efficiency.get('chunks_per_document', 0):.1f}")
                
                # Show first chunk as example
                if chunks:
                    first_chunk = chunks[0].page_content[:100].replace('\n', ' ').strip()
                    print(f"   📝 Sample chunk: \"{first_chunk}...\"")
            else:
                print(f"   ❌ Invalid configuration")
                
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            results[breakpoint_type.value] = 0
    
    # Summary
    print(f"\n📈 Summary of Results:")
    for bp_type, chunk_count in results.items():
        print(f"   {bp_type}: {chunk_count} chunks")
    
    return results


def demonstrate_convenience_functions():
    """Demonstrate convenience functions with semantic chunking."""
    print("\n🔧 Convenience Functions Demonstration")
    print("=" * 60)
    
    documents = create_sample_documents()
    
    # Method 1: Using convenience function with semantic chunking
    print("1. Using split_documents() convenience function:")
    chunks1 = split_documents(
        documents,
        chunking_strategy=ChunkingStrategy.SEMANTIC,
        semantic_breakpoint_type=SemanticChunkerBreakpointType.PERCENTILE,
        semantic_breakpoint_threshold_amount=88.0
    )
    print(f"   ✅ Created {len(chunks1)} chunks with convenience function")
    
    # Method 2: Using ChunkingService directly
    print("\n2. Using ChunkingService class directly:")
    service = ChunkingService(
        chunking_strategy=ChunkingStrategy.SEMANTIC,
        semantic_breakpoint_type=SemanticChunkerBreakpointType.INTERQUARTILE,
        semantic_breakpoint_threshold_amount=1.8
    )
    chunks2 = service.split_documents(documents)
    print(f"   ✅ Created {len(chunks2)} chunks with service class")
    
    # Method 3: Configuration validation and info
    print("\n3. Configuration validation and recommendations:")
    for bp_type in SemanticChunkerBreakpointType:
        service = ChunkingService(semantic_breakpoint_type=bp_type)
        config_info = service.get_semantic_chunker_config_info()
        print(f"   📋 {bp_type.value}: {config_info['recommendation'][:50]}...")


def demonstrate_adaptive_chunking():
    """Demonstrate adaptive chunking with semantic configuration."""
    print("\n🎯 Adaptive Chunking with Semantic Configuration")
    print("=" * 60)
    
    # Create documents with varying lengths
    varied_documents = [
        Document(page_content="Short document."),
        Document(page_content="Medium length document with several sentences that provide more context and information about the topic being discussed."),
        Document(page_content="""
        This is a very long document that contains multiple paragraphs and extensive information.
        It includes detailed explanations, examples, and comprehensive coverage of the topic.
        
        The document spans multiple sections and provides in-depth analysis of various aspects.
        Each section builds upon the previous one, creating a coherent and comprehensive resource.
        
        Such documents require careful chunking to maintain semantic coherence while ensuring
        that the resulting chunks are appropriately sized for embedding and retrieval purposes.
        The adaptive chunking system should optimize parameters based on the document characteristics.
        """)
    ]
    
    print(f"📄 Processing {len(varied_documents)} documents with varying lengths:")
    for i, doc in enumerate(varied_documents):
        print(f"   Doc {i+1}: {len(doc.page_content)} characters")
    
    # Test with adaptive chunking enabled
    service = ChunkingService(
        chunking_strategy=ChunkingStrategy.SEMANTIC,
        adaptive_chunking=True,
        semantic_breakpoint_type=SemanticChunkerBreakpointType.PERCENTILE,
        semantic_breakpoint_threshold_amount=92.0
    )
    
    chunks = service.split_documents(varied_documents)
    efficiency = service.analyze_chunking_efficiency(varied_documents, chunks)
    
    print(f"\n✅ Adaptive semantic chunking results:")
    print(f"   📊 Total chunks: {len(chunks)}")
    print(f"   📊 Average chunk size: {efficiency.get('average_chunk_size', 0):.0f} chars")
    print(f"   📊 Min chunk size: {efficiency.get('min_chunk_size', 0)} chars")
    print(f"   📊 Max chunk size: {efficiency.get('max_chunk_size', 0)} chars")
    print(f"   📊 Chunks per document: {efficiency.get('chunks_per_document', 0):.1f}")


def main():
    """Main demonstration function."""
    print("🚀 Semantic Chunking Configuration Examples")
    print("=" * 80)
    print("This script demonstrates the new semantic chunking features.")
    print("Note: Some features may fall back to text splitter if langchain_experimental is not available.\n")
    
    try:
        # Demonstrate semantic chunking types
        results = demonstrate_semantic_chunking_types()
        
        # Demonstrate convenience functions
        demonstrate_convenience_functions()
        
        # Demonstrate adaptive chunking
        demonstrate_adaptive_chunking()
        
        print("\n🎉 All demonstrations completed successfully!")
        print("\n💡 Tips for production use:")
        print("   - Start with percentile (90-95) for most documents")
        print("   - Use standard_deviation for consistent document structures")
        print("   - Try gradient for domain-specific content (legal, medical)")
        print("   - Enable adaptive_chunking for varied document sizes")
        print("   - Always validate configuration before processing")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        print("Make sure all dependencies are installed and the backend is properly configured.")


if __name__ == "__main__":
    main()
