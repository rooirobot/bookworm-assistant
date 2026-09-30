"""Build the shareable bookshelf page from the master data.

Usage: python scripts/build_share.py
Reads data/books.csv and data/series.csv, keeps only Read books, and writes
share/bookshelf.html (share/template.html with the data and the owner/tagline/intro from
config.json embedded). Publish that
file as your bookshelf artifact (share_url in config.json), keeping the same URL.

Only public-facing fields are exported: no format/ownership, no favourite/reread flags.
"""
import csv
import json
from collections import defaultdict
from html import escape as html_escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLASS = ["subgenre", "tags", "tone", "humour", "pov", "pacing", "complexity"]
BOOK_FIELDS = ["id", "title", "author", "series_id", "series", "series_no", "year", "rating", "notes", "narrator",
               "pages", "audio_hours", "audible_narration", "audible_rating", "gr_rating", "gr_count", "awards",
               "goodreads_url", "audible_url"] + CLASS


def load(name):
    with open(ROOT / "data" / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def num(v):
    try:
        f = float(v)
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return None


def main():
    books, series = load("books.csv"), {s["series_id"]: s for s in load("series.csv")}
    read = [b for b in books if b["status"] == "Read"]

    # Books not researched yet borrow the style fields of a researched book in the same
    # series, so filters and the matcher work before every book has its own data.
    donor = {}
    for b in books:
        if b["subgenre"] and b["series_id"] not in donor:
            donor[b["series_id"]] = b
    out = []
    for b in read:
        d = {k: b.get(k, "") for k in BOOK_FIELDS}
        d["estimated"] = False
        if not d["subgenre"] and b["series_id"] in donor:
            for k in CLASS:
                d[k] = donor[b["series_id"]][k]
            d["estimated"] = True
        d["tags"] = [t for t in d["tags"].split(";") if t]
        d["narrator"] = [n for n in d["narrator"].split(";") if n]
        for k in ["rating", "pages", "audio_hours", "audible_narration", "audible_rating", "gr_rating", "gr_count", "year"]:
            d[k] = num(d[k])
        d["series_no"] = b["series_no"]
        out.append(d)

    by_series = defaultdict(list)
    for d in out:
        by_series[d["series_id"]].append(d)
    ser = []
    for sid, bs in by_series.items():
        s = series.get(sid, {})
        if s.get("series_status") == "standalone" or not bs[0]["series"]:
            continue
        rated = [b["rating"] for b in bs if b["rating"]]
        ser.append({"id": sid, "series": s.get("series") or bs[0]["series"], "author": bs[0]["author"],
                    "world": s.get("world", ""), "total": num(s.get("series_total")), "status": s.get("series_status", ""),
                    "synopsis": s.get("synopsis", ""), "read": len(bs),
                    "avg": round(sum(rated) / len(rated), 1) if rated else None})

    data = {"books": out, "series": ser,
            "researched": sum(1 for b in read if b["data_as_of"]), "total_read": len(read)}
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    owner = cfg.get("owner") or "My"
    tpl = (ROOT / "share" / "template.html").read_text(encoding="utf-8")
    for key, val in {"{{OWNER}}": owner if owner == "My" else f"{owner}'s",
                     "{{TAGLINE}}": cfg.get("tagline", ""), "{{INTRO}}": cfg.get("intro", "")}.items():
        tpl = tpl.replace(key, html_escape(val, quote=False))
    html = tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    (ROOT / "share" / "bookshelf.html").write_text(html, encoding="utf-8", newline="\n")
    print(f"{len(out)} read books, {len(ser)} series, {data['researched']} fully researched -> share/bookshelf.html")


if __name__ == "__main__":
    main()
