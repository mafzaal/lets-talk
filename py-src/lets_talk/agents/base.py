"""Base agent classes and interfaces."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def ainvoke(
        self, 
        input_data: Union[Dict[str, Any], str, BaseMessage],
        config: Optional[RunnableConfig] = None
    ) -> Any:
        """Asynchronously invoke the agent with input data."""
        pass
    
    @abstractmethod
    def invoke(
        self, 
        input_data: Union[Dict[str, Any], str, BaseMessage],
        config: Optional[RunnableConfig] = None
    ) -> Any:
        """Synchronously invoke the agent with input data."""
        pass


class AgentConfig:
    """Configuration class for agents."""
    
    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.extra_config = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
            **self.extra_config
        }
