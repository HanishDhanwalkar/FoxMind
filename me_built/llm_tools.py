import ollama
import requests
from selenium import webdriver
import time 


def get_driver():
    options = webdriver.FirefoxOptions()
    # options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    return driver

driver = get_driver()

def web_search(query: str):
    driver.get("https://duckduckgo.com?q=" + query)
    return driver.

    

# with open("example.html", "w", encoding="utf-8") as f:
#     f.write(driver.page_source)

time.sleep(1)
driver.quit()



available_functions = {
    'request': requests.request,
}



response = ollama.chat(
    'llama3.2',
    messages=[{'role': 'user', 'content': 'get the current time'}],
    tools=[requests.request], # Actual function reference
)


for tool in response.message.tool_calls or []:
    print('Tool:', tool.function.name)
    function_to_call = available_functions.get(tool.function.name)
    if function_to_call:
        print("tool.function.arguments:", tool.function.arguments)
        print('Function output:', function_to_call(**tool.function.arguments))
    else:
        print('Function not found:', tool.function.name)
