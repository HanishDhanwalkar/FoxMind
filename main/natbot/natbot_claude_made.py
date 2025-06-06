import requests
import json
import time
from sys import argv, exit
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import re

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"  # Change this to your preferred model

quiet = False
if len(argv) >= 2:
    if argv[1] == '-q' or argv[1] == '--quiet':
        quiet = True
        print(
            "Running in quiet mode (HTML and other content hidden); \n"
            + "exercise caution when running suggested commands."
        )

prompt_template = """
You are an agent controlling a browser. You are given:

    (1) an objective that you are trying to achieve
    (2) the URL of your current web page
    (3) a simplified text description of what's visible in the browser window (more on that below)

You can issue these commands:
    SCROLL UP - scroll up one page
    SCROLL DOWN - scroll down one page
    CLICK X - click on a given element. You can only click on links, buttons, and inputs!
    TYPE X "TEXT" - type the specified text into the input with id X
    TYPESUBMIT X "TEXT" - same as TYPE above, except then it presses ENTER to submit the form

The format of the browser content is highly simplified; all formatting elements are stripped.
Interactive elements such as links, inputs, buttons are represented like this:

        <link id=1>text</link>
        <button id=2>text</button>
        <input id=3>text</input>

Images are rendered as their alt text like this:

        <img id=4 alt=""/>

Based on your given objective, issue whatever command you believe will get you closest to achieving your goal.
You always start on duckduckgo; you should submit a search query to duckduckgo that will take you to the best page for
achieving your objective. And then interact with that page to achieve your objective.

If you find yourself on duckduckgo and there are no search results displayed yet, you should probably issue a command 
like "TYPESUBMIT 7 "search query"" to get to a more useful page.

Then, if you find yourself on a duckduckgo search results page, you might issue the command "CLICK 24" to click
on the first link in the search results. (If your previous command was a TYPESUBMIT your next command should
probably be a CLICK.)

Don't try to interact with elements that you can't see.

Here are some examples:

EXAMPLE 1:
==================================================
CURRENT BROWSER CONTENT:
------------------
<link id=1>About</link>
<link id=2>Store</link>
<link id=3>Gmail</link>
<link id=4>Images</link>
<link id=5>(duckduckgo apps)</link>
<link id=6>Sign in</link>
<img id=7 alt="(duckduckgo)"/>
<input id=8 alt="Search"></input>
<button id=9>(Search by voice)</button>
<button id=10>(duckduckgo Search)</button>
<button id=11>(I'm Feeling Lucky)</button>
<link id=12>Advertising</link>
<link id=13>Business</link>
<link id=14>How Search works</link>
<link id=15>Carbon neutral since 2007</link>
<link id=16>Privacy</link>
<link id=17>Terms</link>
<text id=18>Settings</text>
------------------
OBJECTIVE: Find a 2 bedroom house for sale in Anchorage AK for under $750k
CURRENT URL: https://www.duckduckgo.com/
YOUR COMMAND: 
TYPESUBMIT 8 "anchorage redfin"
==================================================

EXAMPLE 2:
==================================================
CURRENT BROWSER CONTENT:
------------------
<link id=1>About</link>
<link id=2>Store</link>
<link id=3>Gmail</link>
<link id=4>Images</link>
<link id=5>(duckduckgo apps)</link>
<link id=6>Sign in</link>
<img id=7 alt="(Duckduckgo)"/>
<input id=8 alt="Search"></input>
<button id=9>(Search by voice)</button>
<button id=10>(Duckduckgo Search)</button>
<button id=11>(I'm Feeling Lucky)</button>
<link id=12>Advertising</link>
<link id=13>Business</link>
<link id=14>How Search works</link>
<link id=15>Carbon neutral since 2007</link>
<link id=16>Privacy</link>
<link id=17>Terms</link>
<text id=18>Settings</text>
------------------
OBJECTIVE: Make a reservation for 4 at Dorsia at 8pm
CURRENT URL: https://www.duckduckgo.com/
YOUR COMMAND: 
TYPESUBMIT 8 "dorsia nyc opentable"
==================================================

EXAMPLE 3:
==================================================
CURRENT BROWSER CONTENT:
------------------
<button id=1>For Businesses</button>
<button id=2>Mobile</button>
<button id=3>Help</button>
<button id=4 alt="Language Picker">EN</button>
<link id=5>OpenTable logo</link>
<button id=6 alt ="search">Search</button>
<text id=7>Find your table for any occasion</text>
<button id=8>(Date selector)</button>
<text id=9>Sep 28, 2022</text>
<text id=10>7:00 PM</text>
<text id=11>2 people</text>
<input id=12 alt="Location, Restaurant, or Cuisine"></input> 
<button id=13>Let's go</button>
<text id=14>It looks like you're in Peninsula. Not correct?</text> 
<button id=15>Get current location</button>
<button id=16>Next</button>
------------------
OBJECTIVE: Make a reservation for 4 for dinner at Dorsia in New York City at 8pm
CURRENT URL: https://www.opentable.com/
YOUR COMMAND: 
TYPESUBMIT 12 "dorsia new york city"
==================================================

The current browser content, objective, and current URL follow. Reply with your next command to the browser.

CURRENT BROWSER CONTENT:
------------------
$browser_content
------------------

OBJECTIVE: $objective
CURRENT URL: $url
PREVIOUS COMMAND: $previous_command
YOUR COMMAND:
"""

# Elements to ignore when parsing
BLACKLISTED_ELEMENTS = {
    'html', 'head', 'title', 'meta', 'iframe', 'body', 'script', 'style', 
    'path', 'svg', 'br', 'noscript', 'header', 'footer', 'nav'
}

class OllamaCrawler:
    def __init__(self):
        self.setup_driver()
        self.element_buffer = {}
        
    def setup_driver(self):
        """Initialize Browser driver with appropriate options"""
        browser_options = Options()
        browser_options.add_argument("--no-sandbox")
        browser_options.add_argument("--disable-dev-shm-usage")
        browser_options.add_argument("--disable-blink-features=AutomationControlled")
        # browser_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # browser_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Firefox(options=browser_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # self.driver.set_window_size(1280, 1080)
        self.wait = WebDriverWait(self.driver, 10)
        
    def go_to_page(self, url):
        """Navigate to a URL"""
        if "://" not in url:
            url = "http://" + url
        self.driver.get(url)
        time.sleep(2)
        
    def scroll(self, direction):
        """Scroll the page up or down"""
        if direction == "up":
            self.driver.execute_script("window.scrollBy(0, -window.innerHeight);")
        elif direction == "down":
            self.driver.execute_script("window.scrollBy(0, window.innerHeight);")
        time.sleep(1)
        
    def click(self, element_id):
        """Click on an element by its ID"""
        try:
            element_info = self.element_buffer.get(int(element_id))
            if element_info and 'element' in element_info:
                element = element_info['element']
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)
                
                # Try regular click first
                try:
                    element.click()
                except:
                    # If regular click fails, try JavaScript click
                    self.driver.execute_script("arguments[0].click();", element)
            else:
                print(f"Could not find element with id {element_id}")
        except Exception as e:
            print(f"Error clicking element {element_id}: {e}")
            
    def type(self, element_id, text):
        """Type text into an input element"""
        try:
            element_info = self.element_buffer.get(int(element_id))
            if element_info and 'element' in element_info:
                element = element_info['element']
                # Clear the field first
                element.clear()
                element.send_keys(text)
            else:
                print(f"Could not find input element with id {element_id}")
        except Exception as e:
            print(f"Error typing into element {element_id}: {e}")
            
    def type_and_submit(self, element_id, text):
        """Type text and press enter"""
        self.type(element_id, text)
        try:
            element_info = self.element_buffer.get(int(element_id))
            if element_info and 'element' in element_info:
                element = element_info['element']
                element.send_keys(Keys.RETURN)
        except Exception as e:
            print(f"Error submitting element {element_id}: {e}")
            
    def is_element_visible(self, element):
        """Check if an element is visible on the page"""
        try:
            return (element.is_displayed() and 
                   element.size['height'] > 0 and 
                   element.size['width'] > 0)
        except:
            return False
            
    def get_element_text(self, element):
        """Get text content from an element"""
        try:
            # Try different methods to get text
            text = element.text.strip()
            if not text:
                text = element.get_attribute('value') or ''
            if not text:
                text = element.get_attribute('placeholder') or ''
            if not text:
                text = element.get_attribute('alt') or ''
            if not text:
                text = element.get_attribute('title') or ''
            return text.strip()
        except:
            return ""
            
    def crawl(self):
        """Parse the current page and return simplified HTML"""
        start_time = time.time()
        
        # Get page source and parse with BeautifulSoup
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
            
        # Find all interactive elements
        interactive_selectors = [
            'a', 'button', 'input', 'select', 'textarea', 'img',
            '[onclick]', '[role="button"]', '[role="link"]'
        ]
        
        elements_of_interest = []
        self.element_buffer = {}
        id_counter = 0
        
        # Get all elements using Selenium for better interaction
        all_elements = self.driver.find_elements(By.XPATH, "//*")
        
        for element in all_elements:
            try:
                tag_name = element.tag_name.lower()
                
                # Skip blacklisted elements
                if tag_name in BLACKLISTED_ELEMENTS:
                    continue
                    
                # Check if element is visible and has reasonable size
                if not self.is_element_visible(element):
                    continue
                    
                # Get element text
                text = self.get_element_text(element)
                
                # Classify element type
                element_type = self.classify_element(element, tag_name)
                
                # Skip if not interactive and no meaningful text
                if element_type == "text" and not text:
                    continue
                    
                # Skip very long text elements (likely not important for interaction)
                if len(text) > 200:
                    text = text[:200] + "..."
                    
                # Store element reference
                self.element_buffer[id_counter] = {
                    'element': element,
                    'tag_name': tag_name,
                    'text': text,
                    'type': element_type
                }
                
                # Format for output
                if text:
                    formatted_element = f"<{element_type} id={id_counter}>{text}</{element_type}>"
                else:
                    # For elements without text (like images), include attributes
                    attrs = self.get_relevant_attributes(element)
                    attr_str = f' {attrs}' if attrs else ''
                    formatted_element = f"<{element_type} id={id_counter}{attr_str}/>"
                    
                elements_of_interest.append(formatted_element)
                id_counter += 1
                
                # Limit to prevent token overflow
                if id_counter >= 100:
                    break
                    
            except Exception as e:
                continue
                
        print(f"Parsing time: {time.time() - start_time:.2f} seconds")
        return elements_of_interest[:50]  # Limit to first 50 elements
        
    def classify_element(self, element, tag_name):
        """Classify element type for the LLM"""
        if tag_name == 'a':
            return 'link'
        elif tag_name == 'button' or element.get_attribute('role') == 'button':
            return 'button'
        elif tag_name in ['input', 'textarea', 'select']:
            return 'input'
        elif tag_name == 'img':
            return 'img'
        else:
            # Check if element is clickable
            onclick = element.get_attribute('onclick')
            cursor = element.value_of_css_property('cursor')
            if onclick or cursor == 'pointer':
                return 'button'
            return 'text'
            
    def get_relevant_attributes(self, element):
        """Get relevant attributes for display"""
        attrs = []
        for attr in ['alt', 'placeholder', 'title', 'aria-label']:
            value = element.get_attribute(attr)
            if value:
                attrs.append(f'{attr}="{value[:50]}"')
        return ' '.join(attrs)
        
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'driver'):
            self.driver.quit()

def call_ollama(prompt):
    """Make a request to Ollama API"""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 100
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '').strip()
        else:
            print(f"Ollama API error: {response.status_code}")
            return ""
            
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama: {e}")
        return ""

def get_llm_command(objective, url, previous_command, browser_content):
    """Get command from LLM"""
    prompt = prompt_template
    prompt = prompt.replace("$objective", objective)
    prompt = prompt.replace("$url", url[:100])
    prompt = prompt.replace("$previous_command", previous_command)
    prompt = prompt.replace("$browser_content", browser_content[:4000])
    
    response = call_ollama(prompt)
    
    # Extract just the command from the response
    lines = response.split('\n')
    for line in lines:
        line = line.strip()
        if (line.startswith('SCROLL') or line.startswith('CLICK') or 
            line.startswith('TYPE') or line.startswith('TYPESUBMIT')):
            return line
            
    return response.split('\n')[0].strip() if response else ""

def run_cmd(crawler, cmd):
    """Execute a command"""
    cmd = cmd.split("\n")[0].strip()
    
    if cmd.startswith("SCROLL UP"):
        crawler.scroll("up")
    elif cmd.startswith("SCROLL DOWN"):
        crawler.scroll("down")
    elif cmd.startswith("CLICK"):
        try:
            parts = cmd.split(" ")
            element_id = parts[1]
            crawler.click(element_id)
        except (IndexError, ValueError) as e:
            print(f"Invalid CLICK command: {cmd}")
    elif cmd.startswith("TYPESUBMIT"):
        try:
            parts = cmd.split(" ", 2)
            element_id = parts[1]
            text = parts[2].strip('"')
            crawler.type_and_submit(element_id, text)
        except (IndexError, ValueError) as e:
            print(f"Invalid TYPESUBMIT command: {cmd}")
    elif cmd.startswith("TYPE"):
        try:
            parts = cmd.split(" ", 2)
            element_id = parts[1]
            text = parts[2].strip('"')
            crawler.type(element_id, text)
        except (IndexError, ValueError) as e:
            print(f"Invalid TYPE command: {cmd}")
    
    time.sleep(2)

def print_help():
    print(
        "(g) to visit url\n(u) scroll up\n(d) scroll down\n(c) to click\n(t) to type\n" +
        "(h) to view commands again\n(r/enter) to run suggested command\n(o) change objective\n(q) to quit"
    )

def main():
    # Test Ollama connection
    try:
        test_response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if test_response.status_code != 200:
            print("Error: Cannot connect to Ollama. Make sure it's running on localhost:11434")
            exit(1)
    except requests.exceptions.RequestException:
        print("Error: Cannot connect to Ollama. Make sure it's running on localhost:11434")
        exit(1)
    
    crawler = OllamaCrawler()
    
    try:
        objective = "Make a reservation for 2 at 7pm at bistro vida in menlo park"
        print(f"\nWelcome to Ollama Natbot! Using model: {OLLAMA_MODEL}")
        print("What is your objective?")
        user_input = input().strip()
        if user_input:
            objective = user_input
            
        llm_cmd = ""
        prev_cmd = ""
        crawler.go_to_page("duckduckgo.com") 
        
        while True:
            try:
                browser_content = "\n".join(crawler.crawl())
                prev_cmd = llm_cmd
                llm_cmd = get_llm_command(objective, crawler.driver.current_url, prev_cmd, browser_content)
                
                if not quiet:
                    print(f"\nURL: {crawler.driver.current_url}")
                    print(f"Objective: {objective}")
                    print("----------------")
                    print(browser_content[:1000] + "..." if len(browser_content) > 1000 else browser_content)
                    print("----------------")
                    
                if llm_cmd:
                    print(f"Suggested command: {llm_cmd}")
                else:
                    print("No command suggested")
                    
                command = input("Command (h for help): ").strip()
                
                if command == "r" or command == "":
                    if llm_cmd:
                        run_cmd(crawler, llm_cmd)
                elif command == "g":
                    url = input("URL: ")
                    crawler.go_to_page(url)
                elif command == "u":
                    crawler.scroll("up")
                elif command == "d":
                    crawler.scroll("down")
                elif command == "c":
                    element_id = input("Element ID: ")
                    crawler.click(element_id)
                elif command == "t":
                    element_id = input("Element ID: ")
                    text = input("Text: ")
                    crawler.type(element_id, text)
                elif command == "o":
                    objective = input("New objective: ")
                elif command == "q":
                    break
                elif command == "h":
                    print_help()
                else:
                    print_help()
                    
            except Exception as e:
                print(f"Error: {e}")
                continue
                
    except KeyboardInterrupt:
        print("\n[!] Ctrl+C detected, exiting gracefully.")
    finally:
        crawler.cleanup()

if __name__ == "__main__":
    main()