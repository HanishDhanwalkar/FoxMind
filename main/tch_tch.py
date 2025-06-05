from selenium.webdriver import Firefox,FirefoxOptions

from bs4 import BeautifulSoup

from readability import Document

import time

# def get_driver():
#     options = FirefoxOptions()
#     # options.add_argument("--headless")
#     try:
#         driver  = Firefox(options=options)
#         return driver
#     except Exception as e:
#         print(e)
        
# driver = get_driver()
# driver.get("https://duckduckgo.com/?q=python")
# html = driver.page_source

# time.sleep(2)
# driver.quit()

# print(html[:100])

# with open("example.html", "w", encoding="utf-8") as f:
#     f.write(html)

with open("example.html", "r", encoding="utf-8") as f:
    html = f.readlines()

html = "\n".join(html)
    
    
# PARSING HTML
soup = BeautifulSoup(html, "html.parser")
# Remove unwanted tags
for tag in soup(["script", "style", "header", "footer", "nav", "aside"]): 
    tag.decompose()


# Extract visible text with links
visible_text = []
for a_tag in soup.find_all('a'):
    visible_text.append(f"{a_tag.text} ({a_tag.get('href')})")
for element in soup.find_all(string=True):
    if element.parent.name != 'a':
        visible_text.append(element)
visible_text = "\n".join(visible_text)


with open("example.txt", "w", encoding="utf-8") as f:
    f.write(visible_text)



doc = Document(html)
main_content_html = doc.summary()
main_title = doc.title()

# You can further parse this:
main_soup = BeautifulSoup(main_content_html, "html.parser")
main_text = " ".join(main_soup.stripped_strings)

with open("example_main.txt", "w", encoding="utf-8") as f:
    f.write(main_text)
            
            