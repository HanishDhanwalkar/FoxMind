from playwright.sync_api import sync_playwright
import time
import argparse


class Crawler:
    def __init__(self):
        self.browser = (
            sync_playwright()
            .start()
            .chromium.launch(
                headless=False,  # Set to True for no browser window
            )
        )
        self.page = self.browser.new_page()
        # self.page.set_viewport_size({"width": 1280, "height": 1080}) # Optional: set viewport
        self.black_listed_elements = set([
			"html", "head", "title", "meta", "iframe", "body", "script", "style", "path", "svg", "br", "::marker"
   		])

    def go_to_page(self, url):
        """Navigates to the specified URL."""
        try:
            self.page.goto(
                url=url if "://" in url else "http://" + url, timeout=60000)
            self.client = self.page.context.new_cdp_session(self.page)
            self.page_element_buffer = {}  # Reset buffer for new page
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            # Potentially close browser or handle error appropriately
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
        # Wait for scroll to complete and content to potentially load
        time.sleep(0.5)

    def click(self, element_id_str):
        """Clicks an element by its assigned ID."""
        try:
            element_id = int(element_id_str)
        except ValueError:
            print(f"Invalid element ID: {element_id_str}. Must be an integer.")
            return

        # Inject JavaScript to remove target="_blank" from links to ensure navigation in the same tab
        js_remove_target = """
        links = document.getElementsByTagName("a");
        for (var i = 0; i < links.length; i++) {
            links[i].removeAttribute("target");
        }
        """
        try:
            self.page.evaluate(js_remove_target)
        except Exception as e:
            print(
                f"Error evaluating JavaScript to remove target attributes: {e}")

        element_data = self.page_element_buffer.get(element_id)
        if element_data:
            x = element_data.get("center_x")
            y = element_data.get("center_y")

            if x is not None and y is not None:
                try:
                    self.page.mouse.click(x, y)
                    # Wait for potential navigation or DOM changes
                    time.sleep(1)
                except Exception as e:
                    print(
                        f"Error clicking element {element_id} at ({x},{y}): {e}")
            else:
                print(f"Element {element_id} has no center coordinates.")
        else:
            print(f"Could not find element with ID: {element_id}")

    def type(self, element_id_str, text_to_type):
        """Clicks an element and then types text into it."""
        self.click(element_id_str)  # Click to focus
        try:
            # Add a small delay between key presses
            self.page.keyboard.type(text_to_type, delay=20)
            time.sleep(0.5)  # Wait for text to be processed
        except Exception as e:
            print(f"Error typing into element {element_id_str}: {e}")

    def enter(self):
        """Presses the Enter key."""
        try:
            self.page.keyboard.press("Enter")
            time.sleep(1)  # Wait for potential form submission or navigation
        except Exception as e:
            print(f"Error pressing Enter: {e}")

    def type_and_submit(self, element_id_str, text_to_type):
        # """Clicks an element, types text into it, and then presses Enter."""
        # if "<input" in element_id_str and ('Search' in element_id_str or 'name="q"' in element_id_str):
        #     search_input_id = current_id
        #     print(f"Found search input: id={search_input_id}, element: {element_id_str}")
        # elif "<textarea" in el_str and 'name="q"' in el_str:
        #     search_input_id = current_id
        #     print(f"Found search input: id={search_input_id}, element: {element_id_str}")
        # self.enter()
        try:
            self.type(element_id_str, text_to_type)
            self.enter()
        except Exception as e:
            print(f"Error pressing Enter: {e}")
        
        
    def broswer_actions_options(self):
        options = {"type": self.type,
                   "type_and_submit": self.type_and_submit,
                   "click": self.click,
				   "scroll": self.scroll,
				   }

    def crawl(self):
        """
        Captures a DOM snapshot, processes it to find interactable elements in the current viewport,
        and returns a list of strings representing these elements.
        """
        page = self.page
        self.page_element_buffer.clear() # Clear buffer for new crawl results
        start_time = time.time()

        page_state_as_text = [] # For scrollbar info, not directly part of main output yet

        try:
            device_pixel_ratio = page.evaluate("window.devicePixelRatio")
            if device_pixel_ratio == 0: device_pixel_ratio = 1 # Avoid division by zero

            # Viewport dimensions and scroll position
            win_scroll_x = page.evaluate("window.pageXOffset")
            win_scroll_y = page.evaluate("window.pageYOffset")
            viewport_width = page.evaluate("window.innerWidth")
            viewport_height = page.evaluate("window.innerHeight")

            win_left_bound = win_scroll_x
            win_right_bound = win_scroll_x + viewport_width
            win_upper_bound = win_scroll_y
            win_lower_bound = win_scroll_y + viewport_height
            
            # Scrollbar calculation
            doc_scroll_height = page.evaluate("document.body.scrollHeight")
            if doc_scroll_height == 0 or viewport_height == 0:
                 percentage_progress_start = 0
                 percentage_progress_end = 0
            elif doc_scroll_height <= viewport_height:
                percentage_progress_start = 0
                percentage_progress_end = 100
            else:
                percentage_progress_start = (win_scroll_y / doc_scroll_height) * 100
                percentage_progress_end = ((win_scroll_y + viewport_height) / doc_scroll_height) * 100
                percentage_progress_end = min(percentage_progress_end, 100.0)

            page_state_as_text.append(
                {
                    "x": 0, "y": 0,
                    "text": "[scrollbar {:0.0f}-{:0.0f}%]".format(
                        round(percentage_progress_start), round(percentage_progress_end)
                    ),
                }
            )
            # print(page_state_as_text[0]['text']) # For debugging scrollbar

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
        attributes_indices = nodes["attributes"] # List of lists of indices
        
        # Clickable nodes (set of indices)
        clickable_node_indices = set(nodes.get("isClickable", {}).get("index", []))


        text_value_map = {idx: val for idx, val in zip(nodes["textValue"]["index"], nodes["textValue"]["value"])}
        input_value_map = {idx: val for idx, val in zip(nodes["inputValue"]["index"], nodes["inputValue"]["value"])}
        # input_checked_map = {idx: val for idx, val in zip(nodes["inputChecked"]["index"], nodes["inputChecked"]["value"])} # If needed

        layout_node_map = {node_idx: bound_idx for bound_idx, node_idx in enumerate(layout["nodeIndex"])}
        bounds_list = layout["bounds"] # List of [x,y,width,height] arrays

        elements_in_view_port = []
        child_nodes_text_and_attrs = {} # Stores text and attributes for children of anchors/buttons

        # Ancestry tracking for grouping text under links/buttons
        anchor_ancestry = {"-1": (False, None)} # node_id_str -> (is_anchor_descendant, anchor_id)
        button_ancestry = {"-1": (False, None)} # node_id_str -> (is_button_descendant, button_id)

        def convert_node_name_type(node_name_str, is_node_clickable):
            """Converts HTML tag name to a simplified type (e.g., link, input, button)."""
            if node_name_str == "a": return "link"
            if node_name_str == "input": return "input"
            if node_name_str == "textarea": return "textarea"
            if node_name_str == "img": return "img"
            if node_name_str == "button" or is_node_clickable: return "button"
            return "text"

        def get_attributes_dict(attr_indices_for_node, string_array):
            """
            Extracts specified attributes for a node into a dictionary.
            attr_indices_for_node is like [key_idx1, val_idx1, key_idx2, val_idx2, ...].
            """
            attrs_to_extract = ["type", "placeholder", "aria-label", "title", "alt", "role", "name", "href", "value"]
            found_attrs = {}
            for i in range(0, len(attr_indices_for_node), 2):
                key_idx = attr_indices_for_node[i]
                value_idx = attr_indices_for_node[i+1]
                if key_idx < len(string_array) and value_idx < len(string_array) and value_idx >=0: # value_idx can be -1
                    key = string_array[key_idx]
                    if key in attrs_to_extract:
                        found_attrs[key] = string_array[value_idx]
            return found_attrs

        def build_ancestry_map(ancestry_dict, target_tag, current_node_idx, current_node_name_str, current_parent_idx):
            """Recursively builds ancestry map for target_tag (e.g. 'a' or 'button')."""
            parent_idx_str = str(current_parent_idx)
            if parent_idx_str not in ancestry_dict: # Parent not processed, recurse
                if current_parent_idx >= 0 and current_parent_idx < len(node_name_indices):
                    parent_name_str = strings[node_name_indices[current_parent_idx]].lower()
                    grandparent_idx = parent_indices[current_parent_idx]
                    build_ancestry_map(ancestry_dict, target_tag, current_parent_idx, parent_name_str, grandparent_idx)
                else: # Should not happen if tree is well-formed, base case for root's "parent" -1
                    ancestry_dict[parent_idx_str] = (False, None)


            is_parent_descendant, ultimate_ancestor_id = ancestry_dict.get(parent_idx_str, (False, None))

            if current_node_name_str == target_tag:
                value_to_set = (True, current_node_idx)
            elif is_parent_descendant:
                value_to_set = (True, ultimate_ancestor_id)
            else:
                value_to_set = (False, None)
            
            ancestry_dict[str(current_node_idx)] = value_to_set
            return value_to_set


        # First pass: Iterate over all nodes to build ancestry and collect raw element data
        for i in range(len(node_name_indices)):
            node_name_str = strings[node_name_indices[i]].lower()
            node_parent_idx = parent_indices[i]

            # Build ancestry for anchors and buttons
            is_desc_of_anchor, anchor_id = build_ancestry_map(anchor_ancestry, "a", i, node_name_str, node_parent_idx)
            is_desc_of_button, button_id = build_ancestry_map(button_ancestry, "button", i, node_name_str, node_parent_idx)
            
            if node_name_str in self.black_listed_elements:
                continue

            layout_idx = layout_node_map.get(i)
            if layout_idx is None:
                continue # Node not in layout (e.g. display:none)

            # Element bounding box
            # Bounds are [x, y, width, height]
            # These are physical pixels, need to adjust by devicePixelRatio
            # DOMSnapshot.captureSnapshot says:
            # "Rectangle takes into account the visual viewport and transforms applied to the node,
            # but not page scale and zoom."
            # Playwright's click handles coordinates correctly, so we might not need DPR adjustment here if PW handles it.
            # However, for consistency and if we were to use these coordinates elsewhere, DPR is important.
            # Let's assume Playwright's click takes viewport pixels.
            # The bounds from DOMSnapshot are usually already in CSS pixels if taken from layout.
            # For safety, we'll use the devicePixelRatio as the original code did.
            
            # Let's test without DPR adjustment first for bounds, as Playwright usually works with CSS pixels.
            # If clicks are off, this is a place to revisit.
            # The original code divided by DPR. Let's stick to that for now.
            x, y, width, height = bounds_list[layout_idx]
            x /= device_pixel_ratio
            y /= device_pixel_ratio
            width /= device_pixel_ratio
            height /= device_pixel_ratio


            # Check if element is in viewport
            elem_left_bound = x
            elem_top_bound = y
            elem_right_bound = x + width
            elem_lower_bound = y + height

            # Basic viewport check (partially visible is okay)
            in_viewport = (
                elem_left_bound < win_right_bound and elem_right_bound > win_left_bound and
                elem_top_bound < win_lower_bound and elem_lower_bound > win_upper_bound and
                width > 0 and height > 0 # Element must have dimensions
            )

            if not in_viewport:
                continue

            # --- Attribute Processing ---
            current_node_attributes_indices = []
            # attributes_indices is a list of lists. Each inner list corresponds to a node.
            # The inner list itself contains indices into the main `nodes["attributes"]` array,
            # which then points to string table. This seems overly complex.
            # Let's re-read DOMSnapshot spec for `nodes.attributes`.
            # "attributes": ["List of AttributeNameValue objects." -> This is for computedStyle, not general attributes.
            # The top-level "attributes" in "nodes" is: "Each attribute is a pair of string table indexes."
            # So, nodes["attributes"][i] should be the list of [key_idx, val_idx, ...] for node i.
            
            # The structure is:
            # tree.documents[0].nodes.attributes: [attr_val_for_node0, attr_val_for_node1, ...]
            # where attr_val_for_nodeX is itself a list of indices [key1, value1, key2, value2]
            # This was not correctly indexed in the original `find_attributes` call.
            # attributes_indices = nodes["attributes"] -> This is the list of attribute arrays for each node.
            # So, attributes_indices[i] is the specific list of [key_idx, val_idx,...] for node i.

            node_specific_attr_indices = attributes_indices[i] # This is the list [key_idx, val_idx, ...]
            raw_attrs = get_attributes_dict(node_specific_attr_indices, strings)
            
            meta_data_kv_strings = []
            for k, v in raw_attrs.items():
                meta_data_kv_strings.append(f'{k}="{v}"')


            # --- Node Value / Text Content ---
            actual_node_value = None
            if node_value_indices[i] >= 0: # Direct text content (e.g. for #text nodes)
                actual_node_value = strings[node_value_indices[i]]
            elif i in input_value_map and input_value_map[i] >=0: # Value of an input element
                 actual_node_value = strings[input_value_map[i]]
            elif i in text_value_map and text_value_map[i] >=0: # Text content from textValue (e.g. for <p>)
                 actual_node_value = strings[text_value_map[i]]


            # If this node is a text node (#text) and is a descendant of an anchor or button,
            # aggregate its text into the parent anchor/button's collection.
            is_ancestor_exception = is_desc_of_anchor or is_desc_of_button
            ancestor_node_id_for_grouping = None
            if is_desc_of_anchor:
                ancestor_node_id_for_grouping = anchor_id
            elif is_desc_of_button:
                ancestor_node_id_for_grouping = button_id

            if node_name_str == "#text" and ancestor_node_id_for_grouping is not None:
                text_content = actual_node_value
                if text_content and text_content.strip() and text_content.strip() not in ["|", "•"]:
                    child_nodes_text_and_attrs.setdefault(str(ancestor_node_id_for_grouping), []).append({
                        "type": "text_content", "value": text_content.strip()
                    })
                continue # Text node processed, skip adding it as a separate element

            # Skip adding children of interactive elements if they are not interactive themselves
            # (unless they are the interactive element itself, e.g. a nested button/link)
            if is_ancestor_exception and \
               node_name_str not in ["a", "button", "input", "textarea", "img"] and \
               i != ancestor_node_id_for_grouping: # Don't skip the anchor/button itself
                # Also collect attributes of these children if they are relevant
                if meta_data_kv_strings:
                     child_nodes_text_and_attrs.setdefault(str(ancestor_node_id_for_grouping), []).extend(
                         [{"type": "attribute", "key": k, "value": v} for k,v in raw_attrs.items()]
                     )
                continue


            # Prepare element data
            element_data = {
                "node_index_str": str(i),
                "backend_node_id": backend_node_ids[i],
                "node_name_str": node_name_str,
                "node_value_str": actual_node_value.strip() if actual_node_value else None,
                "meta_strings": meta_data_kv_strings, # List of 'key="value"'
                "is_clickable_flag": i in clickable_node_indices or node_name_str in ["a", "button", "input", "textarea"],
                "origin_x": int(x), "origin_y": int(y),
                "center_x": int(x + (width / 2)), "center_y": int(y + (height / 2)),
            }
            elements_in_view_port.append(element_data)

        # Second pass: Filter and format elements
        elements_of_interest = []
        id_counter = 0
        
        # Add scrollbar info first if needed, or handle it separately
        # For now, let's keep it out of elements_of_interest to match user's expected output format
        # elements_of_interest.append(page_state_as_text[0]['text'])


        for elem_data in elements_in_view_port:
            node_idx_str = elem_data["node_index_str"]
            original_node_name = elem_data["node_name_str"]
            node_val = elem_data["node_value_str"] # Already stripped or None
            is_clickable_direct = elem_data["is_clickable_flag"]
            
            # Consolidate inner text from node value and collected child texts
            combined_inner_text_parts = []
            if node_val:
                combined_inner_text_parts.append(node_val)

            # Add text from children that were grouped under this element (if it's an anchor/button)
            if node_idx_str in child_nodes_text_and_attrs:
                for child_item in child_nodes_text_and_attrs[node_idx_str]:
                    if child_item["type"] == "text_content":
                        combined_inner_text_parts.append(child_item["value"])
            
            final_inner_text = " ".join(combined_inner_text_parts).strip()

            # Consolidate meta attributes
            current_meta_strings = list(elem_data["meta_strings"]) # Start with element's own attrs
            if node_idx_str in child_nodes_text_and_attrs:
                 for child_item in child_nodes_text_and_attrs[node_idx_str]:
                    if child_item["type"] == "attribute":
                        # Avoid duplicate attributes, prioritize parent's if conflict? For now, just add.
                        current_meta_strings.append(f'{child_item["key"]}="{child_item["value"]}"')
            
            # Deduplicate meta strings (simple deduplication by exact string match)
            unique_meta_strings = sorted(list(set(current_meta_strings)))
            meta_attr_string = (" " + " ".join(unique_meta_strings)) if unique_meta_strings else ""


            # Determine element type for output
            # Special handling for input type="submit" or type="button" -> treat as button
            # This requires checking the 'type' attribute from meta_attr_string or raw_attrs
            # For simplicity, convert_node_name_type already handles general clickability.
            # If node is <input type="submit">, original_node_name is "input".
            # We can refine this if needed.
            
            # If an input has type="submit" or type="button", treat it as a "button"
            final_elem_type = original_node_name
            if original_node_name == "input":
                type_attr = None
                for meta_s in unique_meta_strings: # e.g., 'type="submit"'
                    if meta_s.startswith('type="'):
                        type_attr = meta_s.split('"')[1]
                        break
                if type_attr in ["submit", "button", "reset", "image"]: # image input is also a button
                    final_elem_type = "button"
                    # Remove type attribute from meta if we're calling it a button
                    # meta_attr_string = " ".join(s for s in unique_meta_strings if not s.startswith('type="'))
                    # meta_attr_string = (" " + meta_attr_string) if meta_attr_string.strip() else ""


            # Use the simplified type for the output tag
            output_tag_name = convert_node_name_type(final_elem_type, is_clickable_direct)


            # Filtering: Keep if it has text, or is an interactive type, or has meaningful metadata (like placeholder for input)
            if not final_inner_text and output_tag_name not in ["input", "textarea", "button", "link", "img"]:
                # If it's purely text and has no text, skip.
                # For other types, even if no text, they might be important (e.g. an input with placeholder)
                if not meta_attr_string.strip() : # Also skip if no metadata at all
                    continue
            
            # Further filter: if it's just "text" type and has no text and no meaningful attributes, skip.
            if output_tag_name == "text" and not final_inner_text.strip() and not meta_attr_string.strip() :
                continue


            self.page_element_buffer[id_counter] = elem_data # Store original data for click/type actions

            if final_inner_text:
                elements_of_interest.append(
                    f"<{output_tag_name} id={id_counter}{meta_attr_string}>{final_inner_text}</{output_tag_name}>"
                )
            else: # For elements like <input/> or <img/> that don't have closing tags with text
                elements_of_interest.append(
                    f"<{output_tag_name} id={id_counter}{meta_attr_string}/>"
                )
            id_counter += 1
        
        print(f"Parsing time: {time.time() - start_time:.2f} seconds. Found {len(elements_of_interest)} elements.")
        return elements_of_interest

    def close(self):
        """Closes the browser."""
        if self.browser:
            self.browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Playwright Browser Crawler Example")
    parser.add_argument("--run_example", choices=["1", "2"], help="Select the example to run")
    args = parser.parse_args()
    
    
    crawler = Crawler()
    
    
    
    # Examples:
        
    # Example #1 search query on duckduckgo.com
    if args.run_example == "1":
        try:
            crawler.go_to_page("duckduckgo.com")
            elements = crawler.crawl()
            
            if not elements:
                print("No elements found or crawl failed.")
            else:
                print("\n--- Crawled Elements ---")
                for ele_str in elements:
                    print(ele_str)
                print("--- End of Crawled Elements ---\n")

            # Find search input (usually has placeholder 'Search the web without being tracked' or similar)
            search_input_id = None
            search_button_id = None

            for i, el_str in enumerate(elements): # The ID in the string is what we need
                current_id_str = el_str.split("id=")[1].split(" ")[0].split(">")[0].replace("/", "")
                current_id = int(current_id_str)

                # if "<input" in el_str and ('placeholder="Search' in el_str or 'placeholder="Search without being tracked"' in el_str or 'aria-label="Search input"' in el_str or 'name="q"' in el_str):
                if "<input" in el_str and ('Search' in el_str or 'name="q"' in el_str):
                    search_input_id = current_id
                    print(f"Found search input: id={search_input_id}, element: {el_str}")
                elif "<textarea" in el_str and 'name="q"' in el_str:
                    search_input_id = current_id
                    print(f"Found search input: id={search_input_id}, element: {el_str}")
                # if (("<button" in el_str or "<input" in el_str) and 
                #     ('aria-label="Search"' in el_str or 'value="Search"' in el_str or 'Search</button>' in el_str or 'id="search_button"' in el_str or 'S</button>' in el_str)): # S is the icon
                #     # Check if it's the main search button, not other buttons
                #     if "Search</button>" in el_str or 'aria-label="Search"' in el_str and 'type="submit"' in el_str :
                #          search_button_id = current_id
                #          print(f"Found search button: id={search_button_id}, element: {el_str}")


            if search_input_id is not None:
                print(f"\nTyping 'Playwright library' into search input (id={search_input_id})...")
                crawler.type(str(search_input_id), "Playwright library")

                # Option 2: Click search button (if found)
                if search_button_id is not None:
                    print(f"Clicking search button (id={search_button_id})...")
                    crawler.click(str(search_button_id))
                else:
                    print("Search button not explicitly found, relying on Enter or form submission if applicable.")
                    crawler.enter() # Fallback to Enter if button not found

                time.sleep(3) # Wait for search results to load
                print("\n--- Elements after search ---")
                elements_after_search = crawler.crawl()
                for ele_str in elements_after_search:
                    print(ele_str)
                print("--- End of Elements after search ---\n")

            else:
                print("Could not find the search input field to type into.")

        except Exception as e:
            print(f"An error occurred in the main execution: {e}")
        finally:
            print("Closing browser...")
            crawler.close()

    elif args.run_example == "2":
        print("Running example 2: Clicking on a link")
        url = "https://www.duckduckgo.com/?q=cars"
        print(f"Opening {url}")
        crawler.go_to_page(url)
        
        print("\n--- Elements after opening ---")
        elements_after_open = crawler.crawl()
        for ele_str in elements_after_open:
            print(ele_str)
        print("--- End of Elements after opening ---\n")
        
        # print("Clicking the first link...")
        crawler.click(90)
        # print("Closing browser...")
        time.sleep(2)
        crawler.close()
            
                