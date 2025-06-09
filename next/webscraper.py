from playwright.sync_api import sync_playwright
import time



def get_text_from_whole_page(url):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")

        # Define which block tags to extract
        block_tags = ['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']

        # Query DOM and extract readable blocks in order
        blocks = page.evaluate(f"""
            () => {{
                const tags = {block_tags};
                const elements = Array.from(document.querySelectorAll(tags.join(',')));

                return elements.map(el => el.innerText.trim())
                               .filter(text => text.length > 0);
            }}
        """)
        
        browser.close()
        return blocks
    

def get_text_blocks(url):
    """
    Returns a list of text blocks from a given URL 
    IN THE ORDER AS THEY APPEAR On the page.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")

        # Traverse the body in DOM order and get readable blocks
        script = """
        () => {
            const isVisible = (el) => {
                const style = window.getComputedStyle(el);
                return style && style.display !== 'none' && style.visibility !== 'hidden';
            };

            const blockTags = new Set(['P', 'LI', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6']);
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT, null, false);

            const results = [];

            while (walker.nextNode()) {
                const el = walker.currentNode;

                if (!blockTags.has(el.tagName)) continue;
                if (!isVisible(el)) continue;

                const text = el.innerText.trim();
                if (text.length > 0) {
                    results.push(text);
                }
            }

            return results;
        }
        """

        blocks = page.evaluate(script)
        browser.close()
        return blocks

def get_viewport_text_blocks(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(url, wait_until="networkidle")

        script = """
        () => {
            const isVisible = (el) => {
                const style = window.getComputedStyle(el);
                return (
                    style &&
                    style.display !== 'none' &&
                    style.visibility !== 'hidden' &&
                    el.offsetParent !== null
                );
            };

            const isInViewport = (el) => {
                const rect = el.getBoundingClientRect();
                return (
                    rect.top >= 0 &&
                    rect.top < window.innerHeight &&
                    rect.bottom > 0
                );
            };

            const blockTags = new Set(['P', 'LI', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6']);
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT, null, false);
            const results = [];

            while (walker.nextNode()) {
                const el = walker.currentNode;

                if (!blockTags.has(el.tagName)) continue;
                if (!isVisible(el)) continue;
                if (!isInViewport(el)) continue;

                const text = el.innerText.trim();
                if (text.length > 0) {
                    results.push(text);
                }
            }

            return results;
        }
        """

        blocks = page.evaluate(script)
        browser.close()
        return blocks


if __name__ == "__main__":

    with open("output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(get_viewport_text_blocks('https://en.wikipedia.org/wiki/Python_(programming_language)')))



# from bs4 import BeautifulSoup
# import requests

# # Using BeautifulSoup + requests => Gets text across page
# def get_clean_text_blocks(url):
#     response = requests.get(url)
#     soup = BeautifulSoup(response.content, 'html.parser')

#     # Use the content section only for structured sites like Wikipedia
#     content_div = soup.find('div', {'id': 'mw-content-text'}) or soup.body

#     text_blocks = []
    
#     # Define which tags are top-level blocks we care about
#     block_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']

#     for tag in content_div.find_all(block_tags, recursive=True):
#         # Get only visible text, with inline tags flattened
#         text = tag.get_text(separator=' ', strip=True)
#         if text:  # skip empty strings
#             text_blocks.append(text)

#     return text_blocks