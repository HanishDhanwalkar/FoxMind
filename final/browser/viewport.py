from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from termcolor import colored
import os

class VisibleContentExtractor:
    def __init__(self):
        # Setup Firefox options
        self.options = Options()
        self.driver = webdriver.Firefox(options=self.options)
    
    def get_viewport_dimensions(self):
        """Get the current viewport dimensions"""
        return self.driver.execute_script("""
            return {
                width: window.innerWidth,
                height: window.innerHeight,
                scrollX: window.pageXOffset,
                scrollY: window.pageYOffset
            };
        """)
    
    def is_element_in_viewport(self, element):
        """Check if an element is visible in the current viewport"""
        script = """
        var elem = arguments[0];
        var rect = elem.getBoundingClientRect();
        var viewHeight = Math.max(document.documentElement.clientHeight, window.innerHeight);
        var viewWidth = Math.max(document.documentElement.clientWidth, window.innerWidth);
        
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= viewHeight &&
            rect.right <= viewWidth &&
            rect.width > 0 &&
            rect.height > 0 &&
            window.getComputedStyle(elem).visibility !== 'hidden' &&
            window.getComputedStyle(elem).display !== 'none'
        );
        """
        return self.driver.execute_script(script, element)
    
    def get_visible_elements(self):
        """Get all visible elements (divs and links) in the order they appear"""
        all_elements = self.driver.find_elements(By.XPATH, "//*")  # Get all elements
        visible_elements = []
        
        for element in all_elements:
            if self.is_element_in_viewport(element):
                element_data = {
                    'tag': element.tag_name,
                    'text': element.text.strip(),  # Strip whitespace
                    'attributes': self.get_element_attributes(element),
                    'location': element.location,
                    'size': element.size
                }
                visible_elements.append(element_data)
        
        return visible_elements
    
    def get_element_attributes(self, element):
        """Get all attributes of an element"""
        return self.driver.execute_script("""
            var attrs = {};
            for (var i = 0; i < arguments[0].attributes.length; i++) {
                var attr = arguments[0].attributes[i];
                attrs[attr.name] = attr.value;
            }
            return attrs;
        """, element)
    
    def get_current_viewport_screenshot(self, filename="viewport.png"):
        """Take screenshot of current viewport"""
        self.driver.save_screenshot(filename)
        return filename
    
    def close(self):
        self.driver.quit()

# Usage example
if __name__ == "__main__":
    extractor = VisibleContentExtractor()
    
    try:
        # Navigate to webpage
        extractor.driver.get("https://www.duckduckgo.com/search?q=The+Rock")
        
        # Wait for page to load
        extractor.driver.implicitly_wait(1)
        
        # Get viewport info
        viewport = extractor.get_viewport_dimensions()
        print(colored(f"Viewport: {viewport}", "green"))
        
        # Get visible elements
        visible_elements = extractor.get_visible_elements()
        print(colored(f"Found {len(visible_elements)} visible elements", "green"))
        
        # Write visible elements to viewport.txt
        with open("viewport.txt", "w", encoding="utf-8") as f:
            for element in visible_elements:
                f.write(f"Tag: {element['tag']}," + f" Text: " +  element['text'].replace('\n', '\\n') + f", Attributes: {element['attributes']}\n")
                
        
        # Take screenshot of current view
        extractor.get_current_viewport_screenshot("current_view.png")
        
    finally:
        extractor.close()
