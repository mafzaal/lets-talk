"""
RAG (Retrieval Augmented Generation) model implementation.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from lets_talk import config

# Create prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", config.SYSTEM_TEMPLATE),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
    ("human", "Context: {context}")
])

class LangChainRAG:
    """
    RAG implementation using LangChain components.
    """
    def __init__(self, retriever, llm):
        """
        Initialize the RAG model.
        
        Args:
            retriever: Document retriever component
            llm: Language model for generation
        """
        self.retriever = retriever
        self.llm = llm
        self.chain = self._create_chain()
        
    def _create_chain(self):
        """
        Create the RAG chain.
        
        Returns:
            A runnable chain that processes user queries
        """
        # Define the RAG chain
        rag_chain = (
            {"context": self.retriever, "question": RunnablePassthrough(), "chat_history": lambda _: []}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        return rag_chain
    
    async def arun_pipeline(self, user_query: str):
        """
        Run the RAG pipeline with the user query.
        
        Args:
            user_query: User's question
            
        Returns:
            Dict containing the response generator and context
        """
        # Get relevant documents for context
        docs = self.retriever.invoke(user_query)
        context_list = [(doc.page_content, doc.metadata) for doc in docs]
        
        # Create async generator for streaming
        async def generate_response():
            async for chunk in self.chain.astream(user_query):
                yield chunk
        
        return {"response": generate_response(), "context": context_list}