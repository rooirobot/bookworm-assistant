---
name: book-research
description: Research and classify book metadata for the bookshelf (data/books.csv and data/series.csv). Covers series, length, IDs and links, ratings, awards, subgenre, tags, tone, POV, pacing and complexity, plus spoiler-free series synopses. Use when enriching books in the CSV, running a research batch, or adding a new book with full data.
---

# Book research

Fill the researched fields of `data/books.csv` and `data/series.csv`. The field rules and the approved subgenre and tag lists are in `data/SCHEMA.md`. Read it first, because it is the authority.

**Researched book fields:**
- `year`, `publisher`
- `isbn13`, `asin`, `goodreads_url`, `audible_url`
- `pages`, `audio_hours`
- `subgenre`, `tags`, `tone`, `humour`, `pov`, `pacing`, `complexity`
- `gr_rating`, `gr_count`, `audible_rating`, `audible_narration`, `awards`, `data_as_of`

`goodreads_url`, `gr_rating` and `gr_count` stay blank unless Goodreads is switched on in `config.json` (see "Goodreads" below).

**Researched series fields** (done once per series, the first time a batch reaches it): `series_total`, `series_status`, `synopsis`, `goodreads_series_url`, `data_as_of`.

**Synopsis rules:**
- 2–3 sentences, spoiler-free: the premise, the world and the lead character(s) as of book 1
- written in your own words, never copied from a publisher blurb or review site

**Never touch the owner's own fields:**
- `watch` and `world` in `data/series.csv`
- `status`, `rating`, `format`, `narrator`
- `favourite`, `reread`, `notes`

## Output

Researchers do not edit the CSVs. Each batch writes one JSON file, `.work/batch-<first id>.json`:

```json
{"books": [{"id": "012", "year": "2006", "...": "...", "confidence_notes": "..."}],
 "series": [{"series_id": "mistborn", "series_total": "3", "series_status": "complete", "synopsis": "...", "data_as_of": "2026-09-30", "notes": "..."}]}
```

- Every researched field is a string, with `""` when a value is unknown.
- `confidence_notes` is a short list of anything uncertain.
- If a series already has its facts in `series.csv`, copy `series_total` and `series_status` onto each book object instead of adding a series entry.

**Never guess a number.** An empty value with a note beats a plausible one that's wrong.

## Sources, in order

Use the helper `lookup.py` in this skill's folder. It prints JSON.

```
python .claude/skills/book-research/lookup.py aud-search "<title> <author>"
python .claude/skills/book-research/lookup.py aud <ASIN>
python .claude/skills/book-research/lookup.py ol-search "<title> <author>"
python .claude/skills/book-research/lookup.py ol-editions <Open Library work id>
```

1. **Audible catalog API (`aud-search`, then `aud`):** `asin`, `audio_hours`, `audible_rating`, `audible_narration`, the narrator (to cross-check the CSV), the publisher and the series position. No login needed. The store comes from `audible_store` in `config.json`.
2. **Open Library (`ol-search`, then `ol-editions`):** ISBNs, page counts and publishers per edition. Its `first_published` year is often wrong (e.g. it says 2001 for The Final Empire, which came out in 2006), so confirm the year with a second source.
3. **WebSearch:** first publication year, awards, the current series status (was a new book announced? is it finished?), and any gap the tools above can't fill.
4. **Goodreads (opt-in):** only when `"goodreads": true` in `config.json`. See below.

**Checking the store:** the Audible API can return editions that aren't sold in your store. `https://api.audnex.us/books/<ASIN>?region=<store>` helps, but it also returns other-market editions that your store happens to sell, so check the publisher as well.

**Finding your store's ASIN when search only returns another market's edition:** take a known ASIN from the same series and request it with `response_groups=relationships`. The result lists the ASINs of the other books in the series. When it returns a series record instead, query that series record with `response_groups=relationships` again. Some ASINs look like ISBNs, and that's normal.

## Rules and pitfalls

- **Never use dramatized editions.** Skip any Audible product marked "Dramatized Adaptation", "full cast", GraphicAudio, or split into parts ("Part 1 of 2"). Use the regular unabridged audiobook. A multi-POV book read by several narrators is a regular edition, not a dramatization. The exception is an audio drama the owner chose on purpose, marked by `Full cast` in the book's narrator field. After a batch, `python scripts/audit_editions.py` checks every ASIN at no token cost.
- **The edition the owner has wins.** When the CSV lists a narrator, use the ASIN of that narrator's edition.
- **Otherwise, use your store's regular edition.** Audible search often returns another market's edition first. Match the narrator and publisher, and filter by the SKU prefix when a series has two lines (e.g. `BK_BRLL` vs `BK_RHUK`).
- **Keyword search misses some backlists.** Search by author name instead.
- **`publisher`:** the first publisher in your store's market. `year` is the first publication anywhere.
- **`isbn13` and `pages`:** use the first print edition in your store's market. Find it with `ol-editions`. Converting a sourced ISBN-10 to ISBN-13 is exact, so it's allowed. Never infer an ISBN from a publisher's numbering sequence. When sources disagree on pages by more than 10, note the other figure.
- **Check years that were already in the CSV.** Imported spreadsheets are often wrong.
- **Short, common titles** return junk matches. Add the series name or author to the query.
- **`series_total`:** count published books plus books with an announced title. Put the plan in the note, e.g. "5 published; 10 planned". Novellas numbered x.5 don't count. Omnibus editions are split into their original novels.
- **`series_status`:**
  - `complete`: the author or publisher has said the series is finished
  - `ongoing`: more books are announced or expected
  - `standalone`: the book isn't part of a series

  If you're unsure, pick `ongoing` and add a note. This field drives the "finished series only" filter, so be careful with it.
- **`awards`:** major awards only: Hugo, Nebula, World Fantasy, Locus, BSFA, Arthur C. Clarke, Gemmell (Legend, Morningstar, Ravenheart), Goodreads Choice, Audie and SPFBO finalist or winner. Write them as `Award (won 2014)` or `Award (nom 2011)`, separated by `;`. **Awards belong to the edition:** an Audie won by a dramatized adaptation doesn't count for the book.
- **Audible ratings:** use the display values (1 decimal), not the raw averages.
- **`data_as_of`:** today's date.

Title-specific findings live in `known-editions.md` next to this file. Read it before researching a series it mentions, and add to it when you learn something new.

## Classification

Classification is a judgement call, so keep it consistent. The sample books set the scale until your own batches replace them:

| Field | Examples |
|---|---|
| `complexity` | dense: Gardens of the Moon · moderate: The Way of Kings, Red Rising · light: Storm Front |
| `pacing` | slow: The Way of Kings, The Name of the Wind, The Blade Itself · medium: Gardens of the Moon · fast: Red Rising, Storm Front |
| `tone` | dark: The Blade Itself, Gardens of the Moon, Red Rising · balanced: The Way of Kings, Storm Front · light: Good Omens |
| `humour` | lots: Storm Front, Good Omens · some: The Way of Kings, The Blade Itself, Red Rising · none: reserve for genuinely humourless books |

Within one series, match the classification of the books already researched unless a book clearly differs.

**Subgenre:** pick the one that best matches the book. When two fit, name the runner-up in `confidence_notes`.

**Tags:**
- Use 3–6 tags, only from the approved list.
- Tag what the book is actually about, not what merely appears in it.
- Never invent a tag. If an important trait has no matching tag, note it in `confidence_notes`, since that's input for extending the list.

## Running a batch

**Research in batches of 10.** A 10-book batch costs roughly 90k tokens. Run one batch per request unless the owner asks for more.

1. Run `python scripts/next_batch.py` to pick the next 10 books. It picks books that have no `data_as_of` yet, keeps series together, and continues authors that are already started.
2. Run one background agent for the batch. Give it this skill, the batch rows it printed, and the output path `.work/batch-<first id>.json`.
3. **Don't hang:**
   - write the batch file early and update it after each series
   - spend at most about 3 minutes per book, and leave a field blank with a note rather than keep digging
   - give every network call a timeout (`curl --max-time 20`, `Invoke-RestMethod -TimeoutSec 20`)
4. **Save tokens:** use `lookup.py` first, and WebSearch only for the gaps. Within one series, look up the shared facts once.
5. The agent runs `python scripts/merge_batch.py .work/batch-<first id>.json --dry-run` and fixes errors until it prints OK.
6. Then run it without `--dry-run`. It checks the batch (approved vocabulary, valid values, no duplicate ids, series fields present, no dramatized editions) and merges it into both CSVs.
7. Run `python scripts/audit_editions.py`, `python scripts/build.py` and `python scripts/build_share.py`. If `share_url` is set in `config.json`, republish `share/bookshelf.html` to it. Commit and push.
8. Post a short chat summary of the uncertain items and any new series synopses. The owner corrects anything by replying.

## Goodreads (opt-in)

Goodreads has the richest community ratings, but it has no public API, and scraping it is against its terms of use. It also bot-blocks often (an empty HTTP 202). The template leaves it off. If the owner turns it on (`"goodreads": true`):
- `gr-search "<title> <author> <series>"` gives the URL, rating, rating count and pages, and usually still works when book pages are blocked.
- `gr <url>` gives the first-published year, awards, series and genres.
- Go slowly: wait between calls, and don't retry more than once.
