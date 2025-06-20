"""Configuration settings for the application."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Annotated, Any, Literal, Optional, Type, TypeVar
from langchain_core.runnables import RunnableConfig, ensure_config
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ChunkingStrategy(str, Enum):
    """Enumeration for document chunking strategies."""
    SEMANTIC = "semantic"
    TEXT_SPLITTER = "text_splitter"


# Configuration with defaults
# DATA INPUT
DATA_DIR = os.environ.get("DATA_DIR", "data/")
DATA_DIR_PATTERN = os.environ.get("DATA_DIR_PATTERN", "*.md")
WEB_URLS = (os.environ.get("WEB_URLS", "")).split(",")
BASE_URL = os.environ.get("BASE_URL", "")
BLOG_BASE_URL = os.environ.get("BLOG_BASE_URL", "")
INDEX_ONLY_PUBLISHED_POSTS = os.environ.get("INDEX_ONLY_PUBLISHED_POSTS", "True").lower() == "true"
# For RSS configurations
RSS_URL = os.environ.get("RSS_URL", "")

# For output directory to start data
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "output/")
AGENT_PROMPT_FILE = os.environ.get("AGENT_PROMPT_FILE", f"{OUTPUT_DIR}/agent_prompt.md")
AGENT_PROMPT = os.environ.get("AGENT_PROMPT", "")

#For embedding storage
VECTOR_STORAGE_PATH = os.environ.get("VECTOR_STORAGE_PATH", "")
FORCE_RECREATE = os.environ.get("FORCE_RECREATE", "False").lower() == "true"
# For Qdrant vector database
QDRANT_URL = os.environ.get("QDRANT_URL", "")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "lets_talk_documents")

# Document chunking configuration
# Chunking and retrieval strategies
USE_CHUNKING = os.environ.get("USE_CHUNKING", "True").lower() == "true"
CHUNKING_STRATEGY = ChunkingStrategy(os.environ.get("CHUNKING_STRATEGY", ChunkingStrategy.SEMANTIC.value))
# Chunking parameters for text_splitter strategy
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "200"))
# Retrieval parameters
BM25_RETRIEVAL = os.environ.get("BM25_RETRIEVAL", "True").lower() == "true"
MULTI_QUERY_RETRIEVAL = os.environ.get("MULTI_QUERY_RETRIEVAL", "True").lower() == "true"
PARENT_DOCUMENT_RETRIEVAL = os.environ.get("PARENT_DOCUMENT_RETRIEVAL", "True").lower() == "true"
PARENT_DOCUMENT_CHILD_CHUNK_SIZE = int(os.environ.get("PARENT_DOCUMENT_CHILD_CHUNK_SIZE", "200"))
MAX_SEARCH_RESULTS = int(os.environ.get("MAX_SEARCH_RESULTS", "4"))

# Vector database creation configuration
SHOULD_SAVE_STATS = os.environ.get("SHOULD_SAVE_STATS", "True").lower() == "true"
CREATE_VECTOR_DB = os.environ.get("CREATE_VECTOR_DB", "True").lower() == "true"

# Incremental indexing configuration
METADATA_CSV_FILE = os.environ.get("METADATA_CSV_FILE", "blog_metadata.csv")
INCREMENTAL_MODE = os.environ.get("INCREMENTAL_MODE", "auto")  # Options: "auto", "incremental", "full"
CHECKSUM_ALGORITHM = os.environ.get("CHECKSUM_ALGORITHM", "sha256")  # Options: "sha256", "md5"
AUTO_DETECT_CHANGES = os.environ.get("AUTO_DETECT_CHANGES", "True").lower() == "true"

# Performance optimization configuration
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "50"))  # Number of documents to process per batch
ENABLE_BATCH_PROCESSING = os.environ.get("ENABLE_BATCH_PROCESSING", "True").lower() == "true"
ENABLE_PERFORMANCE_MONITORING = os.environ.get("ENABLE_PERFORMANCE_MONITORING", "True").lower() == "true"
ADAPTIVE_CHUNKING = os.environ.get("ADAPTIVE_CHUNKING", "True").lower() == "true"
MAX_BACKUP_FILES = int(os.environ.get("MAX_BACKUP_FILES", "3"))  # Number of backup files to keep
BATCH_PAUSE_SECONDS = float(os.environ.get("BATCH_PAUSE_SECONDS", "0.1"))  # Pause between batches
MAX_CONCURRENT_OPERATIONS = int(os.environ.get("MAX_CONCURRENT_OPERATIONS", "5"))  # Max concurrent operations

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "ollama:snowflake-arctic-embed2:latest")

LLM_MODEL = os.environ.get("LLM_MODEL", "openai:gpt-4o-mini")
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.1"))
# SDG and Evaluation LLM models
SDG_LLM_MODLEL = os.environ.get("SDG_LLM_MODEL", "openai:gpt-4.1")
EVAL_LLM_MODEL = os.environ.get("EVAL_LLM_MODEL", "openai:gpt-4.1")



# Pipeline-specific configurations
# Output directory for statistics and artifacts
STATS_OUTPUT_DIR = os.environ.get("STATS_OUTPUT_DIR", f"{OUTPUT_DIR}/stats")

# Incremental indexing threshold configuration
INCREMENTAL_FALLBACK_THRESHOLD = float(os.environ.get("INCREMENTAL_FALLBACK_THRESHOLD", "0.8"))

# Output filenames configuration
BLOG_STATS_FILENAME = os.environ.get("BLOG_STATS_FILENAME", "blog_stats_latest.json")
BLOG_DOCS_FILENAME = os.environ.get("BLOG_DOCS_FILENAME", "blog_docs.csv")
HEALTH_REPORT_FILENAME = os.environ.get("HEALTH_REPORT_FILENAME", "health_report.json")
CI_SUMMARY_FILENAME = os.environ.get("CI_SUMMARY_FILENAME", "ci_summary.json")
BUILD_INFO_FILENAME = os.environ.get("BUILD_INFO_FILENAME", "vector_store_build_info.json")

# Default values configuration
DEFAULT_INDEXED_TIMESTAMP = float(os.environ.get("DEFAULT_INDEXED_TIMESTAMP", "0.0"))

# Logging configuration
LOG_FORMAT = os.environ.get("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOGGER_NAME = os.environ.get("LOGGER_NAME", "lets_talk")

# Default metadata CSV filename (used when building path)
DEFAULT_METADATA_CSV_FILENAME = os.environ.get("DEFAULT_METADATA_CSV_FILENAME", "blog_metadata.csv")


T = TypeVar("T", bound="Configuration")


@dataclass(kw_only=True)
class Configuration:
    """The configuration for the agent."""

    response_system_prompt: str = field(
        default="",  # Will be set from prompts module
        metadata={"description": "The system prompt used for generating responses."},
    )

    response_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default=LLM_MODEL,
        metadata={
            "description": "The language model used for generating responses. Should be in the form: provider/model-name."
        },
    )

    query_system_prompt: str = field(
        default="",  # Will be set from prompts module
        metadata={
            "description": "The system prompt used for processing and refining queries."
        },
    )

    query_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default=LLM_MODEL,
        metadata={
            "description": "The language model used for processing and refining queries. Should be in the form: provider/model-name."
        },
    )

    query_tone_check_prompt: str = field(
        default="",  # Will be set from prompts module
        metadata={
            "description": "The system prompt used for checking the tone of queries."
        },
    )

    query_tone_check_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default=LLM_MODEL,
        metadata={
            "description": "The language model used for checking the tone of queries. Should be in the form: provider/model-name."
        },
    )

    query_rude_answer_prompt: str = field(
        default="",  # Will be set from prompts module
        metadata={
            "description": "The system prompt used for answering rude or derogatory queries."
        },
    )

    query_rude_answer_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default=LLM_MODEL,
        metadata={
            "description": "The language model used for answering rude or derogatory queries. Should be in the form: provider/model-name."
        },
    )

    react_agent_prompt: str = field(
        default="",  # Will be set from prompts module
        metadata={
            "description": "The system prompt used for the React agent."
        },
    )
    
    react_agent_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default=LLM_MODEL,
        metadata={
            "description": "The language model used for the React agent. Should be in the form: provider/model-name."
        },
    )

    @classmethod
    def from_runnable_config(
        cls: Type[T], config: Optional[RunnableConfig] = None
    ) -> T:
        """Create a Configuration instance from a RunnableConfig object.

        Args:
            cls (Type[T]): The class itself.
            config (Optional[RunnableConfig]): The configuration object to use.

        Returns:
            T: An instance of Configuration with the specified configuration.
        """
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})


def load_configuration_with_prompts() -> Configuration:
    """Load configuration with prompt templates."""
    from lets_talk.shared.prompts.templates import (
        RESPONSE_SYSTEM_PROMPT,
        QUERY_SYSTEM_PROMPT,
        TONE_CHECK_PROMPT,
        RUDE_QUERY_ANSWER_PROMPT,
        REACT_AGENT_PROMPT,
    )
    
    return Configuration(
        response_system_prompt=RESPONSE_SYSTEM_PROMPT,
        query_system_prompt=QUERY_SYSTEM_PROMPT,
        query_tone_check_prompt=TONE_CHECK_PROMPT,
        query_rude_answer_prompt=RUDE_QUERY_ANSWER_PROMPT,
        react_agent_prompt=REACT_AGENT_PROMPT,
    )
