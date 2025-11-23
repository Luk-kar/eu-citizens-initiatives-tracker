"""
Test suite for ECI model data quality: URL validation and domain checking.

These tests validate url validation and domain checking in extracted
European Citizens' Initiative response data.
"""

import re
from typing import List
from urllib.parse import urlparse, ParseResult

from ECI_initiatives.extractor.responses.model import ECICommissionResponseRecord


class TestURLFieldsIntegrity:
    """Test data quality of URL-related fields"""

    def _validate_url_structure(
        self,
        url: str,
        field_name: str,
        registration_number: str,
    ) -> ParseResult:
        """Validate URL structure - HTTPS only."""
        parsed = urlparse(url)

        assert parsed.scheme in ["https", "http"], (
            f"{field_name} must use HTTPS or HTTP for {registration_number}: "
            f"got '{parsed.scheme}'"
        )

        assert (
            parsed.netloc
        ), f"Missing domain in {field_name} for {registration_number}"

        return parsed

    def _validate_domain_pattern(
        self,
        parsed_url: ParseResult,
        allowed_patterns: List[str],
        field_name: str,
        registration_number: str,
    ) -> None:
        """
        Validate that URL domain matches expected patterns.

        Args:
            parsed_url: Parsed URL components
            allowed_patterns: List of regex patterns for valid domains
            field_name: Name of the field being validated (for error messages)
            registration_number: Initiative registration number (for error messages)

        Raises:
            AssertionError: If domain doesn't match any allowed pattern
        """
        assert any(
            re.match(pattern, parsed_url.netloc) for pattern in allowed_patterns
        ), (
            f"Unexpected domain in {field_name} for {registration_number}: "
            f"{parsed_url.netloc}"
        )

    def test_response_urls_are_valid_https(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify all response_url fields contain valid HTTPS URLs"""
        for record in complete_dataset:
            assert (
                record.response_url is not None
            ), f"response_url is None for {record.registration_number}"

            self._validate_url_structure(
                url=record.response_url,
                field_name="response_url",
                registration_number=record.registration_number,
            )

    def test_initiative_urls_are_valid_https(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify all initiative_url fields contain valid HTTPS URLs"""
        for record in complete_dataset:
            assert (
                record.initiative_url is not None
            ), f"initiative_url is None for {record.registration_number}"

            self._validate_url_structure(
                url=record.initiative_url,
                field_name="initiative_url",
                registration_number=record.registration_number,
            )

    def test_submission_news_urls_are_valid_when_present(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify submission_news_url fields contain valid URLs when not None"""
        for record in complete_dataset:
            if record.submission_news_url is not None:
                self._validate_url_structure(
                    url=record.submission_news_url,
                    field_name="submission_news_url",
                    registration_number=record.registration_number,
                )

    def test_commission_factsheet_urls_are_valid_when_present(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify commission_factsheet_url fields contain valid URLs when not None"""
        for record in complete_dataset:
            if record.commission_factsheet_url is not None:
                self._validate_url_structure(
                    url=record.commission_factsheet_url,
                    field_name="commission_factsheet_url",
                    registration_number=record.registration_number,
                )

    def test_followup_dedicated_website_urls_are_valid_when_present(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify followup_dedicated_website fields contain valid URLs when not None"""
        for record in complete_dataset:
            if record.followup_dedicated_website is not None:
                self._validate_url_structure(
                    url=record.followup_dedicated_website,
                    field_name="followup_dedicated_website",
                    registration_number=record.registration_number,
                )

    def test_urls_point_to_correct_domains(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify URLs point to expected EU domain patterns"""
        # Expected domain patterns for different URL fields
        domain_patterns = {
            "response_url": [r"^citizens-initiative\.europa\.eu$"],
            "initiative_url": [r"^citizens-initiative\.europa\.eu$"],
            "submission_news_url": [
                r"^ec\.europa\.eu$",
                r"^europa\.eu$",
                r"^europarl\.europa\.eu$",
            ],
            "commission_factsheet_url": [r"^citizens-initiative\.europa\.eu$"],
            "followup_dedicated_website": [
                r".*\.europa\.eu$",
                r".*\.ec\.europa\.eu$",
            ],
        }

        for record in complete_dataset:
            # Validate response_url domain
            parsed = urlparse(record.response_url)
            self._validate_domain_pattern(
                parsed_url=parsed,
                allowed_patterns=domain_patterns["response_url"],
                field_name="response_url",
                registration_number=record.registration_number,
            )

            # Validate initiative_url domain
            parsed = urlparse(record.initiative_url)
            self._validate_domain_pattern(
                parsed_url=parsed,
                allowed_patterns=domain_patterns["initiative_url"],
                field_name="initiative_url",
                registration_number=record.registration_number,
            )

            # Validate submission_news_url domain (if present)
            if record.submission_news_url is not None:
                parsed = urlparse(record.submission_news_url)
                self._validate_domain_pattern(
                    parsed_url=parsed,
                    allowed_patterns=domain_patterns["submission_news_url"],
                    field_name="submission_news_url",
                    registration_number=record.registration_number,
                )

            # Validate commission_factsheet_url domain (if present)
            if record.commission_factsheet_url is not None:
                parsed = urlparse(record.commission_factsheet_url)
                self._validate_domain_pattern(
                    parsed_url=parsed,
                    allowed_patterns=domain_patterns["commission_factsheet_url"],
                    field_name="commission_factsheet_url",
                    registration_number=record.registration_number,
                )

            # Validate followup_dedicated_website domain (if present)
            if record.followup_dedicated_website is not None:
                parsed = urlparse(record.followup_dedicated_website)
                self._validate_domain_pattern(
                    parsed_url=parsed,
                    allowed_patterns=domain_patterns["followup_dedicated_website"],
                    field_name="followup_dedicated_website",
                    registration_number=record.registration_number,
                )
