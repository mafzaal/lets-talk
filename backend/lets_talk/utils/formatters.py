"""Document and message formatting utilities."""
from typing import List, Optional, Union
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage


def format_docs(docs: List[Document]) -> str:
    """Format a list of documents into a readable string.
    
    Args:
        docs: List of Document objects to format
        
    Returns:
        Formatted string containing document content
    """
    if not docs:
        return "No documents found."
    
    formatted_docs = []
    for i, doc in enumerate(docs, 1):
        # Get document content
        content = doc.page_content.strip()
        
        # Get metadata
        source = doc.metadata.get("source", "Unknown source")
        url = doc.metadata.get("url", "")
        
        # Format document
        doc_str = f"Document {i}:\n"
        if url:
            doc_str += f"URL: {url}\n"
        else:
            doc_str += f"Source: {source}\n"
        doc_str += f"Content: {content}\n"
        
        formatted_docs.append(doc_str)
    
    return "\n" + "="*50 + "\n".join(formatted_docs)


def get_message_text(msg: BaseMessage) -> str:
    """Get the text content of a message.

    This function extracts the text content from various message formats.

    Args:
        msg: The message object to extract text from.

    Returns:
        The extracted text content of the message.

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


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """Truncate text to a maximum length with optional suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length of the truncated text
        suffix: Suffix to add if text is truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_list_items(items: List[str], numbered: bool = False) -> str:
    """Format a list of items into a readable string.
    
    Args:
        items: List of items to format
        numbered: Whether to use numbered list (1., 2., etc.) or bullets (-)
        
    Returns:
        Formatted string
    """
    if not items:
        return ""
    
    formatted_items = []
    for i, item in enumerate(items, 1):
        if numbered:
            formatted_items.append(f"{i}. {item}")
        else:
            formatted_items.append(f"- {item}")
    
    return "\n".join(formatted_items)


def clean_whitespace(text: str) -> str:
    """Clean up excessive whitespace in text.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text with normalized whitespace
    """
    import re
    
    # Replace multiple whitespace characters with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def format_metadata(metadata: dict) -> str:
    """Format document metadata into a readable string.
    
    Args:
        metadata: Dictionary of metadata to format
        
    Returns:
        Formatted metadata string
    """
    if not metadata:
        return "No metadata available."
    
    formatted_items = []
    for key, value in metadata.items():
        if value:  # Only include non-empty values
            formatted_items.append(f"{key.replace('_', ' ').title()}: {value}")
    
    return "\n".join(formatted_items)


def extract_urls_from_text(text: str) -> List[str]:
    """Extract URLs from text using regex.
    
    Args:
        text: Text to extract URLs from
        
    Returns:
        List of URLs found in the text
    """
    import re
    
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    
    return urls


def highlight_text(text: str, query: str, highlight_char: str = "**") -> str:
    """Highlight query terms in text.
    
    Args:
        text: Text to highlight
        query: Query terms to highlight
        highlight_char: Character(s) to use for highlighting
        
    Returns:
        Text with highlighted query terms
    """
    if not query:
        return text
    
    import re
    
    # Simple case-insensitive highlighting
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    highlighted = pattern.sub(f"{highlight_char}\\g<0>{highlight_char}", text)
    
    return highlighted
