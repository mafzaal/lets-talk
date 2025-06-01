"""
RAG (Retrieval Augmented Generation) model implementation.
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
from langchain_experimental.text_splitter import SemanticChunker
from langchain_qdrant import QdrantVectorStore
from lets_talk.utils import blog
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from lets_talk.config import (LLM_MODEL, LLM_TEMPERATURE, MAX_SEARCH_RESULTS)
from langchain.chat_models import init_chat_model
from lets_talk.utils import format_docs
from lets_talk.config import (
    
    QDRANT_URL,
    EMBEDDING_MODEL,
    QDRANT_COLLECTION,
    DATA_DIR,WEB_URLS, BASE_URL, BLOG_BASE_URL,DATA_DIR_PATTERN

)


def load_documents(
    data_dir: str = DATA_DIR,
    pattern: str = DATA_DIR_PATTERN,
    base_url: str = BASE_URL,
    blog_base_url: str = BLOG_BASE_URL,
    web_urls: list[str] = WEB_URLS
) -> list[Document]:
    """Load documents from the specified directory and URLs."""
    
    docs = blog.load_blog_posts(data_dir=data_dir,glob_pattern=pattern)
    #TODO: implement `index_only_published_posts` to filter out unpublished posts
    docs_with_data = blog.update_document_metadata(docs,data_dir_prefix=data_dir+'/', base_url=base_url, blog_base_url=blog_base_url, remove_suffix=pattern)
    loader = WebBaseLoader(web_urls)
    web_docs = loader.load()
    all_docs = docs_with_data + web_docs
    return all_docs


# from lets_talk.chains import chat_llm
# from lets_talk.prompts import rag_prompt_template

def load_vector_store(
    collection_name: str = QDRANT_COLLECTION,
    qdrant_url: str = QDRANT_URL,
    embedding_model_name: str = EMBEDDING_MODEL,
    #TODO: make this configurable
    base_url="http://host.docker.internal:11434"
) -> QdrantVectorStore | None:
    """Load the vector store from the specified path."""
    
    if not collection_name or not qdrant_url or not embedding_model_name:
        return None
    

    embeddings = init_embeddings(embedding_model_name, base_url=base_url)
    
    vector_store = QdrantVectorStore.from_existing_collection(        
        embedding=embeddings, #type: ignore
        collection_name=QDRANT_COLLECTION,
        url=QDRANT_URL,
        prefer_grpc=True,
    )

    return vector_store

def build_retriever(
    vector_store: QdrantVectorStore | None = None,
    all_docs: list[Document] = [],
    max_search_results: int = MAX_SEARCH_RESULTS
) -> EnsembleRetriever | None: 
    """Build a retriever from the vector store."""
    
    if vector_store is None:
        return None
    


    model = init_chat_model(LLM_MODEL, temperature=LLM_TEMPERATURE)

    retriever = vector_store.as_retriever(search_kwargs={"k": max_search_results})

    multi_query_retriever = MultiQueryRetriever.from_llm(
        retriever=retriever, llm=model
    )

    bm25_retriever = BM25Retriever.from_documents(all_docs)  # type: ignore
    retriever_list = [bm25_retriever,  multi_query_retriever]

    ensemble_retriever = EnsembleRetriever(
        # TODO: add support for weights
        retrievers=retriever_list, weights=[0.5, 0.5]  # Adjust weights as needed
    )
    
    return ensemble_retriever
# Load vector store using the utility function
# vector_store:QdrantVectorStore | None = blog.load_vector_store(storage_path=VECTOR_STORAGE_PATH,collection_name=QDRANT_COLLECTION,
#                      qdrant_url=QDRANT_URL,
#                      embedding_model= EMBEDDING_MODEL)

# Create a retriever
vector_store = load_vector_store()
all_docs = load_documents()

retriever = build_retriever(
    vector_store=vector_store,
    all_docs=all_docs,
    max_search_results=MAX_SEARCH_RESULTS
)

# rag_prompt = ChatPromptTemplate.from_template(rag_prompt_template)

# Create chain
# rag_chain = (
#     {"context": itemgetter("question") | retriever, "question": itemgetter("question")}
#     | RunnablePassthrough.assign(context=itemgetter("context"))
#     | {"response": rag_prompt | chat_llm, "context": itemgetter("context")}
# )


