"""
Static site generator for book_progress.
Compiles data and prepares the docs/ directory for GitHub Pages.
"""

import json
import os
import shutil
from datetime import datetime, timezone
from .analyzer import (
    load_books,
    compute_reading_stats,
    compute_daily_reading_spread,
    compute_monthly_reading_spread
)
from .models import Book

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(REPO_ROOT, "data", "books.json")
DOCS_DIR = os.path.join(REPO_ROOT, "docs")


def build(output_dir: str = DOCS_DIR, data_path: str = DATA_PATH):
    """Compile dataset, analytics, and static assets into output_dir."""
    os.makedirs(output_dir, exist_ok=True)

    # 1. Load books and compute stats
    books = load_books(data_path)
    stats = compute_reading_stats(books)
    timeline = compute_daily_reading_spread(books)
    monthly_stats = compute_monthly_reading_spread(timeline, books)

    now_utc = datetime.now(timezone.utc)
    generated_at_str = now_utc.strftime("%Y-%m-%d %H:%M UTC")

    payload = {
        "kpis": stats["kpis"],
        "yearly_stats": stats["yearly_stats"],
        "genre_counts": stats["genre_counts"],
        "language_counts": stats["language_counts"],
        "currently_reading": stats["currently_reading"],
        "books": [b.to_dict() for b in books],
        "timeline": timeline,
        "monthly_stats": monthly_stats,
        "generated_at": generated_at_str,
        "built_at": now_utc.isoformat()
    }

    # 2. Write data.json into docs
    data_dest = os.path.join(output_dir, "data.json")
    with open(data_dest, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"[INFO] Wrote pre-computed stats to {data_dest}")

    return payload


if __name__ == "__main__":
    build()
