# Known editions

Title-specific findings from earlier research, so nobody has to rediscover them. Unless a line says otherwise, these apply to the **US Audible store** (audible.com). Add a line whenever a batch turns up something useful.

## Audio editions

| Series or book | Regular unabridged edition to use | Traps |
|---|---|---|
| Mistborn / Stormlight (Sanderson) | Macmillan Audio; Michael Kramer (and Kate Reading) | Search returns only Gollancz editions. Get the US ASINs via `relationships`. The GraphicAudio Mistborn and its Audie award are a dramatization. |
| The Dresden Files (Butcher) | Penguin Audio; James Marsters | GraphicAudio editions appear in relationships and search. Ghost Story's John Glover recording was replaced by Marsters (2015, B00UVR0LWY). Books 14–18: search returns only Little, Brown (UK), so use the relationships of B005NB2IG0. |
| Codex Alera (Butcher) | Penguin Audio | The UK edition is Little, Brown. |
| The First Law world (Abercrombie) | Recorded Books; Steven Pacey | The standalones have no US-publisher audio, and the US store sells the Gollancz / Steven Pacey editions. |
| The Shattered Sea (Abercrombie) | Recorded Books; John Keating (SKU `BK_RECO`) | Search misses it. Use the relationships of the series record B00KTHVYMM. The UK line is Ben Elliot (`BK_HCUK`). |
| Malazan Book of the Fallen (Erikson) | Brilliance Audio (`BK_BRLL`); Ralph Lister books 1–3, Michael Page books 4–10 | Transworld/RHUK editions (`147355…`, `BK_RHUK`) show up in the same list. |
| The Lord of the Rings (Tolkien) | Andy Serkis (2021; ASINs look like ISBNs, 00084872xx) or Rob Inglis (B0036KVAZ0, B0036KSC1U, B0036GTIBW) | Never the BBC Radio dramatization. |
| Good Omens (Pratchett & Gaiman) | Martin Jarvis (Headline, B07L9DSZ9B) | 0062896954 and B09Q3DNCM1 are full-cast versions. |
| The Kingkiller Chronicle (Rothfuss) | Nick Podehl (US) or Rupert Degas (UK, also sold in the US) | Two readings. Use the one the owner has. |
| The Acts of Caine (Stover) | Audible Studios; Stefan Rudnicki | Keyword search misses it. Search by author. |

## Print editions and data

- **Tor** released some hardcovers and trade paperbacks together (e.g. late Malazan). Open Library often merges them into one record.
- **Goodreads' main edition** for older doorstopper series is usually a later mass-market printing with a much higher page count. Use the first edition's pages.
- **Open Library `first_published`** can be wrong by years. Always confirm the year.
- **Lord of the Rings** predates ISBNs, so leave `isbn13` blank.
