"""
Search tools module containing different search implementations.
"""

from langchain_community.tools.arxiv.tool import ArxivQueryRun
#from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import Tool
from .rss_tool import rss_feed_tool


def create_search_tools(max_results=5):
    """
    Create search tools for the research agent.
    
    Args:
        max_results: Maximum number of results to return
    
    Returns:
        List of search tools for the agent
    """


    def create_rss_feed_tool() -> Tool:
        """
        Create and return an RSS feed tool.
        
        Returns:
            Tool object for RSS feed functionality
        """
        def _rss_feed_tool_wrapper(*args, **kwargs):
            
            return rss_feed_tool(urls=['https://thedataguy.pro/rss.xml'])
                
        return Tool(
            name="RSSFeedReader",
            description="Fetch and read articles from TheDataGuy's RSS feeds. Use this tool when you need the latest blog posts, what's new or latest updates.",
            func=_rss_feed_tool_wrapper
        )


    # Initialize standard search tools
    #duckduckgo_tool = DuckDuckGoSearchResults(max_results=max_results)
    #arxiv_tool = ArxivQueryRun()
    tdg_rss_tool = create_rss_feed_tool()
    
    return [
        tdg_rss_tool,
        #duckduckgo_tool,
        #arxiv_tool,
    ]