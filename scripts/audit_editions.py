"""Check that every researched Audible edition is the plain unabridged audiobook.

Usage: python scripts/audit_editions.py

For each book in data/books.csv with an `asin`, it asks the Audible catalog API (free, no login;
the store comes from config.json) and flags editions that are dramatized or full-cast adaptations,
abridged, split into parts, not in English, or narrated by someone other than the narrator you own.
Books whose narrator field says "Full cast" are audio dramas you chose on purpose and are skipped.
It uses no AI tokens and changes nothing; fix flagged rows through a research batch.
"""
import csv
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "book-research"))
from lookup import AUD, get  # noqa: E402

BAD = re.compile(r"dramati[sz]ed|adaptation|full[- ]cast|\(part \d|part \d+ of|\d+ of \d+\)", re.I)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows = list(csv.DictReader(open(ROOT / "data" / "books.csv", encoding="utf-8", newline="")))
    checked, flagged = 0, []
    for r in rows:
        if not r["asin"]:
            continue
        try:
            p = json.loads(get(f"{AUD}/{r['asin']}?response_groups=product_desc,product_attrs,contributors"))["product"]
        except Exception as e:
            flagged.append((r, f"lookup failed: {e}"))
            continue
        checked += 1
        title = p.get("title") or ""
        narrators = [n["name"] for n in p.get("narrators") or []]
        issues = []
        if r["narrator"].lower() == "full cast":  # an audio drama the owner chose on purpose
            checked += 1
            continue
        if BAD.search(title) or any(BAD.search(n) for n in narrators):
            issues.append("dramatized/full-cast or split edition")
        if p.get("format_type") and p["format_type"] != "unabridged":
            issues.append(f"format {p['format_type']}")
        if p.get("language") and p["language"] != "english":
            issues.append(f"language {p['language']}")
        owned = [n for n in r["narrator"].split(";") if n]
        if owned and narrators and not {n.lower() for n in owned} & {n.lower() for n in narrators}:
            issues.append(f"narrator {', '.join(narrators)} but you own {', '.join(owned)}")
        if issues:
            flagged.append((r, "; ".join(issues) + f" [{title}]"))
        time.sleep(0.3)
    print(f"Checked {checked} Audible editions.")
    for r, why in flagged:
        print(f"FLAG {r['id']} {r['title']} ({r['asin']}): {why}")
    if not flagged:
        print("All clean: no dramatized, abridged, split, foreign or wrong-narrator editions.")


if __name__ == "__main__":
    main()
