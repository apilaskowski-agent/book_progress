"""
Reading analytics and uniform timeline progression engine.
"""

from collections import defaultdict
from datetime import datetime, date, timedelta
import json
from typing import List, Dict, Any, Tuple
from .models import Book


def load_books(json_path: str) -> List[Book]:
    """Load and validate books from JSON file."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    books = []
    for item in data:
        book = Book(**item)
        book.validate()
        books.append(book)
    return books


def compute_reading_stats(books: List[Book]) -> Dict[str, Any]:
    """Compute high-level KPIs, yearly aggregations, and genre counts."""
    finished_books = [b for b in books if b.status == "finished"]
    reading_books = [b for b in books if b.status == "reading"]

    total_pages = sum(b.pages for b in finished_books if b.format == "book" and b.pages)
    total_audio_mins = sum(b.audio_length_minutes for b in finished_books if b.format == "audiobook" and b.audio_length_minutes)
    total_words = sum(b.estimated_word_count for b in finished_books if b.estimated_word_count)

    # Format audio duration
    h = total_audio_mins // 60
    m = total_audio_mins % 60
    audio_hours_formatted = f"{h}h {m}m" if (h or m) else "0h"

    # Yearly breakdown
    yearly_stats = defaultdict(lambda: {
        "year": 0,
        "total_books": 0,
        "books_count": 0,
        "audiobooks_count": 0,
        "pages_read": 0,
        "audio_minutes": 0,
        "audio_hours_formatted": "",
        "words_read": 0,
        "books": []
    })

    # Genre breakdown
    genre_counts = defaultdict(int)

    for b in finished_books:
        end_d = b.get_end_date()
        year = end_d.year if end_d else 2024
        y = yearly_stats[year]
        y["year"] = year
        y["total_books"] += 1
        if b.format == "book":
            y["books_count"] += 1
            if b.pages:
                y["pages_read"] += b.pages
        elif b.format == "audiobook":
            y["audiobooks_count"] += 1
            if b.audio_length_minutes:
                y["audio_minutes"] += b.audio_length_minutes
        if b.estimated_word_count:
            y["words_read"] += b.estimated_word_count
        y["books"].append(b.to_dict())

        for g in b.genres:
            genre_counts[g] += 1

    # Format yearly audio hours
    for yr, y in yearly_stats.items():
        yh = y["audio_minutes"] // 60
        ym = y["audio_minutes"] % 60
        y["audio_hours_formatted"] = f"{yh}h {ym}m" if (yh or ym) else "0h"

    # Sorted yearly list (descending)
    sorted_years = [yearly_stats[yr] for yr in sorted(yearly_stats.keys(), reverse=True)]

    # Genre list sorted by frequency
    sorted_genres = [{"genre": g, "count": c} for g, c in sorted(genre_counts.items(), key=lambda x: -x[1])]

    return {
        "kpis": {
            "total_finished_books": len(finished_books),
            "total_print_books": sum(1 for b in finished_books if b.format == "book"),
            "total_audiobooks": sum(1 for b in finished_books if b.format == "audiobook"),
            "total_pages_read": total_pages,
            "total_audio_minutes": total_audio_mins,
            "total_audio_hours_formatted": audio_hours_formatted,
            "total_words_read": total_words,
            "currently_reading_count": len(reading_books)
        },
        "yearly_stats": sorted_years,
        "genre_counts": sorted_genres,
        "currently_reading": [b.to_dict() for b in reading_books],
        "all_books": [b.to_dict() for b in books]
    }


def compute_daily_reading_spread(books: List[Book]) -> List[Dict[str, Any]]:
    """
    Distribute pages and audio minutes uniformly across each book's reading interval.
    Generates daily pace points for timeline plotting.
    """
    daily_pages = defaultdict(float)
    daily_audio_min = defaultdict(float)

    for b in books:
        if b.status != "finished":
            continue
        start_d = b.get_start_date()
        end_d = b.get_end_date()
        if not start_d or not end_d:
            continue

        days = (end_d - start_d).days + 1
        pages_per_day = (b.pages / days) if (b.format == "book" and b.pages) else 0.0
        min_per_day = (b.audio_length_minutes / days) if (b.format == "audiobook" and b.audio_length_minutes) else 0.0

        cur = start_d
        while cur <= end_d:
            date_str = cur.isoformat()
            if pages_per_day > 0:
                daily_pages[date_str] += pages_per_day
            if min_per_day > 0:
                daily_audio_min[date_str] += min_per_day
            cur += timedelta(days=1)

    all_dates = sorted(set(list(daily_pages.keys()) + list(daily_audio_min.keys())))
    timeline = []
    cum_pages = 0.0
    cum_audio_min = 0.0

    for d in all_dates:
        p = round(daily_pages[d], 1)
        m = round(daily_audio_min[d], 1)
        cum_pages += p
        cum_audio_min += m
        timeline.append({
            "date": d,
            "pages": p,
            "audio_minutes": m,
            "cumulative_pages": round(cum_pages, 1),
            "cumulative_audio_hours": round(cum_audio_min / 60.0, 1)
        })

    return timeline
