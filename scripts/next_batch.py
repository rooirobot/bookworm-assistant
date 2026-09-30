"""Print the next research batch: books in data/books.csv with no data_as_of yet.

Usage: python scripts/next_batch.py [size]      (default 10)

Order: books by an author whose books are already partly researched come first,
so that series stay consistent. Then Read books by rating, Reading, Owned – Unread,
Wishlist and Not Released. Whole series are kept together where they fit.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "books.csv"
STATUS_ORDER = {"Read": 0, "Reading": 1, "Owned – Unread": 2, "Wishlist": 3, "Not Released": 4, "Dropped": 5}


def main():
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    rows = list(csv.DictReader(open(DATA, encoding="utf-8", newline="")))
    todo = [r for r in rows if not r["data_as_of"]]
    started = {r["author"] for r in rows if r["data_as_of"]}

    groups = defaultdict(list)  # (author, series) -> rows, in CSV order
    for r in todo:
        groups[(r["author"], r["series"] or r["title"])].append(r)

    def key(item):
        (author, _), rs = item
        best = min(STATUS_ORDER.get(r["status"], 9) for r in rs)
        rating = max((int(r["rating"]) for r in rs if r["rating"]), default=0)
        return (author not in started, best, -rating, author)

    batch = []
    for _, rs in sorted(groups.items(), key=key):
        if len(batch) + len(rs) <= size or not batch:
            batch.extend(rs[: size - len(batch)] if len(rs) > size else rs)
        if len(batch) >= size:
            break

    print(f"{len(todo)} books still to research; next batch of {len(batch)}:")
    print("id | title | author | series # | narrator")
    for r in batch:
        print(f"{r['id']} | {r['title']} | {r['author']} | {r['series']} {r['series_no']} | {r['narrator']}")


if __name__ == "__main__":
    main()
