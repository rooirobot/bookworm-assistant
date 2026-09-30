---
name: library-import
description: Bring an existing reading list into the bookshelf, from any spreadsheet (xlsx, csv, Google Sheets export, a Goodreads or StoryGraph export) or from the owner's Audible library. Maps columns, statuses and ratings, asks about anything ambiguous, and writes rows to data/books.csv and data/series.csv. Use for first-time setup or when adding a batch of books from another source.
---

# Library import

The goal is clean rows in `data/books.csv` with the **owner's fields** filled: `title`, `author`, `series`, `series_no`, `status`, `rating`, `format`, `narrator` and `notes`. The researched fields come later, from the `book-research` skill.

Ask the owner questions with the AskUserQuestion tool, a few at a time. Keep previews short. Put long lists in chat first, then ask.

## 1. Clear the sample data

The template ships with 10 sample books. Before the first import, ask whether to delete them. They're only examples, but they're fully researched, so some people keep the ones they've actually read.

## 2. Read the source

**A spreadsheet** (xlsx, csv, ods):
- Read it with Python (`openpyxl` for xlsx, `csv` otherwise). Show the owner the columns you found and how you plan to map them.
- Keep the original file in `archive/` and never edit it.
- Common columns to map: title, author, series (often "Series #3" in the title, e.g. Goodreads' "Title (Series, #3)"), status or shelf, rating, date read, format, notes.

**The Audible library** (no export exists, so read the owner's own library page):
- This needs Claude in Chrome with the owner already signed in to Audible. **Never type their password.** If they aren't signed in, ask them to sign in themselves.
- Open `https://www.audible.<store>/library/titles?pageSize=50` (the store is `audible_store` in `config.json`), and read each page with `get_page_text`. Collect title, author, narrator, series and position, plus progress ("Finished" or time left).
- Treat anything with under 2 hours left as Read, and ask about anything in between.
- Store: Format `Audible`, and the narrator as listed (the edition the owner has).

## 3. Clean up

- **Fiction only**, unless the owner wants otherwise. List the non-fiction and children's titles you'd skip, and confirm.
- **Split omnibus editions** into their original novels ("The Riyria Revelations" → 3 books).
- **Fix obvious typos** in titles and author names, and list what you changed.
- **Merge duplicates** across sources. When a book is owned in several formats, join them with `;` (e.g. `Audible;Ebook`).
- **Fill series gaps:** if the owner has books 1 and 3, ask about book 2. It's often read in another format.

## 4. Map statuses and ratings

- **Status** must be one of: Read, Reading, Owned – Unread, Wishlist, Not Released, Dropped. Propose a mapping for the source's values (e.g. Goodreads `read` → Read, `currently-reading` → Reading, `to-read` → Wishlist), and confirm it.
- **Rating** is 1–5 stars: 5 EPIC, 4 Awesome, 3 Good, 2 Meh, 1 Bad. Convert other scales (e.g. 10-point, half stars, words) with a mapping the owner approves. Keep the original wording in `notes` when it says more than a number.
- **Unrated Read books:** ask the owner to rate them series by series. That's much faster than book by book.

## 5. Write the rows

- Give each new book the next free `id` (3 digits). Ids are stable and never reused.
- Keep rows grouped by author, then by series order.
- `series_id` is the series name in kebab-case (`the-first-law`). Standalones get `standalone-<title>`.
- Add a row to `data/series.csv` for every new `series_id`, with `series`, `author` and `world` (for series set in the same world, e.g. Cosmere) filled. Leave the researched fields blank.
- Run `python scripts/build.py` and fix any WARN lines.

## 6. After the import

1. **Taste profile:** interview the owner, briefly, for `profile/taste-profile.md`: favourite books and why, deal-breakers, hard filters for recommendations (e.g. unfinished series, YA, heavy romance), and audio preferences (narrators they love or avoid).
2. **Release watch triage:** show every series where the owner has read more than 2 books, and ask which ones they must hear about the moment a new book is announced. Set `watch` to `priority` for those, `wishlist` for "nice to know", and leave the rest blank.
3. **Research:** offer to start the first `book-research` batch.
4. Update `HANDOFF.md`, then commit and push.
