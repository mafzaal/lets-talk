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
MAX_SEARCH_RESULTS = int(os.environ.get("MAX_SEARCH_RESULTS", "5"))



