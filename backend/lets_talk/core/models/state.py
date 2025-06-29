"""State definitions for agents and workflows."""

from typing import Sequence, TypedDict, Annotated, NotRequired
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langchain_core.documents import Document
from langgraph.graph import MessagesState


def add_queries(existing: Sequence[str], new: Sequence[str]) -> Sequence[str]:
    """Combine existing queries with new queries.

    Args:
        existing (Sequence[str]): The current list of queries in the state.
        new (Sequence[str]): The new queries to be added.

    Returns:
        Sequence[str]: A new list containing all queries from both input sequences.
    """
    return list(existing) + list(new)


class InputState(MessagesState):
    """
    State definition for the Research Agent using LangGraph.
    
    Attributes:
        messages: List of messages in the conversation
        documents: Optional list of Document objects from RAG retrievals
        queries: User queries for document retrieval
        is_rude: Flag indicating if the conversation contains rude content
    """
    
    is_rude: NotRequired[bool]
    
    # Retrieved documents
    documents: NotRequired[list[Document]]
    
    # User messages/queries
    queries: NotRequired[Annotated[list[str], add_queries]]
