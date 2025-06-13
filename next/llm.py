from base_llm import OllamaClient
from browser import Browser
from helper import extract_json_from_response
from termcolor import colored

class LLMAgent:
    def __init__(self, task_description: str, ollama_model: str = "llama3.2", verbose=True):
        self.task_description = task_description
        self.ollama_model = ollama_model
        self.task_complete = False
        self.verbose = verbose
        
        self.client = OllamaClient(model=ollama_model)
        
    
    
        
    def start_browser(self, headless=False, slo_mode=True, verbose=True, starting_url="https://www.duckduckgo.com"):
        self.browser = Browser(headless=headless, slo_mode=slo_mode, verbose=verbose)
        self.browser.navigate(starting_url)
        
        self.browsring_actions = {
            "navigate": self.browser.navigate,
            "type": self.browser.type,
            "click": self.browser.click_element,
            "scroll": self.browser.scroll,
            "fill input text": self.browser.fill_input,
            "get text from viewport": self.browser.get_viewport_text_blocks,
            "done": self.browser.close
        }
        
    def decide_action(self, browser_state: dict) -> dict:
        print("Deciding action...")
        
        llm_res = self.client.generate(f"""
You are a LLM agent that decides browser actions based on the current state. Your overall task to complete is: {self.task_description}
The current browser state is: {browser_state}. This is state is similified webpage.
Your response MUST be a JSON object with the following structure:
{{'action': 'navigate' | 'click' | 'fill_input' | 'done',
    'element_id': 'id',
    'value': 'locator_value' | 'URL' | None,
    'text': 'text_to_type' | None}}

    Note: id for id can be obtained from the browser_state
- If 'action' is 'navigate', 'value' should be the URL.
- If 'action' is 'click' or 'type', 'locator' and 'value' are required. 'text' is required for 'type'.
- If the task is completed, set 'action' to 'done'.
""")    
        if self.verbose:
            print(colored("LLM Response:", "cyan"), llm_res)
        
        action = extract_json_from_response(llm_res)
        return action
    
    def execute_action(self, action: dict) -> dict:
        print(colored("Executing action...", color="light_green"))
        
        if action["action"] in self.browsring_actions:
            self.browsring_actions[action["action"]](action["value"])
        
        return action

    def close(self):
        print("Exiting browser...")
        self.browser.close()
        
if __name__ == "__main__":
    agent = LLMAgent("go to duckduckgo and search for supercars", "deepseek-r1:7b")
    
    agent.start_browser(headless=False, slo_mode=True, verbose=True, starting_url="https://www.duckduckgo.com")
    
    while not agent.task_complete:
        browser_state = agent.browser.crawl()
        action = agent.decide_action(browser_state)
        confirm_action = input(f"Execute action: {action}? (y/n) ")
        if confirm_action.lower() == "y":
            agent.execute_action(action)
            action["action"] = "done"
        
        if action["action"] == "done":
            agent.task_complete = True
    
    agent.close()