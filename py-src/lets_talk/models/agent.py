"""
LangGraph Agent implementation for the Research Agent.
"""
from typing import TypedDict, Annotated, Dict, Any, Literal, Union, cast, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.documents import Document
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from lets_talk.models.research_tools import RAGQueryInput
from lets_talk.config import LLM_MODEL, LLM_TEMPERATURE

class ResearchAgentState(TypedDict):
    """
    State definition for the Research Agent using LangGraph.
    
    Attributes:
        messages: List of messages in the conversation
        context: Additional context information from RAG retrievals
        documents: Optional list of Document objects from uploaded files
    """
    messages: Annotated[list[BaseMessage], add_messages]
    context: str
    documents: Optional[List[Document]]


def call_model(model, state: Dict[str, Any]) -> Dict[str, list[BaseMessage]]:
    """
    Process the current state through the language model.
    
    Args:
        model: Language model with tools bound
        state: Current state containing messages and context
        
    Returns:
        Updated state with model's response added to messages
    """
    try:
        messages = state["messages"]
        context = state.get("context", "")
        
        # Add context from documents if available
        if context:
            # Insert system message with context before the latest user message
            context_message = SystemMessage(content=f"Use the following information from uploaded documents to enhance your response if relevant:\n\n{context}")
            
            # Find the position of the last user message
            for i in range(len(messages)-1, -1, -1):
                if isinstance(messages[i], HumanMessage):
                    # Insert context right after the last user message
                    enhanced_messages = messages[:i+1] + [context_message] + messages[i+1:]
                    break
            else:
                # No user message found, just append context
                enhanced_messages = messages + [context_message]
        else:
            enhanced_messages = messages
        
        # Get response from the model
        response = model.invoke(enhanced_messages)
        return {"messages": [response]}
    except Exception as e:
        # Handle exceptions gracefully
        error_msg = f"Error calling model: {str(e)}"
        print(error_msg)  # Log the error
        # Return a fallback response
        return {"messages": [HumanMessage(content=error_msg)]}


def should_continue(state: Dict[str, Any]) -> Union[Literal["action"], Literal["end"]]:
    """
    Determine if the agent should continue processing or end.
    
    Args:
        state: Current state containing messages and context
        
    Returns:
        "action" if tool calls are present, otherwise "end"
    """
    last_message = state["messages"][-1]
    
    if last_message.tool_calls:
        return "action"
    
    return "end"


def retrieve_from_documents(state: Dict[str, Any], retriever) -> Dict[str, str]:
    """
    Retrieve relevant context from uploaded documents based on the user query.
    
    Args:
        state: Current state containing messages and optional documents
        retriever: Document retriever to use
        
    Returns:
        Updated state with context from document retrieval
    """
    # Get the last user message
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            query = message.content
            break
    else:
        # No user message found
        return {"context": ""}
    
    # Skip if no documents are uploaded
    if not retriever:
        return {"context": ""}
    
    try:
        # Retrieve relevant documents
        docs = retriever.invoke(query)
        if not docs:
            return {"context": ""}
        
        # Extract text from documents
        context = "\n\n".join([f"Document excerpt: {doc.page_content}" for doc in docs])
        return {"context": context}
    except Exception as e:
        print(f"Error retrieving from documents: {str(e)}")
        return {"context": ""}


def document_search_tool(retriever, query: str) -> str:
    """
    Tool function to search within uploaded documents.
    
    Args:
        retriever: Document retriever to use
        query: Search query string
        
    Returns:
        Information retrieved from the documents
    """
    if not retriever:
        return "No documents have been uploaded yet. Please upload a document first."
    
    docs = retriever.invoke(query)
    if not docs:
        return "No relevant information found in the uploaded documents."
    
    # Format the results
    results = []
    for i, doc in enumerate(docs):
        results.append(f"[Document {i+1}] {doc.page_content}")
    
    return "\n\n".join(results)


def convert_inputs(input_object: Dict[str, str]) -> Dict[str, list[BaseMessage]]:
    """
    Convert user input into the format expected by the agent.
    
    Args:
        input_object: Dictionary containing the user's question
        
    Returns:
        Formatted input state for the agent
    """
    return {"messages": [HumanMessage(content=input_object["question"])]}


def parse_output(input_state: Dict[str, Any]) -> str:
    """
    Extract the final response from the agent's state.
    
    Args:
        input_state: The final state of the agent
        
    Returns:
        The content of the last message
    """
    try:
        return cast(str, input_state["messages"][-1].content)
    except (IndexError, KeyError, AttributeError) as e:
        # Handle potential errors when accessing the output
        error_msg = f"Error parsing output: {str(e)}"
        print(error_msg)  # Log the error
        return "I encountered an error while processing your request."


def build_agent_chain(tools, retriever=None):
    """
    Constructs and returns the research agent execution chain.
    
    The chain consists of:
    1. A retrieval node that gets context from documents
    2. An agent node that processes messages
    3. A tool node that executes tools when called
    
    Args:
        tools: List of tools for the agent
        retriever: Optional retriever for document search
        
    Returns:
        Compiled agent chain ready for execution
    """
    # Create an instance of ChatOpenAI
    model = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
    model = model.bind_tools(tools)
    
    # Create document search tool if retriever is provided
    if retriever:
        doc_search_tool = Tool(
            name="DocumentSearch",
            description="Search within the user's uploaded document. Use this tool when you need information from the specific document that was uploaded.",
            func=lambda query: document_search_tool(retriever, query),
            args_schema=RAGQueryInput
        )
        
        # Add document search tool to the tool belt if we have upload capability
        tools = tools.copy()
        tools.append(doc_search_tool)
    
    # Create a node for tool execution
    tool_node = ToolNode(tools)

    # Initialize the graph with our state type
    uncompiled_graph = StateGraph(ResearchAgentState)
    
    # Define model node factory with bound model
    def call_model_node(state):
        return call_model(model, state)

    # Add nodes
    if retriever:
        # Define retrieval node factory with bound retriever
        def retrieve_node(state):
            return retrieve_from_documents(state, retriever)
            
        uncompiled_graph.add_node("retrieve", retrieve_node)
        uncompiled_graph.set_entry_point("retrieve")
        uncompiled_graph.add_edge("retrieve", "agent")
    else:
        uncompiled_graph.set_entry_point("agent")
        
    uncompiled_graph.add_node("agent", call_model_node)
    uncompiled_graph.add_node("action", tool_node)
    
    # Add an end node - this is required for the "end" state to be valid
    uncompiled_graph.add_node("end", lambda state: state)
    
    # Add conditional edges from agent
    uncompiled_graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "action": "action",
            "end": END
        }
    )

    # Complete the loop
    uncompiled_graph.add_edge("action", "agent")
    
    # Compile the graph
    compiled_graph = uncompiled_graph.compile()

    # Create the full chain
    agent_chain = convert_inputs | compiled_graph 
    return agent_chain