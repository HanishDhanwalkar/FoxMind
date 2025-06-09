import os
from bs4 import BeautifulSoup
from selenium import webdriver

class WebCrawler:
    def __init__(self, url):
        self.url = url
        self.driver = self.initialize_driver()

    def initialize_driver(self):
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')  # Run in headless mode
        return webdriver.Firefox(options=options)

    def crawl(self):
        self.driver.get(self.url)
        html = self.driver.page_source

        soup = BeautifulSoup(html, 'html.parser')

        # Extract links from the page
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                yield href

        # Extract text from the page
        for text in soup.get_text().split('\n'):
            yield text.strip()

    def save_to_file(self, filename):
        parent_dir = os.path.dirname(os.path.realpath(__file__))
        directory = os.path.join(parent_dir, 'crawled_data')
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(os.path.join(directory, filename), 'w') as f:
            for item in self.crawl():
                f.write(item + '\n')


if __name__ == "__main__":
    url = "https://duckduckgo.com"
    crawler = WebCrawler(url)
    
    crawler.save_to_file((url.split("/")[-1]).replace(".", "_") + ".txt")
