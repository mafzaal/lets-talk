"""
RAG (Retrieval Augmented Generation) model implementation.
"""
from operator import itemgetter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain_openai.chat_models import ChatOpenAI
from langchain_qdrant import QdrantVectorStore
from lets_talk import config
from lets_talk.utils import blog
import lets_talk.utils.blog as blog

# Load vector store using the utility function
vector_store:QdrantVectorStore = blog.load_vector_store()

# Create a retriever
retriever = vector_store.as_retriever()

llm = ChatOpenAI(model=config.LLM_MODEL, temperature=config.LLM_TEMPERATURE)


from lets_talk.prompts import rag_prompt_template

rag_prompt = ChatPromptTemplate.from_template(rag_prompt_template)

# Create chain
rag_chain = (
    {"context": itemgetter("question") | retriever, "question": itemgetter("question")}
    | RunnablePassthrough.assign(context=itemgetter("context"))
    | {"response": rag_prompt | llm, "context": itemgetter("context")}
)


