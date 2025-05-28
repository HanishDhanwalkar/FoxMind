# agents/__init__.py
"""LLM Browser Agent Package"""

from .browser_agent import BrowserAgent
from .llm.ollama_client import OllamaClient
from .browser.selenium_controller import SeleniumController

__version__ = "0.1.0"
__all__ = ["BrowserAgent", "OllamaClient", "SeleniumController"]
