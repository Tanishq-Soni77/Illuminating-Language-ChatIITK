import ast
import json
import os
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SCRAPE_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraped_data")

URL = "https://www.ecelliitk.org/iitk-startups-24/"
OUTPUT_FILE = "ecell_startups.txt"
START_MARKER = "JSON.parse('[{\"Id\":"
MISSING = {"", "-", "NaN", "nan", "None"}

FIND_BUNDLE = """
return performance.getEntriesByType('resource')
    .map(r => r.name)
    .find(name => name.includes('/static/js/main.') && name.endsWith('.js'));
"""
FETCH_TEXT = """
const done = arguments[arguments.length - 1];
fetch(arguments[0]).then(r => r.text()).then(done).catch(error => done('ERROR ' + error));
"""

FIELDS = [
    ("Location", "Location"),
    ("FoundedYear", "Founded"),
    ("CompanyStage", "Company stage"),
    ("UnicornStatus", "Unicorn status"),
    ("Funding", "Total funding"),
    ("FundingRounds", "Funding rounds"),
    ("Valuation", "Valuation"),
    ("AnnualRevenue", "Annual revenue"),
    ("EBIDTA", "EBITDA"),
    ("NetProfit", "Net profit"),
    ("EmployeeCount", "Employees"),
    ("FounderandKeyPeople", "Founders and key people"),
    ("InvestorName", "Investors"),
    ("FundingRoundFacilitators", "Funding round facilitators"),
    ("Sector", "Sector"),
    ("BusinessModel", "Business model"),
    ("AssociatedLegalEntity", "Legal entity"),
    ("WebsiteLink", "Website"),
]


def fetch_startup_records(driver):
    driver.set_script_timeout(60)
    driver.get(URL)
    bundle_url = WebDriverWait(driver, 20).until(
        lambda d: d.execute_script(FIND_BUNDLE)
    )
    script_text = driver.execute_async_script(FETCH_TEXT, bundle_url)
    start = script_text.index(START_MARKER) + len("JSON.parse('")
    end = script_text.index("}]')", start) + 2
    return json.loads(ast.literal_eval("'" + script_text[start:end] + "'"))


def clean_value(value):
    if value is None or (isinstance(value, float) and value != value):
        return None
    text = " ".join(str(value).split())
    if text in MISSING:
        return None
    return re.sub(r"\s*\[\+(\d+)\]", r" (+\1 more)", text)


def format_startup(record):
    name = clean_value(record.get("Name")) or "Unknown"
    lines = [f"IITK startup: {name}"]
    description = clean_value(record.get("ShortDescription"))
    if description:
        lines.append(f"Description: {description}")
    for key, label in FIELDS:
        value = clean_value(record.get(key))
        if value:
            lines.append(f"{label}: {value}")
    return "\n".join(lines)


def main():
    driver = webdriver.Chrome()
    try:
        records = fetch_startup_records(driver)
    finally:
        driver.quit()

    header = (
        f"IITK startups directory: {len(records)} startups listed on the "
        "E-Cell IIT Kanpur website (ecelliitk.org/iitk-startups-24)."
    )
    blocks = [header] + [format_startup(record) for record in records]
    text = "\n\n".join(blocks)
    os.makedirs(SCRAPE_DIRECTORY, exist_ok=True)
    with open(os.path.join(SCRAPE_DIRECTORY, OUTPUT_FILE), "w", encoding="utf-8") as f:
        f.write(text)
    print(len(records), "startups,", len(text), "characters saved to", OUTPUT_FILE)


if __name__ == "__main__":
    main()
