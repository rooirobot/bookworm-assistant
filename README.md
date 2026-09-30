# Bookworm Assistant 📚

**Claude Code as your personal librarian.** Keep your reading log as a plain CSV you own. Claude researches every book (series, length, narrator, ratings, awards, subgenre, tone, pacing…), writes spoiler-free series synopses, tells you when your favourite series get a new book, recommends what to read next, and builds a filterable page you can share with other readers.

It's a template: click **Use this template**, open the repo in [Claude Code](https://claude.com/claude-code), and say *"set me up"*.

## Why this and not Goodreads, StoryGraph or Hardcover?

Use those too. They're great for tracking and social features. This fills gaps they leave:

| | Tracking apps | Bookworm Assistant |
|---|---|---|
| Your data | In their database | A CSV in your own repo, readable in Excel |
| Per-book detail | Community tags | Researched fields from a fixed vocabulary: subgenre, 32 tags, tone, humour, POV, pacing, complexity, audio length, narrator |
| Audiobooks | An afterthought | First-class: narrator, hours, the regular edition (dramatized and abridged editions are filtered out) |
| New books in your series | Few do it, and only on one store | A free monthly GitHub Action opens an issue when a series you care about gets a title, date or release, including new books in the same world |
| Recommendations | Algorithmic | Claude reads your ratings and your own hard filters ("no unfinished series", "no YA") |
| Sharing | A profile page | A standalone page with filters and an *"If you liked X"* matcher, built from your ratings |

## What you need
- [Claude Code](https://claude.com/claude-code) and a Claude plan
- Python 3.10+ (standard library only)
- A GitHub account, for the release watch
- Optional: [Claude in Chrome](https://claude.com/chrome), to import your Audible library

## Getting started
1. **Use this template** → create your repo (private is a good idea: it holds your ratings and notes).
2. Clone it and run `claude` in the folder. Say *"set me up"*. Claude will:
   - ask your name, your Audible store, and whether to use Goodreads (see "Data sources")
   - import your books from a spreadsheet (xlsx/csv, a Goodreads or StoryGraph export) or from your Audible library
   - help you rate unrated books series by series, and interview you for a taste profile
   - ask which series you'd want release alerts for
3. Say *"next batch"* to research 10 books at a time.
4. Say *"find me some books for my wishlist"* whenever you want recommendations.

## Cost
Research uses Claude tokens: roughly **90k tokens per 10 books**. That's why it runs in batches you start yourself. A 200-book library is about 20 batches, spread over as many sessions as you like. Everything else is free: the scripts, the release watch and the page are plain Python with no AI calls.

## Data sources
- **Audible catalog API**: edition, narrator, length and ratings. It's free and needs no login, but it's unofficial and could change.
- **Open Library**: ISBNs, page counts and publishers. Open data.
- **Web search**: awards, first publication year, series status.
- **Goodreads: off by default.** It has the best community ratings, but no public API, and scraping it is against its terms of use. It's also frequently blocked. If you turn it on (`"goodreads": true` in `config.json`), that's your call.

## Release watch
`.github/workflows/release-watch.yml` runs on the 1st of every month (or by hand from the **Actions** tab). For every series marked `priority` in `data/series.csv`, it checks Audible (and Goodreads, if enabled) for new titles, dates and releases, and opens an issue, which GitHub emails you. It filters out dramatized editions, collections and translations, and ignores namesake authors.

To turn it on: in your repo's **Settings → Actions → General**, allow Actions and give workflows **read and write** permission. The first run reports everything it finds, so run `python scripts/release_watch.py --baseline` once to mark the current state as known.

## The shareable page
`python scripts/build_share.py` writes `share/bookshelf.html`: your Read books with your ratings and notes (never what you own), a shelf of your 5★ series, filters (rating, finished series, subgenre, tone, pacing, complexity, tags, narrator, listening time), a series view, and an *"If you liked…"* matcher. It's a single self-contained HTML file, so you can host it anywhere. In Claude Code, Claude can publish it as a private claude.ai artifact for you to share.

## Layout

| Path | What's in it |
|---|---|
| `data/books.csv` | **Master data.** One row per book. Starts with 10 sample books |
| `data/series.csv` | One row per series: count, status, synopsis, watch flag |
| `data/SCHEMA.md` | Field definitions and the fixed subgenre and tag lists |
| `config.json` | Your name, Audible store, Goodreads switch, share-page text |
| `scripts/` | Build, batch picking, merging, the edition audit, the release watch, and the share page |
| `.claude/skills/` | `library-import` and `book-research`: how Claude does the work, including `known-editions.md`, a growing list of edition traps |
| `library/`, `wishlist/upcoming.md` | Generated views (don't edit) |
| `profile/taste-profile.md` | Your likes, dislikes and hard filters |
| `wishlist/recommendations.md` | Claude's suggestions |
| `HANDOFF.md` | Where things stand, so each session picks up where the last left off |

## Customising
- **Genres:** the subgenre and tag lists in `data/SCHEMA.md` lean toward fantasy and sci-fi. Ask Claude to propose a list for your genres. Change it before the first research batch, then keep it fixed.
- **Page text:** `tagline` and `intro` in `config.json`.
- **Region:** `audible_store` in `config.json`.

## Credits
Started as [RooiRobot](https://github.com/RooiRobot)'s personal bookshelf. Contributions to `known-editions.md` are especially welcome.

MIT licensed. Not affiliated with Audible, Amazon, Goodreads, Open Library or Anthropic.
