from base_llm_async import OllamaClient
from browser import Browser


llmPrompt = """
You are an AI assistant designed to act as a browser agent.
Your goal is to complete tasks given by the user by suggesting browser actions that will lead to completetion of the given task. The task may take multiple steps to complete, and the user may need to navigate to different pages to complete the task.
You are currently on the following web page (content provided below).
Your available actions are:
- NAVIGATE: [URL] (e.g., NAVIGATE: https://www.duckduckgo.com)
- CLICK: [element_id] (e.g., CLICK: myButton)
- TYPE: [text_to_type] INTO: [input_element_id] (e.g., TYPE: John Doe INTO: nameInput)
- SCROLL: [down/up] (e.g., SCROLL: down)

Analyze the current page content and the user's task.
Respond ONLY with the action you want to perform, in the specified format.
If no action is immediately possible or the task is complete, you can respond with "DONE".

Current URL: {currentUrl}
--- Current Page Content ---
{pageContent}
--- End Current Page Content ---

User's Task: "{task}"

What action should I perform?
"""   

currentUrl = ""
pageContent = ""
task = input("Enter a task for the LLM")

browser = Browser()

llm = OllamaClient()

page = browser.crawl()

prompt = llmPrompt.format(currentUrl="https://www.duckduckgo.com", pageContent="This is a test", task="I want to search for something")

        