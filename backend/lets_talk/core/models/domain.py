"""Domain models for the application."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


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


class ContactInput(BaseModel):
    """Input for Contact form."""
    name: str = Field(..., description="Name of the person contacting")
    email: str = Field(..., description="Email address of the person contacting")
    subject: str = Field(..., description="Subject of the contact message")
    message: str = Field(..., description="The message body")


class PipelineJobConfig(BaseModel):
    """Configuration for pipeline jobs."""
    job_id: str = Field(..., description="Unique identifier for the job")
    data_dir: Optional[str] = None
    output_dir: Optional[str] = None
    storage_path: Optional[str] = None
    force_recreate: bool = False
    ci_mode: bool = True
    use_chunking: bool = True
    should_save_stats: bool = True
    chunk_size: int = 1000
    chunk_overlap: int = 200
    collection_name: Optional[str] = None
    embedding_model: Optional[str] = None
    data_dir_pattern: str = "*.md"
    blog_base_url: Optional[str] = None
    base_url: Optional[str] = None
    incremental_mode: str = "auto"
    dry_run: bool = False


class JobExecutionResult(BaseModel):
    """Result of a job execution."""
    job_id: str
    status: str  # "success", "failed", "running"
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    artifacts: Optional[List[str]] = None


class SchedulerJobInfo(BaseModel):
    """Information about a scheduled job."""
    id: str
    name: str
    trigger_type: str
    next_run_time: Optional[datetime] = None
    last_run_time: Optional[datetime] = None
    config: Dict[str, Any]
    is_active: bool = True
