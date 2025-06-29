"""RSS Feed tool for external content retrieval."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from langchain.callbacks.manager import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
import feedparser
import logging

from lets_talk.tools.base import BaseTool

logger = logging.getLogger(__name__)


class RSSFeedInput(BaseModel):
    """Input schema for the RSS Feed Tool."""
    query: Optional[str] = Field(
        default="",
        description="Optional query parameter to search for specific content in the RSS feed"
    )


class RSSFeedTool(BaseTool):
    """Tool for fetching recent articles from RSS feeds."""
    
    name: str = "RSSFeedReader"
    description: str = (
        "Fetches recent articles from RSS feeds. Use this tool when you need information "
        "from blog posts, news, or other regularly updated content sources. You can specify "
        "a query to filter results. The tool returns formatted content with titles, links, "
        "and summaries from the configured RSS feed URL with a maximum of 10 results."
    )
    args_schema: type = RSSFeedInput
    rss_url: str = Field(
        default="https://thedataguy.pro/rss.xml", 
        description="The RSS feed URL to fetch articles from"
    )
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
        return self._fetch_rss_feed(
            urls=[self.rss_url], 
            max_results=self.max_results, 
            max_description_length=self.max_description_length, 
            query=query or ""
        )
    
    async def _arun(
        self,
        query: Optional[str] = "",
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Execute the RSS feed tool asynchronously."""
        # For now, just run synchronously
        return self._run(query, None)
    
    def _fetch_rss_feed(
        self,
        urls: List[str],
        max_results: int = 10,
        max_description_length: int = 400,
        query: str = ""
    ) -> str:
        """Fetch and process RSS feed articles."""
        try:
            articles = []
            
            for url in urls:
                logger.info(f"Fetching RSS feed from: {url}")
                
                try:
                    feed = feedparser.parse(url)
                    
                    if feed.bozo:
                        logger.warning(f"RSS feed parsing issues for {url}: {feed.bozo_exception}")
                    
                    # Process feed entries
                    for entry in feed.entries[:max_results]:
                        title = getattr(entry, 'title', 'No title')
                        link = getattr(entry, 'link', 'No link')
                        description = getattr(entry, 'description', '') or getattr(entry, 'summary', '')
                        
                        # Truncate description if too long
                        if len(description) > max_description_length:
                            description = description[:max_description_length] + "..."
                        
                        # Filter by query if provided
                        if query and query.lower() not in (title + " " + description).lower():
                            continue
                        
                        article = {
                            'title': title,
                            'link': link,
                            'description': description,
                            'published': getattr(entry, 'published', 'Unknown date')
                        }
                        articles.append(article)
                
                except Exception as e:
                    logger.error(f"Error processing RSS feed {url}: {e}")
                    continue
            
            if not articles:
                return f"No articles found in RSS feeds{' matching query: ' + query if query else ''}."
            
            # Format articles for output
            formatted_articles = []
            for i, article in enumerate(articles[:max_results], 1):
                formatted_article = (
                    f"{i}. **{article['title']}**\n"
                    f"   Link: {article['link']}\n"
                    f"   Published: {article['published']}\n"
                    f"   Summary: {article['description']}\n"
                )
                formatted_articles.append(formatted_article)
            
            result = f"Found {len(formatted_articles)} articles:\n\n" + "\n".join(formatted_articles)
            logger.info(f"Successfully processed {len(formatted_articles)} articles from RSS feeds")
            
            return result
            
        except Exception as e:
            error_msg = f"Error fetching RSS feed: {e}"
            logger.error(error_msg)
            return error_msg


def create_rss_feed_tool(rss_url: str, max_results: int = 10) -> RSSFeedTool:
    """Factory function to create an RSS feed tool."""
    return RSSFeedTool(
        rss_url=rss_url,
        max_results=max_results
    )
