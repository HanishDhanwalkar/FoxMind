# agents/llm/ollama_client.py
import aiohttp
import asyncio
import json
from typing import Dict, List, Optional
from ..utils.logger import get_logger

logger = get_logger(__name__)

class OllamaClient:
    """Client for interacting with Ollama API to run LLaMA 3.2 locally."""
    
    def __init__(self, 
                 base_url: str = "http://localhost:11434",
                 model: str = "llama3.2",
                 timeout: int = 60):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def generate(self, 
                      prompt: str, 
                      system_prompt: str = None,
                      temperature: float = 0.1,
                      max_tokens: int = 1000) -> str:
        """Generate text completion using Ollama."""
        try:
            session = await self._get_session()
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            logger.debug(f"Sending request to Ollama: {self.model}")
            
            async with session.post(f"{self.base_url}/api/generate", 
                                   json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error {response.status}: {error_text}")
                
                result = await response.json()
                return result.get("response", "").strip()
                
        except asyncio.TimeoutError:
            logger.error("Ollama request timed out")
            raise Exception("LLM request timed out")
        except Exception as e:
            logger.error(f"Ollama generation failed: {str(e)}")
            raise Exception(f"LLM generation failed: {str(e)}")
    
    async def chat(self, 
                   messages: List[Dict[str, str]],
                   temperature: float = 0.1,
                   max_tokens: int = 1000) -> str:
        """Use chat completion format with message history."""
        try:
            session = await self._get_session()
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
            
            logger.debug(f"Sending chat request to Ollama: {len(messages)} messages")
            
            async with session.post(f"{self.base_url}/api/chat", 
                                   json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error {response.status}: {error_text}")
                
                result = await response.json()
                return result.get("message", {}).get("content", "").strip()
                
        except Exception as e:
            logger.error(f"Ollama chat failed: {str(e)}")
            raise Exception(f"LLM chat failed: {str(e)}")
    
    async def analyze_screenshot(self, 
                               screenshot_path: str, 
                               question: str,
                               model: str = "llava") -> str:
        """Analyze screenshot using vision model (requires llava or similar)."""
        try:
            import base64
            
            # Read and encode image
            with open(screenshot_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            session = await self._get_session()
            
            payload = {
                "model": model,
                "prompt": question,
                "images": [img_data],
                "stream": False
            }
            
            async with session.post(f"{self.base_url}/api/generate", 
                                   json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.warning(f"Vision analysis failed: {error_text}")
                    return "Could not analyze screenshot"
                
                result = await response.json()
                return result.get("response", "").strip()
                
        except Exception as e:
            logger.error(f"Screenshot analysis failed: {str(e)}")
            return "Could not analyze screenshot"
    
    async def is_healthy(self) -> bool:
        """Check if Ollama service is running and model is available."""
        try:
            session = await self._get_session()
            
            # Check if service is up
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status != 200:
                    return False
                
                models = await response.json()
                model_names = [m["name"] for m in models.get("models", [])]
                return self.model in model_names
                
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    async def pull_model(self) -> bool:
        """Pull/download the specified model if not available."""
        try:
            session = await self._get_session()
            
            payload = {"name": self.model}
            
            logger.info(f"Pulling model: {self.model}")
            
            async with session.post(f"{self.base_url}/api/pull", 
                                   json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Model pull failed: {error_text}")
                    return False
                
                # Stream the pull progress
                async for line in response.content:
                    if line:
                        try:
                            progress = json.loads(line.decode('utf-8'))
                            if "status" in progress:
                                logger.info(f"Pull progress: {progress['status']}")
                        except:
                            pass
                
                return True
                
        except Exception as e:
            logger.error(f"Model pull failed: {str(e)}")
            return False
    
    async def cleanup(self):
        """Clean up the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

# Specialized prompts for browser automation
class BrowserAutomationPrompts:
    """Predefined prompts optimized for browser automation tasks."""
    
    @staticmethod
    def action_selection_system_prompt() -> str:
        return """You are a browser automation agent. Your job is to analyze web pages and determine the best actions to complete user objectives.

Key principles:
1. Be decisive - choose clear, specific actions
2. Use CSS selectors or element descriptions that are likely to be unique
3. If you see CAPTCHAs, 2FA prompts, or ambiguous situations, request human help
4. Always explain your reasoning clearly
5. Prefer clicking visible buttons/links over complex interactions
6. Wait for pages to load before taking action

Response format: Always respond with valid JSON containing action, target, value, reasoning, and confidence fields."""
    
    @staticmethod
    def error_recovery_prompt(error_msg: str, attempted_action: str) -> str:
        return f"""The previous action failed with error: {error_msg}

Attempted action: {attempted_action}

Please analyze the current page state and suggest an alternative approach. Consider:
1. Was the element selector incorrect or outdated?
2. Did the page change after navigation?
3. Is there a different way to accomplish the same goal?
4. Should we request human help instead?

Provide your response in the same JSON format with a new action plan."""