# A2Z DSA SHEET

A Data Structures and Algorithms (DSA) learning platform with JSON-based content storage and Python-powered static site generation.

> **Disclaimer:** For educational purposes only

## 📁 Project Structure

```
a2z/
├── pyproject.toml           # Python project configuration
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── Makefile                 # Common commands
├── content/                 # Source content (edit these)
│   └── articles/            # Article JSON files by topic
│       ├── arrays/
│       ├── binary-search/
│       ├── dynamic-programming/
│       └── ...
├── public/                  # Generated output (do not edit)
│   ├── a2z.json             # Master curriculum
│   ├── index.html
│   ├── assets/              # Static assets (logos, images)
│   └── articles/            # Generated HTML articles
├── src/                     # Python package
│   ├── __init__.py          # Package init
│   ├── config.py            # Shared configuration
│   ├── utils.py             # Common utilities
│   ├── render_article.py    # JSON → HTML renderer
│   ├── download_json.py     # Article downloader
│   ├── localize_assets.py   # Asset localizer
│   ├── clean_trackers.py    # URL tracker cleaner
│   └── debitlify.py         # Bit.ly link expander
├── templates/               # HTML templates
│   └── template.html        # Article template
└── tests/                   # Test suite
    ├── test_utils.py
    └── test_clean_trackers.py
```

## 🚀 Quick Start

### Install Dependencies

```bash
# Production only
pip install -r requirements.txt

# With development tools (testing, linting)
pip install -r requirements-dev.txt

# Or using make
make install      # production
make install-dev  # development
```

### Typical Workflow

```bash
# 1. Download latest articles from API
make download
# or: python -m src.download_json

# 2. Render JSON to HTML
make render
# or: python -m src.render_article

# 3. View the result
open public/articles/index.html
```

## 📚 Script Usage

All scripts can be run as modules:

### 1. Render Articles (JSON → HTML)

```bash
# Default: reads from content/articles/, outputs to public/articles/
python -m src.render_article

# Custom paths
python -m src.render_article -c /path/to/content -o /path/to/output

# Skip asset localization (faster, for testing)
python -m src.render_article --skip-localize

# Verbose output
python -m src.render_article -v

# See all options
python -m src.render_article --help
```

### 2. Download Articles from API

```bash
# Default: downloads to content/articles/
python -m src.download_json

# Custom output directory
python -m src.download_json -o /path/to/output

# Adjust parallel workers (default: 10)
python -m src.download_json -w 20

# See all options
python -m src.download_json --help
```

### 3. Clean URL Trackers

```bash
# Remove tracking params (utm_source, fbclid, etc.) from URLs
python -m src.clean_trackers a2z.json
# Creates: a2z_cleaned.json

# Custom output
python -m src.clean_trackers input.json -o output.json
```

### 4. Expand Bit.ly Links

```bash
# Expand shortened URLs to their destinations
python -m src.debitlify a2z.json
# Creates: a2z_expanded.json
```

### 5. Localize Assets

```bash
# Download remote images/assets locally (usually called by render_article.py)
python -m src.localize_assets public/articles/ -v
```

## 🧪 Development

```bash
# Run tests
make test
# or: pytest tests/ -v

# Run linter
make lint
# or: ruff check src/ tests/

# Format code
make format
# or: ruff format src/ tests/

# Run all checks
make check
```

## 📝 Content Editing

**Important:** Always edit source JSON files in `content/articles/`, never the generated HTML in `public/`.

### Article JSON Format

```json
{
  "title": "Problem Title",
  "slug": "problem-slug",
  "content": "<!-- wp:paragraph -->...HTML Content...<!-- /wp:paragraph -->",
  "topics": [{"topic-id": "arrays", "topic-title": "Arrays"}]
}
```
