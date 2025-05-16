"""
RSS Feed tool implementation.
"""

from typing import Optional, Type, ClassVar, List, Any
from pydantic import BaseModel, Field
from langchain.callbacks.manager import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from .base import BaseTool
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from langchain_core.documents import Document
import feedparser


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





def rss_feed_tool(urls: List[str], query: Optional[str] = None, max_results: int = 5, nlp: bool = True) -> str:
    """
    Tool function to fetch and process articles from RSS feeds.
    
    Args:
        urls: List of RSS feed URLs to fetch articles from
        query: Optional query to filter articles by relevance
        max_results: Maximum number of articles to return
        nlp: Whether to use NLP processing on articles
        
    Returns:
        Formatted string with articles from the RSS feeds
    """
    try:
        articles = []
        
        # Process each RSS feed URL
        for url in urls:
            feed = feedparser.parse(url)
            
            if not feed.entries:
                continue
                
            for entry in feed.entries:
                # Create a document-like object similar to what RSSFeedLoader would produce
                content = entry.get('summary', '')
                if 'content' in entry:
                    # Some feeds use 'content' instead of 'summary'
                    content = ''.join(item.get('value', '') for item in entry.content)
                
                # Extract metadata
                title = entry.get('title', 'No title')
                source = feed.feed.get('title', 'Unknown source')
                link = entry.get('link', 'No link')
                published = entry.get('published', 'No publication date')
                
                # Create a simplified document structure
                doc = {
                    'page_content': content,
                    'metadata': {
                        'title': title,
                        'source': source,
                        'link': link,
                        'published': published
                    }
                }
                
                articles.append(doc)
        
        if not articles:
            return "No articles found in the provided RSS feeds."
        
        # Sort articles by relevance if query is provided
        if query:
            # Simple relevance sorting - checking if query terms appear in content
            query_terms = query.lower().split()
            scored_articles = []
            
            for article in articles:
                score = 0
                content = article['page_content'].lower()
                
                # Count occurrences of query terms in content
                for term in query_terms:
                    score += content.count(term)
                
                scored_articles.append((score, article))
            
            # Sort by score in descending order
            scored_articles.sort(reverse=True, key=lambda x: x[0])
            articles = [article for _, article in scored_articles]
        
        # Limit the number of results
        articles = articles[:max_results]
        
        # Format the results
        results = []
        for i, article in enumerate(articles):
            metadata = article['metadata']
            title = metadata.get('title', 'No title')
            source = metadata.get('source', 'Unknown source')
            link = metadata.get('link', 'No link')
            published = metadata.get('published', 'No publication date')
            
            # Format article content
            content = article['page_content'].strip()
            
            # Add metadata about the article
            result = f"### [{i+1}] {title}\n"
            result += f"**Source**: {source}\n"
            result += f"**Link**: {link}\n"
            result += f"**Published**: {published}\n\n"
            
            # Add NLP-processed metadata if available
            if nlp and 'summary' in metadata:
                result += f"**Summary**: {metadata['summary'][:250]}...\n\n"
            
            if nlp and 'keywords' in metadata:
                result += f"**Keywords**: {', '.join(metadata['keywords'][:10])}\n\n"
            
            # Add the article content
            result += f"**Content**:\n{content[:500]}...\n\n"
            
            results.append(result)
        
        return "\n".join(results)
    except Exception as e:
        return f"Error fetching RSS feeds: {str(e)}"


def create_rss_feed_tool() -> Tool:
    """
    Create and return an RSS feed tool.
    
    Returns:
        Tool object for RSS feed functionality
    """
    def _rss_feed_tool_wrapper(*args, **kwargs):
        # Handle both positional and keyword arguments
        if args and not kwargs:
            # If only positional args were provided
            if len(args) >= 1:
                urls = args[0]
            else:
                urls = []
                
            query = args[1] if len(args) >= 2 else None
            max_results = args[2] if len(args) >= 3 else 5
            nlp = args[3] if len(args) >= 4 else True
            
            return rss_feed_tool(urls=urls, query=query, max_results=max_results, nlp=nlp)
        else:
            # If keyword args were provided
            return rss_feed_tool(**kwargs)
            
    return Tool(
        name="RSSFeedReader",
        description="Fetch and read articles from RSS feeds. Use this tool when you need information from specific news sources or blogs that publish RSS feeds.",
        func=_rss_feed_tool_wrapper,
        args_schema=RSSFeedInput
    )


if __name__ == "__main__":
    # Example usage of the RSS feed tool
    urls = ["https://thedataguy.pro/rss.xml","https://news.ycombinator.com/rss"]
    query = "latest research"
    max_results = 5
    nlp = True
    
    result = rss_feed_tool(urls, query, max_results, nlp)
    print(result)