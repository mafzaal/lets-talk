"""Agent factory for creating different types of agents."""
from typing import Optional, Union, Dict, Any
from enum import Enum

from lets_talk.agents.base import BaseAgent, AgentConfig
from lets_talk.agents.rag_agent import RAGAgent
from lets_talk.agents.react_agent import ReactAgent


class AgentType(Enum):
    """Supported agent types."""
    RAG = "rag"
    REACT = "react"


class AgentFactory:
    """Factory class for creating different types of agents."""
    
    @staticmethod
    def create_agent(
        agent_type: Union[AgentType, str],
        config: Optional[AgentConfig] = None,
        **kwargs
    ) -> BaseAgent:
        """Create an agent of the specified type.
        
        Args:
            agent_type: The type of agent to create
            config: Optional configuration for the agent
            **kwargs: Additional arguments to pass to the agent
            
        Returns:
            BaseAgent: The created agent instance
            
        Raises:
            ValueError: If the agent type is not supported
        """
        if isinstance(agent_type, str):
            try:
                agent_type = AgentType(agent_type.lower())
            except ValueError:
                raise ValueError(f"Unsupported agent type: {agent_type}")
        
        if agent_type == AgentType.RAG:
            return RAGAgent(config=config, **kwargs)
        elif agent_type == AgentType.REACT:
            return ReactAgent(config=config, **kwargs)
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")
    
    @staticmethod
    def get_available_agent_types() -> list[str]:
        """Get a list of available agent types.
        
        Returns:
            list[str]: List of available agent type names
        """
        return [agent_type.value for agent_type in AgentType]


# Convenience functions
def create_rag_agent(config: Optional[AgentConfig] = None, **kwargs) -> RAGAgent:
    """Create a RAG agent."""
    return AgentFactory.create_agent(AgentType.RAG, config=config, **kwargs)


def create_react_agent(config: Optional[AgentConfig] = None, **kwargs) -> ReactAgent:
    """Create a ReAct agent."""
    return AgentFactory.create_agent(AgentType.REACT, config=config, **kwargs)


def get_default_agent() -> BaseAgent:
    """Get the default agent (ReAct agent)."""
    return ReactAgent()
