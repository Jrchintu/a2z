"""
Shared configuration for the A2Z DSA project.

This module centralizes all path constants and configuration values
used across the different scripts in the project.
"""

from pathlib import Path

# --- Project Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = PROJECT_ROOT / "content" / "articles"
PUBLIC_DIR = PROJECT_ROOT / "public" / "articles"
TEMPLATE_DIR = PROJECT_ROOT / "templates"
DEFAULT_TEMPLATE = TEMPLATE_DIR / "template.html"
A2Z_JSON = PROJECT_ROOT / "a2z.json"

# --- Network Settings ---
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; A2Z-DSA/1.0)"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_WORKERS = 10
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF = 0.3

# --- Asset Settings ---
ASSETS_DIRNAME = "assets"
MAX_FILE_SIZE_MB = 100

# --- URL Cleaning Settings ---
TRACKING_PARAMS = frozenset({
    # Google Analytics
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    # Google Ads
    'gclid',
    # Facebook
    'fbclid',
    # Microsoft Advertising
    'msclkid',
    # Mailchimp
    'mc_cid', 'mc_eid',
    # Other common trackers
    '_ga',
})

SITES_TO_STRIP_PARAMS = frozenset([
    'geeksforgeeks.org',
    'codingninjas.com',
    'leetcode.com',
])
