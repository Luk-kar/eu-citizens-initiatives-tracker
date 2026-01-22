"""
Tests for CELEX Translator Module.
"""

import pytest
import json
from legislation_titles.celex_translator import CelexTranslator


class TestCelexTranslator:
    """Test suite for CelexTranslator class."""

    def test_init(self, sample_legislation_references):
        """Test initialization with legislation references."""
        translator = CelexTranslator(sample_legislation_references)
        assert translator.referenced_legislation_by_id == sample_legislation_references
        assert translator.celex_ids == []
        assert translator.unresolved_references == []

    def test_parse_referenced_legislation_valid_json(self):
        """Test parsing valid JSON legislation reference."""
        json_str = '{"Article": ["19(2)"], "CELEX": ["52014DC0335"]}'
        result = CelexTranslator.parse_referenced_legislation(json_str)
        assert result == {"Article": ["19(2)"], "CELEX": ["52014DC0335"]}

    def test_parse_referenced_legislation_invalid_json(self):
        """Test parsing invalid JSON returns empty dict."""
        json_str = '{"Article": ["19(2)"'
        result = CelexTranslator.parse_referenced_legislation(json_str)
        assert result == {}

    def test_parse_referenced_legislation_none(self):
        """Test parsing None/NaN returns empty dict."""
        result = CelexTranslator.parse_referenced_legislation(None)
        assert result == {}

    def test_convert_directive_to_celex_valid(self):
        """Test converting valid Directive to CELEX format."""
        assert CelexTranslator.convert_directive_to_celex("2010/63/EU") == "32010L0063"
        assert CelexTranslator.convert_directive_to_celex("2013/1/EU") == "32013L0001"
        assert CelexTranslator.convert_directive_to_celex("2024/999/EU") == "32024L0999"

    def test_convert_directive_to_celex_invalid(self):
        """Test conversion of invalid directive formats."""
        assert (
            CelexTranslator.convert_directive_to_celex("2010") is None
        )  # Missing separator
        assert (
            CelexTranslator.convert_directive_to_celex("2010/63/123") is None
        )  # Too many parts
        assert CelexTranslator.convert_directive_to_celex("") is None  # Empty string
        assert (
            CelexTranslator.convert_directive_to_celex("invalid") is None
        )  # No valid format

    def test_convert_regulation_to_celex_valid(self):
        """Test converting valid Regulation to CELEX format."""
        assert CelexTranslator.convert_regulation_to_celex("178/2002") == "32002R0178"
        assert CelexTranslator.convert_regulation_to_celex("1/2024") == "32024R0001"
        assert CelexTranslator.convert_regulation_to_celex("1234/2020") == "32020R1234"

    def test_convert_regulation_to_celex_invalid(self):
        """Test converting invalid Regulation format returns None."""
        assert CelexTranslator.convert_regulation_to_celex("invalid") is None
        assert CelexTranslator.convert_regulation_to_celex("178-2002") is None
        assert CelexTranslator.convert_regulation_to_celex("178") is None

    def test_extract_all_celex_ids_from_celex_field(self):
        """Test extracting CELEX IDs from CELEX field."""
        references = ['{"CELEX": ["32010L0063", "32002R0178"]}']
        translator = CelexTranslator(references)
        celex_ids, unresolved = translator.extract_all_celex_ids()

        assert set(celex_ids) == {"32010L0063", "32002R0178"}
        assert unresolved == []

    def test_extract_all_celex_ids_from_directives(self):
        """Test extracting and converting Directives to CELEX."""
        references = ['{"Directive": ["2010/63/EU", "2013/1/EU"]}']
        translator = CelexTranslator(references)
        celex_ids, unresolved = translator.extract_all_celex_ids()

        assert set(celex_ids) == {"32010L0063", "32013L0001"}
        assert unresolved == []

    def test_extract_all_celex_ids_from_regulations(self):
        """Test extracting and converting Regulations to CELEX."""
        references = ['{"Regulation": ["178/2002", "1234/2020"]}']
        translator = CelexTranslator(references)
        celex_ids, unresolved = translator.extract_all_celex_ids()

        assert set(celex_ids) == {"32002R0178", "32020R1234"}
        assert unresolved == []

    def test_extract_all_celex_ids_mixed_sources(self, sample_legislation_references):
        """Test extracting CELEX IDs from mixed sources."""
        translator = CelexTranslator(sample_legislation_references)
        celex_ids, unresolved = translator.extract_all_celex_ids()

        # Should contain CELEX from direct references and converted Directives/Regulations
        assert "52014DC0335" in celex_ids
        assert "52020DC0015" in celex_ids
        assert "32010L0063" in celex_ids
        assert "32002R0178" in celex_ids
        assert len(celex_ids) > 0

    def test_extract_all_celex_ids_unresolved_articles(self):
        """Test that standalone Articles are marked as unresolved."""
        references = ['{"Article": ["15"]}']
        translator = CelexTranslator(references)
        celex_ids, unresolved = translator.extract_all_celex_ids()

        assert celex_ids == []
        assert {"type": "Article", "value": "15"} in unresolved

    def test_extract_all_celex_ids_invalid_directive(self):
        """Test that invalid Directives are marked as unresolved."""
        references = ['{"Directive": ["invalid-format"]}']
        translator = CelexTranslator(references)
        celex_ids, unresolved = translator.extract_all_celex_ids()

        assert celex_ids == []
        assert {"type": "Directive", "value": "invalid-format"} in unresolved

    def test_extract_all_celex_ids_invalid_regulation(self):
        """Test that invalid Regulations are marked as unresolved."""
        references = ['{"Regulation": ["invalid-format"]}']
        translator = CelexTranslator(references)
        celex_ids, unresolved = translator.extract_all_celex_ids()

        assert celex_ids == []
        assert {"type": "Regulation", "value": "invalid-format"} in unresolved

    def test_extract_all_celex_ids_deduplication(self):
        """Test that duplicate CELEX IDs are removed."""
        references = [
            '{"CELEX": ["32010L0063"]}',
            '{"CELEX": ["32010L0063"]}',
            '{"Directive": ["2010/63/EU"]}',
        ]
        translator = CelexTranslator(references)
        celex_ids, unresolved = translator.extract_all_celex_ids()

        assert celex_ids == ["32010L0063"]

    def test_extract_all_celex_ids_empty_input(self):
        """Test extraction with empty input list."""
        translator = CelexTranslator([])
        celex_ids, unresolved = translator.extract_all_celex_ids()

        assert celex_ids == []
        assert unresolved == []

    def test_extract_all_celex_ids_none_values(self):
        """Test extraction with None values in list."""
        references = [None, '{"CELEX": ["32010L0063"]}', None]
        translator = CelexTranslator(references)
        celex_ids, unresolved = translator.extract_all_celex_ids()

        assert "32010L0063" in celex_ids

    def test_extract_all_celex_ids_invalid_json(self, invalid_json_references):
        """Test extraction with invalid JSON strings."""
        translator = CelexTranslator(invalid_json_references)
        celex_ids, unresolved = translator.extract_all_celex_ids()

        # Invalid JSON should be skipped, not crash
        assert isinstance(celex_ids, list)
        assert isinstance(unresolved, list)
