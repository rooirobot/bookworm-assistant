# Data schema: `data/books.csv`

This is the master data, with one row per book, and it is the source of truth. Edit this file, then run `python scripts/build.py` to rebuild the views in `library/`.

- Leave a cell empty when the value is unknown.
- Lists are `;`-separated.
- `id` is stable. Never reuse or renumber it.

## Fields

| Field | Values / format |
|---|---|
| `id` | 3-digit id, e.g. `042` |
| `title`, `author` | Author names as they appear on the cover. Co-authors are joined with `&`. |
| `series`, `series_no` | `series_no` may be a decimal for novellas, e.g. `2.5` |
| `series_total` | Number of main books in the series, published or announced |
| `series_status` | `complete` · `ongoing` · `standalone` |
| `year` | Year of first publication |
| `publisher` | Original publisher (US if different) |
| `isbn13`, `asin` | ISBN of the first US edition; Audible ASIN (US) |
| `goodreads_url`, `audible_url` | Full URLs |
| `pages`, `audio_hours` | Integer page count; audiobook length in decimal hours |
| `status` | `Read` · `Reading` · `Owned – Unread` · `Wishlist` · `Not Released` · `Dropped` |
| `rating` | `1`–`5`: 5 EPIC · 4 Awesome · 3 Good · 2 Meh · 1 Bad |
| `format` | `Audible` · `Print` · `Ebook`, `;`-separated if owned in more than one |
| `narrator` | `;`-separated |
| `favourite`, `reread` | `Y` or empty |
| `subgenre` | One value from the list below |
| `tags` | 3–6 values from the list below, `;`-separated |
| `tone` | `dark` · `balanced` · `light` |
| `humour` | `none` · `some` · `lots` |
| `pov` | `1st-single` · `1st-multi` · `3rd-single` · `3rd-multi` · `mixed` |
| `pacing` | `slow` · `medium` · `fast` |
| `complexity` | `light` · `moderate` · `dense` |
| `gr_rating`, `gr_count` | Goodreads average (2 decimals) and number of ratings |
| `audible_rating`, `audible_narration` | Audible US overall and performance stars (1 decimal) |
| `awards` | Major wins and nominations, e.g. `Hugo (won); Locus (nom)` |
| `data_as_of` | Date the researched fields were checked, `YYYY-MM-DD` |
| `notes` | Free text |

## Subgenres (pick one)
Epic Fantasy · Grimdark · Heroic Fantasy · Progression Fantasy · Urban Fantasy · Flintlock / Steampunk · Science Fantasy · Portal Fantasy · Historical Fantasy · Humorous Fantasy · Science Fiction · Crime / Thriller · Classic / Children's

## Tags (pick 3–6)
- **World & magic:** hard-magic · soft-magic · gods-religion · dragons · fae · demons-monsters · gunpowder · airships-tech · space · post-apocalyptic
- **Plot:** heist · war-military · political-intrigue · quest · revenge · mystery · chosen-one · magic-school · tournament-trials · coming-of-age · assassin · thief-rogue
- **Character & style:** morally-grey · antihero · found-family · buddy-duo · overpowered-hero · underdog · frame-story · unreliable-narrator · multi-generational · big-cast

# Data schema: `data/series.csv`

One row per series, and one per standalone book. The Must know series are watched by `scripts/release_watch.py`, a monthly GitHub Action.

| Field | Values / format |
|---|---|
| `series_id` | Slug of the series name, e.g. `red-rising`, or `standalone-<title-slug>` |
| `series`, `author` | As in `books.csv` |
| `world` | Shared world for linked series, e.g. `First Law world`, `Elan (Riyria)`, `Cosmere`. Release alerts for finished Must know series cover new books in the same world. |
| `series_total` | Main books published plus announced titles. Omnibuses are split into their original novels, and x.5 novellas don't count. |
| `series_status` | `complete` · `ongoing` · `standalone` |
| `watch` | `priority` (🔔 Must know: alerts) · `wishlist` (no alerts) · `none` (done with it) · empty (not triaged) |
| `goodreads_series_url` | Goodreads series page. The release check fills it in and saves it. |
| `synopsis` | 2–3 sentences, spoiler-free (premise, world and lead as of book 1), in our own words and never a copied blurb |
| `data_as_of` | Date the researched fields were checked |
| `notes` | Free text, e.g. "5 published; 10 planned" |
