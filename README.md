# 📚 Book Progress Tracker & Reading Analytics

A clean, personal reading and audiobook tracker with interactive statistics, hosted on GitHub Pages.

---

## 🌟 Key Features

* **📖 First-Class Audiobooks & Print Books**: Tracks duration (*hours & minutes*) for audiobooks alongside page and word counts for physical/digital books.
* **🗃️ Git-Backed Database**: All reading history is stored in `data/books.json` with zero external database dependencies or server maintenance fees.
* **📊 Reading Analytics & Pace**: Computes uniform daily page spreads, pages-per-day velocity, audiobook listening hours, and yearly summaries.
* **📱 Responsive GitHub Pages Dashboard**: Hosted free and automated via GitHub Actions (mirroring the `personal_trainer` architecture).

---

## 📂 Repository Structure

```text
.
├── data/
│   └── books.json             # Git-backed reading database
├── src/
│   ├── models.py              # Book data models & schema validation
│   └── analyzer.py            # Aggregations, pace, and timeline spread
├── tests/
│   └── test_books_schema.py   # Automated unit tests
├── .gitignore
└── README.md
```

---

## 🧪 Running Tests

```bash
python3 -m unittest discover tests
```
