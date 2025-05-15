"""
Tools package initialization.

This module exposes all tools and the create_search_tools function.
"""

from .rss_feed_tool import RSSFeedTool
from .datetime_tool import  get_current_datetime
from .blog_posts_tool import get_blog_posts_tool

# Import from langchain_community.tools.arxiv.tool if needed
# from langchain_community.tools.arxiv.tool import ArxivQueryRun 


def create_tools():
    """
    Create search tools for the research agent.
    
    Args:
        max_results: Maximum number of results to return
    
    Returns:
        List of search tools for the agent
    """
    # Initialize custom tools using class-based approach
    #rss_feed_tool = RSSFeedTool()  # Uncomment if needed
    #max_results = 10  # Set a default max_results value if needed    
    # Initialize standard search tools (commented out for now)
    #duckduckgo_tool = DuckDuckGoSearchResults(max_results=max_results)
    #arxiv_tool = ArxivQueryRun()
    
    return [
        #rss_feed_tool,  # Commented out as per the current file
        #duckduckgo_tool,
        #arxiv_tool,
        get_current_datetime,
        get_blog_posts_tool
    ]

__all__ = [
    'create_tools',
    "get_current_datetime",
    'RSSFeedTool',
    'get_blog_posts_tool'
]
