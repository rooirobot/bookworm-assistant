# Contributing

Bookworm Assistant is an open project, and everyone is welcome to help build it. You don't need to be an expert: plenty of useful contributions are a few lines long.

## Ways to help
- **Share what you learn about editions.** When your research turns up a trap (a UK edition hiding the US one, a dramatization that looks like a regular reading, a series with two narrators), add a line to [`.claude/skills/book-research/known-editions.md`](.claude/skills/book-research/known-editions.md). This is the easiest and most valuable contribution.
- **Report problems.** If a script breaks, the release watch misses a book, or Claude gets stuck on a step, open an issue with what you did and what happened.
- **Add features.** Some ideas that would help lots of readers:
  - importers for more sources (Libby, Kindle, Kobo, Calibre, Hardcover)
  - better support for Audible stores outside the US
  - subgenre and tag lists for other genres (romance, mystery, literary fiction, non-fiction), offered as options at setup
  - more release-watch signals (publisher catalogues, author newsletters)
  - improvements to the shareable page (new filters, better matching, accessibility)
  - Open Library ratings or another open source of community ratings
- **Improve the docs.** If something in the README or the skills confused you, a clearer sentence helps the next person.

## How to contribute
1. Open an issue first for anything bigger than a small fix, so we can agree on the approach.
2. Fork the repo and make your change on a branch.
3. Keep the scripts **standard-library Python only**, so they run anywhere, including the free GitHub Action.
4. Run `python scripts/build.py` and `python scripts/build_share.py` with the sample data, and check that both finish without warnings.
5. Don't include your personal reading data in a pull request. Changes to `data/` should only touch the sample books.
6. Open a pull request that explains what changed and why.

Using Claude Code to write your change is fine, and encouraged.

## Ground rules
- Be kind and assume good intent. People come here because they love books.
- Respect the data sources: no features that depend on breaking a site's terms of use unless they're opt-in and clearly explained, like the Goodreads switch.
- Never add anything that handles a user's passwords or payment details.
