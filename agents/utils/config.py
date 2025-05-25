

# agents/utils/config.py
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class OllamaConfig:
    base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "60"))

@dataclass
class BrowserConfig:
    headless: bool = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
    window_width: int = int(os.getenv("BROWSER_WINDOW_WIDTH", "1920"))
    window_height: int = int(os.getenv("BROWSER_WINDOW_HEIGHT", "1080"))
    screenshots_dir: str = os.getenv("SCREENSHOTS_DIR", "screenshots")
    implicit_wait: int = int(os.getenv("BROWSER_IMPLICIT_WAIT", "10"))
    page_load_timeout: int = int(os.getenv("BROWSER_PAGE_LOAD_TIMEOUT", "30"))

@dataclass
class AgentConfig:
    max_steps: int = int(os.getenv("AGENT_MAX_STEPS", "50"))
    max_errors: int = int(os.getenv("AGENT_MAX_ERRORS", "3"))
    screenshot_on_error: bool = os.getenv("AGENT_SCREENSHOT_ON_ERROR", "true").lower() == "true"

class Config:
    """Main configuration class."""
    
    def __init__(self):
        self.ollama = OllamaConfig()
        self.browser = BrowserConfig()
        self.agent = AgentConfig()
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'Config':
        """Create config from dictionary."""
        config = cls()
        
        if 'ollama' in config_dict:
            for key, value in config_dict['ollama'].items():
                if hasattr(config.ollama, key):
                    setattr(config.ollama, key, value)
        
        if 'browser' in config_dict:
            for key, value in config_dict['browser'].items():
                if hasattr(config.browser, key):
                    setattr(config.browser, key, value)
        
        if 'agent' in config_dict:
            for key, value in config_dict['agent'].items():
                if hasattr(config.agent, key):
                    setattr(config.agent, key, value)
        
        return config