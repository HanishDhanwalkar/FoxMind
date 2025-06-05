from selenium.webdriver.common.by import By
from selenium.webdriver import Firefox,FirefoxOptions
from selenium.webdriver.common.keys import Keys

import time
import json


class LLMAgent:
    """
    Simulates an LLM agent that decides browser actions based on the current state,
    demonstrating integration with Ollama's chat function.
    """
    def __init__(self, task_description: str, ollama_model: str = "llama3.2"):
        self.task_description = task_description
        self.ollama_model = ollama_model
        self.chat_history = []
        self.current_step = 0 # Used for hardcoded simulation responses
        
        # Define the sequence of actions for the simulated LLM.
        # In a real LLM, these would be generated dynamically.
        self.simulated_actions = [
            {"action": "navigate", "value": "https://www.google.com"},
            {"action": "type", "locator": "xpath", "value": "//textarea[@name='q'] | //input[@name='q']", "text": "history of AI" + Keys.ENTER},
            {"action": "click", "locator": "xpath", "value": "(//div[@id='search']//a[starts-with(@href, 'http')])[1]"},
            {"action": "done"}
        ]

        print(f"LLM Agent initialized with task: '{self.task_description}' using simulated model: '{self.ollama_model}'")

    def decide_action(self, browser_state: dict) -> dict:
        """
        Decides the next action based on the current browser state and internal plan,
        simulating an Ollama chat interaction.
        Args:
            browser_state (dict): A dictionary containing current_url, page_title,
                                  and a list of interactive_elements.
        Returns:
            dict: An action dictionary (e.g., {"action": "click", "locator": "xpath", "value": "//button[@id='submit']"})
        """
        print(f"\n--- LLM Agent: Current Step {self.current_step + 1} ---")
        print(f"LLM Agent received browser state (URL): {browser_state['current_url']}")
        

        # --- Construct the prompt for the LLM (as if calling Ollama) ---
        system_prompt = """
        You are an autonomous web browsing agent. Your goal is to complete the given task by interacting with the web browser.
        I will provide you with the current browser state, including the URL, page title, and a list of interactive elements.
        Based on this information and the overall task, you must decide the next action to perform.
        Your response MUST be a JSON object with the following structure:
        {'action': 'navigate' | 'click' | 'type' | 'done' | 'wait',
         'locator': 'id' | 'name' | 'xpath' | 'css_selector' | None,
         'value': 'locator_value' | 'URL' | None,
         'text': 'text_to_type' | None}

        - If 'action' is 'navigate', 'value' should be the URL.
        - If 'action' is 'click' or 'type', 'locator' and 'value' are required. 'text' is required for 'type'.
        - If the task is completed, set 'action' to 'done'.
        - If you need to wait for something to load or are unsure, set 'action' to 'wait'.

        Example for navigation: {'action': 'navigate', 'value': 'https://www.example.com'}
        Example for clicking a button by ID: {'action': 'click', 'locator': 'id', 'value': 'submitButton'}
        Example for typing into a search box by XPath: {'action': 'type', 'locator': 'xpath', 'value': '//input[@name="q"]', 'text': 'my query'}
        Example for task completion: {'action': 'done'}
        """

        user_prompt = f"""
        Overall Task: {self.task_description}

        Current Browser State:
        URL: {browser_state['current_url']}
        Page Title: {browser_state['page_title']}
        Interactive Elements: {json.dumps(browser_state['interactive_elements'], indent=2)}

        What is the next action?
        """

        # Append the system and user prompts to chat history
        self.chat_history.append({"role": "system", "content": system_prompt})
        self.chat_history.append({"role": "user", "content": user_prompt})

        # --- Simulate Ollama chat call ---
        # In a real environment, you would uncomment the line below and remove the mock_ollama_response logic.
        # response = chat(model=self.ollama_model, messages=self.chat_history)
        # llm_output = response['message']['content']

        # For simulation, we use a hardcoded sequence of actions.
        if self.current_step < len(self.simulated_actions):
            action_to_perform = self.simulated_actions[self.current_step]
            llm_output = json.dumps(action_to_perform)
            print(f"SIMULATED LLM Output: {llm_output}")
        else:
            llm_output = json.dumps({"action": "done"}) # Task completed or out of steps

        # Append the simulated LLM response to chat history
        self.chat_history.append({"role": "assistant", "content": llm_output})

        # --- Parse the LLM's output ---
        try:
            action_dict = json.loads(llm_output)
            self.current_step += 1 # Increment step for next simulated action
            return action_dict
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM output JSON: {e}")
            print(f"Raw LLM output: {llm_output}")
            return {"action": "wait"} # Fallback action



class BrowserController:
    def __init__(self):
        self.get_driver()
        
    def get_driver(self):
        options = FirefoxOptions()
        # options.add_argument("--headless")
        try:
            self.driver  = Firefox(options=options)
        except Exception as e:
            print(e)

    def get_browser_state(self) -> dict:
        """
        Extracts and returns the current browser state for the LLM.
        Includes URL, page title, and a simplified list of interactive elements.
        """
        state = {
            "current_url": self.driver.current_url,
            "page_title": self.driver.title,
            "interactive_elements": self._get_interactive_elements()
        }
        return state

    def _get_interactive_elements(self) -> list:
        """
        Identifies and describes interactive elements on the page.
        Focuses on links, buttons, and input fields.
        Returns a list of dictionaries, each describing an element.
        """
        interactive_elements = []
        # Define common interactive element tags
        tags = ['a', 'button', 'input', 'textarea', 'select']

        for tag in tags:
            try:
                elements = self.driver.find_elements(By.TAG_NAME, tag)
                for i, el in enumerate(elements):
                    # Attempt to get text, handle cases where text is not directly visible
                    text = el.text.strip()
                    if not text and tag == 'input':
                        text = el.get_attribute('value') or el.get_attribute('placeholder') or ''

                    # Get relevant attributes
                    attrs = {}
                    if tag == 'a':
                        href = el.get_attribute('href')
                        if href: attrs['href'] = href
                    if tag == 'input':
                        input_type = el.get_attribute('type')
                        if input_type: attrs['type'] = input_type
                        placeholder = el.get_attribute('placeholder')
                        if placeholder: attrs['placeholder'] = placeholder
                    
                    element_id = el.get_attribute('id')
                    if element_id: attrs['id'] = element_id
                    element_name = el.get_attribute('name')
                    if element_name: attrs['name'] = element_name
                    element_class = el.get_attribute('class')
                    if element_class: attrs['class'] = element_class

                    # Generate a unique XPath for the element
                    # This is a basic XPath generation; for robust systems, a more advanced one is needed.
                    try:
                        xpath = self.driver.execute_script(
                            """
                            function getElementXPath(element) {
                                if (element && element.id) return '//*[@id="' + element.id + '"]';
                                if (!element || element.nodeType !== 1) return '';
                                var samesiblings = 0;
                                var sibling = element.previousElementSibling;
                                while (sibling) {
                                    if (sibling.nodeName === element.nodeName) samesiblings++;
                                    sibling = sibling.previousElementSibling;
                                }
                                var xpath = getElementXPath(element.parentNode);
                                var name = element.nodeName;
                                if (samesiblings > 0) name += '[' + (samesiblings + 1) + ']';
                                return xpath + '/' + name;
                            }
                            return getElementXPath(arguments[0]);
                            """, el
                        )
                    except Exception as e:
                        xpath = f"//<{tag}>[text()='{text}']" if text else f"//<{tag}>[{i+1}]" # Fallback XPath

                    interactive_elements.append({
                        "tag": tag,
                        "text": text,
                        "attributes": attrs,
                        "xpath": xpath,
                        "is_displayed": el.is_displayed(),
                        "is_enabled": el.is_enabled()
                    })
            except Exception as e:
                print(e)
        return interactive_elements
    
    def execute_action(self, action: dict) -> bool:
        """
        Executes a Selenium action based on the LLM's decision.
        Returns True if the action was successful, False otherwise.
        """
        action_type = action.get("action")
        locator_type = action.get("locator")
        locator_value = action.get("value")
        text_to_type = action.get("text")

        print(f"\n--- Browser Controller: Executing Action '{action_type}' ---")

        try:
            if action_type == "navigate":
                url = action.get("value")
                if url:
                    self.driver.get(url)
                    print(f"Navigated to: {url}")
                    return True
                else:
                    print("Navigation action requires a 'value' (URL).")
                    return False
            elif action_type == "click":
                if not locator_type or not locator_value:
                    print("Click action requires 'locator' and 'value'.")
                    return False
                element = self.driver.find_element(getattr(By, locator_type.upper()), locator_value)
                if element.is_displayed() and element.is_enabled():
                    element.click()
                    print(f"Clicked element using {locator_type}: {locator_value}")
                    return True
                else:
                    print(f"Element not clickable (displayed: {element.is_displayed()}, enabled: {element.is_enabled()})")
                    return False
            elif action_type == "type":
                if not locator_type or not locator_value or text_to_type is None:
                    print("Type action requires 'locator', 'value', and 'text'.")
                    return False
                element = self.driver.find_element(getattr(By, locator_type.upper()), locator_value)
                if element.is_displayed() and element.is_enabled():
                    element.clear() # Clear existing text
                    element.send_keys(text_to_type)
                    print(f"Typed '{text_to_type}' into element using {locator_type}: {locator_value}")
                    return True
                else:
                    print(f"Element not typable (displayed: {element.is_displayed()}, enabled: {element.is_enabled()})")
                    return False
            elif action_type == "done":
                print("Task marked as done by LLM agent.")
                return True # Indicate success for task completion
            elif action_type == "wait":
                print("LLM requested to wait. Pausing for 2 seconds.")
                time.sleep(2)
                return True
            else:
                print(f"Unknown action type: {action_type}")
                return False
        # except NoSuchElementException:
        #     print(f"Element not found for action '{action_type}' with {locator_type}: {locator_value}")
        #     return False
        # except WebDriverException as e:
        #     print(f"WebDriver error during action '{action_type}': {e}")
        #     return False
        except Exception as e:
            print(f"An unexpected error occurred during action '{action_type}': {e}")
            return False

    def close(self):
        """Closes the browser."""
        if self.driver:
            print("Closing browser...")
            self.driver.quit()
            print("Browser closed.")


def run_llm_browser_pipeline(task: str, max_steps: int = 5):
    """
    Main function to run the LLM-driven browser control pipeline.
    """
    browser_controller = None
    llm_agent = LLMAgent(task)
    
    try:
        browser_controller = BrowserController()
        
        for step_count in range(max_steps):
            print(f"\n=== Pipeline Step {step_count + 1}/{max_steps} ===")
            
            # 1. Perception: Get current browser state
            current_state = browser_controller.get_browser_state()
            
            # 2. Decision: LLM decides the next action
            action_to_perform = llm_agent.decide_action(current_state)
            
            if action_to_perform.get("action") == "done":
                print("\nLLM Agent indicates task completion. Exiting pipeline.")
                break
            
            # 3. Execution: Browser controller performs the action
            success = browser_controller.execute_action(action_to_perform)
            
            if not success:
                print(f"Action failed at step {step_count + 1}. Attempting to re-evaluate or exit.")
                # In a real agent, this would trigger error recovery or re-planning.
                # For this demo, we'll just break.
                break
            
            # Small pause to observe the browser action
            time.sleep(3) 

    except Exception as e:
        print(f"\nAn error occurred during the pipeline execution: {e}")
    finally:
        if browser_controller:
            browser_controller.close()
        print("\nPipeline execution finished.")

if __name__ == "__main__":
    task_description = "Research the history of AI and navigate to the first relevant article."
    run_llm_browser_pipeline(task_description)