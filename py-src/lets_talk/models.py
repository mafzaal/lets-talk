from pydantic import BaseModel, Field
from typing import List, Optional

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

