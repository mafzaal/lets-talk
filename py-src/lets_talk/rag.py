"""
RAG (Retrieval Augmented Generation) model implementation.
"""
from operator import itemgetter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain_qdrant import QdrantVectorStore

from lets_talk.utils import blog
import lets_talk.utils.blog as blog
from lets_talk.chains import chat_llm
from lets_talk.prompts import rag_prompt_template

# Load vector store using the utility function
vector_store:QdrantVectorStore = blog.load_vector_store()

# Create a retriever
retriever = vector_store.as_retriever()

rag_prompt = ChatPromptTemplate.from_template(rag_prompt_template)

# Create chain
rag_chain = (
    {"context": itemgetter("question") | retriever, "question": itemgetter("question")}
    | RunnablePassthrough.assign(context=itemgetter("context"))
    | {"response": rag_prompt | chat_llm, "context": itemgetter("context")}
)


