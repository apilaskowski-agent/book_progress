#!/usr/bin/env python3
"""
scripts/add_book.py

CLI tool to fetch online metadata (via Open Library API) and append/update
books in data/books.json.
"""

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import date
from typing import Dict, Any, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from src.models import Book
from src.builder import build

DATA_PATH = os.path.join(REPO_ROOT, "data", "books.json")


def slugify(text: str) -> str:
    """Convert text to URL/ID friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def parse_audio_duration(val: str) -> Optional[int]:
    """Parse '16h 10m', '970m', '16.5h' or plain integer minutes."""
    if not val:
        return None
    val = val.strip().lower()
    if val.isdigit():
        return int(val)

    hours = 0
    mins = 0
    h_match = re.search(r"(\d+(?:\.\d+)?)\s*h", val)
    m_match = re.search(r"(\d+)\s*m", val)

    if h_match:
        hours = float(h_match.group(1))
    if m_match:
        mins = int(m_match.group(1))

    total = int(hours * 60 + mins)
    return total if total > 0 else None


def fetch_open_library_metadata(title: str, author: Optional[str] = None) -> Dict[str, Any]:
    """
    Query Open Library API for book metadata: canonical title, author, cover,
    pages, and genres.
    """
    query_parts = [title]
    if author:
        query_parts.append(author)
    q = urllib.parse.quote(" ".join(query_parts))
    url = f"https://openlibrary.org/search.json?q={q}&limit=3"

    print(f"[INFO] Querying Open Library: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "BookProgressApp/1.0"})

    meta = {
        "title": title,
        "author": author or "Unknown",
        "pages": None,
        "cover_url": None,
        "genres": [],
        "word_count": None
    }

    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            docs = data.get("docs", [])
            if not docs:
                print("[WARN] No match found on Open Library.")
                return meta

            doc = docs[0]
            meta["title"] = doc.get("title", title)
            authors = doc.get("author_name", [])
            if authors:
                meta["author"] = authors[0]

            cover_i = doc.get("cover_i")
            if cover_i:
                meta["cover_url"] = f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg"

            # Genres / Subjects (filter down to readable clean subjects)
            subjects = doc.get("subject", [])
            clean_subjects = [s for s in subjects if len(s) < 30 and not s.lower().startswith("nyt:")]
            meta["genres"] = clean_subjects[:4] if clean_subjects else ["Non-Fiction"]

            # Pages
            pages = doc.get("number_of_pages_median")
            work_key = doc.get("key")

            # If median page count not on work, check top editions
            if not pages and work_key:
                editions_url = f"https://openlibrary.org{work_key}/editions.json?limit=6"
                try:
                    ed_req = urllib.request.Request(editions_url, headers={"User-Agent": "BookProgressApp/1.0"})
                    with urllib.request.urlopen(ed_req, timeout=6) as ed_resp:
                        ed_data = json.loads(ed_resp.read().decode("utf-8"))
                        for entry in ed_data.get("entries", []):
                            p = entry.get("number_of_pages")
                            if p and isinstance(p, int) and p > 20:
                                pages = p
                                break
                except Exception as ed_err:
                    print(f"[WARN] Failed fetching editions: {ed_err}")

            meta["pages"] = pages
            meta["word_count"] = None

    except Exception as e:
        print(f"[WARN] Open Library lookup error: {e}")

    return meta


def add_or_update_book(
    title: str,
    author: Optional[str] = None,
    format_type: str = "book",
    status: str = "reading",
    pages: Optional[int] = None,
    audio_mins: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    rating: Optional[float] = None,
    genres: Optional[list] = None,
    notes: Optional[str] = None,
    words: Optional[int] = None,
    language: str = "English",
    reread: bool = False,
    book_id: Optional[str] = None,
    dry_run: bool = False,
    data_path: str = DATA_PATH
) -> Book:
    """Fetch metadata and persist book record in data/books.json."""
    # 1. Fetch online metadata
    online = fetch_open_library_metadata(title, author)

    final_title = title or online["title"]
    final_author = author or online["author"]
    final_pages = pages or online["pages"]
    final_cover = online["cover_url"]
    final_genres = genres or online["genres"]
    final_words = words  # Left empty/None if not explicitly provided
    base_id = book_id or slugify(final_title)

    # Default start date to today if currently reading and no date provided
    if status == "reading" and not start_date:
        start_date = date.today().isoformat()

    # Load existing books
    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            all_books = json.load(f)
    else:
        all_books = []

    # 2. Re-read / duplicate identification logic
    target_id = base_id
    matching_entries = [b for b in all_books if b.get("id") == base_id or b.get("id", "").startswith(f"{base_id}-")]

    if reread:
        target_id = f"{base_id}-{len(matching_entries) + 1}"
        print(f"[INFO] Recording explicit re-read of '{final_title}' with ID '{target_id}'.")
    elif matching_entries and not book_id:
        exact = next((b for b in all_books if b.get("id") == base_id), None)
        if exact and exact.get("status") == "finished":
            # If the base entry is finished and this entry has different start_date or status is reading, treat as re-read
            if (start_date and start_date != exact.get("start_date")) or status == "reading":
                target_id = f"{base_id}-{len(matching_entries) + 1}"
                print(f"[INFO] Previous finished read of '{final_title}' found. Auto-assigning re-read ID '{target_id}'.")

    book = Book(
        id=target_id,
        title=final_title,
        author=final_author,
        format=format_type,
        status=status,
        start_date=start_date,
        end_date=end_date,
        pages=final_pages if format_type == "book" else None,
        audio_length_minutes=audio_mins if format_type == "audiobook" else None,
        word_count=final_words,
        language=language or "English",
        rating=rating,
        genres=final_genres,
        cover_url=final_cover,
        notes=notes
    )

    book.validate()

    if dry_run:
        print("\n[DRY RUN] Generated book record:")
        print(json.dumps(book.to_dict(), indent=2, ensure_ascii=False))
        return book

    # Update if ID exists, otherwise append
    updated = False
    for i, b in enumerate(all_books):
        if b.get("id") == book.id:
            all_books[i] = book.to_dict()
            updated = True
            print(f"[INFO] Updated existing book '{book.id}'.")
            break

    if not updated:
        all_books.append(book.to_dict())
        print(f"[INFO] Appended new book '{book.id}'.")

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(all_books, f, indent=2, ensure_ascii=False)

    return book


def main():
    parser = argparse.ArgumentParser(description="Add or update a book in book_progress.")
    parser.add_argument("title", help="Book title")
    parser.add_argument("--author", "-a", help="Author name")
    parser.add_argument("--format", "-f", choices=["book", "audiobook"], default="book", help="Format: book or audiobook")
    parser.add_argument("--status", "-s", choices=["finished", "reading", "want_to_read"], default="reading", help="Reading status")
    parser.add_argument("--pages", "-p", type=int, help="Page count (for print/ebook)")
    parser.add_argument("--audio", help="Audio duration, e.g. '16h 10m' or '970m' (for audiobook)")
    parser.add_argument("--words", "-w", type=int, help="Exact word count (optional, left empty if omitted)")
    parser.add_argument("--language", "-l", default="English", help="Language of book/audiobook (default: English)")
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    parser.add_argument("--rating", "-r", type=float, help="Rating (1.0 to 5.0)")
    parser.add_argument("--genres", "-g", help="Comma-separated genres")
    parser.add_argument("--notes", "-n", help="Personal takeaway or review note")
    parser.add_argument("--reread", action="store_true", help="Explicitly record as a new re-read rather than updating an existing entry")
    parser.add_argument("--id", help="Explicit unique book ID (override auto-generated slug)")
    parser.add_argument("--dry-run", action="store_true", help="Print record without saving")
    parser.add_argument("--build", action="store_true", help="Rebuild static site immediately")

    args = parser.parse_args()

    audio_mins = parse_audio_duration(args.audio) if args.audio else None
    genres_list = [g.strip() for g in args.genres.split(",")] if args.genres else None

    book = add_or_update_book(
        title=args.title,
        author=args.author,
        format_type=args.format,
        status=args.status,
        pages=args.pages,
        audio_mins=audio_mins,
        start_date=args.start,
        end_date=args.end,
        rating=args.rating,
        genres=genres_list,
        notes=args.notes,
        words=args.words,
        language=args.language,
        reread=args.reread,
        book_id=args.id,
        dry_run=args.dry_run
    )

    if args.build and not args.dry_run:
        print("[INFO] Rebuilding site...")
        build()


if __name__ == "__main__":
    main()
