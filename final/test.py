import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from llm.base_llm import OllamaClient
from browser.playwright_browser import Crawler

class ActionType(Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    SEARCH = "search"
    ANALYZE = "analyze"
    COMPLETE = "complete"

@dataclass
class Action:
    type: ActionType
    target: Optional[str] = None
    value: Optional[str] = None
    reasoning: Optional[str] = None

@dataclass
class StepResult:
    step_number: int
    action: Action
    page_state: List[str]
    ai_analysis: str
    success: bool
    error: Optional[str] = None

class ResearchAgent:
    def __init__(self, crawler, llm_client, model_name: str = "llama3.2"):
        self.crawler = crawler
        self.llm_client = llm_client
        self.model_name = model_name
        self.step_history: List[StepResult] = []
        self.research_context = ""
        self.findings = []
        
    def execute_research(self, task: str, max_steps: int = 10, starting_url: str = "https://duckduckgo.com") -> Dict[str, Any]:
        """
        Execute a research task using the AI agent.
        
        Args:
            task: The research task to complete
            max_steps: Maximum number of steps allowed
            starting_url: URL to start the research from
            
        Returns:
            Dictionary containing research results and execution details
        """
        print(f"🔍 Starting research task: {task}")
        print(f"📊 Maximum steps allowed: {max_steps}")
        
        # Initialize research context
        self.research_context = task
        self.step_history = []
        self.findings = []
        
        try:
            self.crawler.go_to_page(starting_url)
            
            for step in range(1, max_steps + 1):
                print(f"\n--- Step {step}/{max_steps} ---")
        
                page_state = self.crawler.crawl() # Get current page state
                action = self._decide_next_action(step, page_state, task) # Analyze current situation and decide next action
                
                if action.type == ActionType.COMPLETE:
                    print("✅ Research task completed!")
                    break
                
                step_result = self._execute_action(step, action, page_state)
                self.step_history.append(step_result)
                
                if not step_result.success:
                    print(f"⚠️ Step {step} failed: {step_result.error}")
                    continue
                
                time.sleep(1)
            
            # Generate final research summary
            final_summary = self._generate_final_summary(task)
            
            return {
                "task": task,
                "completed": True,
                "steps_used": len(self.step_history),
                "max_steps": max_steps,
                "findings": self.findings,
                "summary": final_summary,
                "step_history": [self._step_result_to_dict(step) for step in self.step_history]
            }
            
        except Exception as e:
            print(f"❌ Research failed with error: {str(e)}")
            return {
                "task": task,
                "completed": False,
                "error": str(e),
                "steps_used": len(self.step_history),
                "findings": self.findings,
                "step_history": [self._step_result_to_dict(step) for step in self.step_history]
            }
        finally:
            self.crawler.close()
    
    def _decide_next_action(self, step: int, page_state: List[str], task: str) -> Action:
        """Use AI to decide the next action based on current page state and task."""
        
        # Prepare context for AI
        context = self._build_ai_context(step, page_state, task)
        
        prompt = f"""
You are an AI research agent browsing the web to complete a research task.

RESEARCH TASK: {task}
CURRENT STEP: {step}

CURRENT PAGE ELEMENTS:
{chr(10).join(page_state[:50])}  # Limit to first 50 elements to avoid token limits

PREVIOUS FINDINGS:
{chr(10).join(self.findings[-3:])}  # Last 3 findings

CONTEXT FROM PREVIOUS STEPS:
{context}

Analyze the current page and decide the SINGLE BEST next action to take.

Available actions:
1. NAVIGATE - go to a specific URL
2. CLICK - click on an element (provide element ID)
3. TYPE - type text into an input field (provide element ID and text)
4. SCROLL - scroll up or down
5. SEARCH - perform a search query
6. ANALYZE - extract information from current page
7. COMPLETE - task is finished

Respond with ONLY a JSON object in this exact format:
{{
    "action_type": "NAVIGATE|CLICK|TYPE|SCROLL|SEARCH|ANALYZE|COMPLETE",
    "target": "element_id or url or direction",
    "value": "text to type or search query",
    "reasoning": "why this action makes sense for the research task",
    "findings": "any new information discovered (if analyzing)"
}}
"""
        try:
            response = self.llm_client.chat(prompt)
            
            ai_decision = self._parse_ai_response(response['response'])
            action_type = ActionType(ai_decision.get('action_type', 'analyze').lower())
            
            return Action(
                type=action_type,
                target=ai_decision.get('target'),
                value=ai_decision.get('value'),
                reasoning=ai_decision.get('reasoning', '')
            )
            
        except Exception as e:
            print(f"⚠️ AI decision failed: {e}, defaulting to analyze")
            return Action(type=ActionType.ANALYZE, reasoning="Fallback action due to AI error")
    
    def _execute_action(self, step: int, action: Action, page_state: List[str]) -> StepResult:
        """Execute the decided action and return the result."""
        
        print(f"🎯 Executing: {action.type.value}")
        if action.reasoning:
            print(f"💭 Reasoning: {action.reasoning}")
        
        try:
            if action.type == ActionType.NAVIGATE:
                self.crawler.go_to_page(action.target)
                
            elif action.type == ActionType.CLICK:
                self.crawler.click(action.target)
                
            elif action.type == ActionType.TYPE:
                if action.target and action.value:
                    self.crawler.type(action.target, action.value)
                
            elif action.type == ActionType.SCROLL:
                direction = action.target or "down"
                self.crawler.scroll(direction)
                
            elif action.type == ActionType.SEARCH:
                search_performed = self._perform_search(action.value) # Try to find search box and perform search
                if not search_performed:
                    return StepResult(
                        step_number=step,
                        action=action,
                        page_state=page_state,
                        ai_analysis="",
                        success=False,
                        error="Could not find search box"
                    )
                    
            elif action.type == ActionType.ANALYZE:
                analysis = self._analyze_current_page(page_state) # Extract information from current page
                if analysis:
                    self.findings.append(f"Step {step}: {analysis}")
                    
            # Get updated page state after action
            updated_page_state = self.crawler.crawl()
            return StepResult(
                step_number=step,
                action=action,
                page_state=updated_page_state,
                ai_analysis="",
                success=True
            )
            
        except Exception as e:
            return StepResult(
                step_number=step,
                action=action,
                page_state=page_state,
                ai_analysis="",
                success=False,
                error=str(e)
            )
    
    def _perform_search(self, query: str) -> bool:
        """Try to find and use a search box on the current page."""
        page_state = self.crawler.crawl()
        
        # Look for common search element patterns
        search_patterns = ['search', 'query', 'q', 'input']
        
        for element in page_state:
            element_lower = element.lower()
            for pattern in search_patterns:
                if pattern in element_lower and ('input' in element_lower or 'textbox' in element_lower):
                    try:
                        # Extract element ID (this is a simplified approach)
                        # You might need to adjust based on your Crawler's element ID format
                        element_id = self._extract_element_id(element)
                        if element_id:
                            self.crawler.type_and_submit(element_id, query)
                            return True
                    except:
                        continue
        return False
    
    def _analyze_current_page(self, page_state: List[str]) -> str:
        """Use AI to analyze current page content for research insights."""
        
        prompt = f"""
Analyze this webpage content for information relevant to the research task: "{self.research_context}"

PAGE CONTENT:
{chr(10).join(page_state[:100])}

Extract any relevant information, facts, data, or insights that help answer the research question.
Be concise and focus only on information directly related to the research task.
If no relevant information is found, respond with "No relevant information found."

Response:"""

        try:
            response = self.ollama_client.generate(
                model=self.model_name,
                prompt=prompt
            )
            return response['response'].strip()
        except Exception as e:
            return f"Analysis failed: {str(e)}"
    
    def _build_ai_context(self, step: int, page_state: List[str], task: str) -> str:
        """Build context string from previous steps for AI decision making."""
        if not self.step_history:
            return "This is the first step."
        
        recent_steps = self.step_history[-3:]  # Last 3 steps
        context_parts = []
        
        for step_result in recent_steps:
            context_parts.append(
                f"Step {step_result.step_number}: {step_result.action.type.value} "
                f"- {step_result.action.reasoning or 'No reasoning provided'}"
            )
        
        return "; ".join(context_parts)
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response, handling potential JSON formatting issues."""
        try:
            # Try to find JSON in the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback parsing
                return {"action_type": "analyze", "reasoning": "Could not parse AI response"}
                
        except json.JSONDecodeError:
            return {"action_type": "analyze", "reasoning": "Invalid JSON in AI response"}
    
    def _extract_element_id(self, element_text: str) -> Optional[str]:
        """Extract element ID from element text representation."""
        # This is a simplified implementation
        # You'll need to adjust based on how your Crawler formats element information
        if 'id=' in element_text:
            try:
                start = element_text.find('id=') + 3
                end = element_text.find(' ', start)
                if end == -1:
                    end = len(element_text)
                return element_text[start:end].strip('"\'')
            except:
                return None
        return None
    
    def _generate_final_summary(self, task: str) -> str:
        """Generate a final summary of research findings."""
        
        prompt = f"""
Research Task: {task}

Findings from web research:
{chr(10).join(self.findings)}

Please provide a comprehensive summary that:
1. Directly answers the research question
2. Synthesizes key information found
3. Highlights the most important insights
4. Notes any limitations or areas needing further research

Summary:"""

        try:
            response = self.ollama_client.generate(
                model=self.model_name,
                prompt=prompt
            )
            return response['response'].strip()
        except Exception as e:
            return f"Summary generation failed: {str(e)}"
    
    def _step_result_to_dict(self, step_result: StepResult) -> Dict[str, Any]:
        """Convert StepResult to dictionary for JSON serialization."""
        return {
            "step_number": step_result.step_number,
            "action_type": step_result.action.type.value,
            "action_target": step_result.action.target,
            "action_value": step_result.action.value,
            "reasoning": step_result.action.reasoning,
            "success": step_result.success,
            "error": step_result.error,
            "page_elements_count": len(step_result.page_state)
        }


# Example usage
def main():
    """Example of how to use the ResearchAgent."""
    
    # Initialize your crawler and ollama client
    crawler = Crawler()  # Your crawler instance
    llm_client = OllamaClient()  # Your ollama client instance
    
    # Create the research agent
    agent = ResearchAgent(crawler, llm_client)
    
    # Example research tasks
    research_tasks = [
        "Find the current stock price of Apple Inc. (AAPL)",
        "What are the top 3 renewable energy companies by market cap?",
        "Research the latest developments in quantum computing",
        "Find information about Python 3.12 new features"
    ]
    
    # Execute research
    for task in research_tasks:
        result = agent.execute_research(
            task=task,
            max_steps=3,
            starting_url="https://duckduckgo.com"
        )
        
        print(f"\n{'='*60}")
        print(f"RESEARCH RESULTS FOR: {task}")
        print(f"{'='*60}")
        print(f"Completed: {result['completed']}")
        print(f"Steps used: {result['steps_used']}")
        print(f"Summary: {result['summary']}")
        print(f"Findings: {result['findings']}")

if __name__ == "__main__":
    main()