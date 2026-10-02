# Handoff

_Last updated: (not set up yet)_

## Current state
- Fresh copy of the Bookworm Assistant template.
- `data/books.csv` holds 16 **sample** books (fully researched; 10 read, 6 unread) and `data/series.csv` their series. They show what finished rows look like.
- `config.json` has no owner yet.
- `data/suggestions.csv` and `data/book_overviews.csv` hold sample rows for the Reading Hub demo. Replace them once the owner's own suggestions come in.

## Open questions for the owner
- Keep any of the sample books, or delete them all?
- Use Goodreads? (Off by default. See README "Data sources".)

## Next steps
1. First-session setup (see `CLAUDE.md`): name and store in `config.json`, import with the `library-import` skill, taste profile, release-watch triage.
2. Research in 10-book batches with the `book-research` skill ("next batch").
3. Turn on the release-watch Action (README "Release watch") and record a baseline.
4. Build and publish the share page.
5. Ask for wishlist suggestions, then build and publish the Reading Hub (`CLAUDE.md`, "Reading Hub").

## Session log
