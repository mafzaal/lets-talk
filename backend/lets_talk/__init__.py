"""
Let's Talk - A conversational RAG system powered by TheDataGuy's blog content.

This package provides:
- Conversational AI agents for blog content interaction
- RAG (Retrieval-Augmented Generation) capabilities
- Pipeline management for content processing
- API endpoints for web integration
- Scheduler for automated content updates
"""

from lets_talk import agents, api, core, tools, utils, data, shared

__version__ = "0.1.1"
__author__ = "Muhammad Afzaal"
__email__ = "support@thedataguy.pro"

__all__ = [
    "agents",
    "api", 
    "core",
    "tools",
    "utils",
    "data",
    "shared",
]
