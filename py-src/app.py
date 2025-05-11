import os
import getpass
import sys
from pathlib import Path
from operator import itemgetter
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import chainlit as cl
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain_openai.chat_models import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from lets_talk.config import LLM_MODEL, LLM_TEMPERATURE
import lets_talk.utils.blog as blog
from lets_talk.agent import build_agent,parse_output
import pipeline


#build vector store
pipeline.main()

tdg_agent = build_agent()

  
@cl.on_chat_start
async def setup_chain():
    # Check if API key is already set
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # In a real app, you'd want to handle this more gracefully
        api_key = await cl.AskUserMessage(
            content="Please enter your OpenAI API Key:",
            timeout=60,
            raise_on_timeout=True
        ).send()
        os.environ["OPENAI_API_KEY"] = api_key.content

    # Set a loading message
    msg = cl.Message(content="Let's talk about [TheDataGuy](https://thedataguy.pro)'s blog posts, how can I help you?", author="System")
    await msg.send()
    
    # Store the chain in user session
    cl.user_session.set("agent", tdg_agent)
    
    

    

@cl.on_message
async def on_message(message: cl.Message):
    """
    Handler for user messages. Processes the query through the research agent
    and streams the response back to the user.
    
    Args:
        message: The user's message
    """
    agent_executor = cl.user_session.get("agent")
    
    # Create Chainlit message for streaming
    msg = cl.Message(content="")
    
    # Create a parent step for the research process
    with cl.Step(name="Agent") as step:
        # Run the agent executor with callbacks to stream the response
        result = await agent_executor.ainvoke(
            {"question": message.content},
            # config={
            #     "callbacks": [cl.AsyncLangchainCallbackHandler()],
            #     "configurable": {"session_id": message.id}  # Add session_id from message
            # }
        )
        
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
    final_answer = parse_output(result)
    
    # Stream tokens from the final_answer
    await msg.stream_token(final_answer)
    await msg.send()

  