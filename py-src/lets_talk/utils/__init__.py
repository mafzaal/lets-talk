from typing import Optional

from langchain.chat_models import init_chat_model
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage

def load_chat_model(fully_specified_name: str) -> BaseChatModel:
    """Load a chat model from a fully specified name.

    Args:
        fully_specified_name (str): String in the format 'provider/model'.
    """
    if "/" in fully_specified_name:
        provider, model = fully_specified_name.split("/", maxsplit=1)
    else:
        provider = ""
        model = fully_specified_name
    return init_chat_model(model, model_provider=provider)


def get_message_text(msg: BaseMessage) -> str:
    """Get the text content of a message.

    This function extracts the text content from various message formats.

    Args:
        msg (AnyMessage): The message object to extract text from.

    Returns:
        str: The extracted text content of the message.

    Examples:
        >>> from langchain_core.messages import HumanMessage
        >>> get_message_text(HumanMessage(content="Hello"))
        'Hello'
        >>> get_message_text(HumanMessage(content={"text": "World"}))
        'World'
        >>> get_message_text(HumanMessage(content=[{"text": "Hello"}, " ", {"text": "World"}]))
        'Hello World'
    """
    content = msg.content
    if isinstance(content, str):
        return content
    elif isinstance(content, dict):
        return content.get("text", "")
    else:
        txts = [c if isinstance(c, str) else (c.get("text") or "") for c in content]
        return "".join(txts).strip()
    
def _format_doc(doc: Document) -> str:
    """Format a single document as XML.

    Args:
        doc (Document): The document to format.

    Returns:
        str: The formatted document as an XML string.
    """
    metadata = doc.metadata or {}
    meta = "".join(f" {k}={v!r}" for k, v in metadata.items())
    if meta:
        meta = f" {meta}"

    return f"<document{meta}>\n{doc.page_content}\n</document>"


def format_docs(docs: Optional[list[Document]]) -> str:
    """Format a list of documents as XML.

    This function takes a list of Document objects and formats them into a single XML string.

    Args:
        docs (Optional[list[Document]]): A list of Document objects to format, or None.

    Returns:
        str: A string containing the formatted documents in XML format.

    Examples:
        >>> docs = [Document(page_content="Hello"), Document(page_content="World")]
        >>> print(format_docs(docs))
        <documents>
        <document>
        Hello
        </document>
        <document>
        World
        </document>
        </documents>

        >>> print(format_docs(None))
        <documents></documents>
    """
    if not docs:
        return "<documents></documents>"
    formatted = "\n".join(_format_doc(doc) for doc in docs)
    return f"""<documents>
{formatted}
</documents>"""


def format_docs_v2(docs):
    
    """
    Format the documents for display.
    Args:
        docs: List of documents to format
    Returns:
        str: Formatted string representation of the documents

    Format the documents for display in a structured markdown format.
    Each document is formatted with metadata as key-value pairs followed by the document content.
    Documents are separated by horizontal rules for better readability.
        docs: List of documents to format, where each document has metadata and page_content attributes
        str: A formatted string representation of the documents with metadata displayed as key-value pairs,
             followed by the document content, with documents separated by horizontal rules
    Example:
        >>> docs = [Document(page_content="Hello world", metadata={"source": "file.txt", "page": 1})]
        >>> format_docs_v2(docs)
        "**source:** file.txt\n**page:** 1\n\n**content:** Hello world"
    """
    # Render all items from metadata in K:V format
    # and the page content in a single line
    # with a line break between each document
    # and a line break between each metadata item
    # and the page content in a single line
    
    formatted_docs = []
    for doc in docs:
        # Format all metadata as key-value pairs
        metadata_parts = []
        for key, value in doc.metadata.items():
            metadata_parts.append(f"**{key}:** {value}")
        
        # Join metadata items with line breaks
        metadata_str = "\n".join(metadata_parts)
        
        # Add page content with a line break after metadata
        formatted_doc = f"{metadata_str}\n\n**content:** {doc.page_content}"
        formatted_docs.append(formatted_doc)

    # Join all documents with double line breaks for separation
    return "\n\n---\n\n".join(formatted_docs)

__all__ = [
    "load_chat_model",
    "get_message_text",
    "format_docs",
    "format_docs_v2",
]
