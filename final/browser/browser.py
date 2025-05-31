from browser.viewport import VisibleContentExtractor

# Keywords to identify links that are often part of footers or auxiliary navigation
USELESS_LINK_TEXT_KEYWORDS = [
    "privacy", "policy", "terms", "conditions", "service", "about", "contact", 
    "careers", "sitemap", "help", "faq", "support", "accessibility", "cookie", 
    "feedback", "security", "legal", "developer", "api", "status", "blog",
    "press", "investors", "media", "advertising", "partners"
]
# Patterns in hrefs that often indicate non-primary content links
USELESS_LINK_HREF_PATTERNS = [
    "facebook.com", "twitter.com", "linkedin.com", "instagram.com", "youtube.com",
    "pinterest.com", "tel:", "mailto:", "/legal", "/policy", "/about", "/contact",
    "/terms", "/privacy", "#", "javascript:void(0)"
]

class Browser:
    def __init__(self):
        self.extractor = VisibleContentExtractor()
        
    def _get(self, url):
        self.extractor.driver.get(url)
        self.extractor.driver.implicitly_wait(1)
        viewport = self.extractor.get_viewport_dimensions()
        visible_elements = self.extractor.get_visible_elements()
        
        return viewport, visible_elements
    
    def get_curr_page(self):
        return self.extractor.driver.current_url
    
    def get_page_for_llm(self, url):
        viewport, visible_elements = self._get(url)
        page = []
        page .append(f"""Current Page: {self.extractor.driver.current_url}\n"""    )
        
        black_listed_elements = set(["html", "head", "title", "meta", "iframe", "body", "script", "style", "path", "span", "g-popup", "svg", "br", "::marker"])
        for element in visible_elements:
            if element['tag'] not in black_listed_elements:
                if element['tag'] == 'a':
                    if element['attributes'].get('href', '') == '#': 
                        continue
                    else:
                        link =element['attributes'].get('href', '')
                        page.append(f"""<a href="{link}">{element['text']}</a>\n""")
                # elif element['tag'] == 'input' and element['attributes'].get('type', '') == 'submit':
                else:
                    text = element['text'][:50].replace('\n', '\\n')
                    page.append(f"""<{element['tag']}>{text}</{element['tag']}>\n""")
            
        
        return "".join(list(set(page)))

    def close(self):
        self.extractor.close()