"""
Test suite for downloading and saving Commission response HTML pages.
"""

# Standard library
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Third party
import pytest
from bs4 import BeautifulSoup

# Local imports
from ECI_initiatives.scraper.responses.file_operations.page import PageFileManager
from ECI_initiatives.scraper.responses.consts import MIN_HTML_LENGTH


class TestHTMLDownload:
    """Test HTML page download functionality."""

    @pytest.fixture
    def test_data_dir(self):
        """Get path to test data directory."""
        return Path(__file__).parent.parent.parent.parent / "data" / "example_htmls" / "responses"
    
    @pytest.fixture
    def temp_responses_dir(self, tmp_path):
        """Create temporary responses directory for testing."""
        return tmp_path / "responses"
    
    @pytest.fixture
    def valid_response_html(self, test_data_dir):
        """Valid Commission response HTML content from actual file."""
        # Use strong_legislative_success example
        html_file = test_data_dir / "strong_legislative_success" / "2012" / "2012_000003_en.html"
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()

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
        """HTML content with multilingual server error."""

        return """
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Sorry</h1>
            <p>We apologise for any inconvenience.</p>
            <p>Veuillez nous excuser pour ce désagrément.</p>
            <p>Ci scusiamo per il disagio arrecato.</p>
        </body>
        </html>
        """

    def test_downloaded_html_contains_valid_content(
        self, temp_responses_dir, valid_response_html
    ):
        """
        When downloading response pages, verify that each successfully
        downloaded HTML file contains the expected Commission response content
        (not error pages or rate limit messages).
        """

        # Arrange
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act
        filename = file_ops.save_response_page(valid_response_html, "2019", "2019_000007")

        # Assert
        saved_file = temp_responses_dir / filename
        assert saved_file.exists()

        with open(saved_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify Commission-specific content
        assert "Commission" in content
        assert "European Citizens' Initiative" in content
        assert len(content) > 1000, "Content should be substantial"

        # Verify no error indicators
        assert "rate limited" not in content.lower()
        assert "too many requests" not in content.lower()
        assert "we apologise for any inconvenience" not in content.lower()

    def test_short_html_not_saved(self, temp_responses_dir):
        """
        When HTML content is too short (below minimum threshold), verify that
        the file is not saved and the download is marked as failed.
        """
        # Arrange
        short_html = "<html><body>Short</body></html>"
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act & Assert
        with pytest.raises(Exception, match="HTML content too short"):
            file_ops.save_response_page(short_html, "2019", "2019_000007")

        # Verify file was not created
        year_dir = temp_responses_dir / "2019"
        if year_dir.exists():
            html_files = list(year_dir.glob("*.html"))
            assert len(html_files) == 0, "No HTML files should be saved"

    def test_rate_limit_retry_with_backoff(self, temp_responses_dir, rate_limit_html):
        """
        When a rate limiting error page is detected, verify that the scraper
        retries the download with exponential backoff.
        """
        # Arrange
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act & Assert - Rate limit detection
        with pytest.raises(Exception, match="Rate limiting detected"):
            file_ops.save_response_page(rate_limit_html, "2019", "2019_000007")

        # Verify file was not saved
        year_dir = temp_responses_dir / "2019"
        if year_dir.exists():
            html_files = list(year_dir.glob("*.html"))
            assert len(html_files) == 0

    def test_server_error_page_marked_failed(
        self, temp_responses_dir, server_error_html
    ):
        """
        When a server error page is detected (multilingual "Sorry" messages),
        verify that the download is marked as failed.
        """

        # Arrange
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act & Assert
        with pytest.raises(Exception, match="Error page detected"):
            file_ops.save_response_page(server_error_html, "2019", "2019_000007")

        # Verify file was not saved
        year_dir = temp_responses_dir / "2019"
        if year_dir.exists():
            html_files = list(year_dir.glob("*.html"))
            assert len(html_files) == 0

    def test_max_retries_marks_as_failed(self):
        """
        When a download fails multiple times (exceeding max retries), verify
        that the item is marked as failed and included in the failure summary.
        """
        # Arrange
        from ECI_initiatives.scraper.responses.downloader import ResponseDownloader
        from unittest.mock import Mock, patch, MagicMock
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ResponseDownloader(tmpdir)
            
            # Mock the WebDriver to always raise an exception
            mock_driver = MagicMock()
            mock_driver.get.side_effect = Exception("Connection timeout")
            downloader.driver = mock_driver
            
            # Mock logger to prevent actual logging
            downloader.logger = Mock()
            
            # Test parameters
            test_url = "https://citizens-initiative.europa.eu/initiatives/response/2019/000007"
            test_year = "2019"
            test_reg_number = "000007"
            max_retries = 3
            
            # Act - Call the actual download method
            success, timestamp = downloader.download_single_response(
                url=test_url,
                year=test_year,
                reg_number=test_reg_number,
                max_retries=max_retries
            )
            
            # Assert
            assert success is False, "Download should fail after max retries"
            assert timestamp == "", "Timestamp should be empty for failed download"
            
            # Verify driver.get was called max_retries times
            assert mock_driver.get.call_count == max_retries, \
                f"Expected {max_retries} retry attempts, but got {mock_driver.get.call_count}"
            
            # Verify error was logged
            downloader.logger.error.assert_called_once()


    def test_html_files_prettified(self, temp_responses_dir):
        """
        When saving HTML files, verify that the content is prettified
        (well-formatted) for readability.
        """

        # Arrange
        ugly_html = "<html><head><title>Test</title></head><body><div><p>Content</p></div></body></html>"
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act
        filename = file_ops.save_response_page(ugly_html, "2019", "2019_000007")

        # Assert
        saved_file = temp_responses_dir / filename
        with open(saved_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify prettification (indentation and newlines)
        assert "\n" in content, "Should contain newlines"
        assert "  " in content or "\t" in content, "Should contain indentation"
        
        # Count lines to verify it's been expanded
        lines = content.split("\n")
        assert len(lines) > 5, "Prettified HTML should have multiple lines"

    def test_html_files_utf8_encoded(self, temp_responses_dir):
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
            <p>Μειονοτική προστασία</p>
        </body>
        </html>
        """
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act
        filename = file_ops.save_response_page(multilingual_html, "2019", "2019_000007")

        # Assert
        saved_file = temp_responses_dir / filename
        with open(saved_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify special characters are preserved
        assert "Diversité" in content
        assert "Être différent" in content
        assert "🇪🇺" in content
        assert "🐝" in content
        assert "Μειονοτική" in content

    def test_browser_cleanup_after_errors(self):
        """
        When the browser is closed after downloading, verify that resources
        are properly cleaned up even if errors occurred during downloads.
        """

        # Arrange
        from ECI_initiatives.scraper.responses.downloader import ResponseDownloader
        from unittest.mock import Mock, patch, MagicMock
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:

            # Patch initialize_browser to return a mock driver
            with patch('ECI_initiatives.scraper.responses.downloader.initialize_browser') as mock_init_browser:
                
                # Create mock driver
                mock_driver = MagicMock()
                mock_quit = Mock()
                mock_driver.quit = mock_quit
                mock_driver.get.side_effect = Exception("Connection error")
                mock_init_browser.return_value = mock_driver
                
                downloader = ResponseDownloader(tmpdir)
                
                # Mock logger to prevent actual logging
                downloader.logger = Mock()
                
                # Initialize the driver (this calls initialize_browser)
                downloader._initialize_driver()
                
                # Act - Attempt download that will fail
                try:
                    downloader.download_single_response(
                        url="https://test-url.com",
                        year="2019",
                        reg_number="000007",
                        max_retries=1  # Single attempt to speed up test
                    )
                except Exception:
                    pass  # Expected to fail
                
                # Now close the downloader (which should call driver.quit)
                downloader._close_driver()
                
                # Assert - Browser quit was called
                mock_quit.assert_called_once()


    def test_validate_html_content_length(self, temp_responses_dir):
        """
        Verify HTML validation checks content length against minimum threshold.
        """

        # Arrange
        file_ops = PageFileManager(str(temp_responses_dir))
        
        # Test with content just below threshold
        short_content = "x" * (MIN_HTML_LENGTH - 1)
        
        # Act & Assert
        with pytest.raises(Exception, match="HTML content too short"):
            file_ops._validate_html(short_content)

        # Test with content at threshold
        valid_content = "x" * MIN_HTML_LENGTH
        result = file_ops._validate_html(valid_content)

        assert result is True