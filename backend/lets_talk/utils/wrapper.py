

import logging
import os
from typing import Any, Optional, Union
from langchain_core.embeddings import Embeddings
from langchain.embeddings import init_embeddings
from langchain_core.runnables import Runnable
from dotenv import load_dotenv

load_dotenv()

# Define the default Ollama base URL
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

logger = logging.getLogger(__name__)

def init_embeddings_wrapper(
    model: str,
    *,
    provider: Optional[str] = None,
    **kwargs: Any,
) -> Union[Embeddings, Runnable[Any, list[float]]]:
    """Initialize an embeddings model from a model name and optional provider.

    **Note:** Must have the integration package corresponding to the model provider
    installed.

    Args:
        model: Name of the model to use. Can be either:
            - A model string like "openai:text-embedding-3-small"
            - Just the model name if provider is specified
        provider: Optional explicit provider name. If not specified,
            will attempt to parse from the model string. Supported providers
            and their required packages:

            {_get_provider_list()}

        **kwargs: Additional model-specific parameters passed to the embedding model.
            These vary by provider, see the provider-specific documentation for details.

    Returns:
        An Embeddings instance that can generate embeddings for text.

    Raises:
        ValueError: If the model provider is not supported or cannot be determined
        ImportError: If the required provider package is not installed

    .. dropdown:: Example Usage
        :open:

        .. code-block:: python

            # Using a model string
            model = init_embeddings("openai:text-embedding-3-small")
            model.embed_query("Hello, world!")

            # Using explicit provider
            model = init_embeddings(
                model="text-embedding-3-small",
                provider="openai"
            )
            model.embed_documents(["Hello, world!", "Goodbye, world!"])

            # With additional parameters
            model = init_embeddings(
                "openai:text-embedding-3-small",
                api_key="sk-..."
            )

    .. versionadded:: 0.3.9
    """

    # if provider is ollama or `model` starts with `ollama:` and kwargs does not contain `base_url`,
    
    if provider == "ollama" or model.startswith("ollama:") and "base_url" not in kwargs:
        # build ollama base_url
        kwargs["base_url"] = OLLAMA_BASE_URL
        # Call the original function
        logger.info(f"Using Ollama base URL: {OLLAMA_BASE_URL}")
        return init_embeddings(model=model, provider=provider, **kwargs) 
    else:
        # Call the original init_embeddings function with the provided parameters
        return init_embeddings(model=model, provider=provider, **kwargs) 


