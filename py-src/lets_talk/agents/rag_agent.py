"""RAG (Retrieval Augmented Generation) agent implementation."""
import datetime
import logging
from typing import Dict, Any, Literal, Union, cast, Optional, List
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate, 
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
)
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.runnables import RunnableConfig
from langchain_core.documents import Document

from lets_talk.agents.base import BaseAgent, AgentConfig
from lets_talk.core.rag.retriever import retriever
from lets_talk.core.models.state import InputState
from lets_talk.utils.formatters import format_docs, get_message_text
from lets_talk.shared.config import Configuration

logger = logging.getLogger(__name__)


class SearchQuery(BaseModel):
    """Search the indexed documents for a query."""
    query: str


class RAGAgent(BaseAgent):
    """RAG-based conversational agent with document retrieval capabilities."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__("RAG Agent", "Agent with document retrieval capabilities")
        self.config = config or AgentConfig()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> CompiledStateGraph:
        """Build the agent's conversation graph."""
        workflow = StateGraph(InputState)
        
        # Add nodes
        workflow.add_node("generate_query", self._generate_query)
        workflow.add_node("retrieve", self._retrieve)
        workflow.add_node("generate", self._generate)
        
        # Add edges
        workflow.add_edge(START, "generate_query")
        workflow.add_edge("generate_query", "retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)
        
        return workflow.compile()
    
    async def _generate_query(
        self, 
        state: InputState, 
        *, 
        config: RunnableConfig
    ) -> Dict[str, List[str]]:
        """Generate a search query based on the current state and configuration."""
        messages = state["messages"]
        if len(messages) == 1:
            # It's the first user question. Use the input directly to search.
            human_input = get_message_text(messages[-1])
            return {"queries": [human_input]}
        else:
            configuration = Configuration.from_runnable_config(config)
            # Build query generation prompt
            prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(configuration.query_system_prompt),
                MessagesPlaceholder(variable_name="messages"),
            ])
            
            model = init_chat_model(
                configuration.query_model, 
                temperature=0
            ).with_structured_output(SearchQuery)

            message_value = {
                "messages": messages,
                "queries": "\n- ".join(state.get("queries", [])),
                "system_time": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            }
            
            chain = prompt | model
            generated = cast(SearchQuery, await chain.ainvoke(message_value, config))
            return {"queries": [generated.query]}
    
    async def _retrieve(
        self, 
        state: InputState, 
        *, 
        config: RunnableConfig
    ) -> Dict[str, List[Document]]:
        """Retrieve documents based on the generated query."""
        queries = state.get("queries", None)
        query = queries[-1] if queries else self._get_user_message(state)
        
        if not query:
            return {"documents": []}
        
        try:
            if retriever is None:
                logger.warning("Retriever is None, returning empty documents")
                return {"documents": []}
            docs = retriever.invoke(query)
            logger.info(f"Retrieved {len(docs)} documents for query: {query}")
            return {"documents": docs}
        except Exception as e:
            logger.error(f"Error retrieving documents for query '{query}': {e}")
            return {"documents": []}
    
    async def _generate(
        self, 
        state: InputState, 
        *, 
        config: RunnableConfig
    ) -> Dict[str, List[BaseMessage]]:
        """Generate response based on retrieved documents and conversation history."""
        configuration = Configuration.from_runnable_config(config)
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(configuration.response_system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        model = init_chat_model(
            configuration.response_model, 
            temperature=configuration.response_temperature
        )
        
        # Format documents for context
        docs = state.get("documents", [])
        formatted_docs = format_docs(docs) if docs else "No relevant documents found."
        
        message_value = {
            "messages": state["messages"],
            "context": formatted_docs,
            "system_time": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
        }
        
        chain = prompt | model | StrOutputParser()
        response = await chain.ainvoke(message_value, config)
        
        return {"messages": [AIMessage(content=response)]}
    
    def _get_user_message(self, state: InputState) -> str:
        """Extract the latest user message from state."""
        messages = state.get("messages", [])
        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                return message.content
        return ""
    
    async def ainvoke(
        self, 
        input_data: Union[Dict[str, Any], str, BaseMessage],
        config: Optional[RunnableConfig] = None
    ) -> Any:
        """Asynchronously invoke the RAG agent."""
        # Convert input to proper state format
        if isinstance(input_data, str):
            state = {"messages": [HumanMessage(content=input_data)]}
        elif isinstance(input_data, BaseMessage):
            state = {"messages": [input_data]}
        else:
            state = input_data
        
        return await self.graph.ainvoke(state, config)
    
    def invoke(
        self, 
        input_data: Union[Dict[str, Any], str, BaseMessage],
        config: Optional[RunnableConfig] = None
    ) -> Any:
        """Synchronously invoke the RAG agent."""
        # Convert input to proper state format
        if isinstance(input_data, str):
            state = {"messages": [HumanMessage(content=input_data)]}
        elif isinstance(input_data, BaseMessage):
            state = {"messages": [input_data]}
        else:
            state = input_data
        
        return self.graph.invoke(state, config)
