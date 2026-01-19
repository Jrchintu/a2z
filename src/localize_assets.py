#!/usr/bin/env python3
"""
Download and localize remote assets referenced in HTML files.

This script scans HTML files for remote asset URLs (images, CSS backgrounds, etc.)
and downloads them locally, updating the HTML references to point to the local copies.

Uses content hashing for the cache to avoid storing duplicate files, even if they
come from different URLs.

Usage:
    python localize_assets.py /path/to/html_root
    python localize_assets.py /path/to/html_root --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING, Generator
from urllib.parse import unquote, urlparse

import requests
from bs4 import BeautifulSoup

from .config import ASSETS_DIRNAME, DEFAULT_MAX_WORKERS, MAX_FILE_SIZE_MB
from .utils import (
    download_to_file,
    get_file_hash,
    make_session,
    safe_makedir,
    setup_logging,
)

if TYPE_CHECKING:
    pass

LOG = logging.getLogger(__name__)


# --- helpers ---------------------------------------------------------------
def _sanitize_asset_filename(name: str) -> str:
    """Removes unsafe characters from a filename."""
    name = unquote(name or "")
    name = name.split("?")[0].split("#")[0]
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return name or "file"


def _parse_srcset(srcset: str) -> list[tuple[str, str]]:
    """Parses an srcset attribute into a list of (url, descriptor) tuples."""
    if not srcset:
        return []
    result = []
    for p in srcset.split(","):
        parts = p.strip().split()
        if parts:
            result.append((parts[0], " ".join(parts[1:])))
    return result


def _build_srcset(parts: list[tuple[str, str]]) -> str:
    """Builds an srcset string from a list of (url, descriptor) tuples."""
    return ", ".join([f"{u} {d}".strip() for u, d in parts])


def _find_css_urls(text: str) -> list[str]:
    """Finds all url(...) values in a block of CSS."""
    if not text:
        return []
    return [
        m.group(2)
        for m in re.finditer(r"url\(\s*(['\"]?)(.*?)\1\s*\)", text, flags=re.IGNORECASE)
    ]


def _get_asset_nodes(soup: BeautifulSoup) -> Generator[tuple, None, None]:
    """Generator function to find and yield all nodes that might contain asset URLs."""
    # Images and sources, including common lazy-loading attributes
    for tag in soup.find_all(["img", "source"]):
        for attr in ["src", "srcset", "data-src", "data-original"]:
            if tag.has_attr(attr):
                yield tag, attr

    # Linked stylesheets
    for tag in soup.find_all("link", rel="stylesheet", href=True):
        yield tag, "href"

    # Inline styles on any tag
    for tag in soup.find_all(style=True):
        if tag["style"]:
            yield tag, "style"

    # <style> blocks
    for tag in soup.find_all("style"):
        if tag.string:
            yield tag, "style_block"


def _save_cache_index(path: Path, data: dict) -> None:
    """Atomically saves the cache index to prevent corruption."""
    try:
        temp_path = path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        shutil.move(str(temp_path), str(path))
    except IOError as e:
        LOG.error("Could not save cache index: %s", e)


def discover_urls_in_html(html_path: Path) -> set[str]:
    """Finds all remote asset URLs in a single HTML file."""
    urls: set[str] = set()
    try:
        soup = BeautifulSoup(
            html_path.read_text(encoding="utf-8", errors="ignore"), "html.parser"
        )
    except Exception as e:
        LOG.error("Could not read or parse %s: %s", html_path, e)
        return urls

    def add_if_remote(raw_url: str) -> None:
        raw_url = (raw_url or "").strip()
        if not raw_url or raw_url.lower().startswith("data:"):
            return
        url = "https:" + raw_url if raw_url.startswith("//") else raw_url
        if urlparse(url).scheme in ("http", "https"):
            urls.add(url)

    for node, attr in _get_asset_nodes(soup):
        if attr == "srcset":
            for url, _ in _parse_srcset(node[attr]):
                add_if_remote(url)
        elif attr in ["style", "style_block"]:
            content = node[attr] if attr == "style" else node.string
            for url in _find_css_urls(content):
                add_if_remote(url)
        else:
            add_if_remote(node[attr])
    return urls


def download_worker(
    session: requests.Session,
    url: str,
    cache_dir: Path,
    verify_ssl: bool,
    dry_run: bool,
) -> tuple[str, str | None]:
    """Downloads a single URL and saves it to the cache using a content hash."""
    path_part = urlparse(url).path
    fname_base = _sanitize_asset_filename(os.path.basename(path_part))
    _, ext = os.path.splitext(fname_base)

    temp_download_path = cache_dir / f"temp_{hashlib.sha256(url.encode()).hexdigest()}{ext}"

    if dry_run:
        return url, f"dry_run_hash_for_{fname_base}{ext}"

    LOG.info("Downloading: %s", url)
    ok, err = download_to_file(session, url, temp_download_path, verify_ssl=verify_ssl)
    if not ok:
        LOG.warning(" -> FAILED to download %s: %s", url, err)
        return url, None

    try:
        content_hash = get_file_hash(temp_download_path)
        final_cache_fname = f"{content_hash[:32]}{ext}"
        final_cache_path = cache_dir / final_cache_fname

        if final_cache_path.exists():
            temp_download_path.unlink()
            LOG.info(" -> Content hash exists. Discarding duplicate.")
        else:
            temp_download_path.rename(final_cache_path)
            LOG.info(" -> New content, caching as %s", final_cache_fname)
        return url, final_cache_fname
    except Exception as e:
        LOG.error(" -> FAILED processing downloaded file for %s: %s", url, e)
        if temp_download_path.exists():
            temp_download_path.unlink()
        return url, None


def rewrite_html_file(
    html_path: Path,
    assets_dirname: str,
    url_cache: dict[str, str],
    cache_dir: Path,
    dry_run: bool,
) -> None:
    """Rewrites a single HTML file to point to cached/local assets."""
    LOG.info("Rewriting HTML: %s", html_path)
    try:
        text = html_path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(text, "html.parser")
    except Exception as e:
        LOG.error("Could not read or parse %s: %s", html_path, e)
        return

    assets_dir = html_path.parent / assets_dirname
    safe_makedir(assets_dir)

    def handle_url(raw_url: str) -> str | None:
        raw_url = (raw_url or "").strip()
        if not raw_url or raw_url.lower().startswith("data:"):
            return None

        url_to_check = "https:" + raw_url if raw_url.startswith("//") else raw_url

        if urlparse(url_to_check).scheme in ("http", "https"):  # Remote URL
            cached_fname = url_cache.get(url_to_check)
            if not cached_fname:
                LOG.warning(
                    "URL %s not in cache map (download may have failed).", url_to_check
                )
                return None
            cached_asset = cache_dir / cached_fname
            if not cached_asset.is_file():
                LOG.warning(
                    "Asset for %s not found in cache at %s", url_to_check, cached_asset
                )
                return None

            # The cached_fname is already deterministic (hash-based). Use it directly.
            final_name = cached_fname
            dest_path = assets_dir / final_name

            # Copy from cache to local assets dir only if it's not already there.
            if not dry_run and not dest_path.exists():
                shutil.copy2(cached_asset, dest_path)

            return final_name
        else:  # Local URL
            return None  # This script focuses on remote assets

    for node, attr in _get_asset_nodes(soup):
        if attr == "srcset":
            parts = _parse_srcset(node[attr])
            new_parts = []
            for u, d in parts:
                new_path = handle_url(u)
                new_parts.append(
                    (f"{assets_dirname}/{new_path}", d) if new_path else (u, d)
                )
            node[attr] = _build_srcset(new_parts)
        elif attr in ["style", "style_block"]:
            content = node[attr] if attr == "style" else node.string
            for u in _find_css_urls(content):
                new_path = handle_url(u)
                if new_path:
                    content = content.replace(u, f"{assets_dirname}/{new_path}")

            if attr == "style":
                node[attr] = content
            else:
                node.string = content
        else:
            if new_path := handle_url(node[attr]):
                node[attr] = f"{assets_dirname}/{new_path}"

    if not dry_run:
        html_path.write_text(str(soup), encoding="utf-8")
        LOG.info("Saved updated HTML: %s", html_path)


def main_process(
    root_dir: Path,
    assets_dirname: str,
    max_workers: int,
    clear_cache: bool,
    verify_ssl: bool,
    dry_run: bool,
) -> None:
    """Main logic for asset localization."""
    cache_dir = root_dir / ".asset_cache"
    if clear_cache and cache_dir.exists():
        LOG.info("Clearing cache at %s", cache_dir)
        shutil.rmtree(cache_dir)
    safe_makedir(cache_dir)

    cache_index_path = cache_dir / "index.json"
    url_cache: dict[str, str] = {}
    if cache_index_path.is_file():
        try:
            url_cache = json.loads(cache_index_path.read_text(encoding="utf-8"))
            LOG.info("Loaded %d items from cache index.", len(url_cache))
        except (json.JSONDecodeError, IOError) as e:
            LOG.warning("Could not load cache index: %s. Starting fresh.", e)

    html_files = list(root_dir.rglob("*.html"))
    if not html_files:
        LOG.warning("No .html files found in %s. Nothing to do.", root_dir)
        return

    # Phase 1: Discover all unique URLs
    LOG.info("Discovering URLs in %d HTML files...", len(html_files))
    all_urls: set[str] = set()
    for p in html_files:
        all_urls.update(discover_urls_in_html(p))
    urls_to_download = all_urls - url_cache.keys()
    LOG.info(
        "Found %d unique remote assets. %d need to be downloaded.",
        len(all_urls),
        len(urls_to_download),
    )

    # Phase 2: Download new assets in parallel
    if urls_to_download:
        session = make_session()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(download_worker, session, url, cache_dir, verify_ssl, dry_run)
                for url in urls_to_download
            ]
            for future in as_completed(futures):
                try:
                    res_url, cache_name = future.result()
                    if cache_name:
                        url_cache[res_url] = cache_name
                        if not dry_run:
                            _save_cache_index(cache_index_path, url_cache)
                except Exception as exc:
                    LOG.error("A download worker generated an exception: %s", exc)

    # Phase 3: Rewrite all HTML files
    LOG.info("All downloads complete. Rewriting HTML files...")
    for p in html_files:
        rewrite_html_file(p, assets_dirname, url_cache, cache_dir, dry_run)


def main() -> None:
    """Main entry point for the localize_assets script."""
    parser = argparse.ArgumentParser(
        description="Download/localize assets referenced in local HTML files."
    )
    parser.add_argument("root", help="Root folder to scan for HTML files")
    parser.add_argument(
        "--assets-name",
        default=ASSETS_DIRNAME,
        help=f"Name of assets subfolder (default: {ASSETS_DIRNAME})",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f"Number of parallel download workers (default: {DEFAULT_MAX_WORKERS})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write files; only print actions",
    )
    parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="Do not verify SSL certificates",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Delete the asset cache before running",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose debug output",
    )
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)

    root = Path(args.root)
    if not root.is_dir():
        LOG.error("Root path does not exist or is not a directory: %s", root)
        sys.exit(1)

    main_process(
        root,
        args.assets_name,
        args.workers,
        args.clear_cache,
        not args.no_verify_ssl,
        args.dry_run,
    )


if __name__ == "__main__":
    main()
