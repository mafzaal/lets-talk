"""
RSS Feed tool implementation.
"""

from typing import Optional, Type, ClassVar, List, Any
from pydantic import BaseModel, Field
from langchain.callbacks.manager import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from langchain_core.tools.base import ArgsSchema
from .base import BaseTool
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from langchain_core.documents import Document
import feedparser
import asyncio
import aiohttp


class RSSFeedInput(BaseModel):
    """Input schema for the RSS Feed Tool."""
    query: Optional[str] = Field(
        default="",
        description="Optional query parameter to search for specific content in the RSS feed"
    )


class RSSFeedTool(BaseTool):
    """Tool for fetching recent articles from TheDataGuy's tech blog RSS feed."""
    name: str = "RSSFeedReader"
    description: str = "Fetches recent articles from RSS feeds. Use this tool when you need information from blog posts, news, or other regularly updated content sources. You can specify a query to filter results. The tool returns formatted content with titles, links, and summaries from the configured RSS feed URL with a maximum of 10 results."
    args_schema: Optional[ArgsSchema] = RSSFeedInput
    rss_url: str = Field(default="https://thedataguy.pro/rss.xml", description="The RSS feed URL to fetch articles from")
    max_results: int = Field(
        default=10, 
        description="Maximum number of articles to return from the RSS feed"
    )
    max_description_length: int = Field(
        default=400, 
        description="Maximum length of the article description to include in the output"
    )
    
    
    def _run(
        self, 
        query: Optional[str] = "", 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Execute the RSS feed tool."""
        return rss_feed_tool(urls=[self.rss_url], max_results=10, max_description_length=self.max_description_length, query=query)
    
    async def _arun(
        self, 
        query: Optional[str] = "", 
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Execute the RSS feed tool asynchronously."""
        return await rss_feed_tool_async(urls=[self.rss_url], max_results=10, max_description_length=self.max_description_length, query=query)





async def fetch_rss(session, url):
    async with session.get(url) as response:
        return await response.text()

async def rss_feed_tool_async(
    urls: List[str], 
    query: Optional[str] = None, 
    max_results: int = 10, 
    max_description_length: int = 400
) -> str:
    """
    Async version: Fetch and format articles from RSS feeds for LLM context.
    """
    try:
        articles = []
        async with aiohttp.ClientSession() as session:
            rss_texts = await asyncio.gather(*(fetch_rss(session, url) for url in urls))
            for idx, rss_text in enumerate(rss_texts):
                url = urls[idx]
                feed = feedparser.parse(rss_text)
                channel_title = feed.feed.get('title', 'No Title') if hasattr(feed, 'feed') and not isinstance(feed.feed, list) else 'No Title'
                channel_link = feed.feed.get('link', 'No Link') if hasattr(feed, 'feed') and not isinstance(feed.feed, list) else 'No Link'
                if not feed or 'entries' not in feed or not isinstance(feed.entries, list):
                    continue
                if not feed.get('entries'):
                    continue
                if not feed.entries:
                    continue
                for entry in feed.entries:
                    title = entry.get('title', 'No title')
                    link = entry.get('link', '')
                    published = entry.get('published', '')
                    tags = entry.get('tags', []) or []
                    categories = [tag['term'] for tag in tags if 'term' in tag]
                    if not categories:
                        categories = entry.get('categories', [])
                    description = entry.get('description', '')
                    content = description.strip() if isinstance(description, str) else str(description) if description else ''
                    articles.append({
                        'channel_title': channel_title,
                        'channel_link': channel_link,
                        'title': title,
                        'link': link,
                        'published': published,
                        'categories': categories,
                        'content': content
                    })
        if not articles:
            return "No articles found in the provided RSS feeds."
        articles = articles[:max_results]
        results = []
        for i, article in enumerate(articles, 1):
            summary = (
                f"### [{i}] {article['title']}\n"
                f"**Channel**: [{article['channel_title']}]({article['channel_link']})\n"
                f"**Link**: {article['link']}\n"
                f"**Published**: {article['published']}\n"
            )
            if article['categories']:
                summary += f"**Categories**: {', '.join(article['categories'])}\n"
            summary += f"**Summary**: {article['content'][:max_description_length]}...\n"
            results.append(summary)
        return "\n\n".join(results)
    except Exception as e:
        return f"Error fetching RSS feeds: {str(e)}"

def rss_feed_tool(
    urls: List[str], 
    query: Optional[str] = None, 
    max_results: int = 10, 
    max_description_length: int = 400
) -> str:
    """
    Wrapper to run async RSS fetcher in a thread-safe way.
    """
    return asyncio.run(rss_feed_tool_async(urls, query, max_results, max_description_length))

if __name__ == "__main__":
    # Example usage of the RSS feed tool
    urls = ["https://thedataguy.pro/rss.xml","https://news.ycombinator.com/rss"]
    query = "latest research"
    max_results = 5
    nlp = True
    
    result = rss_feed_tool(urls, query, max_results)
    print(result)