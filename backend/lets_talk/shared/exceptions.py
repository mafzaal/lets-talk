"""Custom exceptions for the application."""


class LetsNevermindTalkError(Exception):
    """Base exception for the Let's Talk application."""
    pass


class ConfigurationError(LetsNevermindTalkError):
    """Raised when there's a configuration error."""
    pass


class AgentError(LetsNevermindTalkError):
    """Raised when there's an error with agent operations."""
    pass


class PipelineError(LetsNevermindTalkError):
    """Raised when there's an error in the pipeline execution."""
    pass


class SchedulerError(LetsNevermindTalkError):
    """Raised when there's an error with the scheduler."""
    pass


class VectorStoreError(LetsNevermindTalkError):
    """Raised when there's an error with vector store operations."""
    pass


class DocumentProcessingError(LetsNevermindTalkError):
    """Raised when there's an error processing documents."""
    pass


class ToolError(LetsNevermindTalkError):
    """Raised when there's an error with tool execution."""
    pass


class ValidationError(LetsNevermindTalkError):
    """Raised when validation fails."""
    
    def __init__(self, message: str, errors: list | None = None):
        super().__init__(message)
        self.errors = errors or []


class NotFoundError(LetsNevermindTalkError):
    """Raised when a requested resource is not found."""
    pass


class AuthenticationError(LetsNevermindTalkError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(LetsNevermindTalkError):
    """Raised when authorization fails."""
    pass


class ExternalServiceError(LetsNevermindTalkError):
    """Raised when there's an error with external services."""
    
    def __init__(self, message: str, service_name: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.service_name = service_name
        self.status_code = status_code


class RateLimitError(LetsNevermindTalkError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class TimeoutError(LetsNevermindTalkError):
    """Raised when an operation times out."""
    
    def __init__(self, message: str, timeout_duration: float | None = None):
        super().__init__(message)
        self.timeout_duration = timeout_duration


class MaintenanceError(LetsNevermindTalkError):
    """Raised when the system is under maintenance."""
    pass
