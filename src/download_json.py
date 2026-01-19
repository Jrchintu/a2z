"""
Download article JSON files from TakeUForward API.

This script reads the a2z.json curriculum file and downloads all referenced
articles in parallel, saving them as JSON files organized by category.

Usage:
    python download_json.py
    python download_json.py -o /path/to/output -w 20
"""

from __future__ import annotations

import argparse
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import requests
from tqdm import tqdm

from .config import A2Z_JSON, CONTENT_DIR, DEFAULT_MAX_WORKERS
from .utils import make_session, sanitize_filename

if TYPE_CHECKING:
    pass

LOG = logging.getLogger(__name__)


def download_article_worker(
    post_link: str,
    session: requests.Session,
    output_dir: Path,
) -> str:
    """
    Worker function to download and save a single article.

    Args:
        post_link: URL to the article.
        session: HTTP session for requests.
        output_dir: Directory to save the article.

    Returns:
        Status message indicating success or failure.
    """
    if not post_link:
        return "Skipped: Empty post link."

    try:
        path = urlparse(post_link).path.strip('/')
        path_parts = path.split('/')

        if len(path_parts) < 1:
            return f"Skipped: Could not determine category for {post_link}"

        category = sanitize_filename(path_parts[0])
        slug = sanitize_filename(path_parts[-1])

        if not slug:
            return f"Skipped: Could not determine slug for {post_link}"

        dir_path = output_dir / category
        dir_path.mkdir(parents=True, exist_ok=True)

        filename = dir_path / f"{slug}.json"

        if filename.exists():
            return f"Exists: {filename}"

        api_url = f"https://backend.takeuforward.org/api/blog/article/{path}"
        response = session.get(api_url, timeout=20)
        response.raise_for_status()

        with open(filename, "w", encoding="utf-8") as outfile:
            json.dump(response.json(), outfile, indent=4)

        return f"Success: Saved to {filename}"

    except requests.exceptions.RequestException as e:
        return f"Error (Request): Failed {post_link} with error: {e}"
    except Exception as e:
        return f"Error (General): Failed {post_link} with error: {e}"


def download_all_articles_parallel(
    max_workers: int = DEFAULT_MAX_WORKERS,
    a2z_path: Path | None = None,
    output_dir: Path | None = None,
) -> None:
    """
    Finds all article links in a2z.json and downloads them in parallel.

    Args:
        max_workers: Number of parallel download threads.
        a2z_path: Path to the a2z.json curriculum file.
        output_dir: Directory to save downloaded articles.
    """
    if a2z_path is None:
        a2z_path = A2Z_JSON
    if output_dir is None:
        output_dir = CONTENT_DIR

    output_dir = Path(output_dir)

    try:
        with open(a2z_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading {a2z_path}: {e}")
        return

    # --- Step 1: Collect all post links ---
    all_links = []
    for step in data:
        for sub_step in step.get("sub_steps", []):
            for topic in sub_step.get("topics", []):
                if post_link := topic.get("post_link"):
                    all_links.append(post_link)

    if not all_links:
        LOG.warning("No article links found in %s.", a2z_path)
        return

    LOG.info("Found %d unique articles to process.", len(all_links))
    LOG.info("Output directory: %s", output_dir)

    # --- Step 2: Download in parallel with a progress bar ---
    session = make_session()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks to the executor
        future_to_link = {
            executor.submit(download_article_worker, link, session, output_dir): link
            for link in all_links
        }

        # Process results as they complete, with a tqdm progress bar
        for future in tqdm(
            as_completed(future_to_link),
            total=len(all_links),
            desc="Downloading Articles",
        ):
            link = future_to_link[future]
            try:
                result = future.result()
                if "Error" in result:
                    tqdm.write(result)
            except Exception as exc:
                tqdm.write(f"Article '{link}' generated an exception: {exc}")


def main() -> None:
    """Main entry point for the download script."""
    from .utils import setup_logging

    parser = argparse.ArgumentParser(
        description="Download article JSON files from TakeUForward API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-a", "--a2z-json",
        type=Path,
        default=A2Z_JSON,
        help=f"Path to a2z.json file (default: {A2Z_JSON})",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=CONTENT_DIR,
        help=f"Output directory for downloaded articles (default: {CONTENT_DIR})",
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f"Number of parallel download workers (default: {DEFAULT_MAX_WORKERS})",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose debug output",
    )

    args = parser.parse_args()
    setup_logging(verbose=args.verbose)

    download_all_articles_parallel(
        max_workers=args.workers,
        a2z_path=args.a2z_json,
        output_dir=args.output_dir,
    )
    LOG.info("All downloads complete.")


if __name__ == "__main__":
    main()
