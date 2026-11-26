# 📚 Book Progress Tracker & Reading Analytics

[![Deploy Book Progress Dashboard](https://github.com/apilaskowski/book_progress/actions/workflows/deploy.yml/badge.svg)](https://github.com/apilaskowski/book_progress/actions/workflows/deploy.yml)
[![Live Site](https://img.shields.io/badge/Live%20Dashboard-GitHub%20Pages-blue?style=flat&logo=github)](https://apilaskowski.github.io/book_progress/)

A clean, personal reading and audiobook tracker with interactive statistics, hosted on **GitHub Pages**.

🔗 **Live Site**: [https://apilaskowski.github.io/book_progress/](https://apilaskowski.github.io/book_progress/)

---

## 🌟 Key Features

* **📖 First-Class Audiobooks & Print Books**: Tracks duration (*hours & minutes*) for audiobooks alongside page and word counts for physical/digital books.
* **🗃️ Git-Backed Database**: All reading history is stored in `data/books.json` with zero external database dependencies or server maintenance fees.
* **📊 Interactive Analytics & Charts**:
  - **📈 Cumulative Growth Curve**: Dual Y-axis line chart tracking pages & audio hours read over time.
  - **📊 Monthly Reading Volume**: Grouped bar chart depicting pages read and audio hours per calendar month (using uniform daily spread).
  - **🏷️ Top Genres & Format Ratio**: Donut charts detailing reading preferences.
* **📱 Responsive Foldable Dashboard**: Collapsible by status (*Currently Reading*) and by year (*2025*, *2024*...), with expandable book cards and dark/light mode toggle.
* **⚡ Automated CI/CD**: Automated testing and deployment to GitHub Pages via GitHub Actions on every commit to `main`.

---

## 📂 Repository Structure

```text
.
├── .github/workflows/
│   └── deploy.yml             # CI/CD: Automated tests & GitHub Pages deployment
├── data/
│   └── books.json             # Git-backed reading database
├── docs/                      # Static web app published to GitHub Pages
│   ├── index.html             # Dashboard markup & KPI cards
│   ├── style.css              # Dark/light responsive theme variables & animations
│   ├── app.js                 # Chart.js integration, filtering, & card folding
│   └── data.json              # Pre-computed analytics payload
├── src/
│   ├── models.py              # Book data models & schema validation
│   ├── analyzer.py            # Aggregations, pace, and timeline spread
│   └── builder.py             # Static site compiler
├── scripts/
│   └── add_book.py            # CLI helper to fetch metadata & append book
├── tests/
│   ├── test_books_schema.py   # Schema & math unit tests
│   ├── test_site_builder.py   # Build & asset verification tests
│   └── test_add_book.py       # Metadata fetcher & CLI unit tests
├── build.py                   # Top-level build entrypoint
├── .gitignore
└── README.md
```

---

## 📖 Adding Books & Audiobooks (Online Metadata)

Use the CLI helper to discover cover art, page count, genres, and word count from **Open Library**:

```bash
# 1. Add a print/e-book you are currently reading (auto-fetches cover & pages)
python3 scripts/add_book.py "The Pragmatic Programmer" -a "Andy Hunt" --build

# 2. Add an audiobook you finished (parses audio length, calculates daily pace)
python3 scripts/add_book.py "Born a Crime" -a "Trevor Noah" -f audiobook --audio "8h 44m" -s finished --start "2025-10-01" --end "2025-10-15" -r 5.0 -n "Hilarious and deeply moving memoir." --build

# 3. Dry-run to preview metadata without modifying data/books.json
python3 scripts/add_book.py "Project Hail Mary" --dry-run
```

---

## ⚙️ Enabling GitHub Pages (One-Time Setup)

To activate the live site on GitHub:
1. Go to repository: **Settings** > **Pages**.
2. Under **Build and deployment** > **Source**, select **Deploy from a branch**.
3. Choose branch: **`gh-pages`** (folder: `/root`), then click **Save**.
*(The `gh-pages` branch is created automatically on the first workflow run on `main`).*

---

## 🧪 Local Build & Testing

```bash
# Run full unit test suite
python3 -m unittest discover tests

# Build static dashboard locally into docs/
python3 build.py
```
