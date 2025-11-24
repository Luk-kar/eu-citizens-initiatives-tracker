"""
Test suite for downloading and saving followup website HTML pages.

Tests HTML page download, content validation, error page detection,
and proper UTF-8 encoding for multilingual content.
"""

# Standard library
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Third party
import pytest

# Local imports
from ECI_initiatives.scraper.responses_followup_website.file_operations.page import (
    PageFileManager,
)
from ECI_initiatives.scraper.responses_followup_website.consts import MIN_HTML_LENGTH


class TestHTMLDownload:
    """Test HTML page download functionality."""

    @pytest.fixture
    def temp_followup_dir(self, tmp_path):
        """Create temporary followup websites directory."""
        return tmp_path / "followup_websites"

    @pytest.fixture
    def valid_followup_html(self):
        """Valid followup website HTML content."""
        return (
            """
        <!DOCTYPE html>
        <html>
        <head><title>Minority SafePack Initiative</title></head>
        <body>
            <h1>Minority SafePack - One Million Signatures for Diversity in Europe</h1>
            <p>This is the followup website for our successful European Citizens' Initiative.</p>
            """
            + "x" * 1000
            + """
        </body>
        </html>
        """
        )

    @pytest.fixture
    def rate_limit_html(self):
        """HTML content indicating rate limiting."""
        return """
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Too Many Requests</h1>
            <p>Rate limited - please try again later</p>
        </body>
        </html>
        """

    @pytest.fixture
    def server_error_html(self):
        """HTML content with server error."""
        return """
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Sorry</h1>
            <p>We apologise for any inconvenience.</p>
        </body>
        </html>
        """

    def test_downloaded_html_contains_valid_content(
        self, temp_followup_dir, valid_followup_html
    ):
        """
        When downloading followup website pages, verify that each
        successfully downloaded HTML file contains valid content.
        """
        # Arrange
        file_ops = PageFileManager(str(temp_followup_dir))
        file_ops.setup_directories()

        # Act
        filename = file_ops.save_followup_website_page(
            valid_followup_html, "2019", "2019_000007"
        )

        # Assert
        saved_file = temp_followup_dir / filename
        assert saved_file.exists()

        with open(saved_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify content is substantial
        assert len(content) > 1000, "Content should be substantial"

        # Verify no error indicators
        assert "rate limited" not in content.lower()
        assert "too many requests" not in content.lower()
        assert "we apologise for any inconvenience" not in content.lower()

    def test_short_html_not_saved(self, temp_followup_dir):
        """
        When HTML content is too short (below minimum threshold), verify that
        the file is not saved and an exception is raised.
        """
        # Arrange
        short_html = "<html><body>Short</body></html>"
        file_ops = PageFileManager(str(temp_followup_dir))
        file_ops.setup_directories()

        # Act & Assert
        with pytest.raises(Exception, match="HTML content too short"):
            file_ops.save_followup_website_page(short_html, "2019", "2019_000007")

        # Verify file was not created
        year_dir = temp_followup_dir / "2019"
        if year_dir.exists():
            html_files = list(year_dir.glob("*.html"))
            assert len(html_files) == 0, "No HTML files should be saved"

    def test_rate_limit_detection(self, temp_followup_dir, rate_limit_html):
        """
        When a rate limiting error page is detected, verify that
        an exception is raised and the file is not saved.
        """
        # Arrange
        file_ops = PageFileManager(str(temp_followup_dir))
        file_ops.setup_directories()

        # Act & Assert
        with pytest.raises(Exception, match="Rate limiting detected"):
            file_ops.save_followup_website_page(rate_limit_html, "2019", "2019_000007")

        # Verify file was not saved
        year_dir = temp_followup_dir / "2019"
        if year_dir.exists():
            html_files = list(year_dir.glob("*.html"))
            assert len(html_files) == 0

    def test_server_error_page_detected(self, temp_followup_dir, server_error_html):
        """
        When a server error page is detected, verify that
        an exception is raised and the file is not saved.
        """
        # Arrange
        file_ops = PageFileManager(str(temp_followup_dir))
        file_ops.setup_directories()

        # Act & Assert
        with pytest.raises(Exception, match="Error page detected"):
            file_ops.save_followup_website_page(
                server_error_html, "2019", "2019_000007"
            )

        # Verify file was not saved
        year_dir = temp_followup_dir / "2019"
        if year_dir.exists():
            html_files = list(year_dir.glob("*.html"))
            assert len(html_files) == 0

    def test_html_files_prettified(self, temp_followup_dir):
        """
        When saving HTML files, verify that the content is prettified
        (well-formatted) for readability.
        """
        # Arrange
        ugly_html = "<html><head><title>Test</title></head><body><div><p>Content</p></div></body></html>"
        file_ops = PageFileManager(str(temp_followup_dir))
        file_ops.setup_directories()

        # Act
        filename = file_ops.save_followup_website_page(ugly_html, "2019", "2019_000007")

        # Assert
        saved_file = temp_followup_dir / filename
        with open(saved_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify prettification
        assert "\n" in content, "Should contain newlines"
        lines = content.split("\n")
        assert len(lines) > 5, "Prettified HTML should have multiple lines"

    def test_html_files_utf8_encoded(self, temp_followup_dir):
        """
        When saving HTML files, verify that UTF-8 encoding is used to preserve
        special characters in multilingual content.
        """
        # Arrange
        multilingual_html = """
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Diversité en Europe</h1>
            <p>Être différent, ça compte! 🇪🇺</p>
            <p>Salva le api 🐝</p>
        </body>
        </html>
        """
        file_ops = PageFileManager(str(temp_followup_dir))
        file_ops.setup_directories()

        # Act
        filename = file_ops.save_followup_website_page(
            multilingual_html, "2019", "2019_000007"
        )

        # Assert
        saved_file = temp_followup_dir / filename
        with open(saved_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify special characters are preserved
        assert "Diversité" in content
        assert "Être différent" in content
        assert "🇪🇺" in content
        assert "🐝" in content

    def test_validate_html_content_length(self, temp_followup_dir):
        """
        Verify HTML validation checks content length against minimum threshold.
        """
        # Arrange
        file_ops = PageFileManager(str(temp_followup_dir))

        # Test with content just below threshold
        short_content = "x" * (MIN_HTML_LENGTH - 1)

        # Act & Assert
        with pytest.raises(Exception, match="HTML content too short"):
            file_ops._validate_html(short_content)

        # Test with content at threshold
        valid_content = "x" * MIN_HTML_LENGTH
        result = file_ops._validate_html(valid_content)
        assert result is True
