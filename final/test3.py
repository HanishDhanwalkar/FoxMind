import json
import time
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from llm.base_llm import OllamaClient
from browser.playwright_browser import Crawler

from termcolor import colored

class ActionType(Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    TYPE_SUBMIT = "type_submit"
    SCROLL = "scroll"
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
    page_elements: List[str]
    ai_analysis: str
    success: bool
    error: Optional[str] = None

class ResearchAgent:
    def __init__(self, crawler, llm_client):
        self.crawler = crawler
        self.llm_client = llm_client
        self.step_history: List[StepResult] = []
        self.research_context = ""
        self.findings = []
        
    def execute_research(self, task: str, max_steps: int = 10, starting_url: str = "https://duckduckgo.com") -> Dict[str, Any]:
        print(f"🔍 Starting research task: {task}")
        print(f"📊 Maximum steps allowed: {max_steps}")
        
        self.research_context = task
        self.step_history = []
        self.findings = []
        
        self.crawler.go_to_page(starting_url)
        
        for step in range(1, max_steps + 1):
            print(f"\n----- Step {step}/{max_steps} -----")
            
            elements = self.crawler.crawl()
            print(colored(f"📄 Found {len(elements)} elements on page", "yellow"))
        
            action = self._decide_next_action(step, elements, task)
            
            if action.type == ActionType.COMPLETE:
                print("✅ Research task completed!")
                break
            
            # Execute the decided action
            step_result = self._execute_action(step, action, elements)
            self.step_history.append(step_result)
            
            if not step_result.success:
                print(colored(f"⚠️ Step {step} failed: {step_result.error}", "red"))
                continue
            
            time.sleep(1)
        
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

    
    def _decide_next_action(self, step: int, elements: List[str], task: str) -> Action:
        context = self._build_context_summary() # Build context from previous steps
        print(colored(f"📊 Context summary: {context}", "black"))
        
        elements_text = "\n".join(elements) # Format elements for AI
        prompt = f"""You are an AI research agent. Analyze the current webpage and decide the best next action.

RESEARCH TASK: {task}
CURRENT STEP: {step}

CURRENT PAGE ELEMENTS:
{elements_text}

PREVIOUS CONTEXT: {context}

RECENT FINDINGS:
{chr(10).join(self.findings[-3:]) if self.findings else "No findings yet"}

Based on the research task and current page elements, choose the BEST single action:

1. NAVIGATE - go to a URL (use href from link elements)
2. CLICK - click an element by its ID number (e.g., "5" for <button id=5/>)  
3. TYPE - type text into an input field by ID
4. TYPE_SUBMIT -type text into an input field by ID and submit
5. SCROLL - scroll "up" or "down"
6. ANALYZE - extract information from current page text elements
7. COMPLETE - research task is finished

Look for:
- Search boxes (input elements) to search for the research topic
- Links related to the research task
- Text content that answers the research question
- Navigation elements to explore relevant pages

Also, to search use TYPE_SUBMIT which types the search query and submits it.

Respond ONLY with this JSON format:
{{
    "action": "NAVIGATE|CLICK|TYPE|TYPE_SUBMIT|SCROLL|ANALYZE|COMPLETE",
    "target": "element_id_number OR url OR direction",
    "value": "text_to_type_or_search_query",
    "reasoning": "why this action helps complete the research task"
}}"""

        response = self.llm_client.chat(prompt)
        ai_decision = self._parse_ai_response(response) 
        action_type = ActionType(ai_decision.get('action', 'analyze').lower())
        return Action(
            type=action_type,
            target=ai_decision.get('target'),
            value=ai_decision.get('value'),
            reasoning=ai_decision.get('reasoning', '')
        )
    
    def _execute_action(self, step: int, action: Action, elements: List[str]) -> StepResult:
        """Execute the decided action and return the result."""
        
        print(f"🎯 Executing: {action.type.value}")
        if action.target:
            print(f"🎯 Target: {action.target}")
        if action.value:
            print(f"💬 Value: {action.value}")
        if action.reasoning:
            print(f"💭 Reasoning: {action.reasoning}")
        
        if action.type == ActionType.NAVIGATE:
            self.crawler.go_to_page(action.target)
            
        elif action.type == ActionType.CLICK:
            self.crawler.click(action.target)
            
        elif action.type == ActionType.TYPE:
            if action.target and action.value:
                self.crawler.type(action.target, action.value)
                
        elif action.type == ActionType.TYPE_SUBMIT:
            if action.target and action.value:
                print(colored("typing and submitting"), "yellow")
                self.crawler.type_and_submit(action.target, action.value)
                
        elif action.type == ActionType.SCROLL:
            direction = action.target or "down"
            self.crawler.scroll(direction)
                
        elif action.type == ActionType.ANALYZE:
            # Extract information from current page
            analysis = self._analyze_current_page(elements)
            if analysis and analysis != "No relevant information found.":
                self.findings.append(f"Step {step}: {analysis}")
                print(f"📝 Found: {analysis}")
                
        # Get updated page elements after action
        time.sleep(0.5)  # Brief wait for page to update
        updated_elements = self.crawler.crawl()
        
        return StepResult(
            step_number=step,
            action=action,
            page_elements=updated_elements,
            ai_analysis="",
            success=True
        )
    
    # def _perform_search(self, elements: List[str], query: str) -> bool:
    #     """Find search input and perform search."""
    #     if not query:
    #         return False
            
        # # Look for search input elements
        # for element in elements:
        #     if ('input' in element.lower() and 
        #         ('search' in element.lower() or 'name="q"' in element.lower() or 
        #          'placeholder' in element.lower())):
                
        #         # Extract element ID
        #         element_id = self._extract_element_id(element)
        #         if element_id is not None:
        #             try:
        #                 print(f"🔍 Searching for: {query}")
        #                 self.crawler.type_and_submit(element_id, query)
        #                 return True
        #             except Exception as e:
        #                 print(f"Search failed: {e}")
        #                 continue
        # return False
    
    def _analyze_current_page(self, elements: List[str]) -> str:
        """Use AI to analyze current page elements for research insights."""
        
        # Extract text content from elements
        text_elements = []
        for element in elements:
            if '<text' in element or 'href=' in element:
                # Extract readable content
                content = self._extract_text_content(element)
                if content and len(content.strip()) > 3:
                    text_elements.append(content)
        
        if not text_elements:
            return "No text content found on page."
        
        text_content = "\n".join(text_elements[:20])  # Limit to first 20 text elements
        
        prompt = f"""Analyze this webpage content for information relevant to: "{self.research_context}"

PAGE TEXT CONTENT:
{text_content}

Extract any facts, data, or insights that directly answer or relate to the research question.
Focus on specific, useful information. Ignore navigation text, ads, or irrelevant content.
If no relevant information is found, respond with "No relevant information found."

Relevant information:"""

        try:
            response = self.llm_client.chat(prompt=prompt)
            return response
        except Exception as e:
            return f"Analysis failed: {str(e)}"
    
    def _extract_element_id(self, element: str) -> Optional[str]:
        """Extract element ID from element string."""
        # Look for id=X pattern
        match = re.search(r'id=(\d+)', element)
        if match:
            return match.group(1)
        return None
    
    def _extract_text_content(self, element: str) -> str:
        """Extract readable text content from element string."""
        # For text elements, extract content between tags
        if '<text' in element:
            # Extract text after the closing >
            start = element.find('>')
            if start != -1:
                return element[start+1:].replace('</text>', '').strip()
        
        # For links, extract text content
        elif '<link' in element:
            start = element.find('>')
            if start != -1:
                end = element.find('</link>')
                if end != -1:
                    return element[start+1:end].strip()
                else:
                    return element[start+1:].strip()
        
        return ""
    
    def _build_context_summary(self) -> str:
        """Build a summary of previous steps for context."""
        if not self.step_history:
            return "Starting research task."
        
        recent_steps = self.step_history[-2:]  # Last 2 steps
        context_parts = []
        
        for step_result in recent_steps:
            action_desc = f"{step_result.action.type.value}"
            if step_result.action.target:
                action_desc += f" (target: {step_result.action.target})"
            context_parts.append(f"Step {step_result.step_number}: {action_desc}")
        
        return "; ".join(context_parts)
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response, handling potential JSON formatting issues."""
            # Try to find JSON in the response
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        
        if start_idx != -1 and end_idx != 0:
            json_str = response[start_idx:end_idx]
            parsed = json.loads(json_str)
            return parsed
        else:
            # Fallback: try to extract key information with regex
            action_match = re.search(r'"action":\s*"([^"]+)"', response)
            target_match = re.search(r'"target":\s*"([^"]+)"', response)
            value_match = re.search(r'"value":\s*"([^"]+)"', response)
            reasoning_match = re.search(r'"reasoning":\s*"([^"]+)"', response)
            
            return {
                "action": action_match.group(1) if action_match else "analyze",
                "target": target_match.group(1) if target_match else None,
                "value": value_match.group(1) if value_match else None,
                "reasoning": reasoning_match.group(1) if reasoning_match else "Extracted from malformed response"
            }
                

    def _generate_final_summary(self, task: str) -> str:
        """Generate a final summary of research findings."""
        
        if not self.findings:
            return "No specific findings were gathered during the research process."
        
        findings_text = "\n".join(self.findings)
        
        prompt = f"""Research Task: {task}

Information gathered during web research:
{findings_text}

Provide a clear, concise summary that:
1. Directly answers the research question if possible
2. Lists the key facts and information found
3. Notes if more information is needed

Summary:"""

        try:
            response = self.llm_client.chat(prompt)
            return response
        except Exception as e:
            return f"Could not generate summary. Raw findings: {'; '.join(self.findings)}"
    
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
            "elements_count": len(step_result.page_elements)
        }


# Test script
def main():
    """Test the ResearchAgent with sample tasks."""
    crawler = Crawler()
    llm_client = OllamaClient()
    
    agent = ResearchAgent(crawler, llm_client)
    
    # Test cases
    test_tasks = [
        "What is the current weather in New York?",
        "Find information about Python programming tutorials",
        "Search for the latest news about artificial intelligence",
        "Look up the definition of machine learning"
    ]
    
    print("ResearchAgent Test Suite")
    print("=" * 50)        
    
    # Uncomment this to run actual tests:
    for task in test_tasks:
        print(f"\n{'='*60}")
        print(f"Testing: {task}")
        print('='*60)
        
        result = agent.execute_research(
            task=task,
            max_steps=6,
            starting_url="https://duckduckgo.com"
        )
        
        print(f"✅ Completed: {result['completed']}")
        print(f"📊 Steps used: {result['steps_used']}")
        if result['findings']:
            print(f"🔍 Key findings:")
            for finding in result['findings']:
                print(f"   • {finding}")
        print(f"📋 Summary: {result['summary']}")
    crawler.close()
        
if __name__ == "__main__":
    main()