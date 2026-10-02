"""Monthly release check for the series marked "priority" (🔔 Must know) in data/series.csv.

Plain Python with no LLM, so it runs for free in a GitHub Action.

Signals:
  - Goodreads series page (only if "goodreads": true in config.json):
    a numbered book we don't have yet                            -> "title announced" (or released, if dated in the past)
  - Audible catalog (store from config.json), by author: an English, unabridged book
    that is new to us, with a future release date                -> "release date announced"
    and a past release date                                      -> "released"
  For finished series, new books by the same author are reported too, because a
  new book in the same world usually shows up that way. Claude or you
  confirms whether it really belongs to the world.

It remembers what it has already reported in data/release_watch_state.json, so each
piece of news is reported once. It writes new events to release_report.md (the
GitHub Action turns that file into an issue) and prints them.

Usage: python scripts/release_watch.py [--baseline]
  --baseline  records everything currently found as already known, without reporting it.
              Use it once, after reviewing the first run's findings.
"""
import csv
import html
import json
import re
import sys
import time
import urllib.parse
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "book-research"))
from lookup import AUD, AUD_WEB, CONFIG, get, gr_book, gr_search  # noqa: E402

SERIES = ROOT / "data" / "series.csv"
BOOKS = ROOT / "data" / "books.csv"
STATE = ROOT / "data" / "release_watch_state.json"
REPORT = ROOT / "release_report.md"
TODAY = date.today().isoformat()
NOISE = re.compile(r"dramati[sz]ed|adaptation|\(part \d|part \d+ of|\d+ of \d+\)|collection|box ?set|omnibus|books? \d+\s*[-–]\s*\d+|sampler|excerpt|international edition|summary of|study guide", re.I)


def norm(t):
    t = re.sub(r"\(.*?\)|:.*$", "", t.lower())
    return re.sub(r"[^a-z0-9]+", " ", t).strip().removeprefix("the ")


def same_series(a, b):
    a, b = norm(a), norm(b)
    return bool(a and b) and (a == b or a in b or b in a)


def load(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def series_url(s, books):
    """Find the Goodreads series URL from the first book in the series (and cache it)."""
    if s["goodreads_series_url"]:
        return s["goodreads_series_url"]
    first = next((b for b in books if b["series_id"] == s["series_id"] and b["goodreads_url"]), None)
    url = first["goodreads_url"] if first else None
    if not url:
        hits = gr_search(f"{s['series']} {s['author']}")
        url = hits[0]["url"] if hits else None
    if not url:
        return ""
    info = gr_book(url)
    urls = [x["url"] for x in info.get("series", []) if x.get("url")]
    s["goodreads_series_url"] = urls[0] if urls else ""
    return s["goodreads_series_url"]


def gr_series_books(url, our_name):
    """Numbered main entries from a Goodreads series page: [(position, title, year or None)].
    Each entry names its own series in brackets, e.g. "La torre blanca (La Rueda del Tiempo, #9)".
    Translations and split editions name a different series there, so only entries whose
    bracket name matches ours (or the page's own series name) are kept."""
    page = get(url)
    h1 = re.search(r"<title>\s*(.*?)\s+Series by", page, re.S)
    names = [our_name] + ([html.unescape(h1.group(1))] if h1 else [])
    out = []
    for m in re.finditer(r'data-react-class="ReactComponents.SeriesList" data-react-props="([^"]+)"', page):
        for e in json.loads(html.unescape(m.group(1))).get("series", []):
            b = e["book"]
            # "(Series, #3)" or "(Series #3)"; main books only, no x.5 novellas
            m2 = re.search(r"\(([^()]*?),?\s*#(\d+)\)\s*$", b.get("title", ""))
            if not m2 or NOISE.search(b.get("title", "")):
                continue
            if not any(same_series(m2.group(1), n) for n in names):
                continue  # translation or split edition
            title = re.sub(r"\s*\([^()]*#[\d.]+\)\s*$", "", b["title"]).strip()
            year = b.get("publicationDate")
            out.append((m2.group(2), title, int(year) if str(year or "").isdigit() else None))
    return out


def audible_by_author(author, our_series):
    """New English unabridged books by this author. Namesakes are dropped: we keep only the
    Audible author ids that also appear on a book in one of our series for that author."""
    q = urllib.parse.urlencode({"author": author, "num_results": 50, "products_sort_by": "-ReleaseDate",
                                "response_groups": "product_desc,product_attrs,series,contributors"})
    prods = json.loads(get(f"{AUD}?{q}")).get("products", [])
    ours = {norm(x) for x in our_series}
    ids = {a.get("asin") for p in prods if any(same_series(s.get("title", ""), o) for s in p.get("series") or [] for o in ours)
           for a in p.get("authors") or [] if a.get("name", "").lower() == author.lower()}
    if not ids:  # our books are older than the newest 50: look one of our series up directly
        for name in list(our_series)[:2]:
            q2 = urllib.parse.urlencode({"keywords": f"{name} {author}", "num_results": 10,
                                         "response_groups": "product_desc,series,contributors"})
            for p in json.loads(get(f"{AUD}?{q2}")).get("products", []):
                if any(same_series(s.get("title", ""), o) for s in p.get("series") or [] for o in ours):
                    ids |= {a.get("asin") for a in p.get("authors") or [] if a.get("name", "").lower() == author.lower()}
            if ids:
                break
    if not ids:
        raise RuntimeError(f"couldn't confirm which Audible author '{author}' is ours; skipped to avoid namesakes")
    out = []
    for p in prods:
        if not any(a.get("asin") in ids for a in p.get("authors") or []):
            continue
        title = p.get("title") or ""
        if p.get("language", "english") != "english" or p.get("format_type", "unabridged") != "unabridged" or NOISE.search(title):
            continue
        out.append({"asin": p["asin"], "title": title, "release_date": p.get("release_date") or "",
                    "series_names": [s.get("title", "") for s in p.get("series") or []],
                    "series": ", ".join(f"{s.get('title')} #{s.get('sequence')}".rstrip(" #") for s in p.get("series") or [])})
    return out


def main():
    baseline = "--baseline" in sys.argv
    series, books = load(SERIES), load(BOOKS)
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"seen": {}}
    known_titles = {norm(b["title"]) for b in books}
    watched = [s for s in series if s["watch"] == "priority"]
    events, other, authors_done, problems, notes = [], [], set(), [], []
    # the series names that count as "the same world" for each watched author
    world_of = {s["series_id"]: (s["world"] or s["series_id"]) for s in series}
    watched_worlds = {world_of[s["series_id"]] for s in watched}
    world_series = {}
    for s in series:
        if world_of[s["series_id"]] in watched_worlds:
            world_series.setdefault(s["author"], set()).add(s["series"])
    for s in watched:
        world_series.setdefault(s["author"], set()).add(s["world"] or s["series"])

    def report(key, line, bucket=None):
        if key not in state["seen"]:
            state["seen"][key] = TODAY
            if not baseline:
                (events if bucket is None else bucket).append(line)

    for s in watched:
        try:
            url = series_url(s, books) if CONFIG.get("goodreads") else ""
            if url:
                for pos, title, year in gr_series_books(url, s["series"]):
                    # News only: announced (no year) or published this year or last. Older entries are
                    # translations, split editions or old gaps, not new releases.
                    if norm(title) in known_titles or (year and year < date.today().year - 1):
                        continue
                    when = "released" if year and year <= date.today().year else "title announced"
                    report(f"gr:{s['series_id']}:{norm(title)}",
                           f"**{s['series']} #{pos}: {title}**, {when}{f' ({year})' if year else ''} · [Goodreads]({url})")
            time.sleep(1)
        except Exception as e:  # keep going; one failing series shouldn't stop the run
            problems.append(f"{s['series']} (Goodreads): {e}")

        if s["author"] in authors_done:
            continue
        authors_done.add(s["author"])
        try:
            mine = world_series.get(s["author"], set())
            all_mine = {b["series"] for b in books if b["author"] == s["author"] and b["series"]} | mine
            for p in audible_by_author(s["author"], all_mine):
                if norm(p["title"]) in known_titles:
                    continue
                future = p["release_date"] > TODAY
                if not future and p["release_date"] < f"{date.today().year - 1}":
                    continue  # old back-catalogue, not news
                when = f"pre-order, releases {p['release_date']}" if future else f"released {p['release_date']}"
                in_world = any(same_series(n, x) for n in p["series_names"] for x in mine)
                report(f"aud:{norm(s['author'])}:{norm(p['title'])}:{'future' if future else 'out'}",
                       f"**{p['title']}** by {s['author']}{f' ({p['series']})' if p['series'] else ''}: {when} "
                       f"· [Audible]({AUD_WEB}{p['asin']})", None if in_world else other)
            time.sleep(1)
        except Exception as e:
            problems.append(f"{s['author']} (Audible): {e}")

    # cache any series URLs we resolved
    with open(SERIES, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, series[0].keys())
        w.writeheader()
        w.writerows(series)
    STATE.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    for pr in problems:
        print("WARN", pr)
    if problems and not baseline:
        blocked = sum("bot protection" in pr for pr in problems)
        if blocked >= len(watched) // 2:
            notes.append(f"⚠️ Goodreads blocked {blocked} series checks this run, so title announcements may be missed until next month.")
    if events or other:
        body = [f"# Release watch: {TODAY}", ""] + notes + ([""] if notes else [])
        if events:
            body += [f"{len(events)} new item(s) in your 🔔 Must know series and worlds:", ""] + [f"- {e}" for e in events] + [""]
        if other:
            body += ["<details><summary>Other new books by these authors (" + str(len(other)) + ")</summary>", ""]
            body += [f"- {e}" for e in other] + ["", "</details>"]
        body += ["", "_Ask Claude to confirm these and update `data/books.csv` (Not Released or Wishlist rows)._"]
        REPORT.write_text("\n".join(body) + "\n", encoding="utf-8")
        print("\n".join(body))
    else:
        REPORT.unlink(missing_ok=True)
        print("Baseline recorded." if baseline else "No new release news.")


if __name__ == "__main__":
    main()
