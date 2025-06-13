import os
import ollama
from browser import Browser
from tools import get_available_tools_json

model = "llama3.2"


bws = Browser(slo_mode=True, verbose=True)

TOOLS = {
    'navigate to url':bws.navigate,
    'go_back':bws.go_back,
    # 'get_viewport_state':bws._get_page_state,
    'get_viewport_text':bws.get_viewport_text_blocks,
    'crawl':bws.crawl,
    'click_element':bws.click_element,
    'Press enter':bws.enter,
    'Scroll':bws.scroll,
    'type':bws.type,
    'fill input text':bws.fill_input,
    # 'take screenshot':bws.take_screenshot,
    'Close browser':bws.close
}


ollama_tools = get_available_tools_json()


user_input = input("What would you like to research on?")

system_msg = """You are an AI assistant that can Browser internet pages and perform tasks such as navigating to a URL, clicking on elements, typing text, scrolling, and filling input fields. You can also close the browser window. Next, user will provide tasks or research topic(s), for which you need to navigate/search on the browser. For any search, use duckduckgo.com. (first navigate to duckduckgo.com url, then search for input box element ID by using crawl function, then using fillinput search for required topic)

"""
messages = [
    {'role': 'system', 'content':system_msg},
    {'role': 'user', 'content':user_input}
]


response: ollama.ChatResponse = ollama.chat(
    model=model,
    messages=messages,
    tools=ollama_tools,
    
)

if response.message.tool_calls:
    for tool_call in response.message.tool_calls:
        print(tool_call.function.name)
        print(tool_call.function.arguments)
        
else:
    print("No tools called")
    
TOOLS[tool_call.function.name](**tool_call.function.arguments)