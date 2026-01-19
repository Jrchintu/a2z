# Copilot Instructions for A2Z DSA Sheet

This repository manages the content for a Data Structures and Algorithms (DSA) learning platform. It uses a JSON-based storage system and Python scripts to render static HTML articles.

## 🏗 Architecture & Data Flow

```
a2z/
├── pyproject.toml        # Python project configuration
├── requirements.txt      # Production dependencies
├── Makefile              # Common commands (make render, make download, etc.)
├── content/articles/     # Source JSON files (EDIT THESE)
├── public/articles/      # Generated HTML (DO NOT EDIT)
├── src/                  # Python package
│   ├── __init__.py       # Package init
│   ├── config.py         # Shared configuration constants
│   ├── utils.py          # Common utilities
│   ├── render_article.py
│   ├── download_json.py
│   ├── localize_assets.py
│   ├── clean_trackers.py
│   └── debitlify.py
├── templates/            # HTML templates
└── tests/                # Test suite
```

- **Master Curriculum (`public/a2z.json`):** The central source of truth for the course structure. It defines steps, sub-steps, and topics, linking to external resources (YouTube, LeetCode, etc.).
- **Content Storage (`content/articles/`):** Contains individual problem articles in JSON format.
  - Organized by topic folders (e.g., `arrays/`, `binary-search/`).
  - Each JSON file contains metadata (`title`, `slug`) and a `content` field with raw HTML.
- **Rendering Engine (`src/render_article.py`):** Converts Article JSONs into standalone HTML files using `templates/template.html`.
- **Output Directory (`public/`):** Contains all generated HTML files and static assets.

## 🛠 Critical Workflows

### 1. Rendering Articles

To generate HTML files from the JSON sources, run:

```bash
make render
# or: python -m src.render_article
```

This reads from `content/articles/` and outputs to `public/articles/`.

Options:
- `-c, --content-dir`: Custom content directory
- `-o, --output-dir`: Custom output directory  
- `-t, --template`: Custom template file
- `--skip-localize`: Skip asset localization step
- `-v, --verbose`: Enable verbose output

### 2. Content Editing

- **Do not edit generated HTML files directly.** Always modify the source JSON files in `content/articles/`.
- The `content` field in JSON is a string containing HTML. Be careful with escaping quotes.

### 3. Downloading Articles

```bash
make download
# or: python -m src.download_json
```

Downloads articles from TakeUForward API to `content/articles/`.

## 📝 Content Conventions

### Article JSON Structure

```json
{
  "title": "Problem Title",
  "slug": "problem-slug",
  "content": "<!-- wp:paragraph -->...HTML Content...<!-- /wp:paragraph -->",
  "topics": [{"topic-id": "arrays", "topic-title": "Arrays"}]
}
```

### Code Block Pattern

The project uses a specific tabbed interface for code solutions (C++, Java, Python, JS). When adding/editing code, maintain this HTML structure inside the JSON `content` string:

```html
<div class="code-section secondary-details">
  <div class="code-tabs">
    <button class="code-tab dsa_article_code_active" data-lang="cpp">C++</button>
    <!-- ... other buttons ... -->
  </div>
  <div class="code-content">
    <div class="code-block dsa_article_code_active" data-lang="cpp">
      <pre class="wp-block-code"><code lang="cpp" class="language-cpp">
        // C++ Code Here
      </code></pre>
    </div>
    <!-- ... other code blocks ... -->
  </div>
</div>
```

### HTML Markers

- Use `<!-- wp:paragraph -->` and `<!-- /wp:paragraph -->` to wrap text blocks.
- Use `<!-- Insert ... Here -->` comments as guideposts for where specific content sections (Examples, Approaches, Code) should go.

## 🐍 Python Package

All scripts are in `src/` directory and can be run as modules:

| Command | Purpose |
|---------|---------|
| `python -m src.render_article` | JSON → HTML conversion |
| `python -m src.download_json` | Fetch articles from API |
| `python -m src.localize_assets` | Download remote assets locally |
| `python -m src.clean_trackers` | Remove URL tracking parameters |
| `python -m src.debitlify` | Expand shortened URLs |

**Shared modules:**
- `src/config.py` - Project paths and constants
- `src/utils.py` - Reusable utilities (HTTP sessions, file ops, etc.)

**Dependencies:** `requests`, `tqdm`, `beautifulsoup4`

## 🧪 Development

```bash
# Install dev dependencies
make install-dev

# Run tests
make test

# Run linter
make lint

# Format code
make format
```
