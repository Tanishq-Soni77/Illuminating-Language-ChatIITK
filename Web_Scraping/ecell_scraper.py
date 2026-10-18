import os
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SCRAPE_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraped_data")

HOME_URL = "https://ecelliitk.org/"
INSIDE_TEXT_TAG = (
    "ancestor::p or ancestor::li or ancestor::h1 or ancestor::h2 "
    "or ancestor::h3 or ancestor::h4 or ancestor::h5 or ancestor::h6"
)
TEXT_XPATH = (
    "//h1 | //h2 | //h3 | //h4 | //h5 | //h6 "
    "| //p[not(ancestor::li)] | //li[not(.//li)] "
    f"| //div[not(*)][normalize-space()][not({INSIDE_TEXT_TAG})] "
    f"| //span[not(*)][normalize-space()][not({INSIDE_TEXT_TAG})]"
)


def scroll_through_page(driver, step=600, pause=0.5):
    position = 0
    while position < driver.execute_script("return document.body.scrollHeight"):
        position += step
        driver.execute_script("window.scrollTo(0, arguments[0]);", position)
        time.sleep(pause)


def wait_for_text(driver, minimum=100, timeout=20):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_element(By.TAG_NAME, "body").text) > minimum
        )
    except TimeoutException:
        pass


def read_page_text(driver):
    wait_for_text(driver)
    scroll_through_page(driver)
    lines = []
    for part in driver.find_elements(By.XPATH, TEXT_XPATH):
        line = " ".join(part.get_attribute("textContent").split())
        if line and line not in lines:
            lines.append(line)
    return "\n\n".join(lines)


def scrape_in_new_window(driver, link):
    main_window = driver.current_window_handle
    driver.execute_script("arguments[0].click();", link)
    WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
    new_window = [h for h in driver.window_handles if h != main_window][0]
    driver.switch_to.window(new_window)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        return read_page_text(driver)
    finally:
        driver.close()
        driver.switch_to.window(main_window)


def file_name_for(url):
    slug = url.rstrip("/").rsplit("/", 1)[1].lower().replace("-", "_")
    return f"ecell_{slug}.txt"


def save_text(file_name, text):
    os.makedirs(SCRAPE_DIRECTORY, exist_ok=True)
    with open(os.path.join(SCRAPE_DIRECTORY, file_name), "w", encoding="utf-8") as f:
        f.write(text)
    print(len(text), "characters:", file_name)


driver = webdriver.Chrome()
driver.get(HOME_URL)
WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.TAG_NAME, "a"))
)

pages = {}
for link in driver.find_elements(By.CSS_SELECTOR, "a[target='_blank']"):
    href = link.get_attribute("href")
    if href and "ecelliitk.org" in href and "iitk-startups-24" not in href and href not in pages:
        pages[href] = link
print("E-Cell pages to scrape:", len(pages))

save_text("ecell_home.txt", read_page_text(driver))

skipped = []
for href, link in pages.items():
    try:
        text = scrape_in_new_window(driver, link)
    except WebDriverException as error:
        skipped.append(href)
        print("skipped:", href, "|", str(error).split("\n")[0][:60])
        continue
    save_text(file_name_for(href), text)
    time.sleep(1)

print("saved", len(pages) - len(skipped) + 1, "files, skipped", len(skipped))
driver.quit()