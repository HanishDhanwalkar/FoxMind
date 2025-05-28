# agents/browser_agent.py
import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .llm.ollama_client import OllamaClient
from .browser.selenium_controller import SeleniumController
from .utils.logger import get_logger
from .utils.exceptions import AgentException, HumanInterventionRequired

logger = get_logger(__name__)

class ActionType(Enum):
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    NAVIGATE = "navigate"
    HUMAN_HELP = "human_help"
    COMPLETE = "complete"

@dataclass
class AgentAction:
    action_type: ActionType
    target: Optional[str] = None
    value: Optional[str] = None
    reasoning: Optional[str] = None
    confidence: float = 0.0

@dataclass
class TaskContext:
    objective: str
    current_step: int
    completed_steps: List[str]
    current_url: str
    last_action: Optional[AgentAction] = None
    error_count: int = 0
    max_errors: int = 3

class BrowserAgent:
    """Main agent class that orchestrates LLM reasoning and browser automation."""
    
    def __init__(self, 
                 ollama_model: str = "llama3.2",
                 headless: bool = False,
                 max_steps: int = 50):
        self.llm = OllamaClient(model=ollama_model)
        self.browser = SeleniumController(headless=headless)
        self.max_steps = max_steps
        self.context: Optional[TaskContext] = None
        
    async def execute_task(self, objective: str, starting_url: str = None) -> Dict:
        """Execute a complete task from start to finish."""
        logger.info(f"Starting task: {objective}")
        
        self.context = TaskContext(
            objective=objective,
            current_step=0,
            completed_steps=[],
            current_url=starting_url or "about:blank"
        )
        
        try:
            # Navigate to starting URL if provided
            if starting_url:
                await self._navigate_to_url(starting_url)
            
            # Main execution loop
            while self.context.current_step < self.max_steps:
                try:
                    # Get current page state
                    page_state = await self._get_page_state()
                    
                    # Get next action from LLM
                    action = await self._get_next_action(page_state)
                    
                    # Execute the action
                    result = await self._execute_action(action)
                    
                    # Check if task is complete
                    if action.action_type == ActionType.COMPLETE:
                        logger.info("Task completed successfully!")
                        break
                        
                    # Handle human intervention requests
                    if action.action_type == ActionType.HUMAN_HELP:
                        human_response = await self._request_human_help(action.reasoning)
                        # Continue based on human input
                        continue
                    
                    self.context.current_step += 1
                    self.context.completed_steps.append(f"Step {self.context.current_step}: {action.reasoning}")
                    
                except Exception as e:
                    logger.error(f"Error in step {self.context.current_step}: {str(e)}")
                    self.context.error_count += 1
                    
                    if self.context.error_count >= self.context.max_errors:
                        logger.error("Max errors reached, requesting human help")
                        await self._request_human_help(f"Encountered repeated errors: {str(e)}")
                    
                    await asyncio.sleep(2)  # Brief pause before retry
            
            return {
                "success": True,
                "steps_completed": self.context.current_step,
                "final_url": self.browser.get_current_url(),
                "summary": self.context.completed_steps
            }
            
        except HumanInterventionRequired as e:
            return {
                "success": False,
                "reason": "human_intervention_required",
                "message": str(e),
                "steps_completed": self.context.current_step
            }
        except Exception as e:
            logger.error(f"Task failed: {str(e)}")
            return {
                "success": False,
                "reason": "error",
                "message": str(e),
                "steps_completed": self.context.current_step
            }
        finally:
            self.cleanup()
    
    async def _get_page_state(self) -> Dict:
        """Capture current page state for LLM analysis."""
        try:
            screenshot_path = await self.browser.take_screenshot()
            page_source = self.browser.get_page_source()
            current_url = self.browser.get_current_url()
            
            # Get simplified DOM structure
            interactive_elements = self.browser.get_interactive_elements()
            
            return {
                "url": current_url,
                "title": self.browser.get_title(),
                "screenshot_path": screenshot_path,
                "interactive_elements": interactive_elements,
                "page_source_snippet": page_source[:2000],  # First 2000 chars
                "viewport_size": self.browser.get_viewport_size()
            }
        except Exception as e:
            logger.error(f"Failed to get page state: {str(e)}")
            return {"error": str(e)}
    
    async def _get_next_action(self, page_state: Dict) -> AgentAction:
        """Use LLM to determine the next action based on current state."""
        prompt = self._build_action_prompt(page_state)
        
        try:
            response = await self.llm.generate(prompt)
            action_data = self._parse_llm_response(response)
            
            return AgentAction(
                action_type=ActionType(action_data.get("action", "wait")),
                target=action_data.get("target"),
                value=action_data.get("value"),
                reasoning=action_data.get("reasoning", ""),
                confidence=float(action_data.get("confidence", 0.5))
            )
        except Exception as e:
            logger.error(f"Failed to get next action: {str(e)}")
            return AgentAction(
                action_type=ActionType.HUMAN_HELP,
                reasoning=f"Could not determine next action: {str(e)}"
            )
    
    def _build_action_prompt(self, page_state: Dict) -> str:
        """Build the prompt for the LLM to determine next action."""
        return f"""
You are a browser automation agent. Your objective is: {self.context.objective}

Current context:
- Step: {self.context.current_step}
- URL: {page_state.get('url', 'unknown')}
- Page title: {page_state.get('title', 'unknown')}
- Previous steps completed: {len(self.context.completed_steps)}

Interactive elements on the page:
{json.dumps(page_state.get('interactive_elements', []), indent=2)}

Page content snippet:
{page_state.get('page_source_snippet', '')}

Available actions:
- click: Click on an element (provide CSS selector or element description)
- type: Type text into an input field (provide selector and text)
- scroll: Scroll the page (up/down/to_element)
- wait: Wait for page to load or element to appear
- navigate: Go to a different URL
- human_help: Request human assistance (explain what you need help with)
- complete: Task is finished successfully

Please respond with a JSON object containing:
{{
    "action": "action_type",
    "target": "css_selector_or_description",
    "value": "text_to_type_or_scroll_direction",
    "reasoning": "why_you_chose_this_action",
    "confidence": 0.8
}}

Choose the most appropriate action to progress toward the objective. If you encounter CAPTCHAs, 2FA, or are unsure about something, use "human_help".
"""
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parse LLM response into action dictionary."""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing
                return {"action": "wait", "reasoning": "Could not parse LLM response"}
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse LLM response as JSON: {response}")
            return {"action": "human_help", "reasoning": "Invalid LLM response format"}
    
    async def _execute_action(self, action: AgentAction) -> Dict:
        """Execute the determined action in the browser."""
        logger.info(f"Executing action: {action.action_type.value} - {action.reasoning}")
        
        try:
            if action.action_type == ActionType.CLICK:
                return await self.browser.click_element(action.target)
            elif action.action_type == ActionType.TYPE:
                return await self.browser.type_text(action.target, action.value)
            elif action.action_type == ActionType.SCROLL:
                return await self.browser.scroll(action.value)
            elif action.action_type == ActionType.WAIT:
                await asyncio.sleep(int(action.value) if action.value else 2)
                return {"success": True}
            elif action.action_type == ActionType.NAVIGATE:
                return await self._navigate_to_url(action.value)
            elif action.action_type == ActionType.SCREENSHOT:
                screenshot_path = await self.browser.take_screenshot()
                return {"success": True, "screenshot": screenshot_path}
            else:
                return {"success": True, "message": "Action noted"}
        except Exception as e:
            logger.error(f"Action execution failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _navigate_to_url(self, url: str) -> Dict:
        """Navigate to a specific URL."""
        try:
            await self.browser.navigate_to(url)
            self.context.current_url = url
            return {"success": True, "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _request_human_help(self, reason: str) -> str:
        """Request human intervention."""
        logger.info(f"Requesting human help: {reason}")
        
        print(f"\n🤖 AGENT NEEDS HELP:")
        print(f"Reason: {reason}")
        print(f"Current URL: {self.context.current_url}")
        print(f"Objective: {self.context.objective}")
        print(f"Steps completed: {len(self.context.completed_steps)}")
        
        # Take screenshot for human reference
        screenshot_path = await self.browser.take_screenshot()
        print(f"Screenshot saved: {screenshot_path}")
        
        response = input("\nPlease help and press Enter when ready to continue (or type 'abort' to stop): ")
        
        if response.lower() == 'abort':
            raise HumanInterventionRequired("User requested to abort task")
        
        return response
    
    def cleanup(self):
        """Clean up resources."""
        if self.browser:
            self.browser.quit()
        logger.info("Agent cleanup completed")

# Usage example
async def main():
    agent = BrowserAgent(ollama_model="llama3.2", headless=False)
    
    result = await agent.execute_task(
        objective="Search for 'Python automation' on Google and bookmark the first result",
        starting_url="https://google.com"
    )
    
    print(f"Task result: {result}")

if __name__ == "__main__":
    asyncio.run(main())