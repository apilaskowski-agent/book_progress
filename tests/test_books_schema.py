"""
Unit tests for book_progress models and analytics.
"""

import os
import unittest
from datetime import date
from src.models import Book
from src.analyzer import (
    load_books,
    compute_reading_stats,
    compute_daily_reading_spread,
    compute_monthly_reading_spread
)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(REPO_ROOT, "data", "books.json")


def get_fixture_books():
    """Return a fixed set of books for testing analytics pipelines."""
    return [
        Book(id="b1", title="Book 1", author="Author 1", format="book", status="finished",
             start_date="2024-01-01", end_date="2024-01-15", pages=300, word_count=90000, language="English"),
        Book(id="b2", title="Book 2", author="Author 2", format="book", status="finished",
             start_date="2024-02-01", end_date="2024-02-20", pages=400, word_count=120000, language="English"),
        Book(id="a1", title="Audio 1", author="Author 3", format="audiobook", status="finished",
             start_date="2024-03-01", end_date="2024-03-10", audio_length_minutes=600, language="English"),
        Book(id="b3", title="Book 3", author="Author 4", format="book", status="finished",
             start_date="2025-01-01", end_date="2025-01-20", pages=500, word_count=150000, language="Polish"),
        Book(id="a2", title="Audio 2", author="Author 5", format="audiobook", status="finished",
             start_date="2025-02-01", end_date="2025-02-10", audio_length_minutes=360, language="English"),
        Book(id="r1", title="Reading Book", author="Author 6", format="book", status="reading",
             start_date="2025-03-01", pages=350, language="English")
    ]


class TestBooksSchema(unittest.TestCase):
    def test_load_data_books(self):
        """Verify data/books.json loads and all entries validate successfully."""
        books = load_books(DATA_PATH)
        self.assertGreaterEqual(len(books), 2)
        book_ids = {b.id for b in books}
        self.assertIn("the-inevitable-ruin", book_ids)
        self.assertIn("prince-caspian", book_ids)

        for b in books:
            b.validate()

    def test_word_count_only_book(self):
        """Verify books with word_count but no page count validate and calculate pace."""
        book = Book(
            id="inevitable-ruin-test",
            title="The Inevitable Ruin",
            author="Matt Dinniman",
            format="book",
            status="finished",
            start_date="2026-10-23",
            end_date="2026-11-18",
            pages=None,
            word_count=260000
        )
        book.validate()
        self.assertEqual(book.duration_days, 27)
        self.assertEqual(book.pace_per_day["unit"], "words/day")
        self.assertAlmostEqual(book.pace_per_day["rate"], 9629.6, places=1)
        self.assertEqual(book.pace_per_day["total"], 260000)

    def test_audiobook_and_book_formats(self):
        """Verify format distinction between print/ebook and audiobooks."""
        books = get_fixture_books()
        audiobooks = [b for b in books if b.format == "audiobook"]
        print_books = [b for b in books if b.format == "book"]

        self.assertEqual(len(audiobooks), 2)
        self.assertEqual(len(print_books), 4)

        for a in audiobooks:
            self.assertIsNotNone(a.audio_length_minutes)
            self.assertGreater(a.audio_length_minutes, 0)
            self.assertIn("h", a.audio_duration_formatted)

        for p in print_books:
            if p.status == "finished":
                self.assertTrue(p.pages or p.word_count)

    def test_invalid_dates_rejected(self):
        """Verify end_date before start_date is rejected."""
        with self.assertRaises(ValueError):
            bad_book = Book(
                id="bad-dates",
                title="Bad Dates",
                author="Unknown",
                format="book",
                status="finished",
                start_date="2025-05-10",
                end_date="2025-05-01",
                pages=200
            )
            bad_book.validate()

    def test_compute_reading_stats(self):
        """Verify KPI computations and yearly aggregations with fixture dataset."""
        books = get_fixture_books()
        stats = compute_reading_stats(books)
        kpis = stats["kpis"]

        # 5 finished, 1 reading
        self.assertEqual(kpis["total_finished_books"], 5)
        self.assertEqual(kpis["currently_reading_count"], 1)
        self.assertEqual(kpis["total_print_books"], 3)
        self.assertEqual(kpis["total_audiobooks"], 2)

        # Pages: 300 + 400 + 500 = 1200
        self.assertEqual(kpis["total_pages_read"], 1200)

        # Audio mins: 600 + 360 = 960 mins (16h 0m)
        self.assertEqual(kpis["total_audio_minutes"], 960)
        self.assertEqual(kpis["total_audio_hours_formatted"], "16h 0m")

        # Words: 90000 + 120000 + 150000 = 360000
        self.assertEqual(kpis["total_words_read"], 360000)

        # Yearly stats
        years = [y["year"] for y in stats["yearly_stats"]]
        self.assertIn(2024, years)
        self.assertIn(2025, years)

    def test_daily_reading_spread(self):
        """Verify uniform daily timeline spread with fixture dataset."""
        books = get_fixture_books()
        timeline = compute_daily_reading_spread(books)

        self.assertGreater(len(timeline), 0)
        first_point = timeline[0]
        last_point = timeline[-1]

        self.assertIn("date", first_point)
        self.assertGreater(last_point["cumulative_pages"], 1000)
        self.assertGreater(last_point["cumulative_audio_hours"], 10)

    def test_monthly_reading_spread(self):
        """Verify monthly aggregation for bar charts."""
        books = get_fixture_books()
        timeline = compute_daily_reading_spread(books)
        monthly = compute_monthly_reading_spread(timeline, books)

        self.assertGreater(len(monthly), 0)
        months = [m["month"] for m in monthly]
        self.assertIn("2024-01", months)
        self.assertIn("2025-01", months)

        total_monthly_pages = sum(m["pages"] for m in monthly)
        total_monthly_audio = sum(m["audio_hours"] for m in monthly)

        self.assertAlmostEqual(total_monthly_pages, 1200, delta=5)
        self.assertAlmostEqual(total_monthly_audio, 16.0, delta=1.0)

    def test_language_counts_and_reread_accumulation(self):
        """Verify language breakdown and multiple reads accumulation."""
        books = get_fixture_books()
        stats = compute_reading_stats(books)

        lang_counts = {item["language"]: item["count"] for item in stats["language_counts"]}
        self.assertEqual(lang_counts.get("English"), 4)
        self.assertEqual(lang_counts.get("Polish"), 1)

        # Verify duplicate / re-read aggregation logic
        reread_book = Book(
            id="b1-2",
            title="Book 1",
            author="Author 1",
            format="book",
            status="finished",
            start_date="2026-02-01",
            end_date="2026-02-28",
            pages=300,
            word_count=90000,
            language="English"
        )
        extended_books = books + [reread_book]
        extended_stats = compute_reading_stats(extended_books)

        self.assertEqual(extended_stats["kpis"]["total_pages_read"], 1500)
        self.assertEqual(extended_stats["kpis"]["total_finished_books"], 6)
        self.assertEqual(extended_stats["kpis"]["total_words_read"], 450000)

        years_map = {y["year"]: y for y in extended_stats["yearly_stats"]}
        self.assertIn(2026, years_map)
        self.assertEqual(years_map[2026]["pages_read"], 300)
        self.assertEqual(years_map[2026]["words_read"], 90000)


if __name__ == "__main__":
    unittest.main()
