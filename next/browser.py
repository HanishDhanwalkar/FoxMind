from playwright.sync_api import sync_playwright
import json
import time
import argparse
from termcolor import colored

class Browser:
    def __init__(self, headless=False, slo_mode=False):
        self.playwright = None
        self.browser = None
        self.page = None
        self.slo_mode = slo_mode
        
        self._launch(headless)

    def _launch(self, headless=False):
        """Launches a Firefox browser instance."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.firefox.launch(headless=headless)
        self.page = self.browser.new_page()
        print(colored("Browser launched successfully.", "cyan"))

    def navigate(self, url):
        """Navigates to a specified URL."""
        try:
            self.page.goto(url=url if "://" in url else "https://" + url)
            print(colored((f"Navigated to: {url}"), "cyan"))
            if self.slo_mode:
                time.sleep(1)
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
    
    def _get_page_state(self):
        """
        Retrieves the current state of the page, including URL, title,
        and interactive elements/links that are strictly visible within the viewport.
        """
        url = self.page.url
        title = self.page.title()
        
        # Get viewport dimensions
        viewport_size = self.page.viewport_size
        viewport_width = viewport_size['width']
        viewport_height = viewport_size['height']

        # Define interactive element selectors
        interactive_selectors = [
            'button[id]', 'input[id]', 'select[id]', 'textarea[id]',
            'a[id]', '[onclick][id]', '[role="button"][id]',
            'form[id]', '[tabindex][id]'
        ]
        
        interactive_elements = []
        seen_ids = set()
        
        # Helper function to check if a bounding box intersects the viewport
        def is_in_viewport(bbox, vp_width, vp_height):
            if not bbox:
                return False
            # Check for overlap: element's right edge is to the right of viewport's left edge
            # and element's left edge is to the left of viewport's right edge
            # and element's bottom edge is below viewport's top edge
            # and element's top edge is above viewport's bottom edge
            return (bbox['x'] < vp_width and
                    bbox['x'] + bbox['width'] > 0 and
                    bbox['y'] < vp_height and
                    bbox['y'] + bbox['height'] > 0)

        # Find all interactive elements with IDs that are strictly visible AND in the viewport
        for selector in interactive_selectors:
            elements = self.page.locator(selector).all()
            for element in elements:
                try:
                    element_id = element.get_attribute('id')
                    if element_id and element_id not in seen_ids:
                        # Check if element is generally visible (not display:none, visibility:hidden, etc.)
                        if element.is_visible():
                            # Get the bounding box relative to the viewport
                            bounding_box = element.bounding_box()
                            
                            # Crucial check: Ensure the bounding box actually intersects the viewport
                            if is_in_viewport(bounding_box, viewport_width, viewport_height):
                                seen_ids.add(element_id)
                                
                                # Get element properties using Playwright methods
                                tag_name = element.evaluate('el => el.tagName.toLowerCase()')
                                element_type = element.get_attribute('type') or ''
                                href = element.get_attribute('href') or ''
                                class_name = element.get_attribute('class') or ''
                                
                                # Get text content with fallbacks
                                text = element.text_content() or ''
                                if not text.strip():
                                    # Try other text sources if text_content is empty
                                    text = (element.get_attribute('placeholder') or 
                                            element.get_attribute('value') or 
                                            element.get_attribute('alt') or 
                                            element.get_attribute('title') or '')
                                
                                # Clean up text and truncate
                                text = ' '.join(text.strip().split())[:100]
                                
                                interactive_elements.append({
                                    'id': element_id,
                                    'tag': tag_name,
                                    'type': element_type,
                                    'text': text,
                                    'href': href,
                                    'className': class_name
                                })
                except Exception as e:
                    # Skip elements that can't be processed (e.g., detached from DOM)
                    continue
        
        # Get only links that are strictly visible AND in the current viewport
        links = []
        _i = 1
        link_elements = self.page.locator('a[href]').all()
        for link in link_elements:
            try:
                if link.is_visible():
                    bounding_box = link.bounding_box()
                    if is_in_viewport(bounding_box, viewport_width, viewport_height):
                        href = link.get_attribute('href')
                        # Only include absolute HTTP/HTTPS links
                        if href and (href.startswith('http://') or href.startswith('https://')):
                            text = link.text_content() or ''
                            text = ' '.join(text.strip().split())[:40]
                            links.append({
                                'ID': _i,
                                'text': text,
                                'href': href
                            })
                            _i += 1
            except Exception:
                # Skip links that can't be processed
                continue
        
        return {
            'url': url,
            'title': title,
            'interactive_elements': interactive_elements,
            'links': links
        }
    
    def crawl(self):
        """
        Crawl the current page and extract interactive elements and links.
        Only elements strictly visible within the current viewport are included.
        """
        print(colored("Fetching Page state", "cyan"))
        page_state = self._get_page_state()
        print(colored("\n=== PAGE CRAWL RESULTS STARTS ===", "green"))
        print(f"Cureent Page: {page_state['url']}")
        print(f"Title: {page_state['title']}")
        
        print(f"\nFound {len(page_state['interactive_elements'])} interactive elements (strictly in viewport):")
        for i, element in enumerate(page_state['interactive_elements'], 1):
            print(f"{i:2d}. [{element['tag'].upper()}] ID: {element['id']} | {element['text'][:50]}{'...' if len(element['text']) > 50 else ''}")
        
        print(f"\nFound {len(page_state['links'])} links (strictly in viewport):")
        for i, link in enumerate(page_state['links'], 1):
            print(f"{link['ID']:2d}. {link['text'][:40]}{'...' if len(link['text']) > 40 else ''} -> {link['href']}")
        
        print(colored("\n=== PAGE CRAWL RESULTS ENDS ===", 'green'))
            
    
    def click_element(self, element_id):
        """Click an element by its ID"""
        element = self.page.locator(f"#{element_id}")
        if element.count() == 0:
            print(f"Element with ID '{element_id}' not found")
            return False
        
        # Check if element is visible before clicking
        if not element.is_visible():
            print(f"Element with ID '{element_id}' is not visible")
            return False
        
        element.click()
        print(colored(f"Clicked element with ID: {element_id}", "cyan"))
        return True
        
    def enter(self):
        """Presses the Enter key."""
        self.page.keyboard.press("Enter")
        print(colored(f"Pressed Enter", "cyan"))
        time.sleep(0.5)
        if self.slo_mode:
            time.sleep(1.5)
        
    
    def scroll(self, direction):
        """Scrolls the page up or down by one viewport height, staying within the viewport."""
        if direction == "up":
            self.page.evaluate(
                "(document.scrollingElement || document.body).scrollTop = "
                "Math.max(0, (document.scrollingElement || document.body).scrollTop - window.innerHeight);"
            )
        elif direction == "down":
            self.page.evaluate(
                "(document.scrollingElement || document.body).scrollTop = "
                "Math.min((document.scrollingElement || document.body).scrollHeight - window.innerHeight, "
                "(document.scrollingElement || document.body).scrollTop + window.innerHeight);"
            )
        print(colored(f"Scrolled {direction}", "cyan"))
        
    def type(self, text):
        self.page.keyboard.type(text, delay=50)
        print(colored(f"Typed text: {text[:10]}...", "cyan"))
        time.sleep(0.5)
        if self.slo_mode:
            time.sleep(1.5)
        
    def fill_input(self, element_id, text):
        """Fill an input element with text by its ID"""
        element = self.page.locator(f"#{element_id}")
        if element.count() == 0:
            print(f"Element with ID '{element_id}' not found")
            return False
        
        # Check if element is visible before filling
        if not element.is_visible():
            print(f"Element with ID '{element_id}' is not visible")
            return False
        
        # Check if element is an input or textarea field
        tag_name = element.evaluate("el => el.tagName.toLowerCase()")
        if tag_name not in ['input', 'textarea']:
            print(f"Element with ID '{element_id}' is not an input field (it's a {tag_name})")
            return False
        
        # Scroll element into view if needed (Playwright handles this automatically before fill)
        # element.scroll_into_view_if_needed()
        
        # Clear existing text and fill with new text
        element.fill(text)
        _browser.enter()
        print(colored(f"Filled element '{element_id}' with text: {text}", "cyan"))
        return True

    def take_screenshot(self, filename="screenshot.png"):
        """Takes a screenshot of the current page."""
        try:
            self.page.screenshot(path=filename)
            print(colored(f"Screenshot saved as: {filename}", "cyan"))
        except Exception as e:
            print(f"Error taking screenshot: {e}")

    def close(self):
        """Closes the browser instance."""
        if self.browser:
            self.browser.close()
            print(colored("Browser closed.", "green"))
        if self.playwright:
            self.playwright.stop()
            print(colored("Playwright stopped.", "green"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Browser")
    parser.add_argument("--headless", action="store_true", help="Run the browser in headless mode")
    parser.add_argument("--slo_mo", action="store_true", help="Run the browser in slow motion mode")
    args = parser.parse_args()
    
    
    _browser = Browser(headless=args.headless, slo_mode=args.slo_mo)
    try:
        _browser.navigate("duckduckgo.com")
        
        # # _browser.fill_input("searchbox_input", "cars")
        # _browser.click_element("searchbox_input")
        # _browser.type("cars")
        # _browser.enter()
        
        # _browser.crawl() 
        
        # _browser.scroll("down")
        # _browser.crawl()
        
        # _browser.click_element("Cars.com") # TODO: Check click functionality
        
        
        while True:
            option = input("""Options:\n1. Navigate: (url - default="duckduckgo.com")\n2. crawl\n3. click: (ID)\n4. type: (ID, text)\n5. exit\n==> """)
            
            if option == "1":
                url = input("Enter the url: ")
                if url == "":
                    url = "duckduckgo.com"
                _browser.navigate(url)
            
            elif option == "2":
                _browser.crawl()
                
            elif option == "3":
                element_id = input("Enter the id to click: ")
                _browser.click_element(element_id)
                
            elif option == "4":
                element_id = input("Enter the id of the input field: ")
                text_to_fill = input("Enter the text to type: ")
                _browser.fill_input(element_id, text_to_fill)
                
            elif option == "5":
                _browser.close()
                break
            else:
                print("Invalid option. Please choose from 1-5.")

    except Exception as e:
        print(f"An error occurred during automation: {e}")
    finally:
        if _browser.browser.is_connected():
            _browser.close()
