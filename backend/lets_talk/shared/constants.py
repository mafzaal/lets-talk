"""Application constants and configuration values."""

# API Response Messages
SUCCESS_MESSAGE = "Operation completed successfully"
ERROR_MESSAGE = "An error occurred while processing your request"
VALIDATION_ERROR_MESSAGE = "Invalid input provided"

# Job Status Values
JOB_STATUS_PENDING = "pending"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_CANCELLED = "cancelled"

# Pipeline Modes
PIPELINE_MODE_AUTO = "auto"
PIPELINE_MODE_MANUAL = "manual"
PIPELINE_MODE_INCREMENTAL = "incremental"
PIPELINE_MODE_FULL = "full"

# Scheduler Types
SCHEDULER_TYPE_BACKGROUND = "background"
SCHEDULER_TYPE_BLOCKING = "blocking"

# Executor Types
EXECUTOR_TYPE_THREAD = "thread"
EXECUTOR_TYPE_PROCESS = "process"

# Agent Types
AGENT_TYPE_RAG = "rag"
AGENT_TYPE_REACT = "react"

# File Extensions
MARKDOWN_EXTENSION = ".md"
JSON_EXTENSION = ".json"
CSV_EXTENSION = ".csv"

# Default Values
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_MAX_RESULTS = 10
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_WORKERS = 4

# Time Formats
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
FILENAME_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# HTTP Status Codes (for reference)
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_SERVICE_UNAVAILABLE = 503

# Validation Patterns
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
URL_PATTERN = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

# Tool Names
TOOL_DATETIME = "datetime_tool"
TOOL_RSS_FEED = "rss_feed_tool"
TOOL_CONTACT = "contact_tool"
TOOL_RETRIEVE_DOCS = "retrieve_documents"
TOOL_RETRIEVE_PAGE = "retrieve_page_by_url"
