"""Build the readable views in library/ from data/books.csv.

Usage: python scripts/build.py
"""
import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "books.csv"
SERIES = ROOT / "data" / "series.csv"
LIB = ROOT / "library"

SUBGENRES = ["Epic Fantasy", "Grimdark", "Heroic Fantasy", "Progression Fantasy", "Urban Fantasy",
             "Flintlock / Steampunk", "Science Fantasy", "Portal Fantasy", "Historical Fantasy",
             "Humorous Fantasy", "Science Fiction", "Crime / Thriller", "Classic / Children's"]
TAGS = """hard-magic soft-magic gods-religion dragons fae demons-monsters gunpowder airships-tech space
post-apocalyptic heist war-military political-intrigue quest revenge mystery chosen-one magic-school
tournament-trials coming-of-age assassin thief-rogue morally-grey antihero found-family buddy-duo
overpowered-hero underdog frame-story unreliable-narrator multi-generational big-cast""".split()
STATUSES = ["Read", "Reading", "Owned – Unread", "Wishlist", "Not Released", "Dropped"]
ENUMS = {"tone": {"dark", "balanced", "light"},
         "humour": {"none", "some", "lots"}, "pacing": {"slow", "medium", "fast"},
         "complexity": {"light", "moderate", "dense"},
         "pov": {"1st-single", "1st-multi", "3rd-single", "3rd-multi", "mixed"}}


SERIES_ENUMS = {"series_status": {"complete", "ongoing", "standalone"}, "watch": {"priority", "wishlist", "none"}}


def load(path=DATA):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def split(v):
    return [x.strip() for x in v.split(";") if x.strip()]


def validate_series(series, rows):
    errs = []
    ids = {x["series_id"] for x in series}
    errs += [f"series row missing for {r['id']} {r['title']} ({r['series_id']!r})" for r in rows if r["series_id"] not in ids]
    for x in series:
        for f, ok in SERIES_ENUMS.items():
            if x[f] and x[f] not in ok:
                errs.append(f"series {x['series_id']}: bad {f} {x[f]!r}")
    return errs


def validate(rows):
    errs = []
    ids = Counter(r["id"] for r in rows)
    errs += [f"duplicate id {i}" for i, n in ids.items() if n > 1]
    for r in rows:
        who = f'{r["id"]} {r["title"]}'
        if r["status"] not in STATUSES:
            errs.append(f"{who}: bad status {r['status']!r}")
        if r["rating"] and r["rating"] not in "12345":
            errs.append(f"{who}: bad rating {r['rating']!r}")
        if r["subgenre"] and r["subgenre"] not in SUBGENRES:
            errs.append(f"{who}: unknown subgenre {r['subgenre']!r}")
        errs += [f"{who}: unknown tag {t!r}" for t in split(r["tags"]) if t not in TAGS]
        for f, ok in ENUMS.items():
            if r[f] and r[f] not in ok:
                errs.append(f"{who}: bad {f} {r[f]!r}")
    return errs


def stars(r):
    return "★" * int(r) + "☆" * (5 - int(r)) if r else ""


def link(title, url):
    return f"[{title}]({url})" if url else title


def num(n):
    return n[:-2] if n.endswith(".0") else n


def build_books(rows):
    c = Counter(r["status"] for r in rows)
    out = ["# Reading Log", "",
           "_Generated from `data/books.csv` by `scripts/build.py`. Don't edit by hand._", "",
           "**Totals:** " + " · ".join(f"{s}: {c[s]}" for s in STATUSES if c[s]), "",
           "| Author | Series | # | Title | Year | Status | Rating | Subgenre | Format | Narrator | Notes |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        fav = " ❤️" if r["favourite"] == "Y" else ""
        out.append(f"| {r['author']} | {r['series']} | {num(r['series_no'])} | "
                   f"{link(r['title'], r['goodreads_url'])}{fav} | {r['year']} | {r['status']} | "
                   f"{stars(r['rating'])} | {r['subgenre']} | {r['format'].replace(';', ',')} | "
                   f"{r['narrator'].replace(';', ',')} | {r['notes']} |")
    return "\n".join(out) + "\n"


def table(title, counter, ratings, head):
    out = [f"## {title}", "", f"| {head} | Books read | Avg rating |", "|---|---|---|"]
    for k, n in counter.most_common():
        avg = sum(ratings[k]) / len(ratings[k]) if ratings[k] else None
        out.append(f"| {k} | {n} | {f'{avg:.1f}' if avg else ''} |")
    return out + [""]


def build_stats(rows):
    read = [r for r in rows if r["status"] == "Read"]
    out = ["# Stats", "", "_Generated from `data/books.csv`. Counts are for books with status Read._", ""]
    for title, head, keyf in [
        ("By subgenre", "Subgenre", lambda r: [r["subgenre"]] if r["subgenre"] else []),
        ("By tag", "Tag", lambda r: split(r["tags"])),
        ("By author", "Author", lambda r: [r["author"]]),
        ("By narrator", "Narrator", lambda r: split(r["narrator"].replace(",", ";"))),
        ("By decade", "Decade", lambda r: [f"{r['year'][:3]}0s"] if r["year"] else []),
        ("By tone", "Tone", lambda r: [r["tone"]] if r["tone"] else []),
        ("By complexity", "Complexity", lambda r: [r["complexity"]] if r["complexity"] else []),
    ]:
        cnt, rat = Counter(), defaultdict(list)
        for r in read:
            for k in keyf(r):
                cnt[k] += 1
                if r["rating"]:
                    rat[k].append(int(r["rating"]))
        if cnt:
            out += table(title, cnt, rat, head)
    return "\n".join(out)


WATCH_LABEL = {"priority": "🔔 Must know", "wishlist": "Wishlist", "none": "Done with it", "": ""}


def build_series(series, rows):
    by = defaultdict(list)
    for r in rows:
        by[r["series_id"]].append(r)
    out = ["# Series Guide", "", "_Generated from `data/series.csv` and `data/books.csv`. Don't edit by hand._", ""]
    for x in (x for x in series if x["series_status"] != "standalone"):
        bs = by[x["series_id"]]
        read = sum(r["status"] == "Read" for r in bs)
        rated = [int(r["rating"]) for r in bs if r["rating"]]
        head = f"## {x['series']}"
        meta = [x["author"]]
        if x["world"]:
            meta.append(x["world"])
        meta.append(f"{read} of {x['series_total'] or len(bs)} read")
        if rated:
            meta.append(f"{sum(rated) / len(rated):.1f}★ avg")
        if x["series_status"]:
            meta.append(x["series_status"])
        if x["watch"]:
            meta.append(WATCH_LABEL[x["watch"]])
        out += [head, "", " · ".join(meta), ""]
        out += [x["synopsis"] or "_Synopsis not researched yet._", ""]
        coming = [r for r in bs if r["status"] == "Not Released"]
        if coming:
            out += ["**Coming:** " + "; ".join(f"{r['title']} ({r['notes'] or 'no date'})" for r in coming), ""]
    return "\n".join(out)


def build_upcoming(series, rows):
    watched = {x["series_id"]: x for x in series if x["watch"] == "priority"}
    worlds = {x["world"] for x in watched.values() if x["world"]}
    out = ["# Release Watchlist", "",
           "_Generated. Series marked 🔔 Must know in `data/series.csv`. For finished series, new books in the same world count._", "",
           "| Series | World | Author | Status | Next book | Notes |", "|---|---|---|---|---|---|"]
    by = defaultdict(list)
    for r in rows:
        by[r["series_id"]].append(r)
    for x in sorted(watched.values(), key=lambda x: (x["world"] or x["series"])):
        coming = [r for r in by[x["series_id"]] if r["status"] == "Not Released"]
        nxt = "; ".join(r["title"] for r in coming) or "—"
        out.append(f"| {x['series']} | {x['world']} | {x['author']} | {x['series_status'] or '?'} | {nxt} | {x['notes']} |")
    out += ["", f"Also watching for new books in these worlds: {', '.join(sorted(worlds))}." if worlds else ""]
    return "\n".join(out) + "\n"


def main():
    rows = load()
    series = load(SERIES)
    errs = validate(rows) + validate_series(series, rows)
    for e in errs:
        print("WARN", e)
    (LIB / "books.md").write_text(build_books(rows), encoding="utf-8", newline="\n")
    (LIB / "stats.md").write_text(build_stats(rows), encoding="utf-8", newline="\n")
    (LIB / "series.md").write_text(build_series(series, rows), encoding="utf-8", newline="\n")
    (ROOT / "wishlist" / "upcoming.md").write_text(build_upcoming(series, rows), encoding="utf-8", newline="\n")
    print(f"{len(rows)} books, {len(series)} series, {len(errs)} warnings -> "
          "library/books.md, library/stats.md, library/series.md, wishlist/upcoming.md")


if __name__ == "__main__":
    main()
