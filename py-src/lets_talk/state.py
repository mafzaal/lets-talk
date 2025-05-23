

from typing import Sequence, TypedDict, Annotated,  NotRequired
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langchain_core.documents import Document


def add_queries(existing: Sequence[str], new: Sequence[str]) -> Sequence[str]:
    """Combine existing queries with new queries.

    Args:
        existing (Sequence[str]): The current list of queries in the state.
        new (Sequence[str]): The new queries to be added.

    Returns:
        Sequence[str]: A new list containing all queries from both input sequences.
    """
    return list(existing) + list(new)


class InputState(TypedDict):
    """
    State definition for the Research Agent using LangGraph.
    
    Attributes:
        messages: List of messages in the conversation
        documents: Optional list of Document objects from RAG retrievals
    """
    messages: Annotated[list[BaseMessage], add_messages]
    question: str
    is_rude: NotRequired[bool]
    documents: NotRequired[list[Document]]
    queries: NotRequired[Annotated[list[str], add_queries]]
    