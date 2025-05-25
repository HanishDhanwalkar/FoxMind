# agents/browser/selenium_controller.py
import asyncio
import os
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    ElementClickInterceptedException, StaleElementReferenceException
)

from ..utils.logger import get_logger

logger = get_logger(__name__)

class SeleniumController:
    """Selenium-based browser controller for Firefox automation."""
    
    def __init__(self, 
                 headless: bool = False,
                 implicit_wait: int = 10,
                 page_load_timeout: int = 30,
                 window_size: Tuple[int, int] = (1920, 1080),
                 screenshots_dir: str = "screenshots"):
        
        self.headless = headless
        self.implicit_wait = implicit_wait
        self.page_load_timeout = page_load_timeout
        self.window_size = window_size
        self.screenshots_dir = screenshots_dir
        self.driver: Optional[webdriver.Firefox] = None
        self.wait: Optional[WebDriverWait] = None
        
        # Create screenshots directory
        os.makedirs(screenshots_dir, exist_ok=True)
        
        self._setup_driver()
    
    def _setup_driver(self):
        """Initialize Firefox WebDriver with appropriate options."""
        try:
            # Firefox options
            options = Options()
            if self.headless:
                options.add_argument("--headless")
            
            # Performance and compatibility options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f"--window-size={self.window_size[0]},{self.window_size[1]}")
            
            # Disable notifications and location requests
            options.set_preference("dom.webnotifications.enabled", False)
            options.set_preference("geo.enabled", False)
            
            # Initialize driver
            self.driver = webdriver.Firefox(options=options)
            self.driver.implicitly_wait(self.implicit_wait)
            self.driver.set_page_load_timeout(self.page_load_timeout)
            
            # Set window size
            self.driver.set_window_size(*self.window_size)
            
            # Initialize WebDriverWait
            self.wait = WebDriverWait(self.driver, 10)
            
            logger.info("Firefox WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Scroll failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _find_element(self, selector: str, timeout: int = 10):
        """Find element by CSS selector with various fallback strategies."""
        try:
            # Try direct CSS selector first
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                return element
            except:
                pass
            
            # Try by ID
            if selector.startswith("#"):
                element = self.driver.find_element(By.ID, selector[1:])
                return element
            
            # Try by text content (for buttons, links)
            elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{selector}')]")
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    return elem
            
            # Try by partial text
            elements = self.driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{selector.lower()}')]")
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    return elem
            
            return None
            
        except Exception as e:
            logger.error(f"Element finding failed: {str(e)}")
            return None
    
    async def take_screenshot(self, filename: str = None) -> str:
        """Take a screenshot and save it."""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Take screenshot
            self.driver.save_screenshot(filepath)
            
            logger.info(f"Screenshot saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Screenshot failed: {str(e)}")
            return ""
    
    def get_page_source(self) -> str:
        """Get the current page source."""
        try:
            return self.driver.page_source
        except Exception as e:
            logger.error(f"Failed to get page source: {str(e)}")
            return ""
    
    def get_current_url(self) -> str:
        """Get the current URL."""
        try:
            return self.driver.current_url
        except Exception as e:
            logger.error(f"Failed to get current URL: {str(e)}")
            return ""
    
    def get_title(self) -> str:
        """Get the current page title."""
        try:
            return self.driver.title
        except Exception as e:
            logger.error(f"Failed to get page title: {str(e)}")
            return ""
    
    def get_viewport_size(self) -> Dict:
        """Get the current viewport size."""
        try:
            size = self.driver.get_window_size()
            return {"width": size["width"], "height": size["height"]}
        except Exception as e:
            logger.error(f"Failed to get viewport size: {str(e)}")
            return {"width": 0, "height": 0}
    
    async def wait_for_element(self, selector: str, timeout: int = 10) -> bool:
        """Wait for an element to be present and visible."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
            )
            return True
        except TimeoutException:
            logger.warning(f"Element not found within timeout: {selector}")
            return False
        except Exception as e:
            logger.error(f"Wait for element failed: {str(e)}")
            return False
    
    async def wait_for_page_load(self, timeout: int = 30) -> bool:
        """Wait for page to finish loading."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            return True
        except TimeoutException:
            logger.warning("Page load timeout exceeded")
            return False
        except Exception as e:
            logger.error(f"Wait for page load failed: {str(e)}")
            return False
    
    def execute_script(self, script: str, *args) -> any:
        """Execute JavaScript in the browser."""
        try:
            return self.driver.execute_script(script, *args)
        except Exception as e:
            logger.error(f"Script execution failed: {str(e)}")
            return None
    
    async def handle_alert(self, action: str = "accept") -> Dict:
        """Handle JavaScript alert/confirm dialogs."""
        try:
            alert = WebDriverWait(self.driver, 5).until(EC.alert_is_present())
            
            alert_text = alert.text
            
            if action.lower() == "accept":
                alert.accept()
            elif action.lower() == "dismiss":
                alert.dismiss()
            
            return {"success": True, "alert_text": alert_text, "action": action}
            
        except TimeoutException:
            return {"success": False, "error": "No alert present"}
        except Exception as e:
            logger.error(f"Alert handling failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def switch_to_frame(self, frame_selector: str) -> Dict:
        """Switch to an iframe."""
        try:
            frame = self.driver.find_element(By.CSS_SELECTOR, frame_selector)
            self.driver.switch_to.frame(frame)
            return {"success": True}
        except Exception as e:
            logger.error(f"Frame switch failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def switch_to_default_content(self):
        """Switch back to main content from iframe."""
        try:
            self.driver.switch_to.default_content()
        except Exception as e:
            logger.error(f"Switch to default content failed: {str(e)}")
    
    def quit(self):
        """Close the browser and clean up."""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Browser cleanup failed: {str(e)}")

# Helper functions for common browser automation patterns
class BrowserPatterns:
    """Common browser automation patterns and utilities."""
    
    @staticmethod
    async def fill_form(controller: SeleniumController, form_data: Dict[str, str]) -> Dict:
        """Fill out a form with provided data."""
        results = {"success": True, "filled_fields": []}
        
        for field_name, value in form_data.items():
            # Try different selectors for the field
            selectors = [
                f"input[name='{field_name}']",
                f"#{field_name}",
                f"input[id='{field_name}']",
                f"textarea[name='{field_name}']"
            ]
            
            filled = False
            for selector in selectors:
                result = await controller.type_text(selector, value)
                if result["success"]:
                    results["filled_fields"].append(field_name)
                    filled = True
                    break
            
            if not filled:
                results["success"] = False
                results["error"] = f"Could not find field: {field_name}"
                break
        
        return results
    
    @staticmethod
    async def search_and_click(controller: SeleniumController, search_text: str) -> Dict:
        """Search for text on page and click the first matching element."""
        try:
            # Try to find clickable elements containing the text
            elements = controller.driver.find_elements(
                By.XPATH, 
                f"//a[contains(text(), '{search_text}') or contains(@title, '{search_text}')] | //button[contains(text(), '{search_text}')]"
            )
            
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    element.click()
                    return {"success": True, "clicked_text": search_text}
            
            return {"success": False, "error": f"No clickable element found with text: {search_text}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}"Failed to initialize WebDriver: {str(e)}")
            raise Exception(f"Browser initialization failed: {str(e)}")
    
    async def navigate_to(self, url: str) -> Dict:
        """Navigate to a specific URL."""
        try:
            logger.info(f"Navigating to: {url}")
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.driver.get, url)
            
            # Wait for page to load
            await asyncio.sleep(2)
            
            current_url = self.driver.current_url
            logger.info(f"Navigation completed. Current URL: {current_url}")
            
            return {
                "success": True,
                "url": current_url,
                "title": self.driver.title
            }
            
        except Exception as e:
            logger.error(f"Navigation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_interactive_elements(self, limit: int = 20) -> List[Dict]:
        """Get list of interactive elements on the current page."""
        try:
            elements = []
            
            # Common interactive element selectors
            selectors = [
                ("button", "button"),
                ("input[type='submit']", "submit_button"),
                ("input[type='button']", "button"),
                ("a[href]", "link"),
                ("input[type='text']", "text_input"),
                ("input[type='email']", "email_input"),
                ("input[type='password']", "password_input"),
                ("textarea", "textarea"),
                ("select", "select"),
                ("input[type='checkbox']", "checkbox"),
                ("input[type='radio']", "radio"),
            ]
            
            for selector, element_type in selectors:
                try:
                    found_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in found_elements[:5]:  # Limit per type
                        try:
                            if elem.is_displayed() and elem.is_enabled():
                                elem_info = {
                                    "type": element_type,
                                    "tag": elem.tag_name,
                                    "text": elem.text[:100] if elem.text else "",
                                    "id": elem.get_attribute("id") or "",
                                    "class": elem.get_attribute("class") or "",
                                    "name": elem.get_attribute("name") or "",
                                    "placeholder": elem.get_attribute("placeholder") or "",
                                    "href": elem.get_attribute("href") or "",
                                    "css_selector": self._generate_css_selector(elem)
                                }
                                elements.append(elem_info)
                                
                                if len(elements) >= limit:
                                    break
                        except StaleElementReferenceException:
                            continue
                            
                except Exception as e:
                    logger.debug(f"Error finding elements with selector {selector}: {str(e)}")
                    continue
                
                if len(elements) >= limit:
                    break
            
            return elements
            
        except Exception as e:
            logger.error(f"Failed to get interactive elements: {str(e)}")
            return []
    
    def _generate_css_selector(self, element) -> str:
        """Generate a CSS selector for an element."""
        try:
            # Try ID first
            elem_id = element.get_attribute("id")
            if elem_id:
                return f"#{elem_id}"
            
            # Try name attribute
            name = element.get_attribute("name")
            if name:
                return f"[name='{name}']"
            
            # Try class if it's specific enough
            class_name = element.get_attribute("class")
            if class_name and len(class_name.split()) <= 3:
                classes = ".".join(class_name.split())
                return f".{classes}"
            
            # Fallback to tag name with text content
            text = element.text[:30] if element.text else ""
            if text:
                return f"{element.tag_name}:contains('{text}')"
            
            return element.tag_name
            
        except:
            return element.tag_name
    
    async def click_element(self, selector: str, timeout: int = 10) -> Dict:
        """Click an element by CSS selector or description."""
        try:
            logger.info(f"Attempting to click: {selector}")
            
            # Try to find element
            element = await self._find_element(selector, timeout)
            if not element:
                return {"success": False, "error": f"Element not found: {selector}"}
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            await asyncio.sleep(0.5)
            
            # Try different click methods
            try:
                # Standard click
                element.click()
            except ElementClickInterceptedException:
                # Try JavaScript click if regular click is intercepted
                self.driver.execute_script("arguments[0].click();", element)
            
            logger.info(f"Successfully clicked element: {selector}")
            return {"success": True, "selector": selector}
            
        except Exception as e:
            logger.error(f"Click failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def type_text(self, selector: str, text: str, clear_first: bool = True) -> Dict:
        """Type text into an input field."""
        try:
            logger.info(f"Typing text into: {selector}")
            
            element = await self._find_element(selector)
            if not element:
                return {"success": False, "error": f"Element not found: {selector}"}
            
            # Clear field if requested
            if clear_first:
                element.clear()
            
            # Type the text
            element.send_keys(text)
            
            logger.info(f"Successfully typed text into: {selector}")
            return {"success": True, "selector": selector, "text": text}
            
        except Exception as e:
            logger.error(f"Type text failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def scroll(self, direction: str = "down", pixels: int = 500) -> Dict:
        """Scroll the page in specified direction."""
        try:
            if direction.lower() == "down":
                self.driver.execute_script(f"window.scrollBy(0, {pixels});")
            elif direction.lower() == "up":
                self.driver.execute_script(f"window.scrollBy(0, -{pixels});")
            elif direction.lower() == "top":
                self.driver.execute_script("window.scrollTo(0, 0);")
            elif direction.lower() == "bottom":
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            await asyncio.sleep(1)  # Wait for scroll to complete
            return {"success": True, "direction": direction}
            
        except Exception as e:
