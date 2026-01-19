"""
Shared utility functions for the A2Z DSA project.

This module provides common functionality used across multiple scripts,
including HTTP session management, file operations, and text processing.
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import (
    DEFAULT_BACKOFF,
    DEFAULT_MAX_WORKERS,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    MAX_FILE_SIZE_MB,
)

if TYPE_CHECKING:
    from typing import Any

LOG = logging.getLogger(__name__)


def make_session(
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
    user_agent: str = DEFAULT_USER_AGENT,
) -> requests.Session:
    """
    Creates a requests Session with automatic retries for network robustness.

    Args:
        retries: Number of retry attempts for failed requests.
        backoff: Backoff factor for exponential delay between retries.
        user_agent: User-Agent header to use for requests.

    Returns:
        Configured requests Session object.
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": user_agent})
    return session


def sanitize_filename(name: str | None) -> str:
    """
    Sanitizes a string to be used as a valid filename.

    Removes unsafe characters and normalizes spaces to underscores.

    Args:
        name: The string to sanitize.

    Returns:
        A safe filename string.
    """
    if not name:
        return ""
    name = unquote(name.strip())
    name = name.replace(" ", "_")
    name = name.split("?")[0].split("#")[0]  # Remove query params and fragments
    name = re.sub(r'[^A-Za-z0-9._-]', '_', name)
    return name or "file"


def safe_makedir(path: Path) -> None:
    """
    Creates a directory if it doesn't exist.

    Args:
        path: The directory path to create.
    """
    path.mkdir(parents=True, exist_ok=True)


def get_file_hash(path: Path, algorithm: str = "sha256") -> str:
    """
    Calculates the hash of a file's content.

    Args:
        path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal hash string.
    """
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def download_to_file(
    session: requests.Session,
    url: str,
    dest: Path,
    verify_ssl: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
    max_mb: int = MAX_FILE_SIZE_MB,
) -> tuple[bool, str | None]:
    """
    Downloads a URL to a specific destination file path.

    Uses a temporary file to ensure atomic writes.

    Args:
        session: The requests Session to use.
        url: The URL to download.
        dest: Destination file path.
        verify_ssl: Whether to verify SSL certificates.
        timeout: Request timeout in seconds.
        max_mb: Maximum file size in megabytes.

    Returns:
        Tuple of (success: bool, error_message: str | None).
    """
    tmp = dest.with_suffix(dest.suffix + ".part")
    safe_makedir(dest.parent)

    try:
        with session.get(url, stream=True, timeout=timeout, verify=verify_ssl) as r:
            r.raise_for_status()
            max_bytes = max_mb * 1024 * 1024
            with open(tmp, "wb") as fh:
                size = 0
                for chunk in r.iter_content(chunk_size=8192):
                    size += len(chunk)
                    if size > max_bytes:
                        raise RuntimeError(f"File exceeded max size of {max_mb} MB")
                    fh.write(chunk)
            tmp.rename(dest)
        return True, None
    except Exception as e:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        return False, str(e)


def setup_logging(
    verbose: bool = False,
    log_format: str = "%(levelname)s: %(message)s",
) -> None:
    """
    Configures logging for the application.

    Args:
        verbose: If True, sets level to DEBUG; otherwise INFO.
        log_format: Format string for log messages.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format=log_format)


def parse_srcset(srcset: str) -> list[tuple[str, str]]:
    """
    Parses an srcset attribute into a list of (url, descriptor) tuples.

    Args:
        srcset: The srcset attribute value.

    Returns:
        List of (url, descriptor) tuples.
    """
    if not srcset:
        return []
    result = []
    for part in srcset.split(","):
        parts = part.strip().split()
        if parts:
            url = parts[0]
            descriptor = " ".join(parts[1:]) if len(parts) > 1 else ""
            result.append((url, descriptor))
    return result


def build_srcset(parts: list[tuple[str, str]]) -> str:
    """
    Builds an srcset string from a list of (url, descriptor) tuples.

    Args:
        parts: List of (url, descriptor) tuples.

    Returns:
        Formatted srcset string.
    """
    return ", ".join([f"{u} {d}".strip() for u, d in parts])


def find_css_urls(text: str) -> list[str]:
    """
    Finds all url(...) values in a block of CSS.

    Args:
        text: CSS text to search.

    Returns:
        List of URLs found in url() declarations.
    """
    if not text:
        return []
    return [
        m.group(2)
        for m in re.finditer(r'url\(\s*([\'"]?)(.*?)\1\s*\)', text, flags=re.IGNORECASE)
    ]
