"""Tests for the utils module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.utils import (
    build_srcset,
    find_css_urls,
    get_file_hash,
    parse_srcset,
    sanitize_filename,
)


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_empty_string(self):
        assert sanitize_filename("") == ""

    def test_none(self):
        assert sanitize_filename(None) == ""

    def test_spaces_to_underscores(self):
        assert sanitize_filename("hello world") == "hello_world"

    def test_removes_special_characters(self):
        assert sanitize_filename("file@name#test!") == "file_name_test_"

    def test_preserves_valid_characters(self):
        assert sanitize_filename("valid-file_name.txt") == "valid-file_name.txt"

    def test_removes_query_params(self):
        assert sanitize_filename("file.txt?v=123") == "file.txt"

    def test_removes_fragments(self):
        assert sanitize_filename("file.txt#section") == "file.txt"

    def test_url_decoding(self):
        assert sanitize_filename("hello%20world.txt") == "hello_world.txt"


class TestParseSrcset:
    """Tests for parse_srcset function."""

    def test_empty_string(self):
        assert parse_srcset("") == []

    def test_single_url(self):
        result = parse_srcset("image.jpg")
        assert result == [("image.jpg", "")]

    def test_url_with_descriptor(self):
        result = parse_srcset("image.jpg 2x")
        assert result == [("image.jpg", "2x")]

    def test_multiple_entries(self):
        result = parse_srcset("small.jpg 1x, large.jpg 2x")
        assert result == [("small.jpg", "1x"), ("large.jpg", "2x")]

    def test_width_descriptors(self):
        result = parse_srcset("small.jpg 480w, large.jpg 1024w")
        assert result == [("small.jpg", "480w"), ("large.jpg", "1024w")]


class TestBuildSrcset:
    """Tests for build_srcset function."""

    def test_empty_list(self):
        assert build_srcset([]) == ""

    def test_single_entry(self):
        result = build_srcset([("image.jpg", "2x")])
        assert result == "image.jpg 2x"

    def test_multiple_entries(self):
        result = build_srcset([("small.jpg", "1x"), ("large.jpg", "2x")])
        assert result == "small.jpg 1x, large.jpg 2x"

    def test_empty_descriptor(self):
        result = build_srcset([("image.jpg", "")])
        assert result == "image.jpg"


class TestFindCssUrls:
    """Tests for find_css_urls function."""

    def test_empty_string(self):
        assert find_css_urls("") == []

    def test_single_url(self):
        result = find_css_urls("background: url('image.jpg');")
        assert result == ["image.jpg"]

    def test_double_quotes(self):
        result = find_css_urls('background: url("image.jpg");')
        assert result == ["image.jpg"]

    def test_no_quotes(self):
        result = find_css_urls("background: url(image.jpg);")
        assert result == ["image.jpg"]

    def test_multiple_urls(self):
        result = find_css_urls(
            "background: url('bg.jpg'); border-image: url('border.png');"
        )
        assert result == ["bg.jpg", "border.png"]


class TestGetFileHash:
    """Tests for get_file_hash function."""

    def test_hash_file(self, tmp_path: Path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        
        result = get_file_hash(test_file)
        
        # SHA256 of "hello world"
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert result == expected

    def test_different_content_different_hash(self, tmp_path: Path):
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        assert get_file_hash(file1) != get_file_hash(file2)

    def test_same_content_same_hash(self, tmp_path: Path):
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("same content")
        file2.write_text("same content")
        
        assert get_file_hash(file1) == get_file_hash(file2)
