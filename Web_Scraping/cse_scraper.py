import os
import re
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SCRAPE_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraped_data")

START_URL = "https://www.cse.iitk.ac.in/"
CONTENT_SELECTOR = "div.agileinfo-contact-main-address"


def collect_page_urls(driver, start_url):
    driver.get(start_url)
    urls = set()
    for link in driver.find_elements(By.CSS_SELECTOR, "a"):
        href = link.get_attribute("href")
        if href and "cse.iitk.ac.in/pages/" in href:
            urls.add(href)
    return sorted(urls)


def scrape_page(driver, url):
    driver.get(url)
    content = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, CONTENT_SELECTOR))
    )
    lines = []
    parts = content.find_elements(
        By.XPATH, ".//h4 | .//p[not(ancestor::li)] | .//tr | .//li[not(.//li)]"
    )
    for part in parts:
        if part.tag_name == "tr":
            cells = [c.text.strip() for c in part.find_elements(By.CSS_SELECTOR, "th, td")]
            line = " | ".join(cell for cell in cells if cell)
        else:
            line = part.text.strip()
            if " | " in line:
                continue
        if line:
            lines.append(line)
    return "\n\n".join(lines)


def file_name_for(url):
    name = url.rsplit("/", 1)[1].replace(".html", "")
    name = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return f"cse_{name.lower()}.txt"


driver = webdriver.Chrome()
urls = collect_page_urls(driver, START_URL)
print("pages found:", len(urls))

skipped = []
for url in urls:
    try:
        text = scrape_page(driver, url)
    except TimeoutException:
        skipped.append(url)
        continue
    file_name = file_name_for(url)
    os.makedirs(SCRAPE_DIRECTORY, exist_ok=True)
    with open(os.path.join(SCRAPE_DIRECTORY, file_name), "w", encoding="utf-8") as f:
        f.write(text)
    print(len(text), "characters:", file_name)
    time.sleep(1)

print("saved", len(urls) - len(skipped), "pages, skipped", len(skipped))
for url in skipped:
    print("skipped:", url)
driver.quit()