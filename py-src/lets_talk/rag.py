"""
RAG (Retrieval Augmented Generation) model implementation.
"""
# from operator import itemgetter
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.runnables import RunnablePassthrough
# from langchain.prompts import ChatPromptTemplate
# from langchain.schema.runnable import RunnablePassthrough
from langchain_qdrant import QdrantVectorStore
from lets_talk.utils import blog
import lets_talk.utils.blog as blog
from lets_talk.config import (
    
    QDRANT_URL,
    VECTOR_STORAGE_PATH,
    EMBEDDING_MODEL,
    QDRANT_COLLECTION
)

# from lets_talk.chains import chat_llm
# from lets_talk.prompts import rag_prompt_template

# Load vector store using the utility function
vector_store:QdrantVectorStore | None = blog.load_vector_store(storage_path=VECTOR_STORAGE_PATH,collection_name=QDRANT_COLLECTION,
                     qdrant_url=QDRANT_URL,
                     embedding_model= EMBEDDING_MODEL)

# Create a retriever
retriever = vector_store.as_retriever() if vector_store is not None else None

# rag_prompt = ChatPromptTemplate.from_template(rag_prompt_template)

# Create chain
# rag_chain = (
#     {"context": itemgetter("question") | retriever, "question": itemgetter("question")}
#     | RunnablePassthrough.assign(context=itemgetter("context"))
#     | {"response": rag_prompt | chat_llm, "context": itemgetter("context")}
# )


