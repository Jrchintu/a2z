"""
Expand shortened URLs (bit.ly, etc.) in files.

This script reads a file, finds all unique bit.ly links, expands them to their
final destination URLs, and then replaces them in the original content.

Usage:
    python debitlify.py <input_file_path>
    python debitlify.py a2z.json
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import requests

from .utils import setup_logging

LOG = logging.getLogger(__name__)

# Common URL shortener domains
SHORTENER_PATTERNS = [
    r"https?://bit\.ly/[^\s\"']+",
    r"https?://t\.co/[^\s\"']+",
    r"https?://tinyurl\.com/[^\s\"']+",
    r"https?://goo\.gl/[^\s\"']+",
    r"https?://ow\.ly/[^\s\"']+",
]


def expand_shortened_url(url: str, timeout: int = 5) -> str:
    """
    Follows a shortened URL to its final destination.

    Uses a HEAD request for efficiency as we only need the headers.

    Args:
        url: The shortened URL to expand.
        timeout: Request timeout in seconds.

    Returns:
        The expanded URL, or the original if expansion fails.
    """
    try:
        # The `requests.head` method is faster as it doesn't download the page body.
        # `allow_redirects=True` is on by default and handles the redirection.
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        return response.url
    except requests.RequestException as e:
        LOG.warning("Could not expand %s: %s", url, e)
        return url


def expand_urls_in_file(
    input_path: Path,
    output_path: Path | None = None,
    patterns: list[str] | None = None,
) -> None:
    """
    Expands all shortened URLs in a file and saves the result.

    Args:
        input_path: Path to the input file.
        output_path: Path for output file. If None, appends '_expanded' to input name.
        patterns: Regex patterns to match shortened URLs. Uses default if None.
    """
    if output_path is None:
        output_path = input_path.with_stem(f"{input_path.stem}_expanded")

    if patterns is None:
        patterns = SHORTENER_PATTERNS

    try:
        content = input_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        LOG.error("File not found at '%s'", input_path)
        sys.exit(1)
    except Exception as e:
        LOG.error("Error reading file: %s", e)
        sys.exit(1)

    # Find all unique shortened links using the patterns
    shortened_links: set[str] = set()
    for pattern in patterns:
        shortened_links.update(re.findall(pattern, content))

    if not shortened_links:
        LOG.info("No shortened links found in the file.")
        return

    LOG.info("Found %d unique shortened links. Expanding them now...", len(shortened_links))

    # Create a mapping from shortened links to their expanded versions.
    link_map = {}
    for link in shortened_links:
        LOG.info("Expanding: %s", link)
        expanded = expand_shortened_url(link)
        link_map[link] = expanded
        LOG.info(" -> %s", expanded)

    # Replace all occurrences in the original content.
    LOG.info("Replacing links in the content...")
    for original, expanded in link_map.items():
        content = content.replace(original, expanded)

    # Save the modified content to the output file.
    try:
        output_path.write_text(content, encoding="utf-8")
        LOG.info("Success! Modified content saved to '%s'", output_path)
    except Exception as e:
        LOG.error("Error saving the file: %s", e)
        sys.exit(1)


def main() -> None:
    """Main entry point for the debitlify script."""
    parser = argparse.ArgumentParser(
        description="Expand shortened URLs (bit.ly, etc.) in a file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.debitlify a2z.json
  python -m src.debitlify input.json -o output.json
        """,
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the input file",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Path to the output file (default: <input>_expanded.<ext>)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose debug output",
    )

    args = parser.parse_args()
    setup_logging(verbose=args.verbose)

    expand_urls_in_file(args.input_file, args.output)


if __name__ == "__main__":
    main()
