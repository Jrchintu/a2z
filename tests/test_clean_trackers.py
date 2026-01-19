"""Tests for the clean_trackers module."""

import pytest

from src.clean_trackers import clean_url


class TestCleanUrl:
    """Tests for clean_url function."""

    def test_no_tracking_params(self):
        url = "https://example.com/page"
        assert clean_url(url) == url

    def test_removes_utm_params(self):
        url = "https://example.com/page?utm_source=google&utm_medium=cpc"
        assert clean_url(url) == "https://example.com/page"

    def test_removes_fbclid(self):
        url = "https://example.com/page?fbclid=abc123"
        assert clean_url(url) == "https://example.com/page"

    def test_removes_gclid(self):
        url = "https://example.com/page?gclid=xyz789"
        assert clean_url(url) == "https://example.com/page"

    def test_preserves_non_tracking_params(self):
        url = "https://example.com/page?id=123&utm_source=google"
        assert clean_url(url) == "https://example.com/page?id=123"

    def test_leetcode_strips_all_params(self):
        url = "https://leetcode.com/problems/two-sum?param=value"
        assert clean_url(url) == "https://leetcode.com/problems/two-sum"

    def test_geeksforgeeks_strips_all_params(self):
        url = "https://www.geeksforgeeks.org/article?ref=123"
        assert clean_url(url) == "https://www.geeksforgeeks.org/article"

    def test_youtube_standardization(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=abc&index=1"
        assert clean_url(url) == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_youtube_preserves_timestamp(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120"
        assert clean_url(url) == "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120"

    def test_youtu_be_conversion(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert clean_url(url) == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_youtu_be_with_timestamp(self):
        url = "https://youtu.be/dQw4w9WgXcQ?t=60"
        assert clean_url(url) == "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=60"
