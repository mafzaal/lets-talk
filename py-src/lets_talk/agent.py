import datetime
from typing import Dict, Any, Literal, Union, cast
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage,AIMessage
from langchain_core.prompts import (ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
)
from langgraph.graph import StateGraph, START,END
from langgraph.prebuilt import ToolNode
from pydantic  import BaseModel
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.runnables import RunnableConfig
from langchain_core.documents import Document
from lets_talk.tools import create_tools
import lets_talk.rag as rag
from lets_talk.state import InputState
from lets_talk.utils import format_docs, get_message_text
from lets_talk.config import Configuration


class SearchQuery(BaseModel):
    """Search the indexed documents for a query."""

    query: str


async def generate_query(
    state: InputState, *, config: RunnableConfig
) -> dict[str, list[str]]:
    """Generate a search query based on the current state and configuration.

    This function analyzes the messages in the state and generates an appropriate
    search query. For the first message, it uses the user's input directly.
    For subsequent messages, it uses a language model to generate a refined query.

    Args:
        state (State): The current state containing messages and other information.
        config (RunnableConfig | None, optional): Configuration for the query generation process.

    Returns:
        dict[str, list[str]]: A dictionary with a 'queries' key containing a list of generated queries.

    Behavior:
        - If there's only one message (first user input), it uses that as the query.
        - For subsequent messages, it uses a language model to generate a refined query.
        - The function uses the configuration to set up the prompt and model for query generation.
    """

    
    
    messages = state["messages"]
    if len(messages) == 1:
        # It's the first user question. We will use the input directly to search.
        human_input = get_message_text(messages[-1])
        return {"queries": [human_input]}
    else:
        configuration = Configuration.from_runnable_config(config)
        # Feel free to customize the prompt, model, and other logic!
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(configuration.query_system_prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        model = init_chat_model(configuration.query_model,temperature=0).with_structured_output(
            SearchQuery
        )

        message_value = {
                "messages":messages,
                "queries": "\n- ".join(state.get("queries", []) + [state["question"]]),
                "system_time": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            }
        
        chain = prompt | model

        generated = cast(SearchQuery, await chain.ainvoke(message_value, config))
        return {
            "queries": [generated.query],
        }



async def retrieve(state: InputState, *, config: RunnableConfig) -> dict[str, list[Document]]:

    """Retrieve documents based on the generated query.
    This function uses the generated query to search for relevant documents
    in the indexed data. It uses the RAG retriever to perform the search.
    Args:
        state (State): The current state containing messages and other information.
        config (RunnableConfig | None, optional): Configuration for the retrieval process.
    Returns:
        dict[str, list[Document]]: A dictionary with a 'documents' key containing a list of retrieved documents.
    """

    queries = state.get("queries", None)
    query = queries[-1] if queries else state["question"]
    docs = await rag.retriever.ainvoke(query,config=config)

    return {"documents": docs}


def retrieve_context(query: str) -> str:
    docs =  rag.retriever.invoke(query)
    if not docs:
        return "No relevant documents found."
   
    context = format_docs(docs)
    return  context



async def is_rude_question(state: InputState, *, config:RunnableConfig) -> Dict[str, Union[bool, list[BaseMessage]]]:
    """
    Check if the query is rude or negative.

    Args:
        question: The user's query
    Returns:
        True if the question is rude, False otherwise
    """

    
    question = state.get("question","") 

    if not question:
        # Get the last human message from state
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_message = get_message_text(msg)
                break

    if not question:
        return {"is_rude": False}
    

    # Check the tone of the last message
    configuration = Configuration.from_runnable_config(config)
    prompt = ChatPromptTemplate.from_template(configuration.query_tone_check_prompt)
    llm = init_chat_model(configuration.query_tone_check_model,temperature=0)

    tone_check_chain = prompt | llm | StrOutputParser()

    response = await tone_check_chain.ainvoke({"question": question}, config)
    
    is_rude = False
    if isinstance(response, str):
        is_rude = response.strip().lower() == "yes"
    elif isinstance(response, list):
        # Check first element if it's a list
        is_rude = str(response[0]).strip().lower() == "yes" if response else False
    else:
        # Handle dictionary or other types
        is_rude = str(response).strip().lower() == "yes"

    return {"is_rude": is_rude}


# async def check_question_tone(state: InputState, *, config: RunnableConfig) -> Dict[str, Union[bool, list[BaseMessage]]]:
#     """
#     Check the tone of the user's query and adjust the state accordingly.
    
#     Args:
#         state: Current state containing messages and context
#     Returns:
#         Updated state with tone information and optional messages
#     """


#     last_message = state.get("question","") 

#     if not last_message:
#         # Get the last human message from state
#         for msg in reversed(state["messages"]):
#             if isinstance(msg, HumanMessage):
#                 last_message = get_message_text(msg)
#                 break

#     if not last_message:
#         return {"is_rude": False, "messages": []}
    

#     # Check the tone of the last message
#     is_rude = await is_rude_question(str(last_message), config)

#     return {"is_rude": is_rude}

async def handle_rude_question(question: str, config: RunnableConfig) -> BaseMessage:
        """
        Generate a polite response to a rude question.
        
        Args:
            question: The user's rude question
            config: Configuration for the model
        
        Returns:
            A polite AI message response
        """
        configuration = Configuration.from_runnable_config(config)
        
        prompt = ChatPromptTemplate.from_template(configuration.query_rude_answer_prompt)
        llm = init_chat_model(configuration.query_rude_answer_model, temperature=0.5)

        rude_query_answer_chain = prompt | llm 
        
        return await rude_query_answer_chain.ainvoke({"question": question}, config)



TOOLS = create_tools()



# Update the call_model function to include current datetime
async def call_model(state: Dict[str, Any], * , config:RunnableConfig) -> Dict[str, list[BaseMessage]]:
    """
    Process the current state through the language model.
    
    Args:
        model: Language model with tools bound
        state: Current state containing messages and context
        
    Returns:
        Updated state with model's response added to messages
    """
    try:
        configuration = Configuration.from_runnable_config(config)
        messages = state["messages"]
        
        
        # Insert system message with context before the latest user message
        system_message = SystemMessage(
            content=configuration.react_agent_prompt.format(
                system_time=datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            )
        )

        llm = init_chat_model(configuration.react_agent_model,temperature=0).bind_tools(TOOLS)

        # Find the position of the last user message
        for i in range(len(messages)-1, -1, -1):
            if isinstance(messages[i], HumanMessage):
                # Insert system right after the last user message
                enhanced_messages = messages[:i+1] + [system_message] + messages[i+1:]
                break
        else:
            # No user message found, just append context
            enhanced_messages = messages + [system_message, HumanMessage(content=state["question"])]
        
        # Get response from the model
        response = await llm.ainvoke(enhanced_messages,config)

        return {"messages": [response]}
    except Exception as e:
        # Handle exceptions gracefully
        error_msg = f"Error calling model: {str(e)}"
        print(error_msg)  # Log the error
        # Return a fallback response
        return {"messages": [HumanMessage(content=error_msg)]}


def should_continue(state: Dict[str, Any]) -> Union[Literal["action"], Literal["respond"]]:
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
    
    return "respond"





# def convert_inputs(input_object: Dict[str, str]) -> Dict[str, list[BaseMessage]]:
#     """
#     Convert user input into the format expected by the agent.
    
#     Args:
#         input_object: Dictionary containing the user's question
        
#     Returns:
#         Formatted input state for the agent
#     """
#     return {"messages": [HumanMessage(content=input_object["question"])]}


# def parse_output(input_state: Dict[str, Any]) -> str:
#     """
#     Extract the final response from the agent's state.
    
#     Args:
#         input_state: The final state of the agent
        
#     Returns:
#         The content of the last message
#     """
#     try:
#         return cast(str, input_state["messages"][-1].content)
#     except (IndexError, KeyError, AttributeError) as e:
#         # Handle potential errors when accessing the output
#         error_msg = f"Error parsing output: {str(e)}"
#         print(error_msg)  # Log the error
#         return "I encountered an error while processing your request."


async def respond(
    state: InputState, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """Call the LLM powering our "agent"."""

    if state.get("is_rude", False):
        # Handle rude questions
        rude_response = await handle_rude_question(state["question"], config)
        return {"messages": [rude_response]}
  

    found_tool_call = False
    # If there's a tool call message anywhere in the messages
    for message in state["messages"]:
        if isinstance(message, AIMessage) and getattr(message, "tool_calls", None):
            # Found a tool call message
            found_tool_call = True
            break

    # Check if the last message is an AI message and has tool calls
    if found_tool_call and state["messages"] and isinstance(state["messages"][-1], AIMessage):
        # If the last message is an AI message, return it (could be from a tool call response)
        return {"messages": [state["messages"][-1]]}
        
    

    configuration = Configuration.from_runnable_config(config)
    # Feel free to customize the prompt, model, and other logic!
    prompt = ChatPromptTemplate.from_messages(
        [
            MessagesPlaceholder(variable_name="messages"),
            SystemMessagePromptTemplate.from_template(configuration.response_system_prompt),
            HumanMessagePromptTemplate.from_template("{question}")
            
        ]
    )
    model = init_chat_model(configuration.response_model, temperature=0)

    chain = prompt | model

    documents = state.get("documents", [])
    contenxt = format_docs(documents)

    response = await chain.ainvoke(
        {
            "messages": state["messages"],
            "context": contenxt,
            "question": state["question"],
            "system_time": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
        }, config
        )
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}



def build_graph() -> StateGraph:
       
       
    tool_node = ToolNode(TOOLS)

    # Initialize the graph with our state type
    builder = StateGraph(state_schema=InputState,config_schema=Configuration)
   
    builder.add_node("is_rude_question", is_rude_question)
    #builder.add_node("generate_query", generate_query)
    builder.add_node("retrieve", retrieve)
    builder.add_node("agent", call_model)
    builder.add_node("action", tool_node)
    builder.add_node("respond", respond)
    

    
    # Add an end node - this is required for the "end" state to be valid
    # uncompiled_graph.add_node("end", lambda state: state)

    builder.add_edge(START, "is_rude_question")
    builder.add_edge(START, "retrieve")
    builder.add_edge(START, "agent")

   

    #builder.add_edge("generate_query", "retrieve")
    builder.add_edge("is_rude_question", "respond")
    builder.add_edge("retrieve", "respond")
    builder.add_edge("agent", "respond")
    
    
    # Add conditional edges from agent
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "action": "action",
            "respond": "respond"
        }
    )

    # Complete the loop
    builder.add_edge("action", "agent")
    builder.add_edge("respond", END)
    
    return builder


def create_agent(builder) -> StateGraph:
    """
    Create and return the agent chain.
    """

    # Compile the graph
    graph = builder.compile()

    return graph 

