"""Check a research batch and merge it into the master data.

Usage: python scripts/merge_batch.py .work/batch-<id>.json [--dry-run]

The batch file is {"books": [...], "series": [...]} as described in the book-research skill.
Checks: known book ids, no duplicates, approved subgenres and tags, valid enum values, and
series_total/series_status present for every series book. On any error nothing is written.
It merges researched fields only; the owner's own fields are never touched.
Audio dramas are refused unless the owner put "Full cast" in the book's narrator field
(meaning they chose that audio drama on purpose).
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build  # noqa: E402

BOOK_FIELDS = ("year publisher isbn13 asin goodreads_url audible_url pages audio_hours subgenre tags tone humour pov "
               "pacing complexity gr_rating gr_count audible_rating audible_narration awards data_as_of").split()
SERIES_FIELDS = ("series_total", "series_status", "synopsis", "goodreads_series_url", "data_as_of", "notes")


def rw(path, rows=None):
    if rows is None:
        with open(path, encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def main():
    src, dry = Path(sys.argv[1]), "--dry-run" in sys.argv
    batch = json.loads(src.read_text(encoding="utf-8"))
    books, series = rw(build.DATA), rw(build.SERIES)
    by_id = {b["id"]: b for b in books}
    ser_by_id = {s["series_id"]: s for s in series}
    batch_series = {s["series_id"]: s for s in batch.get("series", [])}

    errs, ids = [], [str(b["id"]) for b in batch["books"]]
    errs += [f"duplicate id {i}" for i in set(ids) if ids.count(i) > 1]
    for b in batch["books"]:
        i = str(b["id"])
        if i not in by_id:
            errs.append(f"{i}: not in books.csv")
            continue
        tags = [t.strip() for t in str(b.get("tags", "")).split(";") if t.strip()]
        errs += [f"{i}: unknown tag {t!r}" for t in tags if t not in build.TAGS]
        if b.get("subgenre") and b["subgenre"] not in build.SUBGENRES:
            errs.append(f"{i}: unknown subgenre {b['subgenre']!r}")
        for f, ok in build.ENUMS.items():
            if b.get(f) and b[f] not in ok:
                errs.append(f"{i}: bad {f} {b[f]!r}")
        sid = by_id[i]["series_id"]
        if by_id[i]["series"]:
            known = batch_series.get(sid) or ser_by_id.get(sid) or {}
            if not (known.get("series_total") or b.get("series_total")) or not (known.get("series_status") or b.get("series_status")):
                errs.append(f"{i}: series_total/series_status missing for {sid}")
        if re.search(r"dramati[sz]ed|adaptation|full[- ]cast", json.dumps({k: v for k, v in b.items() if k != "confidence_notes"}), re.I) and by_id[i]["narrator"].lower() != "full cast":
            errs.append(f"{i}: looks like a dramatized/full-cast edition; use the regular unabridged audiobook")
    for sid in batch_series:
        if sid not in ser_by_id:
            errs.append(f"series {sid}: not in series.csv")
    if errs:
        print("NOT MERGED:\n  " + "\n  ".join(errs))
        sys.exit(1)

    for b in batch["books"]:
        row = by_id[str(b["id"])]
        for k in BOOK_FIELDS:
            if str(b.get(k, "")):
                row[k] = str(b[k])
        # series facts may arrive on the book objects only
        s = ser_by_id.get(row["series_id"])
        if s and row["series"]:
            for k in ("series_total", "series_status"):
                if b.get(k) and not s[k]:
                    s[k] = str(b[k])
    for sid, u in batch_series.items():
        s = ser_by_id[sid]
        for k in SERIES_FIELDS:
            if str(u.get(k, "")):
                s[k] = str(u[k])
    notes = [f"{b['id']} {by_id[str(b['id'])]['title']}: {b['confidence_notes']}" for b in batch["books"] if b.get("confidence_notes")]
    if dry:
        print(f"OK (dry run): {len(ids)} books, {len(batch_series)} series would merge")
        return
    rw(build.DATA, books)
    rw(build.SERIES, series)
    done = sum(1 for b in books if b["data_as_of"])
    print(f"Merged {len(ids)} books, {len(batch_series)} series. Researched: {done} of {len(books)}.")
    if notes:
        print("Uncertain:\n  " + "\n  ".join(notes))


if __name__ == "__main__":
    main()
