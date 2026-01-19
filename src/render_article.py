"""
Render article JSON files to standalone HTML pages.

This script reads JSON article files from the content directory and
generates static HTML files using a template, outputting them to the
public articles directory.

Usage:
    python render_article.py
    python render_article.py -c /path/to/content -o /path/to/output
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from .config import CONTENT_DIR, DEFAULT_TEMPLATE, PUBLIC_DIR

if TYPE_CHECKING:
    pass

LOG = logging.getLogger(__name__)


def read_template(template_path: Path | None = None) -> str:
    """
    Reads the HTML template file.

    Args:
        template_path: Path to the template file. Uses default if None.

    Returns:
        Template content as string.

    Raises:
        SystemExit: If template file is not found.
    """
    if template_path is None:
        template_path = DEFAULT_TEMPLATE
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        LOG.error("Template file not found at '%s'.", template_path)
        LOG.error("Expected location: %s", DEFAULT_TEMPLATE)
        sys.exit(1)


def create_html_from_json(
    json_filepath: Path | str,
    html_filepath: Path | str,
    template_content: str,
) -> None:
    """
    Creates a single HTML file from a JSON file using a template.

    Args:
        json_filepath: Path to the source JSON file.
        html_filepath: Path to the output HTML file.
        template_content: The HTML template string.
    """
    try:
        with open(json_filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        title = data.get("title", "Article")
        content = data.get("content", "<p>No content found.</p>")

        # Clean up empty paragraphs and paragraphs containing only comments/whitespace
        # Pattern: <p> followed by any sequence of whitespace OR comments, followed by </p>
        # We use \s instead of \s* inside the group to avoid catastrophic backtracking
        content = re.sub(r"<p>(?:\s|<!--.*?-->)*</p>", "", content, flags=re.DOTALL)
        # Also remove paragraphs containing only break tags
        content = re.sub(r"<p>\s*<br\s*/?>\s*</p>", "", content, flags=re.IGNORECASE)

        # Fix nested paragraphs which cause layout issues (extra spacing)
        # Replace <p>...<p> with <p> (effectively removing the outer start tag)
        content = re.sub(r"<p>(\s*<p>)", r"\1", content, flags=re.IGNORECASE)
        # Replace </p>...</p> with </p> (removing the outer end tag)
        content = re.sub(r"</p>(\s*</p>)", r"\1", content, flags=re.IGNORECASE)

        # Replace placeholders in the template with actual data
        output_html = template_content.replace("{TITLE}", title)
        output_html = output_html.replace("{CONTENT}", content)

        with open(html_filepath, "w", encoding="utf-8") as f:
            f.write(output_html)

    except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
        LOG.warning("Skipping %s due to an error: %s", json_filepath, e)


def process_articles_directory(
    content_dir: Path | str,
    output_dir: Path | str,
    template_content: str,
) -> list[str]:
    """
    Walks through content directory, finds all .json files, and converts them.

    Outputs HTML to the public/articles directory, mirroring the structure.

    Args:
        content_dir: Directory containing JSON article files.
        output_dir: Directory for generated HTML files.
        template_content: The HTML template string.

    Returns:
        List of paths to generated HTML files.
    """
    LOG.info("Processing articles from: %s", content_dir)
    LOG.info("Output directory: %s", output_dir)

    if not os.path.isdir(content_dir):
        LOG.error("'%s' is not a valid directory.", content_dir)
        return []

    generated_html_files = []
    for dirpath, _, filenames in os.walk(content_dir):
        for filename in filenames:
            if filename.endswith(".json"):
                json_filepath = os.path.join(dirpath, filename)

                # Calculate relative path from content directory
                relative_dir = os.path.relpath(dirpath, content_dir)

                # Create mirrored output directory structure in public/
                output_subdir = os.path.join(output_dir, relative_dir)
                os.makedirs(output_subdir, exist_ok=True)

                base_name = os.path.splitext(filename)[0]
                html_filepath = os.path.join(output_subdir, base_name + ".html")

                LOG.debug("Converting '%s'", filename)
                create_html_from_json(json_filepath, html_filepath, template_content)
                generated_html_files.append(html_filepath)

    LOG.info("Processing complete. Converted %d files.", len(generated_html_files))
    return generated_html_files


def generate_main_index(html_paths: list[str], output_dir: str) -> None:
    """
    Generates a main index.html file with a simple list of all created files.

    Args:
        html_paths: List of paths to generated HTML files.
        output_dir: Directory where the index file will be created.
    """
    LOG.info("Generating main index file...")
    if not html_paths:
        LOG.warning("No HTML files were generated, skipping index file creation.")
        return

    # Create relative paths from the output directory for cleaner links
    list_items = []
    for path in sorted(html_paths):
        rel_path = os.path.relpath(path, output_dir).replace(os.sep, "/")
        list_items.append(f'<li><a href="{rel_path}">{rel_path}</a></li>')

    list_html = "<ul>\n" + "\n".join(list_items) + "\n</ul>"

    index_html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Article Index</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            /* Default to Dark Theme */
            --primary-color: #3b82f6;
            --bg-body: #0f172a;
            --bg-surface: #1e293b;
            --border-color: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --link-color: #60a5fa;
            --radius-lg: 8px;
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
        }}
        body {{ 
            font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 2rem; 
            background-color: var(--bg-body); 
            color: var(--text-primary); 
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        h1 {{ 
            color: var(--text-primary); 
            border-bottom: 1px solid var(--border-color); 
            padding-bottom: 1rem; 
            margin-bottom: 2rem;
        }}
        ul {{ 
            list-style-type: none; 
            padding: 0; 
            background-color: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-md);
            overflow: hidden;
        }}
        li {{ 
            margin: 0; 
            border-bottom: 1px solid var(--border-color); 
            padding: 0;
        }}
        li:last-child {{ border-bottom: none; }}
        a {{ 
            display: block;
            padding: 1rem;
            text-decoration: none; 
            color: var(--link-color); 
            transition: background-color 0.2s;
        }}
        a:hover {{ 
            background-color: var(--border-color);
            text-decoration: none; 
        }}
        @media (max-width: 768px) {{
            body {{ padding: 0; }}
            h1 {{ padding-left: 1rem; padding-right: 1rem; }}
            ul {{ border-radius: 0; border: none; border-top: 1px solid var(--border-color); border-bottom: 1px solid var(--border-color); }}
        }}
    </style>
</head>
<body>
    <h1>Generated Articles Index</h1>
    {list_html}
</body>
</html>
"""
    index_filepath = os.path.join(output_dir, "index.html")
    with open(index_filepath, "w", encoding="utf-8") as f:
        f.write(index_html_content)

    LOG.info("Successfully created main index at '%s'", os.path.abspath(index_filepath))


def run_asset_localization(output_dir: Path | str) -> None:
    """
    Runs the localize_assets.py script on the directory where HTML was generated.

    Args:
        output_dir: Directory containing generated HTML files.
    """
    LOG.info("Running asset localization...")
    script_path = Path(__file__).parent / "localize_assets.py"

    if not script_path.exists():
        LOG.warning(
            "localize_assets.py not found at '%s'. Skipping localization.", script_path
        )
        return

    try:
        # We run the script on the output articles directory and add the verbose flag.
        # It will find all the .html files inside it recursively.
        command = [sys.executable, str(script_path), str(output_dir), "-v"]
        LOG.debug("Executing: %s", " ".join(command))
        subprocess.run(command, check=True, text=True)
        LOG.info("Asset localization complete.")
    except subprocess.CalledProcessError:
        LOG.error("Asset localization FAILED. The script exited with a non-zero status.")
    except FileNotFoundError:
        LOG.error("'%s' not found. Cannot run subprocess.", sys.executable)


def main() -> None:
    """Main entry point for the render script."""
    from .utils import setup_logging

    parser = argparse.ArgumentParser(
        description="Render article JSON files to HTML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.render_article                    # Use default directories
  python -m src.render_article -c /path/to/content -o /path/to/output
        """,
    )
    parser.add_argument(
        "-c", "--content-dir",
        type=Path,
        default=CONTENT_DIR,
        help=f"Directory containing article JSON files (default: {CONTENT_DIR})",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=PUBLIC_DIR,
        help=f"Directory for generated HTML files (default: {PUBLIC_DIR})",
    )
    parser.add_argument(
        "-t", "--template",
        type=Path,
        default=DEFAULT_TEMPLATE,
        help=f"Path to HTML template file (default: {DEFAULT_TEMPLATE})",
    )
    parser.add_argument(
        "--skip-localize",
        action="store_true",
        help="Skip running asset localization after rendering",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose debug output",
    )

    args = parser.parse_args()
    setup_logging(verbose=args.verbose)

    template = read_template(args.template)

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate HTML files from JSON
    generated_files = process_articles_directory(
        str(args.content_dir),
        str(args.output_dir),
        template,
    )

    if generated_files:
        # 2. Create the main index.html
        generate_main_index(generated_files, str(args.output_dir))

        # 3. Run the asset localizer on the output directory
        if not args.skip_localize:
            run_asset_localization(args.output_dir)


if __name__ == "__main__":
    main()

