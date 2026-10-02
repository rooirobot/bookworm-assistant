"""Build the owner's private Reading Hub page from the master data.

Usage: python scripts/build_hub.py
Reads data/books.csv, data/series.csv, data/suggestions.csv, data/book_overviews.csv
(spoiler-free "did I read this?" overviews for unread books) and config.json, and writes
hub/hub.html (hub/template.html with the data embedded). In Claude Code, Claude publishes
it as a private claude.ai artifact with a small database, keeping the same URL
(hub_url in config.json). Opened as a plain file it still works, but choices only last
until the page is reloaded.

The page has three tabs:
  Discover    data/suggestions.csv: a daily "Tonight's pick", a one-at-a-time deck, a cover
              row of new books and a compact row of the series you've started
  Up next     unread books (Wishlist / Owned – Unread / Reading), one card per series
              showing the next book, ranked: started series by rating, then owned, then the rest
  Watchlist   watched series that are ongoing or have announced books, plus a dated timeline

Covers come from hub/covers/<asin>.jpg (scripts/fetch_covers.py) and are published
next to the page, because the page can't load images from Amazon.

The owner's choices (want / not for me, queue order, watch level) are saved in the
artifact's database, not here. Claude reads them back with ArtifactData and applies
them to the CSVs.
"""
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "book-research"))
from lookup import AUD_WEB, CONFIG  # noqa: E402

OPEN = {"Wishlist", "Owned – Unread", "Reading"}
DATE = re.compile(r"(?:[Dd]ue|[Rr]elease)\D{0,12}(\d{4}-\d{2}-\d{2})")  # a release date, not an "as of" date
NEXT_IN_NOTES = [re.compile(r"([A-Z][\w'’ ]+?)\s*(?:\([^)]*\)\s*)?due (\d{4}-\d{2}-\d{2})"),
                 re.compile(r"([A-Z][\w'’ ]+?)\s*\(due (\d{4}-\d{2}-\d{2})")]


def load(name):
    path = ROOT / "data" / name
    if not path.exists():  # suggestions and overviews are optional
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def avg(xs):
    xs = [x for x in xs if x]
    return round(sum(xs) / len(xs), 1) if xs else None


OVERVIEWS = {}
COVERS = set()


def cover(asin):
    return f"covers/{asin}.jpg" if asin in COVERS else ""


def book_card(b):
    ov = OVERVIEWS.get(b["id"], {})
    return {"overview": ov.get("overview", ""), "cues": [c.strip() for c in ov.get("cues", "").split(";") if c.strip()],
            "id": b["id"], "title": b["title"], "cover": cover(b["asin"]), "no": b["series_no"], "status": b["status"],
            "narrator": b["narrator"], "hours": b["audio_hours"], "year": b["year"],
            "audible": b["audible_url"], "goodreads": b["goodreads_url"],
            "rating": b["audible_rating"], "subgenre": b["subgenre"], "notes": b["notes"]}


def build_queue(books, series):
    by_series = defaultdict(list)
    for b in books:
        by_series[b["series_id"] or "solo-" + b["id"]].append(b)
    author_avg = defaultdict(list)
    for b in books:
        if b["status"] == "Read" and b["rating"]:
            for a in b["author"].split(" & "):
                author_avg[a].append(num(b["rating"]))

    queue = []
    for sid, bs in by_series.items():
        bs.sort(key=lambda b: num(b["series_no"]) or 0)
        todo = [b for b in bs if b["status"] in OPEN]
        if not todo:
            continue
        s = series.get(sid, {})
        read = [b for b in bs if b["status"] == "Read"]
        s_avg = avg([num(b["rating"]) for b in read])
        a_avg = avg([x for a in todo[0]["author"].split(" & ") for x in author_avg[a]])
        nxt = todo[0]
        owned = nxt["status"] in ("Owned – Unread", "Reading")
        if nxt["status"] == "Reading":
            tier, score = "reading", 1000
        elif read:
            tier, score = "continue", 500 + (s_avg or a_avg or 3) * 20 + (10 if owned else 0) - len(todo) * 0.1
        elif owned:
            tier, score = "owned", 300 + (a_avg or 3) * 20
        else:
            tier, score = "wishlist", 100 + (a_avg or 3) * 20
        queue.append({
            "key": sid, "series": s.get("series") or nxt["series"], "author": nxt["author"],
            "standalone": s.get("series_status") == "standalone" or not nxt["series"],
            "status": s.get("series_status", ""), "total": s.get("series_total", ""),
            "read": len(read), "avg": s_avg, "author_avg": a_avg, "tier": tier, "score": round(score, 2),
            "synopsis": s.get("synopsis", ""), "next": book_card(nxt),
            "more": [book_card(b) for b in todo[1:]],
        })
    queue.sort(key=lambda q: -q["score"])
    return queue


def build_watch(books, series):
    by_series = defaultdict(list)
    for b in books:
        by_series[b["series_id"]].append(b)
    watch, timeline, worlds = [], [], []
    for s in series:
        if s["watch"] not in ("priority", "wishlist"):
            continue
        bs = sorted(by_series[s["series_id"]], key=lambda b: num(b["series_no"]))
        coming = [b for b in bs if b["status"] == "Not Released"]
        if s["series_status"] != "ongoing" and not coming:
            if s["watch"] == "priority" and s["world"]:
                worlds.append(s["world"])
            continue
        read = [b for b in bs if b["status"] == "Read"]
        nxt = []
        for b in coming:
            m = DATE.search(b["notes"])
            d = m.group(1) if m else ""
            nxt.append({"title": b["title"], "no": b["series_no"], "date": d, "notes": b["notes"], "audible": b["audible_url"]})
            if d:
                timeline.append({"date": d, "title": b["title"], "series": s["series"], "level": s["watch"]})
        if not coming:
            m = next((m for rx in NEXT_IN_NOTES if (m := rx.search(s["notes"]))), None)
            if m:
                timeline.append({"date": m.group(2), "title": m.group(1).strip(), "series": s["series"], "level": s["watch"]})
        watch.append({"key": s["series_id"], "series": s["series"], "author": s["author"], "level": s["watch"],
                      "status": s["series_status"], "total": s["series_total"], "read": len(read),
                      "avg": avg([num(b["rating"]) for b in read]), "next": nxt, "notes": s["notes"]})
    order = {"priority": 0, "wishlist": 1}
    watch.sort(key=lambda w: (order[w["level"]], not w["next"], w["series"]))
    timeline.sort(key=lambda t: t["date"])
    return watch, timeline, sorted(set(worlds))


def main():
    books = load("books.csv")
    COVERS.update(p.stem for p in (ROOT / "hub" / "covers").glob("*.jpg"))
    OVERVIEWS.update({o["id"]: o for o in load("book_overviews.csv")})
    series_rows = load("series.csv")
    series = {s["series_id"]: s for s in series_rows}
    queue = build_queue(books, series)
    watch, timeline, worlds = build_watch(books, series_rows)
    sugg = [s for s in load("suggestions.csv") if s["decision"] not in ("picked", "rejected")]
    rated = defaultdict(list)
    for b in books:
        if b["status"] == "Read" and b["rating"]:
            rated[b["series"]].append(num(b["rating"]))
    for s in sugg:
        s["audible"] = AUD_WEB + s["asin"] if s["asin"] else ""
        s["cover"] = cover(s["asin"])
        s["because_avg"] = avg(rated.get(s["because"], []))
    data = {"built": date.today().isoformat(), "queue": queue, "watch": watch, "timeline": timeline,
            "worlds": worlds, "suggestions": sugg,
            "counts": {"read": sum(b["status"] == "Read" for b in books), "books": len(books)}}
    tpl = (ROOT / "hub" / "template.html").read_text(encoding="utf-8")
    owner = CONFIG.get("owner") or ""
    html = tpl.replace("{{OWNER}}", f"{owner}'s" if owner else "My")
    html = html.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    (ROOT / "hub" / "hub.html").write_text(html, encoding="utf-8", newline="\n")
    print(f"{len(queue)} queue entries, {len(watch)} watched series, {len(timeline)} dated releases, "
          f"{len(sugg)} suggestions -> hub/hub.html")


if __name__ == "__main__":
    main()
