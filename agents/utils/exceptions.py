
# agents/utils/exceptions.py
"""Custom exceptions for the browser agent."""

class AgentException(Exception):
    """Base exception for agent-related errors."""
    pass

class HumanInterventionRequired(AgentException):
    """Raised when the agent needs human assistance."""
    pass

class BrowserException(AgentException):
    """Raised when browser operations fail."""
    pass

class LLMException(AgentException):
    """Raised when LLM operations fail."""
    pass

class TaskTimeoutException(AgentException):
    """Raised when a task exceeds maximum time or steps."""
    pass