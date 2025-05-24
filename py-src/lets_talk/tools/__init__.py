"""
Tools package initialization.

This module exposes all tools and the create_tools function.
"""

from .rss_feed_tool import RSSFeedTool
from .datetime_tool import get_current_datetime
from .blog_posts_tool import get_blog_posts_tool
from .contact_tool import contact_form_tool

# Import from langchain_community.tools.arxiv.tool if needed
# from langchain_community.tools.arxiv.tool import ArxivQueryRun 


def create_tools():
    """
    Create tools for the chat application.
    
    Returns:
        List of tools for the agent
    """
    return [
        #get_current_datetime,
        get_blog_posts_tool,
        contact_form_tool
    ]

__all__ = [
    'create_tools',
    "get_current_datetime",
    'RSSFeedTool',
    'get_blog_posts_tool',
    'contact_form_tool'
]
