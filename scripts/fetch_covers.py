"""Cache Audible cover art for the Reading Hub.

Usage: python scripts/fetch_covers.py [--all]
Looks up the ASINs in data/books.csv (unread books only, unless --all) and
data/suggestions.csv in your Audible store's catalog, records the image URL in
data/covers.csv (asin, cover) and saves a 300px copy as hub/covers/<asin>.jpg.
The page can't load images from Amazon, so the copies are published next to it.
Cover art belongs to its publishers, so hub/covers/ is git-ignored: keep it local.
ASINs already cached are skipped, so reruns are cheap.
"""
import csv
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "book-research"))
from lookup import AUD, get  # noqa: E402

OUT = ROOT / "data" / "covers.csv"
IMG = ROOT / "hub" / "covers"
OPEN = {"Wishlist", "Owned – Unread", "Reading", "Not Released"}


def load(name):
    with open(ROOT / "data" / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    every = "--all" in sys.argv
    have = {r["asin"]: r["cover"] for r in load("covers.csv")} if OUT.exists() else {}
    want = [b["asin"] for b in load("books.csv") if b["asin"] and (every or b["status"] in OPEN)]
    if (ROOT / "data" / "suggestions.csv").exists():
        want += [s["asin"] for s in load("suggestions.csv") if s["asin"]]
    todo = sorted({a for a in want if a not in have})
    for i in range(0, len(todo), 40):
        chunk = todo[i:i + 40]
        q = urllib.parse.urlencode({"asins": ",".join(chunk), "response_groups": "media", "image_sizes": "500"})
        for p in json.loads(get(f"{AUD}?{q}")).get("products", []):
            img = (p.get("product_images") or {}).get("500")
            if img:
                have[p["asin"]] = img
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["asin", "cover"])
        w.writerows(sorted(have.items()))
    IMG.mkdir(exist_ok=True)
    for asin, url in have.items():
        dest = IMG / f"{asin}.jpg"
        if not dest.exists():
            req = urllib.request.Request(url.replace("._SL500_", "._SL300_"), headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                dest.write_bytes(r.read())
    missing = [a for a in todo if a not in have]
    print(f"{len(have)} covers cached -> data/covers.csv" + (f"; no cover for {', '.join(missing)}" if missing else ""))


if __name__ == "__main__":
    main()
