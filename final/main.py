from browser.playwright_browser_copy import Crawler
from llm.base_llm import OllamaClient

from termcolor import colored

class AutomationAgent:
    def __init__(self):
        self.crawler = Crawler()
        self.llm_client = OllamaClient()
        self.research_notes = []
        self.current_url = None
        self.action_history = []

    def run_research(self, query: str, max_steps: int = 10):
        self.research_notes = []
        self.action_history = []
        self.current_url = None

        initial_prompt = f"""You are an autonomous web Browse and research agent. Your goal is to gather information on the following query: "{query}".

You have the following tools:
- `go_to_page(url)`: Navigates the browser to a given URL.
- `scroll(direction)`: Scrolls the current page "up" or "down".
- `click(element_id)`: Clicks an element by its ID.
- `type(element_id, text)`: Types text into an input field identified by its ID.
- `enter()`: Presses the Enter key.
- `type_and_submit(element_id, text)`: Types text into an input field and presses Enter.
- `finish_research(answer)`: Call this when you have fully answered the query.

If some elements are unclickable, try pressing enter.

After each action, I will provide you with the updated page state (a list of simplified HTML elements with IDs). You will then decide the next action.
Always start from from duckduckgo.com. Use duckduckgo to find the best page for your research. Only return the relevant action.
What is your first action? 
"""
        
        print("\n--- Starting Research ---")
        self.crawler.go_to_page("duckduckgo.com")
        llm_response = self.llm_client.chat(initial_prompt)
        print(colored(f"LLM Initial Response: {llm_response}", "green"))
        
        steps = 0
        while steps < max_steps:
            if "finish_research" in llm_response.lower():
                answer = llm_response.split("finish_research(")[1].split(")")[0].strip('"\'')
                print(f"\n--- Research Complete ---\nAnswer: {answer}")
                break

            action = self._parse_llm_action(llm_response)

            if not action:
                print("LLM did not provide a valid action. Asking for clarification.")
                llm_response = self.llm_client.chat("I need a valid action. What should I do next? Choose from `go_to_page`, `scroll`, `click`, `type`, `type_and_submit`, or `finish_research`.")
                continue

            try:
                if action["name"] == "go_to_page":
                    self.crawler.go_to_page(action["args"]["url"])
                    self.current_url = action["args"]["url"]
                    print(f"Navigated to: {self.current_url}")
                elif action["name"] == "scroll":
                    self.crawler.scroll(action["args"]["direction"])
                    print(f"Scrolled {action['args']['direction']}")
                elif action["name"] == "click":
                    self.crawler.click(action["args"]["element_id"])
                    print(f"Clicked element ID: {action['args']['element_id']}")
                elif action["name"] == "type":
                    self.crawler.type(action["args"]["element_id"], action["args"]["text"])
                    print(f"Typed '{action['args']['text']}' into element ID: {action['args']['element_id']}")
                elif action["name"] == "type_and_submit":
                    self.crawler.type_and_submit(action["args"]["element_id"], action["args"]["text"])
                    print(f"Typed '{action['args']['text']}' and submitted into element ID: {action['args']['element_id']}")
                else:
                    print(f"Unknown action: {action['name']}")
                    llm_response = self.llm_client.chat(f"Unknown action: {action['name']}. Please provide a valid action from the allowed tools.")
                    steps += 1
                    continue
            except Exception as e:
                print(f"Error executing action {action['name']}: {e}. Retrying with LLM.")
                llm_response = self.llm_client.chat(f"Error executing previous action: {e}. The page state might have changed or the element was invalid. Please re-evaluate and suggest the next action.")
                steps += 1
                continue

            # After action, get new page state and send to LLM
            current_elements = self.crawler.crawl()
            current_url = self.crawler.page.url
            
            # Context for the LLM
            page_context = f"Current URL: {current_url}\n"
            page_context += "Current Visible Elements (ID, Tag, Attributes, Text):\n"
            for element in current_elements:
                page_context += f"{element}\n"
            page_context += f"\nYour goal is to answer: \"{query}\". What is your next action? Think step-by-step and explain your reasoning before providing the action."
            
            print(f"\n--- Current Page State ---")
            print(f"URL: {current_url}")
            print(f"Elements ({len(current_elements)} found):")
            # print(current_elements) # Be careful with printing too many elements, can flood console
            print("--- Sending to LLM ---")
            
            llm_response = self.llm_client.chat(page_context)
            self.action_history.append((action, llm_response)) # Store history
            print(f"LLM Response: {llm_response}")
            steps += 1
        
        print("\n--- Max steps reached. Research may be incomplete. ---")
        self.crawler.close()

    def _parse_llm_action(self, llm_output: str):
        """
        Parses the LLM's output to extract the action and its arguments.
        Expected format: `action_name(arg1=value1, arg2=value2)`
        """
        import re
        match = re.search(r"(\w+)\((.*)\)", llm_output.strip())
        if not match:
            print(colored("Could not parse LLM action from:"), llm_output)
            return None

        action_name = match.group(1)
        args_str = match.group(2)
        args = {}

        # Basic parsing for key=value arguments
        arg_pairs = re.findall(r'(\w+)=["\']?([^"\']*)["\']?', args_str)
        for key, value in arg_pairs:
            args[key] = value

        return {"name": action_name, "args": args}

    def close(self):
        self.crawler.close()

if __name__ == "__main__":
    agent = AutomationAgent()
    try:
        agent.run_research("What is the current population of India in 2025?")
        # agent.run_research("Find the latest news about AI in healthcare.")
    except Exception as e:
        print(f"An error occurred during automation: {e}")
    finally:
        agent.close()
