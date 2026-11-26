"""
Data models and schema validation for book_progress.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional, Literal, Dict, Any

BookFormat = Literal["book", "audiobook"]
BookStatus = Literal["finished", "reading", "want_to_read"]


@dataclass
class Book:
    id: str
    title: str
    author: str
    format: BookFormat
    status: BookStatus
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    pages: Optional[int] = None
    audio_length_minutes: Optional[int] = None
    estimated_word_count: Optional[int] = None
    rating: Optional[float] = None
    genres: List[str] = field(default_factory=list)
    cover_url: Optional[str] = None
    notes: Optional[str] = None

    def validate(self):
        """Validate book data integrity."""
        if not self.id or not isinstance(self.id, str):
            raise ValueError(f"Book missing valid 'id': {self}")
        if not self.title or not isinstance(self.title, str):
            raise ValueError(f"Book '{self.id}' missing valid 'title'")
        if not self.author or not isinstance(self.author, str):
            raise ValueError(f"Book '{self.id}' missing valid 'author'")
        if self.format not in ("book", "audiobook"):
            raise ValueError(f"Book '{self.id}' format must be 'book' or 'audiobook', got '{self.format}'")
        if self.status not in ("finished", "reading", "want_to_read"):
            raise ValueError(f"Book '{self.id}' status must be 'finished', 'reading', or 'want_to_read', got '{self.status}'")

        if self.format == "book":
            if self.status == "finished" and (not self.pages or self.pages <= 0):
                raise ValueError(f"Print/ebook '{self.id}' must have positive 'pages' count")
        elif self.format == "audiobook":
            if self.status == "finished" and (not self.audio_length_minutes or self.audio_length_minutes <= 0):
                raise ValueError(f"Audiobook '{self.id}' must have positive 'audio_length_minutes'")

        # Validate date formats if present
        start_d = self.get_start_date()
        end_d = self.get_end_date()

        if self.status == "finished":
            if not start_d or not end_d:
                raise ValueError(f"Finished book '{self.id}' must have valid 'start_date' and 'end_date'")
            if end_d < start_d:
                raise ValueError(f"Book '{self.id}' end_date ({self.end_date}) precedes start_date ({self.start_date})")

        if self.rating is not None and not (0.5 <= self.rating <= 5.0):
            raise ValueError(f"Book '{self.id}' rating must be between 0.5 and 5.0, got {self.rating}")

    def get_start_date(self) -> Optional[date]:
        if not self.start_date:
            return None
        return datetime.strptime(self.start_date, "%Y-%m-%d").date()

    def get_end_date(self) -> Optional[date]:
        if not self.end_date:
            return None
        return datetime.strptime(self.end_date, "%Y-%m-%d").date()

    @property
    def duration_days(self) -> int:
        """Total days spent reading/listening (inclusive)."""
        s = self.get_start_date()
        e = self.get_end_date() or date.today()
        if not s:
            return 1
        return max(1, (e - s).days + 1)

    @property
    def pace_per_day(self) -> Dict[str, Any]:
        """Calculates pace (pages/day or audio minutes/day)."""
        days = self.duration_days
        if self.format == "book" and self.pages:
            return {
                "unit": "pages/day",
                "rate": round(self.pages / days, 1),
                "total": self.pages,
                "days": days
            }
        elif self.format == "audiobook" and self.audio_length_minutes:
            rate_min = round(self.audio_length_minutes / days, 1)
            return {
                "unit": "min/day",
                "rate": rate_min,
                "total": self.audio_length_minutes,
                "days": days
            }
        return {"unit": "unknown", "rate": 0, "total": 0, "days": days}

    @property
    def audio_duration_formatted(self) -> Optional[str]:
        """Convert audio minutes into 'Xh Ym' string."""
        if not self.audio_length_minutes:
            return None
        h = self.audio_length_minutes // 60
        m = self.audio_length_minutes % 60
        if h > 0 and m > 0:
            return f"{h}h {m}m"
        elif h > 0:
            return f"{h}h"
        return f"{m}m"

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "format": self.format,
            "status": self.status,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "pages": self.pages,
            "audio_length_minutes": self.audio_length_minutes,
            "audio_duration_formatted": self.audio_duration_formatted,
            "estimated_word_count": self.estimated_word_count,
            "rating": self.rating,
            "genres": self.genres,
            "cover_url": self.cover_url,
            "notes": self.notes,
            "duration_days": self.duration_days,
            "pace": self.pace_per_day
        }
        return d
