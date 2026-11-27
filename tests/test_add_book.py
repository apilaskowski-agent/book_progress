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
            self.assertEqual(saved[0]["language"], "English")
            self.assertIsNone(saved[0]["word_count"])

    def test_explicit_words_and_empty_default(self):
        """Verify explicit words are stored and omitted words are null."""
        # 1. With explicit words
        book_with_words = add_or_update_book(
            title="Demon in White",
            author="Christopher Ruocchio",
            pages=760,
            words=275000,
            language="English",
            dry_run=True
        )
        self.assertEqual(book_with_words.word_count, 275000)
        self.assertEqual(book_with_words.language, "English")

        # 2. Without words: must remain None (no page estimate heuristic)
        book_no_words = add_or_update_book(
            title="Empire of Silence",
            author="Christopher Ruocchio",
            pages=620,
            words=None,
            dry_run=True
        )
        self.assertIsNone(book_no_words.word_count)

    def test_reread_and_duplicate_preservation(self):
        """Verify re-reads create unique IDs and do not overwrite prior history."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_json = os.path.join(temp_dir, "test_books.json")
            with open(temp_json, "w", encoding="utf-8") as f:
                json.dump([], f)

            # 1. First read of Dune in 2024
            read1 = add_or_update_book(
                title="Dune",
                author="Frank Herbert",
                pages=688,
                status="finished",
                start_date="2024-03-01",
                end_date="2024-03-28",
                data_path=temp_json
            )
            self.assertEqual(read1.id, "dune")

            # 2. Second read (re-read) of Dune in 2026
            read2 = add_or_update_book(
                title="Dune",
                author="Frank Herbert",
                pages=688,
                status="finished",
                start_date="2026-01-10",
                end_date="2026-02-05",
                data_path=temp_json
            )
            self.assertEqual(read2.id, "dune-2")

            # Verify both reads exist in JSON file
            with open(temp_json, "r", encoding="utf-8") as f:
                all_books = json.load(f)

            self.assertEqual(len(all_books), 2)
            ids = [b["id"] for b in all_books]
            self.assertIn("dune", ids)
            self.assertIn("dune-2", ids)


if __name__ == "__main__":
    unittest.main()
