from selenium import webdriver
import time 


def get_driver():
    options = webdriver.FirefoxOptions()
    # options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    return driver

driver = get_driver()

driver.get("https://duckduckgo.com")

with open("example.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)

time.sleep(1)
driver.quit()