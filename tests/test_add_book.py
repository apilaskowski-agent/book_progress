"""
Unit tests for scripts/add_book.py
"""

import json
import os
import tempfile
import unittest

from scripts.add_book import (
    slugify,
    parse_audio_duration,
    add_or_update_book
)


class TestAddBook(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("Project Hail Mary"), "project-hail-mary")
        self.assertEqual(slugify("Thinking, Fast and Slow!"), "thinking-fast-and-slow")
        self.assertEqual(slugify("  Spaces   And -- Dashes  "), "spaces-and-dashes")

    def test_parse_audio_duration(self):
        self.assertEqual(parse_audio_duration("16h 10m"), 970)
        self.assertEqual(parse_audio_duration("7h 45m"), 465)
        self.assertEqual(parse_audio_duration("8.5h"), 510)
        self.assertEqual(parse_audio_duration("450m"), 450)
        self.assertEqual(parse_audio_duration("120"), 120)
        self.assertIsNone(parse_audio_duration(""))
        self.assertIsNone(parse_audio_duration("invalid"))

    def test_add_or_update_book_dry_run(self):
        book = add_or_update_book(
            title="Clean Code",
            author="Robert C. Martin",
            format_type="book",
            status="finished",
            pages=464,
            start_date="2025-04-01",
            end_date="2025-04-20",
            rating=5.0,
            dry_run=True
        )
        self.assertEqual(book.id, "clean-code")
        self.assertEqual(book.pages, 464)
        self.assertEqual(book.duration_days, 20)
        self.assertAlmostEqual(book.pace_per_day["rate"], 23.2, places=1)

    def test_add_book_writes_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_json = os.path.join(temp_dir, "test_books.json")
            with open(temp_json, "w", encoding="utf-8") as f:
                json.dump([], f)

            book = add_or_update_book(
                title="Test Book",
                author="Test Author",
                format_type="audiobook",
                status="finished",
                audio_mins=360,
                start_date="2025-01-01",
                end_date="2025-01-06",
                rating=4.5,
                data_path=temp_json
            )

            with open(temp_json, "r", encoding="utf-8") as f:
                saved = json.load(f)

            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0]["id"], "test-book")
            self.assertEqual(saved[0]["audio_length_minutes"], 360)
            self.assertEqual(saved[0]["audio_duration_formatted"], "6h")


if __name__ == "__main__":
    unittest.main()
