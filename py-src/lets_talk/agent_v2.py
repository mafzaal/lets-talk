import logging
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
import lets_talk.rag as rag
from lets_talk.utils import format_docs
from lets_talk.tools import RSSFeedTool
from lets_talk.config import AGENT_PROMPT, AGENT_PROMPT_FILE, BASE_URL, BLOG_BASE_URL, LLM_MODEL,LLM_TEMPERATURE

# initialize logging
logger = logging.getLogger(__name__)


@tool 
def retrive_documents(query: str) -> str:
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
        docs = rag.retriever.invoke(query) # type: ignore
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
            # search rag.all_docs metadata for the url
            for doc in rag.all_docs: # type: ignore
                if doc.metadata.get("url") == url or doc.metadata.get("source") == url:
                    logger.info(f"Found document for URL: {url}")
                    return format_docs([doc]) # type: ignore
            logger.warning(f"No content found for the URL: {url}")
            return f"No content found for the URL: {url}. Please ensure the URL is correct and exists in the knowledge base."
        else:
            logger.warning(f"External URL not supported: {url}")
            return f"External URLs are not supported in this version. Please use URLs from the blog or knowledge base .i.e {BASE_URL} or {BLOG_BASE_URL}."
    except Exception as e:
        logger.error(f"Error retrieving page for URL '{url}': {e}")
        return f"An error occurred while retrieving the page: {e}"

    


from lets_talk.config import (RSS_URL)
tools =[retrive_documents, retrieve_page_by_url]

if RSS_URL:
    logger.info(f"RSS URL is set to: {RSS_URL}")
    tools.append(RSSFeedTool(rss_url=RSS_URL))

# Initialize the chat model with the specified model name and temperature
model = init_chat_model(LLM_MODEL, temperature=LLM_TEMPERATURE)

# read `agent_prompt.md` from current directory
import os
from lets_talk.config import AGENT_PROMPT

agent_system_prompt = AGENT_PROMPT


def read_file(file_path):
    """Read and return the contents of a file."""
    with open(file_path, 'r') as file:
        return file.read()

if os.path.exists(AGENT_PROMPT_FILE):
    logger.info("Reading agent prompt from %s", AGENT_PROMPT_FILE)
    agent_system_prompt = read_file(AGENT_PROMPT_FILE)
    logger.info("Agent prompt loaded successfully.")
else:
    logger.warning("Agent prompt file %s not found. Using default prompt.", AGENT_PROMPT_FILE)




def create_agent(prompt: str = AGENT_PROMPT,
                 model = model,
                 tools = tools):
    """Create and return the agent."""
    logger.info("Creating agent with provided prompt, model, and tools.")

    agent = create_react_agent(
        model = model,
        tools = tools,
        prompt = prompt,
        version="v2",
    )

    logger.info("Agent created successfully.")
    return agent


logger.info("Initializing agent instance.")
agent = create_agent(prompt=agent_system_prompt, model=model, tools=tools)
logger.info("Agent instance initialized and ready.")
