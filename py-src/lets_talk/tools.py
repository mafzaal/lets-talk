"""
Search tools module containing different search implementations.
"""

from langchain_community.tools.arxiv.tool import ArxivQueryRun
#from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import Tool
from .rss_tool import rss_feed_tool
import datetime


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
            
            return rss_feed_tool(urls=['https://thedataguy.pro/rss.xml'], max_results=10)
                
        return Tool(
            name="RSSFeedReader",
            description="Fetches recent articles from TheDataGuy's tech blog. Use this tool when you need information about data engineering, analytics, or when asked about recent tech trends, tutorials or best practices from TheDataGuy blog. The tool returns content from https://thedataguy.pro/rss.xml with a maximum of 10 results.",
            func=_rss_feed_tool_wrapper
        )


    def create_datetime_tool() -> Tool:
        """
        Create and return a date-time tool.
        
        Returns:
            Tool object for providing current date and time
        """
        def _datetime_tool_wrapper(*args, **kwargs):
            now = datetime.datetime.now()
            formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
            weekday = now.strftime("%A")
            
            result = {
                "current_datetime": formatted_datetime,
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "year": now.year,
                "month": now.month,
                "month_name": now.strftime("%B"),
                "day": now.day,
                "weekday": weekday,
                "hour": now.hour,
                "minute": now.minute,
                "second": now.second,
                "timezone": str(datetime.datetime.now().astimezone().tzinfo)
            }
            
            return f"Current date and time information: {result}"
                
        return Tool(
            name="CurrentDateTime",
            description="Provides the current date and time information. Use this tool when you need to know the current date, time, day of week, or other temporal information.",
            func=_datetime_tool_wrapper
        )


    # Initialize standard search tools
    #duckduckgo_tool = DuckDuckGoSearchResults(max_results=max_results)
    #arxiv_tool = ArxivQueryRun()
    tdg_rss_tool = create_rss_feed_tool()
    datetime_tool = create_datetime_tool()
    
    return [
        tdg_rss_tool,
        #duckduckgo_tool,
        #arxiv_tool,
        datetime_tool
    ]