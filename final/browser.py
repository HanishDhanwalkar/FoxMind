from llm import OllamaClient

client = OllamaClient()

with open("final/crawled_data/viewport.txt", "r", encoding="utf-8") as f:
    html_content = f.read()

prompt = f"""
Below is the scraped html code of a webpage. You need to reconstruct the webpage from the html code. Don't add elements that are not provided. DONOT assume anything. This is complete website. Add <html> and other neccessary tags.
{html_content}
"""

res  = client.chat(prompt)

print(res)