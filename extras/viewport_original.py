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
        """Get all visible elements in the viewport"""
        all_elements = self.driver.find_elements(By.XPATH, "//*")
        visible_elements = []
        
        for element in all_elements:
            if self.is_element_in_viewport(element):
                visible_elements.append(element)
        
        return visible_elements
    
    def interact_with_element(self, element):
        """Interact with a visible element based on its type"""
        tag_name = element.tag_name.lower()
        
        if tag_name == 'a':
            element.click()
            print(colored(f"Clicked link: {element.text}", "blue"))
        elif tag_name in ['input', 'textarea']:
            input_value = input(f"Type text for {tag_name} (current value: '{element.get_attribute('value')}'): ")
            element.clear()
            element.send_keys(input_value)
            print(colored(f"Typed in {tag_name}: {input_value}", "blue"))
            if tag_name == 'input':
                element.send_keys("enter")  # Simulate pressing Enter
        else:
            print(colored(f"Element of type '{tag_name}' is not interactable in this way.", "red"))
    
    def close(self):
        self.driver.quit()

# Usage example
if __name__ == "__main__":
    extractor = VisibleContentExtractor()
    
    try:
        # Navigate to webpage
        extractor.driver.get("https://duckduckgo.com/?q=supercars")
        
        # Wait for page to load
        extractor.driver.implicitly_wait(2)
        
        while True:
            # Get visible elements
            visible_elements = extractor.get_visible_elements()
            print(colored(f"Found {len(visible_elements)} visible elements", "green"))
            
            for idx, element in enumerate(visible_elements):
                print(f"{idx}: {element.tag_name} - {element.text[:30]}... (ID: {element.get_attribute('id')})")
            
            # Prompt user for action
            action = input("Enter the index of the element to interact with (or 'exit' to quit): ")
            if action.lower() == 'exit':
                break
            
            try:
                index = int(action)
                if 0 <= index < len(visible_elements):
                    extractor.interact_with_element(visible_elements[index])
                else:
                    print(colored("Invalid index. Please try again.", "red"))
            except ValueError:
                print(colored("Please enter a valid number or 'exit'.", "red"))
        
    finally:
        extractor.close()
