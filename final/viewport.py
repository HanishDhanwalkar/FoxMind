# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.firefox.options import Options

# from termcolor import colored
# import os

# class VisibleContentExtractor:
#     def __init__(self):
#         # Setup Firefox options
#         self.options = Options()
#         self.driver = webdriver.Firefox(options=self.options)
    
#     def get_viewport_dimensions(self):
#         """Get the current viewport dimensions"""
#         return self.driver.execute_script("""
#             return {
#                 width: window.innerWidth,
#                 height: window.innerHeight,
#                 scrollX: window.pageXOffset,
#                 scrollY: window.pageYOffset
#             };
#         """)
    
#     def is_element_in_viewport(self, element):
#         """Check if an element is visible in the current viewport"""
#         script = """
#         var elem = arguments[0];
#         var rect = elem.getBoundingClientRect();
#         var viewHeight = Math.max(document.documentElement.clientHeight, window.innerHeight);
#         var viewWidth = Math.max(document.documentElement.clientWidth, window.innerWidth);
        
#         return (
#             rect.top >= 0 &&
#             rect.left >= 0 &&
#             rect.bottom <= viewHeight &&
#             rect.right <= viewWidth &&
#             rect.width > 0 &&
#             rect.height > 0 &&
#             window.getComputedStyle(elem).visibility !== 'hidden' &&
#             window.getComputedStyle(elem).display !== 'none'
#         );
#         """
#         return self.driver.execute_script(script, element)
    
#     def get_visible_images(self):
#         """Get only images that are currently visible in viewport"""
#         all_images = self.driver.find_elements(By.TAG_NAME, "img")
#         visible_images = []
        
#         for img in all_images:
#             if self.is_element_in_viewport(img):
#                 img_data = {
#                     'src': img.get_attribute('src'),
#                     'alt': img.get_attribute('alt'),
#                     'width': img.get_attribute('width'),
#                     'height': img.get_attribute('height'),
#                     'location': img.location,
#                     'size': img.size
#                 }
#                 visible_images.append(img_data)
        
#         return visible_images
    
#     def get_visible_elements_by_tag(self, tag_name):
#         """Get visible elements by tag name"""
#         all_elements = self.driver.find_elements(By.TAG_NAME, tag_name)
#         visible_elements = []
        
#         for element in all_elements:
#             if self.is_element_in_viewport(element):
#                 element_data = {
#                     'tag': element.tag_name,
#                     'text': element.text,
#                     'attributes': self.get_element_attributes(element),
#                     'location': element.location,
#                     'size': element.size
#                 }
#                 visible_elements.append(element_data)
        
#         return visible_elements
    
#     def get_element_attributes(self, element):
#         """Get all attributes of an element"""
#         return self.driver.execute_script("""
#             var attrs = {};
#             for (var i = 0; i < arguments[0].attributes.length; i++) {
#                 var attr = arguments[0].attributes[i];
#                 attrs[attr.name] = attr.value;
#             }
#             return attrs;
#         """, element)
    
#     def get_visible_html_content(self):
#         """Get HTML content of only visible elements"""
#         script = """
#         function getVisibleHTML() {
#             var viewHeight = Math.max(document.documentElement.clientHeight, window.innerHeight);
#             var viewWidth = Math.max(document.documentElement.clientWidth, window.innerWidth);
#             var visibleElements = [];
            
#             function isElementVisible(elem) {
#                 if (!elem || elem.nodeType !== 1) return false;
                
#                 var rect = elem.getBoundingClientRect();
#                 var style = window.getComputedStyle(elem);
                
#                 return (
#                     rect.top >= 0 &&
#                     rect.left >= 0 &&
#                     rect.bottom <= viewHeight &&
#                     rect.right <= viewWidth &&
#                     rect.width > 0 &&
#                     rect.height > 0 &&
#                     style.visibility !== 'hidden' &&
#                     style.display !== 'none'
#                 );
#             }
            
#             function traverseDOM(node) {
#                 if (node.nodeType === 1) { // Element node
#                     if (isElementVisible(node)) {
#                         visibleElements.push({
#                             tagName: node.tagName,
#                             outerHTML: node.outerHTML,
#                             textContent: node.textContent,
#                             className: node.className,
#                             id: node.id
#                         });
#                     }
#                 }
                
#                 for (var i = 0; i < node.childNodes.length; i++) {
#                     traverseDOM(node.childNodes[i]);
#                 }
#             }
            
#             traverseDOM(document.body);
#             return visibleElements;
#         }
        
#         return getVisibleHTML();
#         """
#         return self.driver.execute_script(script)
    
#     def get_current_viewport_screenshot(self, filename="viewport.png"):
#         """Take screenshot of current viewport"""
#         self.driver.save_screenshot(filename)
#         return filename
    
#     def close(self):
#         self.driver.quit()

# # Usage example
# if __name__ == "__main__":
#     extractor = VisibleContentExtractor()
    
#     try:
#         # Navigate to webpage
#         extractor.driver.get("https://duckduckgo.com")
        
#         # Wait for page to load
#         extractor.driver.implicitly_wait(3)
        
#         # Get viewport info
#         viewport = extractor.get_viewport_dimensions()
#         print(colored(f"Viewport: {viewport}", "green"))
        
#         # Get visible images
#         visible_images = extractor.get_visible_images()
#         print(colored(f"Found {len(visible_images)} visible images", "green"))
        
#         # Get visible elements by tag
#         visible_divs = extractor.get_visible_elements_by_tag("div")
#         print(colored(f"Found {len(visible_divs)} visible div elements", "green"))
#         print("\n".join([str(div) for div in visible_divs])) 
        
#         links = extractor.get_visible_elements_by_tag("a")
#         print(colored(f"Found {len(links)} visible link elements", "green"))
#         print("\n".join([str(link) for link in links])) 
        
#         # Get all visible HTML content
#         # visible_content = extractor.get_visible_html_content()
#         # print(colored(f"Found {len(visible_content)} visible elements total", "green"))
#         # print("\n".join([str(content) for content in visible_content]))
        
#         # Take screenshot of current view
#         extractor.get_current_viewport_screenshot("current_view.png")
        
#         # You can scroll and repeat the process
#         # extractor.driver.execute_script("window.scrollBy(0, 500);")
#         # Then call the methods again to get newly visible content
        
#         with open("viewport.txt", "w", encoding="utf-8") as f:
            
#             viewport_content = "\n".join([str(i) for i in visible_divs + links])
#             f.write(viewport_content)
        
#     finally:
#         extractor.close()

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
        extractor.driver.get("https://google.com")
        
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
