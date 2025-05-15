"""
RSS Feed tool implementation.
"""

from typing import Optional, Type, ClassVar, List, Any
from pydantic import BaseModel, Field
from langchain.callbacks.manager import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from .rss_tool import rss_feed_tool
from .base import BaseTool


class RSSFeedInput(BaseModel):
    """Input schema for the RSS Feed Tool."""
    query: Optional[str] = Field(
        default="",
        description="Optional query parameter to search for specific content in the RSS feed"
    )


class RSSFeedTool(BaseTool):
    """Tool for fetching recent articles from TheDataGuy's tech blog RSS feed."""
    name: ClassVar[str] = "RSSFeedReader"
    description: ClassVar[str] = "Fetches recent articles from TheDataGuy's tech blog. Use this tool when you need information about data engineering, analytics, or when asked about recent tech trends, tutorials or best practices from TheDataGuy blog. The tool returns content from https://thedataguy.pro/rss.xml with a maximum of 10 results."
    args_schema: ClassVar[Type[BaseModel]] = RSSFeedInput
    
    def _run(
        self, 
        query: Optional[str] = "", 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Execute the RSS feed tool."""
        return rss_feed_tool(urls=['https://thedataguy.pro/rss.xml'], max_results=10)
    
    async def _arun(
        self, 
        query: Optional[str] = "", 
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Execute the RSS feed tool asynchronously."""
        raise NotImplementedError("RSSFeedReader does not support async")
