from base_llm import OllamaClient
from browser import Browser
from helper import extract_json_from_response
from termcolor import colored

class LLMAgent:
    def __init__(self, task_description: str, ollama_model: str = "llama3.2", verbose: bool = True):
        self.task_description = task_description
        self.ollama_model = ollama_model
        self.task_complete = False
        self.verbose = verbose
        
        self.client = OllamaClient(model=ollama_model, verbose=verbose)
        
    
    
        
    def start_browser(self, headless=False, slo_mode=True, verbose=True, starting_url="https://www.duckduckgo.com"):
        self.browser = Browser(headless=headless, slo_mode=slo_mode, verbose=verbose)
        self.browser.navigate(starting_url)
        
        self.browsing_actions = {
            "navigate": self.browser.navigate,
            "type": self.browser.type,
            "click": self.browser.click_element,
            "scroll": self.browser.scroll,
            "fill_input": self.browser.fill_input,
            "get text from viewport": self.browser.get_viewport_text_blocks,
            "close": self.browser.close
        }
        
    def decide_action(self, browser_state: dict) -> dict:
        print("Deciding action...")
        
        llm_res = self.client.generate(f"""
You are a LLM agent that decides browser actions based on the current state. Your overall task to complete is: {self.task_description}
The current browser state is:
{browser_state}

*This is state is similified webpage.*
Your response MUST be a JSON object with the following structure:
```json
{{'action': 'navigate' | 'click' | 'fill_input' | 'done',
    'element_id': 'id',
    'value': 'locator_value' | 'URL' | 'up/down' |None,
    'text': 'text_to_type' | None}}
```

    Note: id for id can be obtained from the browser_state. 
    Also, if you find a search box, you can directly use it using 'fill_input' action. No need to click on it before.
- If 'action' is 'navigate', 'value' should be the URL.
- If 'action' is 'click' or 'type', 'locator' and 'value' are required. 'text' is required for 'type'.
- If the task is completed, set 'action' to 'done'.

For eg.,
If task to is to search 'some research topic to search' using ducduckgo and page contents are:
Current Page: https://duckduckgo.com/
Title: DuckDuckGo - Protection. Privacy. Peace of mind.

Found 2 interactive elements (strictly in viewport):
 1. [INPUT] ID: searchbox_input | Search without being tracked
 2. [FORM] ID: searchbox_homepage |

Found 3 links (strictly in viewport):
 1. Duck.ai -> https://duck.ai

Expected outout:
```json
{{
  "action": "fill_input",
  "element_id": "searchbox_input",
  "value": None,
  "text": "some research topic to search"
}}
```

""")    
        if self.verbose:
            print(colored("LLM Response:", "cyan"), llm_res)
        
        action = extract_json_from_response(llm_res)
        return action
    
    def execute_action(self, action: dict) -> dict:
        print(colored("Executing action...", color="light_green"))
        
        if action["action"] in ["navigate", "scroll"]:
            self.browsing_actions[action["action"]](action["value"])
        elif action["action"] in ["fill_input", "type"]:
            self.browsing_actions[action["action"]](action["element_id"], action["text"])
        elif action["action"] == "click":
            self.browsing_actions[action["action"]](action["element_id"])
        else:
            
            print(colored(f"Unknown action: {action['action']}", "red"))
        
        return action

    def close(self):
        print("Exiting browser...")
        self.browser.close()
        
if __name__ == "__main__":
    agent = LLMAgent("Find top 3 afforadable 1BK apartments in Byculla, Maharastra", "deepseek-r1:7b")
    
    agent.start_browser(headless=False, slo_mode=True, verbose=True, starting_url="https://www.duckduckgo.com")
    
    while not agent.task_complete:
        browser_state = agent.browser.crawl()
        action = agent.decide_action(browser_state)
        confirm_action = input(f"Execute action: {action}? (y/n) ")
        if confirm_action.lower() == "y":
            agent.execute_action(action)
            exit = input("Exit? (y/n) ")
            if exit.lower() == "y":
                action["action"] = "done"
                
        
        if action["action"] == "done":
            agent.task_complete = True
    
    agent.close()