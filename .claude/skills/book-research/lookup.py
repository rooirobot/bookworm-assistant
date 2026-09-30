"""Fetch raw book facts from Open Library, the Audible catalog API and (optionally) Goodreads.

Usage:
  python lookup.py ol-search "red rising pierce brown"     # candidate Open Library works
  python lookup.py ol-editions <work id, e.g. OL17075754W> # print editions of one work
  python lookup.py aud-search "red rising pierce brown"    # candidate Audible products
  python lookup.py aud <ASIN>                              # facts from one Audible product
  python lookup.py gr-search "red rising pierce brown"     # Goodreads, only if enabled
  python lookup.py gr <goodreads_url_or_id>                # Goodreads, only if enabled

Every command prints JSON. The output is raw facts only: choosing the edition and
classifying the book is left to the researcher (see SKILL.md).

The Audible store comes from "audible_store" in config.json (us, uk, ca, au, de, fr, in, it, jp, es).
Goodreads has no public API and scraping it is against its terms of use, so the gr commands
only run when "goodreads": true is set in config.json. That choice is yours.
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
try:
    CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
except (OSError, ValueError):
    CONFIG = {}

UA = "bookworm-assistant (personal reading log)"
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")
TLD = {"us": "com", "uk": "co.uk", "ca": "ca", "au": "com.au", "de": "de", "fr": "fr",
       "in": "in", "it": "it", "jp": "co.jp", "es": "es"}[CONFIG.get("audible_store", "us")]
AUD = f"https://api.audible.{TLD}/1.0/catalog/products"
AUD_WEB = f"https://www.audible.{TLD}/pd/"
AUD_GROUPS = "product_desc,product_attrs,contributors,rating,series"
OL = "https://openlibrary.org"


def get(url, browser=False):
    req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA if browser else UA, "Accept-Language": "en-US"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8")
        if r.status == 202 and not body:
            raise RuntimeError("blocked by bot protection (HTTP 202 challenge); wait a while and retry")
        return body


def year(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).year if ms else None


# --- Open Library (default source: free, open data, no scraping) ---

def ol_search(q):
    fields = "key,title,author_name,first_publish_year,number_of_pages_median,ratings_average,ratings_count"
    rows = json.loads(get(f"{OL}/search.json?limit=8&fields={fields}&q=" + urllib.parse.quote(q))).get("docs", [])
    return [{"work": r["key"].split("/")[-1], "title": r.get("title"), "authors": r.get("author_name"),
             "first_published": r.get("first_publish_year"), "pages_median": r.get("number_of_pages_median"),
             "ol_rating": round(r["ratings_average"], 2) if r.get("ratings_average") else None,
             "ol_count": r.get("ratings_count"), "url": f"{OL}{r['key']}"} for r in rows]


def ol_editions(work):
    work = work.split("/")[-1]
    rows = json.loads(get(f"{OL}/works/{work}/editions.json?limit=100")).get("entries", [])
    out = [{"isbn13": (r.get("isbn_13") or [None])[0], "isbn10": (r.get("isbn_10") or [None])[0],
            "publishers": r.get("publishers"), "publish_date": r.get("publish_date"),
            "pages": r.get("number_of_pages"), "format": r.get("physical_format"),
            "language": [x["key"].split("/")[-1] for x in r.get("languages") or []]} for r in rows]
    return [e for e in out if e["isbn13"] or e["isbn10"]]


# --- Audible catalog API (no login) ---

def aud_product(p):
    rt = p.get("rating") or {}
    ov, pf = rt.get("overall_distribution") or {}, rt.get("performance_distribution") or {}
    mins = p.get("runtime_length_min")
    return {
        "asin": p["asin"], "title": p.get("title"),
        "authors": [a["name"] for a in p.get("authors") or []],
        "narrators": [n["name"] for n in p.get("narrators") or []],
        "publisher": p.get("publisher_name"), "release_date": p.get("release_date"),
        "format": p.get("format_type"), "language": p.get("language"),
        "audio_hours": round(mins / 60, 1) if mins else None,
        "audible_rating": ov.get("display_average_rating"), "audible_narration": pf.get("display_average_rating"),
        "audible_ratings_count": ov.get("num_ratings"),
        "series": [{"series": s.get("title"), "position": s.get("sequence")} for s in p.get("series") or []],
        "audible_url": AUD_WEB + p["asin"],
    }


def aud_search(q):
    url = f"{AUD}?keywords={urllib.parse.quote(q)}&num_results=10&response_groups={AUD_GROUPS}"
    return [aud_product(p) for p in json.loads(get(url)).get("products", [])]


def aud(asin):
    return aud_product(json.loads(get(f"{AUD}/{asin}?response_groups={AUD_GROUPS}"))["product"])


# --- Goodreads (opt-in; see the module docstring) ---

def need_goodreads():
    if not CONFIG.get("goodreads"):
        raise RuntimeError('Goodreads is disabled. Set "goodreads": true in config.json to use it '
                           "(your choice: it scrapes goodreads.com, which its terms of use don't allow).")


def gr_search(q):
    need_goodreads()
    rows = json.loads(get("https://www.goodreads.com/book/auto_complete?format=json&q=" + urllib.parse.quote(q), browser=True))
    return [{"title": r["title"], "author": r["author"]["name"], "url": "https://www.goodreads.com" + r["bookUrl"].split("?")[0],
             "pages": r.get("numPages"), "gr_rating": r.get("avgRating"), "gr_count": r.get("ratingsCount")} for r in rows[:8]]


def gr_book(ref):
    need_goodreads()
    url = ref if ref.startswith("http") else f"https://www.goodreads.com/book/show/{ref}"
    html = get(url, browser=True)
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        return {"error": "no __NEXT_DATA__ on page (blocked or layout changed)", "url": url}
    st = json.loads(m.group(1))["props"]["pageProps"]["apolloState"]
    book = next(v for k, v in st.items() if k.startswith("Book:") and "details" in v)
    work = next(v for k, v in st.items() if k.startswith("Work:") and "details" in v)
    series = []
    for s in book.get("bookSeries") or []:
        ref_ = st.get(s["series"]["__ref"], {})
        series.append({"series": ref_.get("title"), "position": s.get("userPosition"), "url": ref_.get("webUrl")})
    d, wd = book["details"], work["details"]
    return {
        "goodreads_url": book.get("webUrl", url).split("?")[0],
        "title": book.get("title"),
        "edition": {"format": d.get("format"), "pages": d.get("numPages"), "publisher": d.get("publisher"),
                    "isbn13": d.get("isbn13"), "year": year(d.get("publicationTime"))},
        "first_published": year(wd.get("publicationTime")),
        "series": series,
        "gr_rating": round(work["stats"]["averageRating"], 2),
        "gr_count": work["stats"]["ratingsCount"],
        "awards": [{"name": a["name"], "category": a.get("category"), "designation": a.get("designation"),
                    "year": year(a.get("awardedAt"))} for a in wd.get("awardsWon") or []],
        "genres": [g["genre"]["name"] for g in book.get("bookGenres") or [] if g.get("genre")][:10],
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    cmds = {"ol-search": ol_search, "ol-editions": ol_editions, "aud-search": aud_search, "aud": aud,
            "gr-search": gr_search, "gr": gr_book}
    if len(sys.argv) != 3 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    try:
        out = cmds[sys.argv[1]](sys.argv[2])
    except Exception as e:  # report, don't crash the researcher's loop
        out = {"error": f"{type(e).__name__}: {e}"}
    print(json.dumps(out, indent=2, ensure_ascii=False))
