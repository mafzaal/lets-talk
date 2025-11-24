"""RAG retriever implementation."""
import logging
from typing import List, Optional
from langchain.schema.document import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_community.document_loaders import WebBaseLoader
from langchain.chat_models import init_chat_model
from langchain_core.vectorstores.base import VectorStoreRetriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever


from lets_talk.core.pipeline.services.document_loader import load_blog_posts

from lets_talk.shared.config import (
    BM25_RETRIEVAL, LLM_MODEL, LLM_TEMPERATURE, MAX_SEARCH_RESULTS, 
    MULTI_QUERY_RETRIEVAL, PARENT_DOCUMENT_RETRIEVAL,
    QDRANT_URL, EMBEDDING_MODEL, QDRANT_COLLECTION, DATA_DIR, WEB_URLS, 
    BASE_URL, BLOG_BASE_URL, DATA_DIR_PATTERN, VECTOR_STORAGE_PATH
)
from lets_talk.utils.wrapper import init_embeddings_wrapper

logger = logging.getLogger(__name__)


def load_documents(
    data_dir: str = DATA_DIR,
    pattern: str = DATA_DIR_PATTERN,
    base_url: str = BASE_URL,
    blog_base_url: str = BLOG_BASE_URL,
    web_urls: List[str] = WEB_URLS
) -> List[Document]:
    """Load documents from the specified directory and URLs."""
    logger.info("Loading blog posts from directory: %s", data_dir)
    docs = load_blog_posts(
        data_dir=data_dir, 
        data_dir_pattern=pattern,
        blog_base_url=blog_base_url,
        base_url=base_url
    )
    logger.info("Loaded %d blog posts with metadata", len(docs))
    
    if web_urls:
        loader = WebBaseLoader(web_urls)
        logger.info("Loading web documents from URLs: %s", web_urls)
        web_docs = loader.load()
        logger.info("Loaded %d web documents", len(web_docs))
        all_docs = docs + web_docs
    else:
        all_docs = docs
    
    logger.info("Total documents loaded: %d", len(all_docs))
    return all_docs


def load_vector_store(
    collection_name: str = QDRANT_COLLECTION,
    qdrant_url: str = QDRANT_URL,
    storage_path: str = VECTOR_STORAGE_PATH,
    embedding_model_name: str = EMBEDDING_MODEL
) -> Optional[QdrantVectorStore]:
    """
    Load the vector store from the specified collection, creating it if it doesn't exist.
    
    Args:
        collection_name: Name of the Qdrant collection
        qdrant_url: URL for remote Qdrant instance (takes priority if provided)
        storage_path: Path to local vector store (used if qdrant_url is not provided)
        embedding_model_name: Name of the embedding model
        
    Returns:
        QdrantVectorStore instance or None if loading fails
    """
    logger.info("Loading vector store: collection=%s, url=%s, path=%s, embedding_model=%s", 
                collection_name, qdrant_url, storage_path, embedding_model_name)
    
    if not collection_name or not embedding_model_name:
        logger.warning("Missing collection_name or embedding_model_name. Returning None.")
        return None
    
    if not qdrant_url and not storage_path:
        logger.warning("Neither qdrant_url nor storage_path provided. Returning None.")
        return None
    
    embeddings = init_embeddings_wrapper(embedding_model_name)
    
    try:
        if qdrant_url:
            # Use remote Qdrant
            logger.info(f"Loading vector store from remote Qdrant at {qdrant_url}")
            try:
                # First, try to connect to existing collection
                vector_store = QdrantVectorStore.from_existing_collection(        
                    embedding=embeddings,# type: ignore
                    collection_name=collection_name,
                    url=qdrant_url,
                    prefer_grpc=True,
                )
                logger.info("Vector store loaded successfully from existing remote collection")
                return vector_store
            except Exception as e:
                logger.warning(f"Failed to load existing remote collection '{collection_name}': {e}")
                logger.info("Attempting to create new collection...")
                
                # Create a Qdrant client to check/create collection
                client = QdrantClient(url=qdrant_url, prefer_grpc=True)
                
                # Check if collection exists
                collections = client.get_collections()
                collection_exists = any(col.name == collection_name for col in collections.collections)
                
                if not collection_exists:
                    logger.info(f"Collection '{collection_name}' does not exist. Creating it...")
                    
                    # Get embedding dimension from the embeddings model
                    sample_embedding = embeddings.embed_query("sample text")
                    vector_size = len(sample_embedding)
                    
                    # Create collection with vector parameters
                    client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=vector_size,
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"Collection '{collection_name}' created successfully with vector size {vector_size}")
                else:
                    logger.info(f"Collection '{collection_name}' already exists")
                
                # Now create vector store from the collection (existing or newly created)
                vector_store = QdrantVectorStore.from_existing_collection(        
                    embedding=embeddings,# type: ignore
                    collection_name=collection_name,
                    url=qdrant_url,
                    prefer_grpc=True,
                )
                logger.info("Vector store loaded successfully after collection creation/verification")
                return vector_store
        else:
            # Use local Qdrant storage
            logger.info(f"Loading vector store from local path at {storage_path}")
            from pathlib import Path
            
            storage_path_obj = Path(storage_path)
            if not storage_path_obj.exists():
                logger.warning(f"Vector store not found at {storage_path}. Cannot load.")
                return None
            
            # Initialize local Qdrant client
            try:
                client = QdrantClient(path=storage_path)
                
                # Check if collection exists
                collections = client.get_collections()
                collection_exists = any(col.name == collection_name for col in collections.collections)
                
                if not collection_exists:
                    logger.warning(f"Collection '{collection_name}' does not exist in local storage at {storage_path}")
                    return None
                
                # Create vector store with the local client
                vector_store = QdrantVectorStore(
                    client=client,
                    collection_name=collection_name,
                    embedding=embeddings, # type: ignore
                )
                logger.info(f"Vector store loaded successfully from local path {storage_path}")
                return vector_store
            except Exception as local_error:
                logger.error(f"Failed to load vector store from local path: {local_error}")
                return None
            
    except Exception as e:
        logger.error(f"Error loading vector store: {e}")
        return None


def build_retriever(
    vector_store: Optional[QdrantVectorStore] = None,
    all_docs: List[Document] = None, # type: ignore
    max_search_results: int = MAX_SEARCH_RESULTS,
    model_name: str = LLM_MODEL,    
    temperature: float = LLM_TEMPERATURE,
) -> Optional[VectorStoreRetriever]:
    """Build a retriever from the vector store."""
    if vector_store is None:
        logger.warning("No vector store provided. Returning None.")
        return None
    
    if all_docs is None:
        all_docs = []
    
    logger.info("Initializing retriever from vector store")
    retriever = vector_store.as_retriever(search_kwargs={"k": max_search_results})
    retriever_list = []
    
    if MULTI_QUERY_RETRIEVAL:
        logger.info("MULTI_QUERY_RETRIEVAL enabled. Initializing chat model: %s", model_name)
        model = init_chat_model(model_name, temperature=temperature)

        multi_query_retriever = MultiQueryRetriever.from_llm(
            retriever=retriever, llm=model
        )
        logger.info("MultiQueryRetriever added")
        retriever_list.append(multi_query_retriever)

    if BM25_RETRIEVAL and all_docs:
        logger.info("BM25_RETRIEVAL enabled. Creating BM25Retriever from documents.")
        bm25_retriever = BM25Retriever.from_documents(all_docs)
        retriever_list.append(bm25_retriever)
        logger.info("BM25Retriever added")

    if PARENT_DOCUMENT_RETRIEVAL:
        logger.info("PARENT_DOCUMENT_RETRIEVAL enabled, but not implemented yet.")
        # TODO: Create a retriever that retrieves parent documents
        pass

    if len(retriever_list) == 0:
        logger.info("No additional retrievers added. Returning base retriever.")
        return retriever
    
    equal_weighting = [1/len(retriever_list)] * len(retriever_list)
    logger.info("Creating EnsembleRetriever with %d retrievers", len(retriever_list))
    ensemble_retriever = EnsembleRetriever(
        retrievers=retriever_list, weights=equal_weighting
    )
    logger.info("EnsembleRetriever created successfully")
    return ensemble_retriever # type: ignore


# Initialize global components

def create_retriever() -> Optional[VectorStoreRetriever]:
    """Create and return the retriever."""
    logger.info("Loading vector store and documents for retriever creation")
    vector_store = load_vector_store()
    all_docs = load_documents()

    retriever = build_retriever(
        vector_store=vector_store,
        all_docs=all_docs,
        max_search_results=MAX_SEARCH_RESULTS
    )
    return retriever

