"""
Search tools module containing different search implementations.
"""

from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import Tool

def create_search_tools(max_results=5):
    """
    Create search tools for the research agent.
    
    Args:
        max_results: Maximum number of results to return
    
    Returns:
        List of search tools for the agent
    """
    # Initialize standard search tools
    #tavily_tool = TavilySearchResults(max_results=max_results)
    duckduckgo_tool = DuckDuckGoSearchResults(max_results=max_results)
    arxiv_tool = ArxivQueryRun()
    
    return [
        #tavily_tool,
        duckduckgo_tool,
        arxiv_tool,
    ]