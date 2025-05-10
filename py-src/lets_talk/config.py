import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration with defaults
DATA_DIR = os.environ.get("DATA_DIR", "data/")
VECTOR_STORAGE_PATH = os.environ.get("VECTOR_STORAGE_PATH", "./db/vectorstore_v3")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "Snowflake/snowflake-arctic-embed-l")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "thedataguy_documents")
BLOG_BASE_URL = os.environ.get("BLOG_BASE_URL", "https://thedataguy.pro/blog/")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.environ.get("TEMPERATURE", "0"))



SYSTEM_TEMPLATE = """
You are a helpful assistant that answers questions based on the context provided. 
Generate a concise answer to the question in markdown format and include a list of relevant links to the context.
Use links from context to help user to navigate to to find more information. If context is unrelated to question, say "I don't know".
"""