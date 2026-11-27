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


class TestBooksSchema(unittest.TestCase):
    def test_load_sample_books(self):
        """Verify data/books.json loads and validates successfully."""
        books = load_books(DATA_PATH)
        self.assertEqual(len(books), 10)

    def test_audiobook_and_book_formats(self):
        """Verify format distinction between print/ebook and audiobooks."""
        books = load_books(DATA_PATH)
        audiobooks = [b for b in books if b.format == "audiobook"]
        print_books = [b for b in books if b.format == "book"]

        self.assertEqual(len(audiobooks), 4)
        self.assertEqual(len(print_books), 6)

        for a in audiobooks:
            self.assertIsNotNone(a.audio_length_minutes)
            self.assertGreater(a.audio_length_minutes, 0)
            self.assertIn("h", a.audio_duration_formatted)

        for p in print_books:
            if p.status == "finished":
                self.assertIsNotNone(p.pages)
                self.assertGreater(p.pages, 0)

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
        """Verify KPI computations and yearly aggregations."""
        books = load_books(DATA_PATH)
        stats = compute_reading_stats(books)
        kpis = stats["kpis"]

        # 9 finished, 1 reading
        self.assertEqual(kpis["total_finished_books"], 9)
        self.assertEqual(kpis["currently_reading_count"], 1)
        self.assertEqual(kpis["total_print_books"], 5)
        self.assertEqual(kpis["total_audiobooks"], 4)

        # Pages should be sum of 5 finished books (320 + 688 + 616 + 400 + 303 = 2327)
        self.assertEqual(kpis["total_pages_read"], 2327)

        # Audio mins: 970 + 465 + 1505 + 918 = 3858 mins (~64h 18m)
        self.assertEqual(kpis["total_audio_minutes"], 3858)
        self.assertEqual(kpis["total_audio_hours_formatted"], "64h 18m")

        # Yearly stats should cover 2024 and 2025
        years = [y["year"] for y in stats["yearly_stats"]]
        self.assertIn(2024, years)
        self.assertIn(2025, years)

    def test_daily_reading_spread(self):
        """Verify uniform daily timeline spread."""
        books = load_books(DATA_PATH)
        timeline = compute_daily_reading_spread(books)

        self.assertGreater(len(timeline), 0)
        first_point = timeline[0]
        last_point = timeline[-1]

        # Points should have dates and cumulative values
        self.assertIn("date", first_point)
        self.assertGreater(last_point["cumulative_pages"], 2000)
        self.assertGreater(last_point["cumulative_audio_hours"], 50)

    def test_monthly_reading_spread(self):
        """Verify monthly aggregation for bar charts."""
        books = load_books(DATA_PATH)
        timeline = compute_daily_reading_spread(books)
        monthly = compute_monthly_reading_spread(timeline, books)

        self.assertGreater(len(monthly), 0)
        months = [m["month"] for m in monthly]
        self.assertIn("2024-01", months)
        self.assertIn("2025-01", months)

        total_monthly_pages = sum(m["pages"] for m in monthly)
        total_monthly_audio = sum(m["audio_hours"] for m in monthly)

        # Pages should closely match total 2327 pages
        self.assertAlmostEqual(total_monthly_pages, 2327, delta=5)
        # Audio hours should closely match ~64.3 hours
        self.assertAlmostEqual(total_monthly_audio, 64.3, delta=1.0)

    def test_language_counts_and_reread_accumulation(self):
        """Verify language breakdown and multiple reads accumulation."""
        books = load_books(DATA_PATH)
        stats = compute_reading_stats(books)

        # Check language breakdown
        lang_counts = stats["language_counts"]
        self.assertGreater(len(lang_counts), 0)
        self.assertEqual(lang_counts[0]["language"], "English")
        self.assertEqual(lang_counts[0]["count"], 9)

        # Verify duplicate / re-read aggregation logic
        reread_dune = Book(
            id="dune-2",
            title="Dune",
            author="Frank Herbert",
            format="book",
            status="finished",
            start_date="2026-02-01",
            end_date="2026-02-28",
            pages=688,
            word_count=188000,
            language="English"
        )
        extended_books = books + [reread_dune]
        extended_stats = compute_reading_stats(extended_books)

        # Both reads are counted towards total pages (2327 + 688 = 3015)
        self.assertEqual(extended_stats["kpis"]["total_pages_read"], 3015)
        self.assertEqual(extended_stats["kpis"]["total_finished_books"], 10)
        self.assertEqual(extended_stats["kpis"]["total_words_read"], 188000)

        # 2026 year should now exist and contain the re-read
        years_map = {y["year"]: y for y in extended_stats["yearly_stats"]}
        self.assertIn(2026, years_map)
        self.assertEqual(years_map[2026]["pages_read"], 688)
        self.assertEqual(years_map[2026]["words_read"], 188000)



if __name__ == "__main__":
    unittest.main()
