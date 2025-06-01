"""
RAG (Retrieval Augmented Generation) module.

This module implements components for Retrieval Augmented Generation systems including:
- Document loading from web and local sources
- Vector store management with Qdrant
- Various retrieval strategies (BM25, MultiQuery, Ensemble)
- Utility functions for building and configuring retrievers

The module supports different embedding models and retrieval techniques that can be 
configured through the application settings.
"""
# from operator import itemgetter
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.runnables import RunnablePassthrough
# from langchain.prompts import ChatPromptTemplate
# from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.document import Document
from langchain_qdrant import QdrantVectorStore
from langchain_community.document_loaders import WebBaseLoader
from langchain.embeddings import init_embeddings
from langchain.chat_models import init_chat_model
from langchain_core.vectorstores.base import VectorStoreRetriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_qdrant import QdrantVectorStore
# from langchain.retrievers import ParentDocumentRetriever
# from langchain.storage import InMemoryStore
# from langchain_text_splitters import RecursiveCharacterTextSplitter
#from qdrant_client import QdrantClient, models

from lets_talk.utils import blog
from lets_talk.config import (BM25_RETRIEVAL, LLM_MODEL, LLM_TEMPERATURE, MAX_SEARCH_RESULTS, MULTI_QUERY_RETRIEVAL, OLLAMA_BASE_URL, PARENT_DOCUMENT_RETRIEVAL)


from lets_talk.config import (
    
    QDRANT_URL,
    EMBEDDING_MODEL,
    QDRANT_COLLECTION,
    DATA_DIR,WEB_URLS, BASE_URL, BLOG_BASE_URL,DATA_DIR_PATTERN

)

import logging

# Set up logger
logger = logging.getLogger(__name__)

# parent_docs = documents
# child_document_splitter = RecursiveCharacterTextSplitter(chunk_size=200)
# store = InMemoryStore()

# parent_document_retriever = ParentDocumentRetriever(
#     vectorstore = parent_document_vectorstore,
#     docstore=store,
#     child_splitter=child_document_splitter,
# )


def load_documents(
    data_dir: str = DATA_DIR,
    pattern: str = DATA_DIR_PATTERN,
    base_url: str = BASE_URL,
    blog_base_url: str = BLOG_BASE_URL,
    web_urls: list[str] = WEB_URLS
) -> list[Document]:
    """Load documents from the specified directory and URLs."""
    logger.info("Loading blog posts from directory: %s", data_dir)
    docs = blog.load_blog_posts(data_dir=data_dir,glob_pattern=pattern)
    logger.info("Loaded %d blog posts", len(docs))
    #TODO: implement `index_only_published_posts` to filter out unpublished posts
    docs_with_data = blog.update_document_metadata(docs,data_dir_prefix=data_dir+'/', base_url=base_url, blog_base_url=blog_base_url, remove_suffix=pattern)
    logger.info("Updated document metadata for blog posts")
    loader = WebBaseLoader(web_urls)
    logger.info("Loading web documents from URLs: %s", web_urls)
    web_docs = loader.load()
    logger.info("Loaded %d web documents", len(web_docs))
    all_docs = docs_with_data + web_docs
    logger.info("Total documents loaded: %d", len(all_docs))
    return all_docs


# from lets_talk.chains import chat_llm
# from lets_talk.prompts import rag_prompt_template

def load_vector_store(
    collection_name: str = QDRANT_COLLECTION,
    qdrant_url: str = QDRANT_URL,
    embedding_model_name: str = EMBEDDING_MODEL
) -> QdrantVectorStore | None:
    """Load the vector store from the specified path."""
    logger.info("Loading vector store: collection=%s, url=%s, embedding_model=%s", collection_name, qdrant_url, embedding_model_name)
    if not collection_name or not qdrant_url or not embedding_model_name:
        logger.warning("Missing collection_name, qdrant_url, or embedding_model_name. Returning None.")
        return None
    
    embeddings = init_embeddings(embedding_model_name)

    if embedding_model_name.startswith("ollama:"):
        base_url = OLLAMA_BASE_URL
        logger.info("Using Ollama embeddings with base_url: %s", base_url)
        embeddings = init_embeddings(embedding_model_name, base_url=base_url)
    
    vector_store = QdrantVectorStore.from_existing_collection(        
        embedding=embeddings, #type: ignore
        collection_name=QDRANT_COLLECTION,
        url=QDRANT_URL,
        prefer_grpc=True,
    )
    logger.info("Vector store loaded successfully")
    return vector_store

def build_retriever(
    vector_store: QdrantVectorStore | None = None,
    all_docs: list[Document] = [],
    max_search_results: int = MAX_SEARCH_RESULTS,
    model_name: str = LLM_MODEL,    
    temperature: float = LLM_TEMPERATURE,
) -> EnsembleRetriever | VectorStoreRetriever | None: 
    """Build a retriever from the vector store."""
    if vector_store is None:
        logger.warning("No vector store provided. Returning None.")
        return None
    
    logger.info("Initializing retriever from vector store")
    retriever = vector_store.as_retriever(search_kwargs={"k": max_search_results})
    retriever_list = []
    
    if MULTI_QUERY_RETRIEVAL:
        logger.info("MULTI_QUERY_RETRIEVAL enabled. Initializing chat model: %s", model_name)
        model = init_chat_model(model_name, temperature=temperature)
        if model_name.startswith("ollama:"):
            base_url = OLLAMA_BASE_URL
            logger.info("Using Ollama chat model with base_url: %s", base_url)
            model = init_embeddings(model_name, base_url=base_url)
        multi_query_retriever = MultiQueryRetriever.from_llm(
            retriever=retriever, llm=model # type: ignore
        )
        logger.info("MultiQueryRetriever added")
        retriever_list.append(multi_query_retriever)

    if BM25_RETRIEVAL:
        logger.info("BM25_RETRIEVAL enabled. Creating BM25Retriever from documents.")
        bm25_retriever = BM25Retriever.from_documents(all_docs)  # type: ignore
        retriever_list.append(bm25_retriever)
        logger.info("BM25Retriever added")

    if PARENT_DOCUMENT_RETRIEVAL:
        logger.info("PARENT_DOCUMENT_RETRIEVAL enabled, but not implemented yet.")
        # TODO: Create a retriever that retrieves parent documents
        pass

    if len(retriever_list) == 0:
        logger.info("No additional retrievers added. Returning base retriever.")
        return retriever
    
    retriever_list.append(retriever)  # type: ignore
    equal_weighting = [1/len(retriever_list)] * len(retriever_list)
    logger.info("Creating EnsembleRetriever with %d retrievers", len(retriever_list))
    ensemble_retriever = EnsembleRetriever(
        # TODO: add support for weights
        retrievers=retriever_list, weights=equal_weighting  # type: ignore
    )
    logger.info("EnsembleRetriever created successfully")
    return ensemble_retriever

# Create a retriever
logger.info("Loading vector store and documents for retriever creation")
vector_store = load_vector_store()
all_docs = load_documents()

retriever = build_retriever(
    vector_store=vector_store,
    all_docs=all_docs,
    max_search_results=MAX_SEARCH_RESULTS
)
logger.info("Retriever created: %s", type(retriever).__name__ if retriever else "None")

# Load vector store using the utility function
# vector_store:QdrantVectorStore | None = blog.load_vector_store(storage_path=VECTOR_STORAGE_PATH,collection_name=QDRANT_COLLECTION,
#                      qdrant_url=QDRANT_URL,
#                      embedding_model= EMBEDDING_MODEL)

# rag_prompt = ChatPromptTemplate.from_template(rag_prompt_template)
# Create chain
# rag_chain = (
#     {"context": itemgetter("question") | retriever, "question": itemgetter("question")}
#     | RunnablePassthrough.assign(context=itemgetter("context"))
#     | {"response": rag_prompt | chat_llm, "context": itemgetter("context")}
# )


