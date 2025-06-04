from playwright.sync_api import sync_playwright

class Browser:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    def launch(self, headless=True):
        """Launches a Firefox browser instance."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.firefox.launch(headless=headless)
        self.page = self.browser.new_page()
        print("Browser launched successfully.")

    def navigate(self, url):
        """Navigates to a specified URL."""
        try:
            self.page.goto(url)
            print(f"Navigated to: {url}")
        except Exception as e:
            print(f"Error navigating to {url}: {e}")

    
    def scroll(self, direction):
        """Scrolls the page up or down by one viewport height."""
        if direction == "up":
            self.page.evaluate(
                "(document.scrollingElement || document.body).scrollTop = "
                "(document.scrollingElement || document.body).scrollTop - window.innerHeight;"
            )
        elif direction == "down":
            self.page.evaluate(
                "(document.scrollingElement || document.body).scrollTop = "
                "(document.scrollingElement || document.body).scrollTop + window.innerHeight;"
            )
        # Wait for scroll to complete and content to potentially load
        # time.sleep(0.5)


    def click_element(self, selector):
        """Clicks an element identified by a CSS selector."""
        try:
            self.page.click(selector)
            print(f"Clicked element with selector: {selector}")
        except Exception as e:
            print(f"Error clicking element {selector}: {e}")

    def fill_input(self, selector, value):
        """Fills an input field with a given value."""
        try:
            self.page.fill(selector, value)
            print(f"Filled input {selector} with value: '{value}'")
        except Exception as e:
            print(f"Error filling input {selector}: {e}")

    def extract_text(self, selector):
        """Extracts text content from an element identified by a CSS selector."""
        try:
            text = self.page.text_content(selector)
            print(f"Extracted text from {selector}: '{text}'")
            return text
        except Exception as e:
            print(f"Error extracting text from {selector}: {e}")
            return None

    def take_screenshot(self, filename="screenshot.png"):
        """Takes a screenshot of the current page."""
        try:
            self.page.screenshot(path=filename)
            print(f"Screenshot saved as: {filename}")
        except Exception as e:
            print(f"Error taking screenshot: {e}")

    def close(self):
        """Closes the browser instance."""
        if self.browser:
            self.browser.close()
            print("Browser closed.")
        if self.playwright:
            self.playwright.stop()
            print("Playwright stopped.")

if __name__ == "__main__":
    browser = Browser()
    try:
        browser.launch(headless=False)  # Set to False to see the browser actions
        
        # 1. Navigate
        browser.navigate("https://www.duckduckgo.com")

        # # 2. Fill input and click (search for something)
        # browser.fill_input("textarea[name='q']", "IPL 2025 Finals")
        # browser.click_element("input[name='btnK']") # This might need adjustment based on Google's exact button selector

        # # Wait for navigation after search (optional, but good practice)
        # browser.page.wait_for_load_state("networkidle")

        # 3. Extract text (e.g., search results title)
        # This selector might need to be more specific depending on the search results page structure
        # first_result_title = browser.extract_text("h3") 
        # if first_result_title:
        #     print(f"First search result title: {first_result_title}")

        # 4. Scroll down
        browser.scroll("down")

        # 6. Take a screenshot
        browser.take_screenshot("Duckduckgo Search_results.png")

        # 7. Navigate to another page and click a link
        browser.navigate("https://www.wikipedia.org/")
        browser.click_element("a[id='js-link-box-en']") # Click on the English Wikipedia link
        
        # 8. Extract text from the new page
        welcome_text = browser.extract_text("h1")
        if welcome_text:
            print(f"Wikipedia Welcome text: {welcome_text}")

    except Exception as e:
        print(f"An error occurred during automation: {e}")
    finally:
        browser.close()