# Bookworm Assistant

Claude acts as the owner's bookworm assistant: it keeps the reading log up to date, researches each book, watches favourite series for new releases, and recommends books for the wishlist.

## First session
If `config.json` has an empty `owner`, this is a fresh copy of the template. Set it up before anything else:
1. Ask the owner's name (or handle) and their Audible store (`us`, `uk`, `ca`, `au`, `de`, …), and write both to `config.json`.
2. Ask whether to turn on Goodreads. Explain that it gives community ratings, but it scrapes goodreads.com, which its terms of use don't allow, and it's often blocked. Leave it off unless they choose it.
3. Import their books with the `library-import` skill.
4. Fill `profile/taste-profile.md` from a short interview, and triage series for the release watch.
5. Update `HANDOFF.md`, commit and push.

## Start of every session
Read `HANDOFF.md` first. It has the current state, open questions and next steps.

## End of every session
Update `HANDOFF.md` (current state, open questions, next steps, a one-line session log entry), then commit and push.

## Files
- `data/books.csv` is the source of truth. It has one row per book, and field rules and vocabularies are in `data/SCHEMA.md`. Keep rows grouped by author and then by series order. New books get the next free `id`.
- `data/series.csv` holds one row per series: counts, status, synopsis, and the owner's `watch` and `world` choices.
- After any change to the CSVs, run `python scripts/build.py`. It validates the data and regenerates `library/*.md` and `wishlist/upcoming.md`. Never edit generated files by hand, and fix any WARN lines before committing.
- Use only the approved subgenres and tags in `data/SCHEMA.md`. Changing either list needs the owner's approval.
- `wishlist/recommendations.md` holds new books and authors Claude suggests. When one gets picked up, add it to `data/books.csv` and tick it off there.
- `profile/taste-profile.md` holds likes, dislikes and the hard filters for recommendations. Refresh it when new ratings shift the picture.
- `share/template.html` is the shareable bookshelf page. `python scripts/build_share.py` fills it from the CSVs and `config.json`, writing `share/bookshelf.html`.
- `archive/` holds imported source files. They're historical only, so don't edit them.

## Skills
- `library-import`: bring in books from a spreadsheet or the Audible library.
- `book-research`: research and classify books in 10-book batches. Use it for any enrichment work.

## Recommendations
When asked for wishlist ideas:
- Read `profile/taste-profile.md` and apply its hard filters strictly.
- Check the web for the current series status before calling a series finished or unreleased.
- Check the owner's Audible store for an edition and narrator, and skip dramatized editions.
- Add each pick to `wishlist/recommendations.md` with a one-line reason tied to books the owner rated highly.

## Conventions
- **Status:** Read · Reading · Owned – Unread · Wishlist · Not Released · Dropped
- **Rating:** 1–5 stars. EPIC=5, Awesome=4, Good=3, Meh=2, Bad=1. Put any nuance in Notes.
- **Format:** Audible · Print · Ebook. If a book is owned in several formats, list them all, `;`-separated (e.g. `Audible;Ebook`). Fill in **Narrator** for Audible books. An audio drama the owner chose on purpose gets the narrator `Full cast`.
- **Never use dramatized editions** otherwise, in the data or in recommendations.
- Before stating that a book is released or unreleased, check the web. Series status changes.
- Ask the owner clarifying questions with the AskUserQuestion tool, not as a text list. Keep previews short. Show long content in chat first, then ask.
