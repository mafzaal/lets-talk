"""
Research tools implementation for the agent.

This module implements input schemas and tools specifically for research purposes.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from langchain_core.tools import Tool
from langchain_core.documents import Document
import feedparser
import datetime

class ArxivQueryInput(BaseModel):
    """Input for arXiv query."""
    query: str = Field(..., description="The search query to find papers on arXiv")
    max_results: int = Field(default=5, description="The maximum number of results to return")

class RAGQueryInput(BaseModel):
    """Input for RAG query."""
    query: str = Field(..., description="The query to search in the uploaded document")

class WebSearchInput(BaseModel):
    """Input for web search."""
    query: str = Field(..., description="The search query for web search")
    max_results: int = Field(default=5, description="The maximum number of results to return")

class DocumentAnalysisInput(BaseModel):
    """Input for document analysis."""
    query: str = Field(..., description="The specific question to analyze in the document")
    include_citations: bool = Field(default=True, description="Whether to include citations in the response")

class RSSFeedInput(BaseModel):
    """Input for RSS feed tool."""
    urls: List[str] = Field(..., description="List of RSS feed URLs to fetch articles from")
    query: Optional[str] = Field(None, description="Optional query to filter articles by relevance")
    max_results: int = Field(default=5, description="Maximum number of articles to return")
    nlp: bool = Field(default=True, description="Whether to use NLP processing on articles (extracts keywords and summaries)")


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
    urls = ["https://news.ycombinator.com/rss","http://fox13now.com/2013/12/30/new-year-new-laws-obamacare-pot-guns-and-drones/"]
    query = "latest research"
    max_results = 5
    nlp = True
    
    result = rss_feed_tool(urls, query, max_results, nlp)
    print(result)