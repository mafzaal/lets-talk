import sys
from pathlib import Path
from langchain.schema.runnable.config import RunnableConfig
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from lets_talk.config import (CREATE_VECTOR_DB,VECTOR_STORAGE_PATH)

# Load environment variables from .env file
load_dotenv()

if CREATE_VECTOR_DB:
    import pipeline
    #build vector store
    print("=== create vector db ===")
    # Use configuration from config rather than hardcoded values
    pipeline.create_vector_database()
    print("========================")
else:
    # Check if the vector store exists
    print("=== check vector db ===")
    if not Path(VECTOR_STORAGE_PATH).exists():
        print(f"Vector store not found at {VECTOR_STORAGE_PATH}. Please create it first.")
        sys.exit(1)

import chainlit as cl
from lets_talk.agent import create_agent, build_graph

tdg_agent = create_agent(build_graph())

  
@cl.on_chat_start
async def setup_chain():
    # Check if API key is already set
    # api_key = os.environ.get("OPENAI_API_KEY")
    # if not api_key:
    #     # In a real app, you'd want to handle this more gracefully
    #     response = await cl.AskUserMessage(
    #         content="Please enter your OpenAI API Key:",
    #         timeout=60,
    #         raise_on_timeout=True
    #     ).send()
        
    #     os.environ["OPENAI_API_KEY"] = response

    # Store the chain in user session
    cl.user_session.set("agent", tdg_agent)
    
    # response = tdg_agent.invoke({"question": "Greet the user and provide latest 2 blog posts"})
    # content = parse_output(response)

    # Set a loading message
    welcome_message = "Welcome to Let's Talk! How can I help you today?"
    msg = cl.Message(content=welcome_message, author="System")
    await msg.send()


    

@cl.on_message
async def on_message(message: cl.Message):
    """
    Handler for user messages. Processes the query through the research agent
    and streams the response back to the user.
    
    Args:
        message: The user's message
    """
    agent_executor = cl.user_session.get("agent")
    
    # Check if agent_executor exists
    if not agent_executor:
        await cl.Message(content="Agent not initialized properly. Please refresh the page.").send()
        return
        
    # Create Chainlit message for streaming
    # msg = cl.Message(content="")

    configurable = {"thread_id": cl.context.session.id}
    cb = cl.LangchainCallbackHandler()
    final_answer = cl.Message(content="")

    async for response_msg, metadata in agent_executor.astream({"question": message.content}, stream_mode="messages", config=RunnableConfig(callbacks=[cb], configurable=configurable)):
        if (
            response_msg.content
            and not isinstance(response_msg, HumanMessage)
            and metadata["langgraph_node"] == "agent"
        ):
            await final_answer.stream_token(response_msg.content)

    await final_answer.send()
    
    # Create a parent step for the research process
    # with cl.Step(name="Agent") as step:
    #     # Run the agent executor with callbacks to stream the response
    #     result = await agent_executor.ainvoke(
    #         {"question": message.content},
    #         # config={
    #         #     "callbacks": [cl.AsyncLangchainCallbackHandler()],
    #         #     "configurable": {"session_id": message.id}  # Add session_id from message
    #         # }
    #     )
        
        # Add steps from agent's intermediate steps
        # for i, step_data in enumerate(result.get("intermediate_steps", [])):
        #     step_name = f"Using: {step_data[0].tool}"
        #     step_input = str(step_data[0].tool_input)
        #     step_output = str(step_data[1])
            
        #     # Create individual steps as children of the main step
        #     with cl.Step(name=step_name, type="tool") as substep:
        #         await cl.Message(
        #             content=f"**Input:** {step_input}\n\n**Output:** {step_output}",
        #         ).send()
   
    # Get the final answer
    # final_answer = result["messages"][-1].content
    
    # # Stream tokens from the final_answer
    # await msg.stream_token(final_answer)
    # await msg.send()

  