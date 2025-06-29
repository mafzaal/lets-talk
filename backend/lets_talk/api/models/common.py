"""Common API models shared across endpoints."""
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class ChunkingStrategy(str, Enum):
    """Enumeration for document chunking strategies."""
    SEMANTIC = "semantic"
    TEXT_SPLITTER = "text_splitter"


class JobConfig(BaseModel):
    """Configuration for pipeline jobs."""
    data_dir: Optional[str] = None
    storage_path: Optional[str] = None
    force_recreate: bool = False
    ci_mode: bool = True
    use_chunking: bool = True
    should_save_stats: bool = True
    chunk_size: int = 1000
    chunk_overlap: int = 200
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC
    collection_name: Optional[str] = None
    embedding_model: Optional[str] = None
    data_dir_pattern: str = "*.md"
    blog_base_url: Optional[str] = None
    base_url: Optional[str] = None
    incremental_mode: str = "auto"
    dry_run: bool = False


class JobResponse(BaseModel):
    """Response model for job information."""
    id: str
    name: str
    next_run_time: Optional[str]
    trigger: str


class BaseResponse(BaseModel):
    """Base response model with common fields."""
    message: str
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now()
        super().__init__(**data)
