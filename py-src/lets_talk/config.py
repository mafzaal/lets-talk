
"""Define the configurable parameters for the agent."""

from __future__ import annotations

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration with defaults
DATA_DIR = os.environ.get("DATA_DIR", "data/")
VECTOR_STORAGE_PATH = os.environ.get("VECTOR_STORAGE_PATH", "./db/vectorstore")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "Snowflake/snowflake-arctic-embed-l")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "thedataguy_documents")
BASE_URL = os.environ.get("BASE_URL", "https://thedataguy.pro/")
BLOG_BASE_URL = os.environ.get("BLOG_BASE_URL", "https://thedataguy.pro/blog/")
RSS_URL = os.environ.get("RSS_URL", "https://thedataguy.pro/rss.xml")
LLM_MODEL = os.environ.get("LLM_MODEL", "openai:gpt-4o-mini")
LLM_TEMPERATURE = float(os.environ.get("TEMPERATURE", "0"))
SDG_LLM_MODLEL = os.environ.get("SDG_LLM_MODEL", "gpt-4.1")
EVAL_LLM_MODEL = os.environ.get("EVAL_LLM_MODEL", "gpt-4.1")
MAX_SEARCH_RESULTS = int(os.environ.get("MAX_SEARCH_RESULTS", "5"))

# Document chunking configuration
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "200"))

# Vector database creation configuration
FORCE_RECREATE = os.environ.get("FORCE_RECREATE", "False").lower() == "true"
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./stats")
USE_CHUNKING = os.environ.get("USE_CHUNKING", "True").lower() == "true"
SHOULD_SAVE_STATS = os.environ.get("SHOULD_SAVE_STATS", "True").lower() == "true"
CREATE_VECTOR_DB = os.environ.get("CREATE_VECTOR_DB", "True").lower() == "true"


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