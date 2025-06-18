"""ReAct agent implementation using LangGraph."""
import logging
import os
from typing import Any, Dict, List, Optional, Union
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent

from lets_talk.agents.base import BaseAgent, AgentConfig
from lets_talk.core.rag.retriever import retriever, all_docs
from lets_talk.tools.datetime.datetime_utils import get_current_datetime
from lets_talk.utils.formatters import format_docs
from lets_talk.tools.external.rss_feed import RSSFeedTool
from lets_talk.shared.config import (
    AGENT_PROMPT, AGENT_PROMPT_FILE, BASE_URL, BLOG_BASE_URL, 
    LLM_MODEL, LLM_TEMPERATURE, RSS_URL
)

logger = logging.getLogger(__name__)


@tool
def retrieve_documents(query: str) -> str:
    """Retrieve relevant documents from the knowledge base to answer user questions.
    
    Use this tool when you need to search for specific information, facts, or content
    that may be in the document collection. Provide a clear search query related to
    what information you need to find.
    
    Args:
        query: The search query to find relevant documents
        
    Returns:
        Formatted text containing the retrieved document content
    """
    logger.info(f"Retrieving documents for query: {query}")
    try:
        docs = retriever.invoke(query)
        logger.info(f"Retrieved {len(docs) if docs else 0} documents for query: {query}")
        return format_docs(docs)
    except Exception as e:
        logger.error(f"Error retrieving documents for query '{query}': {e}")
        return f"An error occurred while retrieving documents: {e}"


@tool
def retrieve_page_by_url(url: str) -> str:
    """Retrieve a specific page by URL from the knowledge base.
    
    Use this tool when you have a specific URL and want to retrieve its content.
    
    Args:
        url: The URL of the page to retrieve
        
    Returns:
        The content of the page at the specified URL
    """
    logger.info(f"Retrieving page for URL: {url}")
    try:
        if url.startswith(BASE_URL) or url.startswith(BLOG_BASE_URL):
            # Search all_docs metadata for the url
            for doc in all_docs:
                if doc.metadata.get("url") == url or doc.metadata.get("source") == url:
                    logger.info(f"Found document for URL: {url}")
                    return format_docs([doc])
            logger.warning(f"No content found for the URL: {url}")
            return f"No content found for the URL: {url}. Please ensure the URL is correct and exists in the knowledge base."
        else:
            logger.warning(f"External URL not supported: {url}")
            return f"External URLs are not supported in this version. Please use URLs from the blog or knowledge base i.e {BASE_URL} or {BLOG_BASE_URL}."
    except Exception as e:
        logger.error(f"Error retrieving page for URL '{url}': {e}")
        return f"An error occurred while retrieving the page: {e}"


class ReactAgent(BaseAgent):
    """ReAct agent with tool-based reasoning capabilities."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__("ReAct Agent", "Tool-enabled conversational agent")
        self.config = config or AgentConfig(
            model_name=LLM_MODEL,
            temperature=LLM_TEMPERATURE
        )
        self.tools = self._setup_tools()
        self.prompt = self._load_prompt()
        self.agent = self._create_agent()
    
    def _setup_tools(self) -> List[Any]:
        """Set up the agent's tools."""
        tools = [retrieve_documents, retrieve_page_by_url, get_current_datetime]
        
        if RSS_URL:
            logger.info(f"RSS URL is set to: {RSS_URL}")
            tools.append(RSSFeedTool(rss_url=RSS_URL))
        
        return tools
    
    def _load_prompt(self) -> str:
        """Load the agent prompt from file or use default."""
        if os.path.exists(AGENT_PROMPT_FILE):
            logger.info("Reading agent prompt from %s", AGENT_PROMPT_FILE)
            try:
                with open(AGENT_PROMPT_FILE, 'r') as file:
                    prompt = file.read()
                logger.info("Agent prompt loaded successfully.")
                return prompt
            except Exception as e:
                logger.error(f"Error loading prompt file: {e}")
        
        logger.warning("Agent prompt file %s not found. Using default prompt.", AGENT_PROMPT_FILE)
        return AGENT_PROMPT
    
    def _create_agent(self):
        """Create and return the ReAct agent."""
        logger.info("Creating ReAct agent with provided prompt, model, and tools.")
        
        model = init_chat_model(
            self.config.model_name, 
            temperature=self.config.temperature
        )
        
        agent = create_react_agent(
            model=model,
            tools=self.tools,
            prompt=self.prompt,
            version="v2",
        )
        
        logger.info("ReAct agent created successfully.")
        return agent
    
    async def ainvoke(
        self, 
        input_data: Union[Dict[str, Any], str, BaseMessage],
        config: Optional[RunnableConfig] = None
    ) -> Any:
        """Asynchronously invoke the ReAct agent."""
        # Convert input to proper format
        if isinstance(input_data, str):
            input_data = {"messages": [HumanMessage(content=input_data)]}
        elif isinstance(input_data, BaseMessage):
            input_data = {"messages": [input_data]}
        
        return await self.agent.ainvoke(input_data, config)
    
    def invoke(
        self, 
        input_data: Union[Dict[str, Any], str, BaseMessage],
        config: Optional[RunnableConfig] = None
    ) -> Any:
        """Synchronously invoke the ReAct agent."""
        # Convert input to proper format
        if isinstance(input_data, str):
            input_data = {"messages": [HumanMessage(content=input_data)]}
        elif isinstance(input_data, BaseMessage):
            input_data = {"messages": [input_data]}
        
        return self.agent.invoke(input_data, config)


# Create default agent instance
logger.info("Initializing default ReAct agent instance.")
default_agent = ReactAgent()
logger.info("Default ReAct agent instance initialized and ready.")
