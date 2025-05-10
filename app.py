import os
import getpass
import sys
from pathlib import Path
from operator import itemgetter
from config import LLM_MODEL, LLM_TEMPERATURE
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
import blog_utils
    
# Load vector store using the utility function
vector_store = blog_utils.load_vector_store()

# Create a retriever
retriever = vector_store.as_retriever()

# Set up ChatOpenAI with environment variables

llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

# Create RAG prompt template
rag_prompt_template = """\
You are a helpful assistant that answers questions based on the context provided. 
Generate a concise answer to the question in markdown format and include a list of relevant links to the context.
Use links from context to help user to navigate to to find more information.
You have access to the following information:

Context:
{context}

Question:
{question}

If context is unrelated to question, say "I don't know".
"""

rag_prompt = ChatPromptTemplate.from_template(rag_prompt_template)

# Create chain
retrieval_augmented_qa_chain = (
    {"context": itemgetter("question") | retriever, "question": itemgetter("question")}
    | RunnablePassthrough.assign(context=itemgetter("context"))
    | {"response": rag_prompt | llm, "context": itemgetter("context")}
)


  
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
    cl.user_session.set("chain", retrieval_augmented_qa_chain)

    

@cl.on_message
async def on_message(message: cl.Message):
    # Get chain from user session
    chain = cl.user_session.get("chain")
    
    print(message.content)
    # Call the chain with the user message
    response = chain.invoke({"question": message.content})
    
    # Get the sources to display them
    # sources = []
    # for doc in response["context"]:
    #     if "url" in doc.metadata:
    #         # Get title from post_title metadata if available, otherwise derive from URL
    #         title = doc.metadata.get("post_title", "")
    #         if not title:
    #             title = doc.metadata["url"].split("/")[-2].replace("-", " ").title()
                
    #         sources.append(
    #             cl.Source(
    #                 url=doc.metadata["url"],
    #                 title=title
    #             )
    #         )

    # Send the response with sources
    await cl.Message(
        content=response["response"].content,
        #sources=sources
    ).send()

