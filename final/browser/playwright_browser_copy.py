# Remove footer and redundunt links from results - TODO: may need to be adjusted

from playwright.sync_api import sync_playwright
import time

# Elements that are generally structural or non-interactive, or handled specially
black_listed_elements = set([
    "html", "head", "title", "meta", "iframe", "body", "script", "style",
    "path", "svg", "br", "::marker",
])

# Keywords to identify links that are often part of footers or auxiliary navigation
USELESS_LINK_TEXT_KEYWORDS = [
    "privacy", "policy", "terms", "conditions", "service", "about", "contact", 
    "careers", "sitemap", "help", "faq", "support", "accessibility", "cookie", 
    "feedback", "security", "legal", "developer", "api", "status", "blog",
    "press", "investors", "media", "advertising", "partners"
]
# Patterns in hrefs that often indicate non-primary content links
USELESS_LINK_HREF_PATTERNS = [
    "facebook.com", "twitter.com", "linkedin.com", "instagram.com", 
    "pinterest.com", "tel:", "mailto:", "/legal", "/policy", "/about", "/contact",
    "/terms", "/privacy", "#", "javascript:void(0)" 
    # Removed "youtube.com" as it can be a valid search result
]


class Crawler:
    def __init__(self):
        self.browser = (
            sync_playwright()
            .start()
            .chromium.launch(
                headless=False, # Set to True for no browser window
            )
        )
        self.page = self.browser.new_page()
        # self.page.set_viewport_size({"width": 1280, "height": 1080}) # Optional: set viewport

    def go_to_page(self, url):
        """Navigates to the specified URL."""
        try:
            self.page.goto(url=url if "://" in url else "http://" + url, timeout=60000)
            self.client = self.page.context.new_cdp_session(self.page)
            self.page_element_buffer = {} # Reset buffer for new page
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            if self.browser:
                self.browser.close()
            raise

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
        time.sleep(0.5) # Wait for scroll to complete and content to potentially load

    def click(self, element_id_str):
        """Clicks an element by its assigned ID."""
        try:
            element_id = int(element_id_str)
        except ValueError:
            print(f"Invalid element ID: {element_id_str}. Must be an integer.")
            return

        js_remove_target = """
        links = document.getElementsByTagName("a");
        for (var i = 0; i < links.length; i++) {
            links[i].removeAttribute("target");
        }
        """
        try:
            self.page.evaluate(js_remove_target)
        except Exception as e:
            print(f"Error evaluating JavaScript to remove target attributes: {e}")

        element_data = self.page_element_buffer.get(element_id)
        if element_data:
            x = element_data.get("center_x")
            y = element_data.get("center_y")
            
            if x is not None and y is not None:
                try:
                    print(f"Attempting to click element ID {element_id} at ({x},{y}) - Text: {element_data.get('node_value_str', '')[:50]}")
                    self.page.mouse.click(x, y)
                    # Wait for navigation or significant DOM change, especially after click
                    try:
                        self.page.wait_for_load_state('domcontentloaded', timeout=5000)
                        print(f"Click on ID {element_id}: DOMContentLoaded.")
                    except Exception as e_load:
                        print(f"Click on ID {element_id}: Timeout or error waiting for load state after click: {e_load}. Proceeding.")
                        time.sleep(1) # Fallback sleep
                except Exception as e:
                    print(f"Error clicking element {element_id} at ({x},{y}): {e}")
            else:
                print(f"Element {element_id} has no center coordinates.")
        else:
            print(f"Could not find element with ID: {element_id}")

    def type(self, element_id_str, text_to_type):
        """Clicks an element and then types text into it."""
        self.click(element_id_str) 
        # Check if click opened a new page or changed context significantly before typing
        # For simplicity, assuming click focuses correctly.
        try:
            element_data = self.page_element_buffer.get(int(element_id_str))
            if element_data:
                 # Re-fetch the element through Playwright to ensure it's still attached and typeable
                # This is more robust but adds overhead. For now, we rely on the click focusing.
                print(f"Attempting to type '{text_to_type}' into element ID {element_id_str}")
            self.page.keyboard.type(text_to_type, delay=50) 
            time.sleep(0.5) 
        except Exception as e:
            print(f"Error typing into element {element_id_str}: {e}")

    def enter(self):
        """Presses the Enter key."""
        try:
            self.page.keyboard.press("Enter")
            try:
                self.page.wait_for_load_state('domcontentloaded', timeout=5000)
                print("Enter pressed: DOMContentLoaded.")
            except Exception as e_load:
                print(f"Enter pressed: Timeout or error waiting for load state: {e_load}. Proceeding.")
                time.sleep(1) # Fallback sleep
        except Exception as e:
            print(f"Error pressing Enter: {e}")
    def type_and_submit(self, element_id_str, text_to_type):
        try:
            self.type(element_id_str, text_to_type)
            self.enter()
        except Exception as e:
            print(f"Error pressing Enter: {e}")

    def crawl(self):
        """
        Captures a DOM snapshot, processes it to find interactable elements in the current viewport,
        filters out footer content and useless links, and returns a list of strings 
        representing these elements.
        """
        page = self.page
        self.page_element_buffer.clear() 
        start_time = time.time()

        try:
            # Ensure page is somewhat settled before snapshot
            page.wait_for_timeout(100) # Small delay for any immediate JS execution
            device_pixel_ratio = page.evaluate("window.devicePixelRatio")
            if device_pixel_ratio == 0: device_pixel_ratio = 1

            win_scroll_x = page.evaluate("window.pageXOffset")
            win_scroll_y = page.evaluate("window.pageYOffset")
            viewport_width = page.evaluate("window.innerWidth")
            viewport_height = page.evaluate("window.innerHeight")

            win_left_bound = win_scroll_x
            win_right_bound = win_scroll_x + viewport_width
            win_upper_bound = win_scroll_y
            win_lower_bound = win_scroll_y + viewport_height
            
            # ... (scrollbar calculation remains the same) ...

            tree = self.client.send(
                "DOMSnapshot.captureSnapshot",
                {"computedStyles": [], "includeDOMRects": True, "includePaintOrder": True},
            )
        except Exception as e:
            print(f"Error during page evaluation or DOM snapshot: {e}")
            return []

        strings = tree["strings"]
        document = tree["documents"][0]
        nodes = document["nodes"]
        layout = document["layout"]

        node_name_indices = nodes["nodeName"]
        node_value_indices = nodes["nodeValue"]
        parent_indices = nodes["parentIndex"]
        backend_node_ids = nodes["backendNodeId"]
        attributes_indices = nodes["attributes"]
        
        clickable_node_indices = set(nodes.get("isClickable", {}).get("index", []))

        text_value_map = {idx: val for idx, val in zip(nodes["textValue"]["index"], nodes["textValue"]["value"])}
        input_value_map = {idx: val for idx, val in zip(nodes["inputValue"]["index"], nodes["inputValue"]["value"])}

        layout_node_map = {node_idx: bound_idx for bound_idx, node_idx in enumerate(layout["nodeIndex"])}
        bounds_list = layout["bounds"]

        elements_in_view_port = []
        child_nodes_text_and_attrs = {} 

        anchor_ancestry = {"-1": (False, None)} 
        button_ancestry = {"-1": (False, None)}
        footer_ancestry = {"-1": (False, None)} 

        def convert_node_name_type(node_name_str, is_node_clickable):
            if node_name_str == "a": return "link"
            if node_name_str == "input": return "input"
            if node_name_str == "textarea": return "textarea"
            if node_name_str == "img": return "img"
            if node_name_str == "button" or is_node_clickable: return "button"
            return "text"

        def get_attributes_dict(attr_indices_for_node, string_array):
            attrs_to_extract = ["type", "placeholder", "aria-label", "title", "alt", "role", "name", "href", "value", "id", "class"]
            found_attrs = {}
            for i in range(0, len(attr_indices_for_node), 2):
                key_idx = attr_indices_for_node[i]
                value_idx = attr_indices_for_node[i+1]
                if key_idx < len(string_array) and value_idx < len(string_array) and value_idx >=0:
                    key = string_array[key_idx]
                    if key in attrs_to_extract:
                        found_attrs[key] = string_array[value_idx]
            return found_attrs

        def build_ancestry_map(ancestry_dict, target_tag, current_node_idx, current_node_name_str, current_parent_idx):
            parent_idx_str = str(current_parent_idx)
            if parent_idx_str not in ancestry_dict: 
                if current_parent_idx >= 0 and current_parent_idx < len(node_name_indices):
                    parent_name_str = strings[node_name_indices[current_parent_idx]].lower()
                    grandparent_idx = parent_indices[current_parent_idx]
                    build_ancestry_map(ancestry_dict, target_tag, current_parent_idx, parent_name_str, grandparent_idx)
                else: 
                    ancestry_dict[parent_idx_str] = (False, None)

            is_parent_descendant, ultimate_ancestor_id = ancestry_dict.get(parent_idx_str, (False, None))

            is_semantic_footer = False
            if target_tag == "footer": 
                node_specific_attr_indices = attributes_indices[current_node_idx]
                raw_attrs = get_attributes_dict(node_specific_attr_indices, strings)
                node_id_attr = raw_attrs.get("id","").lower()
                node_class_attr = raw_attrs.get("class","").lower().split()
                if raw_attrs.get("role") == "contentinfo" or \
                   node_id_attr == "footer" or "site-footer" in node_id_attr or \
                   "footer" in node_class_attr or "site-footer" in node_class_attr or "colophon" in node_class_attr : # Common WP footer class
                    is_semantic_footer = True

            if current_node_name_str == target_tag or is_semantic_footer:
                value_to_set = (True, current_node_idx)
            elif is_parent_descendant:
                value_to_set = (True, ultimate_ancestor_id)
            else:
                value_to_set = (False, None)
            
            ancestry_dict[str(current_node_idx)] = value_to_set
            return value_to_set

        # First pass: Iterate over all nodes
        for i in range(len(node_name_indices)):
            node_name_str = strings[node_name_indices[i]].lower()
            node_parent_idx = parent_indices[i]

            is_desc_of_anchor, anchor_id = build_ancestry_map(anchor_ancestry, "a", i, node_name_str, node_parent_idx)
            is_desc_of_button, button_id = build_ancestry_map(button_ancestry, "button", i, node_name_str, node_parent_idx)
            build_ancestry_map(footer_ancestry, "footer", i, node_name_str, node_parent_idx)
            
            if node_name_str in black_listed_elements:
                continue

            layout_idx = layout_node_map.get(i)
            if layout_idx is None:
                continue

            x, y, width, height = bounds_list[layout_idx]
            x /= device_pixel_ratio
            y /= device_pixel_ratio
            width /= device_pixel_ratio
            height /= device_pixel_ratio

            in_viewport = (
                x < win_right_bound and (x + width) > win_left_bound and
                y < win_lower_bound and (y + height) > win_upper_bound and
                width > 1 and height > 1 # Ensure minimal dimensions
            )

            if not in_viewport:
                continue
            
            node_specific_attr_indices = attributes_indices[i] 
            raw_attrs = get_attributes_dict(node_specific_attr_indices, strings)
            
            meta_data_kv_strings = []
            for k, v_raw in raw_attrs.items():
                v = ' '.join(v_raw.split())
                meta_data_kv_strings.append(f'{k}="{v}"')

            actual_node_value = None
            if node_value_indices[i] >= 0: 
                actual_node_value = strings[node_value_indices[i]]
            elif i in input_value_map and input_value_map[i] >=0: 
                 actual_node_value = strings[input_value_map[i]]
            elif i in text_value_map and text_value_map[i] >=0: 
                 actual_node_value = strings[text_value_map[i]]

            is_ancestor_exception = is_desc_of_anchor or is_desc_of_button
            ancestor_node_id_for_grouping = anchor_id if is_desc_of_anchor else (button_id if is_desc_of_button else None)

            if node_name_str == "#text" and ancestor_node_id_for_grouping is not None:
                text_content = actual_node_value
                if text_content and text_content.strip() and text_content.strip() not in ["|", "•"]:
                    child_nodes_text_and_attrs.setdefault(str(ancestor_node_id_for_grouping), []).append({
                        "type": "text_content", "value": ' '.join(text_content.split()) 
                    })
                continue 

            if is_ancestor_exception and \
               node_name_str not in ["a", "button", "input", "textarea", "img"] and \
               i != ancestor_node_id_for_grouping: 
                if meta_data_kv_strings: 
                     child_nodes_text_and_attrs.setdefault(str(ancestor_node_id_for_grouping), []).extend(
                         [{"type": "attribute", "key": k, "value": v} for k,v in raw_attrs.items()]
                     )
                continue

            element_data = {
                "node_index_str": str(i),
                "backend_node_id": backend_node_ids[i],
                "node_name_str": node_name_str,
                "node_value_str": ' '.join(actual_node_value.split()) if actual_node_value else None, 
                "meta_strings": meta_data_kv_strings, 
                "raw_attrs": raw_attrs, 
                "is_clickable_flag": i in clickable_node_indices or node_name_str in ["a", "button", "input", "textarea"],
                "origin_x": int(x), "origin_y": int(y),
                "center_x": int(x + (width / 2)), "center_y": int(y + (height / 2)),
            }
            elements_in_view_port.append(element_data)

        # Second pass: Filter and format elements
        elements_of_interest = []
        id_counter = 0
        
        for elem_data in elements_in_view_port:
            node_idx_str = elem_data["node_index_str"]
            original_node_name = elem_data["node_name_str"]
            node_val = elem_data["node_value_str"] 
            is_clickable_direct = elem_data["is_clickable_flag"]
            raw_attrs_for_elem = elem_data["raw_attrs"]

            # Determine output_tag_name early for filtering
            final_elem_type = original_node_name
            if original_node_name == "input":
                type_attr = raw_attrs_for_elem.get("type")
                if type_attr in ["submit", "button", "reset", "image"]: 
                    final_elem_type = "button"
            output_tag_name = convert_node_name_type(final_elem_type, is_clickable_direct)

            # Filter 1: Skip elements in footer
            is_in_footer = footer_ancestry.get(node_idx_str, (False, None))[0]
            if is_in_footer:
                # print(f"DEBUG: Skipping element in footer: ID {node_idx_str} name {original_node_name} text: {node_val[:50] if node_val else ''}")
                continue
            
            # Consolidate text
            combined_inner_text_parts = []
            if node_val:
                combined_inner_text_parts.append(node_val)

            if node_idx_str in child_nodes_text_and_attrs:
                for child_item in child_nodes_text_and_attrs[node_idx_str]:
                    if child_item["type"] == "text_content":
                        combined_inner_text_parts.append(child_item["value"])
            final_inner_text = " ".join(combined_inner_text_parts).strip()

            # Consolidate meta strings
            current_meta_strings = list(elem_data["meta_strings"]) 
            if node_idx_str in child_nodes_text_and_attrs:
                 for child_item in child_nodes_text_and_attrs[node_idx_str]:
                    if child_item["type"] == "attribute":
                        child_attr_val_sanitized = ' '.join(child_item["value"].split())
                        current_meta_strings.append(f'{child_item["key"]}="{child_attr_val_sanitized}"')
            unique_meta_strings = sorted(list(set(current_meta_strings)))
            meta_attr_string = (" " + " ".join(unique_meta_strings)) if unique_meta_strings else ""


            # Filter 2: Useless Link Filtering
            if output_tag_name == "link":
                lower_final_inner_text = final_inner_text.lower()
                is_short_generic_link = len(final_inner_text.split()) <= 3 
                if is_short_generic_link and any(keyword in lower_final_inner_text for keyword in USELESS_LINK_TEXT_KEYWORDS):
                    # print(f"DEBUG: Skipping useless link by text (short & generic): '{final_inner_text}'")
                    continue
                
                href_val = raw_attrs_for_elem.get("href")
                if href_val:
                    lower_href_val = href_val.lower()
                    if any(pattern in lower_href_val for pattern in USELESS_LINK_HREF_PATTERNS):
                        # print(f"DEBUG: Skipping useless link by href: '{href_val}'")
                        continue
            
            # Filter 3: Strict removal of empty "text" elements
            if output_tag_name == "text" and not final_inner_text: # final_inner_text is already stripped
                # print(f"DEBUG: Skipping empty text element (id={id_counter})")
                continue

            # Filter 4: Links or buttons must have text OR a significant accessibility attribute
            if output_tag_name in ["link", "button"] and not final_inner_text:
                aria_label = raw_attrs_for_elem.get("aria-label","").strip()
                title_attr = raw_attrs_for_elem.get("title","").strip()
                if not aria_label and not title_attr:
                    # print(f"DEBUG: Skipping {output_tag_name} (id={id_counter}) with no text, aria-label, or title.")
                    continue
            
            # Filter 5: General catch-all for other non-essential elements that are empty
            # (i.e., not input, textarea, img, and already passed link/button/text checks)
            # if they lack both text and metadata.
            if output_tag_name not in ["input", "textarea", "img", "link", "button", "text"] and \
               not final_inner_text and \
               not meta_attr_string.strip():
                # print(f"DEBUG: Skipping other empty element type {output_tag_name} (id={id_counter}) with no text and no meta.")
                continue
                
            # If element has survived all filters, add it
            self.page_element_buffer[id_counter] = elem_data 

            if final_inner_text:
                elements_of_interest.append(
                    f"<{output_tag_name} id={id_counter}{meta_attr_string}>{final_inner_text}</{output_tag_name}>"
                )
            else: # For elements like <input/> or <img/> that don't have closing tags with text but passed filters
                elements_of_interest.append(
                    f"<{output_tag_name} id={id_counter}{meta_attr_string}/>"
                )
            id_counter += 1
        
        print(f"Parsing time: {time.time() - start_time:.2f} seconds. Found {len(elements_of_interest)} elements after filtering.")
        return elements_of_interest

    def close(self):
        if self.browser:
            self.browser.close()

if __name__ == "__main__":
    crawler = Crawler()
    try:
        print("\n--- Testing on DuckDuckGo (Initial Page) ---")
        crawler.go_to_page("duckduckgo.com")
        elements_ddg_initial = crawler.crawl()
        if not elements_ddg_initial:
            print("No elements found on DuckDuckGo (Initial) or crawl failed.")
        else:
            print("\n--- Crawled Elements (DuckDuckGo Initial) ---")
            for ele_str in elements_ddg_initial:
                print(ele_str)
            print(f"--- End of Crawled Elements (DuckDuckGo Initial) - Count: {len(elements_ddg_initial)} ---\n")

            search_input_id = None
            search_button_id = None
            
            # Find search input and button from the initial crawl
            for el_str in elements_ddg_initial: 
                try:
                    current_id_match = el_str.split("id=")[1].split(" ")[0].split(">")[0].replace("/", "")
                    if not current_id_match.isdigit(): continue
                    current_id = int(current_id_match)

                    raw_attrs_for_current_element = crawler.page_element_buffer.get(current_id, {}).get("raw_attrs", {})
                    
                    if ("<input" in el_str or "<textarea" in el_str) and \
                       (raw_attrs_for_current_element.get("name") == "q" or \
                        "search" in raw_attrs_for_current_element.get("placeholder","").lower() or "search" in raw_attrs_for_current_element.get("aria-label","").lower()):
                        search_input_id = current_id
                        print(f"Found search input: id={search_input_id}, element: {el_str}")

                    is_button_tag = "<button" in el_str
                    is_input_button_type = ("<input" in el_str and raw_attrs_for_current_element.get("type") in ["submit", "button"])
                    
                    if (is_button_tag or is_input_button_type) and \
                       ("search" in raw_attrs_for_current_element.get("aria-label","").lower() or \
                        raw_attrs_for_current_element.get("id","").lower() == "search_button" or \
                        raw_attrs_for_current_element.get("id","").lower() == "search_button_homepage" or \
                        el_str.endswith("Search</button>") or ">S</button>" in el_str or 'value="S"' in el_str):
                        if not (search_input_id is not None and current_id == search_input_id) :
                             search_button_id = current_id
                             print(f"Found search button: id={search_button_id}, element: {el_str}")
                except Exception as e_parse:
                    print(f"Error parsing element string for ID: {el_str[:100]}... - {e_parse}")


            if search_input_id is not None:
                print(f"\nTyping 'Playwright library python' into search input (id={search_input_id})...")
                crawler.type_and_submit(str(search_input_id), "Playwright library python")
             
                time.sleep(1) 

                print("\n--- Crawling Elements after search (DuckDuckGo) ---")
                elements_after_search = crawler.crawl()
                if not elements_after_search:
                    print("No elements found after search or crawl failed.")
                else:
                    for ele_str in elements_after_search:
                        print(ele_str)
                    print(f"--- End of Elements after search (DuckDuckGo) - Count: {len(elements_after_search)} ---\n")
            else:
                print("Could not find the search input field on DuckDuckGo to type into.")

    except Exception as e:
        print(f"An error occurred in the main execution: {e}")
    finally:
        print("Closing browser...")
        crawler.close()
