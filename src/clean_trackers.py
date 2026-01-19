"""
Clean tracking parameters from URLs in files.

This script reads a file, finds all URLs, and recursively removes common
tracking parameters (utm_source, fbclid, gclid, etc.) from their query strings.
It includes special rules for specific sites and standardizes YouTube URLs.

Usage:
    python clean_trackers.py <input_file_path>
    python clean_trackers.py a2z.json
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlencode, urlparse, urlunparse

from .config import SITES_TO_STRIP_PARAMS, TRACKING_PARAMS
from .utils import setup_logging

LOG = logging.getLogger(__name__)


def clean_url(url: str) -> str:
    """
    Recursively removes known tracking parameters from a URL.

    Includes special rules to strip all parameters and fragments from specific
    sites, and to standardize YouTube URLs, keeping only the video ID and timestamp.

    Args:
        url: The URL to clean.

    Returns:
        The cleaned URL.
    """
    try:
        # 1. Parse the URL into its components (scheme, netloc, path, etc.)
        parsed_url = urlparse(url)

        # --- Site-Specific Rules ---
        # Rule for sites in SITES_TO_STRIP_PARAMS: remove all query params and fragments.
        if any(site in parsed_url.netloc for site in SITES_TO_STRIP_PARAMS):
            cleaned_url_parts = parsed_url._replace(query="", fragment="")
            return urlunparse(cleaned_url_parts)

        # Rule for YouTube: standardize the URL, keeping only 'v' and 't' parameters.
        if "youtube.com" in parsed_url.netloc or "youtu.be" in parsed_url.netloc:
            video_id = None
            timestamp = None
            query_params = parse_qs(parsed_url.query)

            if "youtube.com" in parsed_url.netloc:
                if "v" in query_params:
                    video_id = query_params["v"][0]
            elif "youtu.be" in parsed_url.netloc:
                video_id = parsed_url.path.lstrip("/")

            # Check for and preserve the timestamp parameter 't'
            if "t" in query_params:
                timestamp = query_params["t"][0]

            if video_id:
                # Build the clean URL, adding the timestamp back if it exists.
                clean_youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                if timestamp:
                    clean_youtube_url += f"&t={timestamp}"
                return clean_youtube_url

        # --- General Tracker Removal ---
        # 2. Parse the query string into a dictionary of parameters.
        query_params = parse_qs(parsed_url.query)

        # 3. Recursively clean parameters
        # This new dictionary will hold parameters that are not trackers.
        cleaned_params = {}
        for key, values in query_params.items():
            # If the key is not a tracking parameter, keep it.
            if key not in TRACKING_PARAMS:
                cleaned_values = []
                for value in values:
                    # Decode the value in case it's a URL-encoded URL.
                    decoded_value = unquote(value)
                    # Check if the value itself is a URL that might have trackers.
                    if decoded_value.startswith(("http://", "https://")):
                        # If it is, clean it recursively.
                        cleaned_values.append(clean_url(decoded_value))
                    else:
                        # Otherwise, keep the original value.
                        cleaned_values.append(value)
                cleaned_params[key] = cleaned_values

        # 4. Rebuild the query string from the cleaned dictionary
        cleaned_query = urlencode(cleaned_params, doseq=True)

        # 5. Reconstruct the URL with the cleaned query string
        cleaned_url_parts = parsed_url._replace(query=cleaned_query)

        return urlunparse(cleaned_url_parts)
    except Exception as e:
        # If any error occurs during parsing, return the original URL.
        LOG.warning("Could not parse or clean URL %s: %s", url, e)
        return url


def clean_urls_in_file(input_path: Path, output_path: Path | None = None) -> None:
    """
    Cleans all URLs in a file and saves the result.

    Args:
        input_path: Path to the input file.
        output_path: Path for output file. If None, appends '_cleaned' to input name.
    """
    if output_path is None:
        output_path = input_path.with_stem(f"{input_path.stem}_cleaned")

    try:
        content = input_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        LOG.error("File not found at '%s'", input_path)
        sys.exit(1)
    except Exception as e:
        LOG.error("Error reading file: %s", e)
        sys.exit(1)

    # Find all unique URLs in the content.
    urls = set(re.findall(r'https?://[^\s"]+', content))

    if not urls:
        LOG.info("No URLs found in the file.")
        return

    LOG.info("Found %d unique URLs. Cleaning them now...", len(urls))

    # Create a mapping from original URLs to their cleaned versions.
    url_map = {}
    for url in urls:
        cleaned = clean_url(url)
        # Only add to the map if the URL was actually changed.
        if url != cleaned:
            url_map[url] = cleaned
            LOG.debug("Original: %s\nCleaned:  %s\n", url, cleaned)

    # Replace all tracked URLs in the original content.
    LOG.info("Replacing %d tracked URLs in the content...", len(url_map))
    for original, cleaned in url_map.items():
        # Replace the original URL string to ensure we don't accidentally
        # modify parts of other, longer URLs.
        content = content.replace(f'"{original}"', f'"{cleaned}"')

    # Save the modified content to the output file.
    try:
        output_path.write_text(content, encoding="utf-8")
        LOG.info("Success! Modified content saved to '%s'", output_path)
    except Exception as e:
        LOG.error("Error saving the file: %s", e)
        sys.exit(1)


def main() -> None:
    """Main entry point for the clean_trackers script."""
    parser = argparse.ArgumentParser(
        description="Remove tracking parameters from URLs in a file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.clean_trackers a2z.json
  python -m src.clean_trackers input.json -o output.json
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
        help="Path to the output file (default: <input>_cleaned.<ext>)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose debug output",
    )

    args = parser.parse_args()
    setup_logging(verbose=args.verbose)

    clean_urls_in_file(args.input_file, args.output)


if __name__ == "__main__":
    main()
