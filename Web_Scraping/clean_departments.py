from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent
RAW_DIR = BASE / "raw" / "departments"
CLEAN_DIR = BASE / "scraped_data" / "departments"

BOILERPLATE_SHARE = 0.30   # a line on 30%+ of a department's pages is boilerplate
MIN_PAGES = 10             # below this, the share is too noisy to trust
MIN_LETTERS = 12           # a page with fewer letters than this has no readable content
REMOVED_DIR = BASE / "raw" / "removed_pages"
ERROR_MARKER = "the requested page cannot be found"   # wording of the site's own 404 page

def read_page(path):
    text = path.read_text(encoding="utf-8")
    header, _, body = text.partition("\n")
    url = header.removeprefix("SOURCE: ").strip()
    return url, body.splitlines()

def department_key(url):
    parsed = urlparse(url)
    first = parsed.path.strip("/").split("/")[0]
    return f"{parsed.netloc}/{first}"


def load_departments():
    departments = {}
    for path in sorted(RAW_DIR.glob("*.txt")):
        url, lines = read_page(path)
        departments.setdefault(department_key(url), []).append((path, url, lines))
    return departments

def find_boilerplate(pages):
    counts = Counter()
    for _, _, lines in pages:
        counts.update({line.strip() for line in lines if line.strip()})
    cutoff = len(pages) * BOILERPLATE_SHARE
    return {line for line, n in counts.items() if n >= cutoff}


DEPARTMENT_NAMES = {
    "aero": "aerospace_engineering",
    "bsbe": "biological_sciences_bioengineering",
    "che": "chemical_engineering",
    "ce": "civil_engineering",
    "ee": "electrical_engineering",
    "mse": "materials_science_engineering",
    "me": "mechanical_engineering",
    "doms": "management_sciences",
    "design": "design",
    "see": "sustainable_energy_engineering",
    "space": "space_planetary_astronomical_sciences",
    "dis": "intelligent_systems",
    "chm": "chemistry",
    "es": "earth_sciences",
    "phy": "physics",
    "math": "mathematics",
    "sds": "statistics_data_science",
    "hss": "humanities_social_sciences",
    "eco": "economic_sciences",
    "gsmst": "gangwal_school_medical_science",
    "kss": "kotak_school_sustainability",
    "wsais": "wadhwani_school_ai",
    "msp": "materials_science_programme",
    "net": "nuclear_engineering_technology",
    "celp": "photonics_science_engineering",
}


def is_error_page(lines):
    return ERROR_MARKER in " ".join(" ".join(lines).split()).lower()


def tidy(lines):
    text = "\n".join(lines)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.strip()


def save_page(path, url, body):
    path.write_text(f"SOURCE: {url}\n\n{body}\n", encoding="utf-8")


def clean_department(key, pages):
    segment = key.split("/")[-1]
    name = DEPARTMENT_NAMES.get(segment, segment)
    # error pages are junk, so they must not vote on what counts as boilerplate
    real_pages = [page for page in pages if not is_error_page(page[2])]
    boilerplate = find_boilerplate(real_pages) if len(real_pages) >= MIN_PAGES else set()
    shared = {}
    stats = Counter(pages=len(pages))
    for path, url, lines in pages:
        kept = []
        for line in lines:
            text = line.strip()
            if text in boilerplate:
                shared.setdefault(text, None)
            else:
                kept.append(line)
        stats["raw"] += sum(len(line) + 1 for line in lines)
        body = tidy(kept)
        if not body:
            stats["empty"] += 1
            continue
        save_page(CLEAN_DIR / path.name, url, body)
        stats["written"] += 1
        stats["clean"] += len(body)
    if shared:
        body = tidy(list(shared))
        save_page(CLEAN_DIR / f"{name}_site_wide_content.txt", f"https://{key}/", body)
        stats["clean"] += len(body)
    stats["shared"] = len(shared)
    return name, stats


def remove_redundant_pages():
    """Move unreadable and exact-duplicate pages out of the cleaned folder, keeping a manifest."""
    REMOVED_DIR.mkdir(parents=True, exist_ok=True)
    pages = []
    for path in sorted(CLEAN_DIR.glob("*.txt")):
        if path.name.endswith("_site_wide_content.txt"):
            continue
        url, lines = read_page(path)
        pages.append((path, url, " ".join("\n".join(lines).split())))

    seen = {}
    log = []
    # shortest URL first, so the most canonical address of a page is the one kept
    for path, url, body in sorted(pages, key=lambda page: (len(page[1]), page[0].name)):
        if ERROR_MARKER in body.lower():
            reason, kept = "error page", ""
        elif sum(ch.isalpha() for ch in body) < MIN_LETTERS:
            reason, kept = "no readable content", ""
        else:
            identity = (department_key(url), body)
            if identity not in seen:
                seen[identity] = path.name
                continue
            reason, kept = "duplicate", seen[identity]
        path.replace(REMOVED_DIR / path.name)
        log.append(f"{path.name}\t{url}\t{reason}\t{kept}")

    # every run rebuilds the cleaned folder from raw/, so the manifest is rewritten, not appended to
    manifest = REMOVED_DIR / "manifest.tsv"
    manifest.write_text("file\turl\treason\tkept_instead\n" + "\n".join(log) + "\n", encoding="utf-8")
    return Counter(line.split("\t")[2] for line in log)


def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    total = Counter()
    print(f"{'department':<42}{'pages':>6}{'kept':>6}{'empty':>6}{'shared':>7}{'raw KB':>9}{'clean KB':>9}")
    for key, pages in sorted(load_departments().items()):
        name, s = clean_department(key, pages)
        total.update(s)
        print(f"{name:<42}{s['pages']:>6}{s['written']:>6}{s['empty']:>6}{s['shared']:>7}{s['raw'] // 1000:>9}{s['clean'] // 1000:>9}")
    print(f"{'TOTAL':<42}{total['pages']:>6}{total['written']:>6}{total['empty']:>6}{total['shared']:>7}{total['raw'] // 1000:>9}{total['clean'] // 1000:>9}")
    removed = remove_redundant_pages()
    print("removed:", dict(removed), "| remaining pages:", len(list(CLEAN_DIR.glob("*.txt"))))


if __name__ == "__main__":
    main()
