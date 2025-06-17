"""Define the configurable parameters for the agent."""

from __future__ import annotations

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

#OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./stats")

#For embedding storage
VECTOR_STORAGE_PATH = os.environ.get("VECTOR_STORAGE_PATH", f"{OUTPUT_DIR}/vectorstore")
FORCE_RECREATE = os.environ.get("FORCE_RECREATE", "False").lower() == "true"
# For Qdrant vector database
QDRANT_URL = os.environ.get("QDRANT_URL", "")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "lets_talk_documents")


# Document chunking configuration
# Chunking and retrieval strategies
USE_CHUNKING = os.environ.get("USE_CHUNKING", "True").lower() == "true"
CHUNKING_STRATEGY = os.environ.get("CHUNKING_STRATEGY", "semantic") # Options: "semantic", "text_splitter"
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

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "ollama:snowflake-arctic-embed2:latest")

LLM_MODEL = os.environ.get("LLM_MODEL", "openai:gpt-4o-mini")
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.1"))
# SDG and Evaluation LLM models
SDG_LLM_MODLEL = os.environ.get("SDG_LLM_MODEL", "openai:gpt-4.1")
EVAL_LLM_MODEL = os.environ.get("EVAL_LLM_MODEL", "openai:gpt-4.1")

# Models for the agent
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")








from dataclasses import dataclass, field, fields
from typing import Annotated, Any, Literal, Optional, Type, TypeVar
from langchain_core.runnables import RunnableConfig, ensure_config
from lets_talk import prompts


@dataclass(kw_only=True)
class Configuration:
    """The configuration for the agent."""

    response_system_prompt: str = field(
        default=prompts.RESPONSE_SYSTEM_PROMPT,
        metadata={"description": "The system prompt used for generating responses."},
    )

    response_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default=LLM_MODEL,
        metadata={
            "description": "The language model used for generating responses. Should be in the form: provider/model-name."
        },
    )

    query_system_prompt: str = field(
        default=prompts.QUERY_SYSTEM_PROMPT,
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
        default=prompts.TONE_CHECK_PROMPT,
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
        default=prompts.RUDE_QUERY_ANSWER_PROMPT,
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
        default=prompts.REACT_AGENT_PROMPT,
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
        """Create an IndexConfiguration instance from a RunnableConfig object.

        Args:
            cls (Type[T]): The class itself.
            config (Optional[RunnableConfig]): The configuration object to use.

        Returns:
            T: An instance of IndexConfiguration with the specified configuration.
        """
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})


T = TypeVar("T", bound=Configuration)