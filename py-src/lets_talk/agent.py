from operator import itemgetter
from typing import TypedDict, Annotated, Dict, Any, Literal, Union, cast, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage,AIMessage
from langchain_core.documents import Document
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import ToolNode
from lets_talk.models import RAGQueryInput
from lets_talk.config import LLM_MODEL, LLM_TEMPERATURE
from lets_talk.tools import create_search_tools
from datetime import datetime
import lets_talk.rag as rag


class InputState(TypedDict):
    """
    State definition for the Research Agent using LangGraph.
    
    Attributes:
        messages: List of messages in the conversation
        context: Additional context information from RAG retrievals
        documents: Optional list of Document objects from uploaded files
    """
    messages: Annotated[list[BaseMessage], add_messages]
    context: str
    question: str
    is_rude: bool = False
    documents: Optional[list[Document]]
    



# Update the call_model function to include current datetime
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
        
        # Insert system message with context before the latest user message
        from lets_talk.prompts import rag_prompt_template
        sys_prompt = rag_prompt_template.format(
            context=context,
            question=messages[-1].content,
        )
        
        context_message = SystemMessage(content=sys_prompt)

        # Find the position of the last user message
        for i in range(len(messages)-1, -1, -1):
            if isinstance(messages[i], HumanMessage):
                # Insert context right after the last user message
                enhanced_messages = messages[:i+1] + [context_message] + messages[i+1:]
                break
        else:
            # No user message found, just append context
            enhanced_messages = messages + [context_message]
        
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


def retrieve_from_blog(state: Dict[str, Any]) -> Dict[str, str]:
  
    # Get the last user message
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            query = message.content
            break
    else:
        # No user message found
        query = state["question"]
    
    try:
        context = blog_search_tool(query)
        #response = rag.rag_chain.invoke({"question": query})
        #context = response["response"].content

        return {"context": context}
    except Exception as e:
        print(f"Error retrieving from documents: {str(e)}")
        return {"context": ""}


def blog_search_tool(query: str) -> str:
    docs =  rag.retriever.invoke(query)
    if not docs:
        return "No relevant documents found."
    
    context = "\n\n---".join([ f"link: {doc.metadata["url"] }\n\n{doc.page_content}" for doc in docs])
    return  context



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



def check_question_tone(state: Dict[str, Any]) -> Dict[str, str]:
    """
    Check the tone of the user's query and adjust the state accordingly.
    
    Args:
        state: Current state containing messages and context
    Returns:
        Updated state with tone information
    """
    last_message = state["messages"][-1]
    
    if isinstance(last_message, HumanMessage):
        # Check the tone of the last message
        state["is_rude"] = is_rude_question(last_message.content)

        if state["is_rude"]:
            # If the question is rude, respond with a positive message
            from lets_talk.chains import rude_query_answer_chain
            response = rude_query_answer_chain.invoke({"question": last_message.content})
            state["messages"].append(response)
       
    return state


def is_rude_question(question: str) -> bool:
    """
    Check if the query is rude or negative.

    Args:
        question: The user's query
    Returns:
        True if the question is rude, False otherwise
    """
    from lets_talk.chains import tone_check_chain

    response = tone_check_chain.invoke({"question": question})
    return response.content.strip().lower() == "yes"



def build_graph() -> StateGraph:
       
    tools = create_search_tools(5)

    # Create an instance of ChatOpenAI
    from lets_talk.chains import chat_llm
    model = chat_llm
    model = model.bind_tools(tools)
    
    # Create document search tool if retriever is provided
    
    # doc_search_tool = Tool(
    #     name="TheDataGuy Blog Search",
    #     description="Search within blog posts of thedataguy.pro. ALWAYS use this tool to retrieve the context.",
    #     func=lambda query: blog_search_tool(query),
    #     args_schema=RAGQueryInput
    # )
    
    # Add document search tool to the tool belt if we have upload capability
    # tools = tools.copy()
    # tools.append(doc_search_tool)
    
    # Create a node for tool execution
    tool_node = ToolNode(tools)

    # Initialize the graph with our state type
    uncompiled_graph = StateGraph(InputState)
    
    # Define model node factory with bound model
    def call_model_node(state):
        return call_model(model, state)

    
    # Define retrieval node factory with bound retriever
    def retrieve_node(state):
        return retrieve_from_blog(state)
    



    uncompiled_graph.add_node("check_question_tone", check_question_tone)
    uncompiled_graph.set_entry_point("check_question_tone")
    uncompiled_graph.add_node("retrieve", retrieve_node)
    #uncompiled_graph.set_entry_point("retrieve")
    uncompiled_graph.add_node("agent", call_model_node)

    
    uncompiled_graph.add_conditional_edges(
        "check_question_tone",
        lambda state: "end" if state["is_rude"] else "retrieve",
        {
            "retrieve": "retrieve",
            "end": END
        }
    )

   
    uncompiled_graph.add_edge("retrieve", "agent")
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
    
    return uncompiled_graph


def create_agent_chain(uncompiled_graph) -> StateGraph:
    """
    Create and return the agent chain.
    """

    # Compile the graph
    compiled_graph = uncompiled_graph.compile()

    # Create the full chain
    agent_chain = convert_inputs | compiled_graph 
    return agent_chain


def build_agent():
    """
    Build the agent with the defined graph and return it.
    """
    uncompiled_graph = build_graph()
    agent_chain = create_agent_chain(uncompiled_graph)
    
    return agent_chain