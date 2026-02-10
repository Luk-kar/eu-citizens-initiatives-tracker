"""
Test suite for ECI model data quality: Text content completeness and quality.

These tests validate text content completeness and quality in extracted
European Citizens' Initiative response data.
"""

import html
import re
from typing import List

from bs4 import BeautifulSoup
import pytest

from ECI_initiatives.data_pipeline.extractor.responses.model import (
    ECICommissionResponseRecord,
)


class TestTextFieldsCompleteness:
    """Test data quality of text content fields"""

    # Minimum substantial text length (characters)
    MIN_SUBSTANTIAL_LENGTH = 50

    # Excessive whitespace patterns
    EXCESSIVE_WHITESPACE = re.compile(r"\s{3,}")  # 3+ consecutive spaces
    EXCESSIVE_NEWLINES = re.compile(r"\n{3,}")  # 3+ consecutive newlines

    def _is_empty_or_whitespace(self, text: str) -> bool:
        """
        Check if text is empty or contains only whitespace.

        Args:
            text: Text to check

        Returns:
            True if empty or whitespace-only
        """
        return not text or not text.strip()

    def _has_substantial_content(self, text: str, min_length: int = None) -> bool:
        """
        Check if text contains substantial content (not just whitespace).

        Args:
            text: Text to check
            min_length: Minimum length for substantial content (default: MIN_SUBSTANTIAL_LENGTH)

        Returns:
            True if text has substantial content
        """
        if not text:
            return False

        min_len = min_length if min_length is not None else self.MIN_SUBSTANTIAL_LENGTH
        cleaned = text.strip()
        return len(cleaned) >= min_len

    def _contains_html_tags(self, text: str) -> bool:
        """
        Check if text contains HTML tags like <p>, <div>, etc.

        Uses BeautifulSoup to reliably detect HTML tags.

        Args:
            text: Text to check

        Returns:
            True if HTML tags found
        """
        if not text:
            return False

        # Parse with BeautifulSoup
        soup = BeautifulSoup(text, "html.parser")

        # If BeautifulSoup finds any tags, HTML is present
        # Note: soup.find_all() returns all tags in the document
        tags = soup.find_all()

        return len(tags) > 0

    def _contains_html_entities(self, text: str) -> bool:
        """
        Check if text contains unescaped HTML entities like &nbsp; &#160;

        Uses html.unescape() to detect if text changes when HTML entities are decoded.

        Args:
            text: Text to check

        Returns:
            True if HTML entities found
        """
        if not text:
            return False

        # If unescaping changes the text, entities were present
        unescaped = html.unescape(text)
        return text != unescaped

    def _get_html_entity_examples(self, text: str, max_examples: int = 5) -> List[str]:
        """
        Extract examples of HTML entities found in text.
        Uses standard library html.entities for comprehensive coverage.
        """

        found = []

        # Check named entities (e.g., &nbsp; &amp; &lt; &gt; &quot;)
        # These are HTML entities with names like &entityname;
        for name in html.entities.name2codepoint:

            entity = f"&{name};"
            if entity in text and len(found) < max_examples:
                found.append(entity)

        # Check numeric decimal entities (e.g., &#160; &#38; &#60;)
        # These use decimal Unicode codepoints: &#number;
        numeric = re.findall(r"&#\d+;", text)

        for entity in set(numeric):
            if len(found) < max_examples:
                found.append(entity)

        return found

    def _has_excessive_whitespace(self, text: str) -> bool:
        """
        Check if text has excessive consecutive whitespace or newlines.

        Args:
            text: Text to check

        Returns:
            True if excessive whitespace found
        """
        return bool(
            self.EXCESSIVE_WHITESPACE.search(text)
            or self.EXCESSIVE_NEWLINES.search(text)
        )

    def test_initiative_titles_are_not_empty(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify initiative_title is never empty or whitespace-only"""
        for record in complete_dataset:
            assert (
                record.initiative_title is not None
            ), f"initiative_title is None for {record.registration_number}"

            assert not self._is_empty_or_whitespace(record.initiative_title), (
                f"initiative_title is empty or whitespace-only for "
                f"{record.registration_number}"
            )

            # Title should be reasonably short (not truncated text)
            title_length = len(record.initiative_title)
            assert title_length < 500, (
                f"initiative_title suspiciously long ({title_length} chars) for "
                f"{record.registration_number}: {record.initiative_title[:100]}..."
            )

    def test_submission_text_is_not_empty(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify submission_text contains substantial content"""
        for record in complete_dataset:
            assert (
                record.submission_text is not None
            ), f"submission_text is None for {record.registration_number}"

            assert self._has_substantial_content(record.submission_text), (
                f"submission_text lacks substantial content for "
                f"{record.registration_number}. "
                f"Length: {len(record.submission_text.strip())} chars "
                f"(minimum: {self.MIN_SUBSTANTIAL_LENGTH})"
            )

    def test_commission_answer_text_is_not_empty_when_present(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify commission_answer_text contains substantial content when not None"""
        for record in complete_dataset:
            if record.commission_answer_text is not None:
                assert self._has_substantial_content(record.commission_answer_text), (
                    f"commission_answer_text present but lacks substantial content for "
                    f"{record.registration_number}. "
                    f"Length: {len(record.commission_answer_text.strip())} chars "
                    f"(minimum: {self.MIN_SUBSTANTIAL_LENGTH})"
                )

    def test_text_fields_do_not_contain_html_artifacts(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify text fields are cleaned of HTML tags and entities"""
        for record in complete_dataset:
            # Check initiative_title
            if record.initiative_title:
                assert not self._contains_html_tags(record.initiative_title), (
                    f"initiative_title contains HTML tags for {record.registration_number}: "
                    f"{record.initiative_title[:200]}..."
                )

                # Check for HTML entities
                if self._contains_html_entities(record.initiative_title):
                    examples = self._get_html_entity_examples(record.initiative_title)
                    if examples:
                        pytest.fail(
                            f"initiative_title contains HTML entities for "
                            f"{record.registration_number}:\n"
                            f"  Found: {', '.join(examples)}\n"
                            f"  Title: {record.initiative_title[:200]}..."
                        )

            # Check submission_text
            if record.submission_text:
                assert not self._contains_html_tags(record.submission_text), (
                    f"submission_text contains HTML tags for {record.registration_number}. "
                    f"Preview: {record.submission_text[:200]}..."
                )

                # HTML entities in body text are less critical but should be noted
                if self._contains_html_entities(record.submission_text):
                    examples = self._get_html_entity_examples(record.submission_text)
                    if examples:
                        # Only fail on common problematic entities
                        problematic = ["&nbsp;", "&#160;"]
                        if any(entity.split()[0] in problematic for entity in examples):
                            pytest.fail(
                                f"submission_text contains problematic HTML entities for "
                                f"{record.registration_number}: {', '.join(examples)}"
                            )

            # Check commission_answer_text
            if record.commission_answer_text:
                assert not self._contains_html_tags(record.commission_answer_text), (
                    f"commission_answer_text contains HTML tags for "
                    f"{record.registration_number}. "
                    f"Preview: {record.commission_answer_text[:200]}..."
                )

    def test_text_fields_have_proper_whitespace_normalization(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify text fields don't have excessive whitespace or malformed spacing"""
        for record in complete_dataset:
            # Check initiative_title
            if record.initiative_title:
                assert not self._has_excessive_whitespace(record.initiative_title), (
                    f"initiative_title has excessive whitespace for "
                    f"{record.registration_number}: "
                    f"{repr(record.initiative_title[:200])}"
                )

                # Title should not start/end with whitespace
                assert record.initiative_title == record.initiative_title.strip(), (
                    f"initiative_title has leading/trailing whitespace for "
                    f"{record.registration_number}: "
                    f"{repr(record.initiative_title)}"
                )

            # Check submission_text
            if record.submission_text:
                assert not self._has_excessive_whitespace(record.submission_text), (
                    f"submission_text has excessive whitespace for "
                    f"{record.registration_number}: "
                    f"{repr(record.submission_text[:200])}"
                )

                # Should not start/end with whitespace
                assert record.submission_text == record.submission_text.strip(), (
                    f"submission_text has leading/trailing whitespace for "
                    f"{record.registration_number}"
                )

            # Check commission_answer_text
            if record.commission_answer_text:
                assert not self._has_excessive_whitespace(
                    record.commission_answer_text
                ), (
                    f"commission_answer_text has excessive whitespace for "
                    f"{record.registration_number}: "
                    f"{repr(record.commission_answer_text[:200])}"
                )

                # Should not start/end with whitespace
                assert (
                    record.commission_answer_text
                    == record.commission_answer_text.strip()
                ), (
                    f"commission_answer_text has leading/trailing whitespace for "
                    f"{record.registration_number}"
                )
