import sys
from pathlib import Path
from langchain.schema.runnable.config import RunnableConfig
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
from lets_talk.config import (CREATE_VECTOR_DB,VECTOR_STORAGE_PATH)
from lets_talk.core.startup import startup_application, log_startup_summary
import logging

# Setup logging for the app
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize application with database migrations
try:
    logger.info("Initializing Chainlit application...")
    startup_info = startup_application(
        app_name="Chainlit Chat Application",
        require_database=True,
        fail_on_migration_error=False
    )
    log_startup_summary(startup_info)
    if not startup_info["success"]:
        logger.warning("Application initialization had issues, but continuing...")
except Exception as e:
    logger.error(f"Failed to initialize application: {e}")
    logger.warning("Continuing with application startup despite initialization errors")



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

# from lets_talk.agent import create_agent, build_graph
#tdg_agent = create_agent(build_graph())
from lets_talk.agent_v2 import agent as tdg_agent


  
@cl.on_chat_start
async def setup_chain():
   
    # Store the chain in user session
    cl.user_session.set("agent", tdg_agent)
    
    # response = tdg_agent.invoke({"question": "Greet the user and provide latest 2 blog posts"})
    # content = parse_output(response)

    # Set a loading message
    welcome_message = "Welcome to TheDataGuy Chat! How can I help you today?"
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

    final_answer = cl.Message(content="")
    print("Session Id:",cl.context.session.id)
    configurable = {"thread_id": cl.context.session.id}
    cb = cl.LangchainCallbackHandler()
    runnable_config= RunnableConfig(callbacks=[cb], configurable=configurable)

    async for response_msg, metadata in agent_executor.astream({"messages": [HumanMessage(content=message.content)]}, stream_mode="messages", config=runnable_config):
        if (
            response_msg.content
            and not isinstance(response_msg, HumanMessage)
            and metadata["langgraph_node"] == "agent"
        ):
            await final_answer.stream_token(response_msg.content)

    await final_answer.send()
    
   
  