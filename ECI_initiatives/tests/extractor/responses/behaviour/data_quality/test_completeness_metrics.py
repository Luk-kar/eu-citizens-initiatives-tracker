"""
Test suite for ECI model data quality: Data completeness and distribution metrics.

These tests validate data completeness and distribution metrics in extracted
European Citizens' Initiative response data.
"""

from typing import List

from ECI_initiatives.data_pipeline.extractor.responses.model import (
    ECICommissionResponseRecord,
)
from .validation_helpers import (
    is_empty_value,
)
from .test_boolean_fields import TestBooleanFieldsConsistency


class TestDataCompletenessMetrics:
    """Test overall data completeness across the dataset"""

    # Define mandatory fields that must be present in every record
    MANDATORY_FIELDS = {
        "response_url",
        "initiative_url",
        "initiative_title",
        "registration_number",
        "commission_submission_date",
        "submission_text",
        "official_communication_adoption_date",
        "commission_answer_text",
        "final_outcome_status",
    } | TestBooleanFieldsConsistency.BOOLEAN_FIELDS

    # Define optional fields with expected distribution
    # These should have SOME data but not necessarily 100%
    OPTIONAL_FIELDS = {
        "submission_news_url",
        "commission_meeting_date",
        "commission_officials_met",
        "parliament_hearing_date",
        "parliament_hearing_video_urls",
        "plenary_debate_date",
        "plenary_debate_video_urls",
        "official_communication_document_urls",
        "law_implementation_date",
        "commission_deadlines",
        "commission_rejection_reason",
        "laws_actions",
        "policies_actions",
        "court_cases_referenced",
        "followup_latest_date",
        "followup_most_future_date",
        "commission_factsheet_url",
        "followup_dedicated_website",
        "referenced_legislation_by_id",
        "referenced_legislation_by_name",
        "followup_events_with_dates",
    }

    # Procedural milestone fields that should be highly complete
    # (Most initiatives should have these as part of standard ECI process)
    PROCEDURAL_FIELDS = {
        "commission_meeting_date": 0.8,  # 80% - most initiatives have meetings
        "parliament_hearing_date": 0.8,  # 80% - most have hearings
        "plenary_debate_date": 0.6,  # 60% - many have plenary debates
    }

    def _calculate_completeness_rate(
        self, dataset: List[ECICommissionResponseRecord], field_name: str
    ) -> float:
        """
        Calculate completeness rate for a field.

        Args:
            dataset: List of records
            field_name: Name of field to check

        Returns:
            Completeness rate (0.0 to 1.0)
        """
        if not dataset:
            return 0.0

        non_empty_count = 0

        for record in dataset:

            value = getattr(record, field_name, None)

            if not is_empty_value(value):
                non_empty_count += 1

        return non_empty_count / len(dataset)

    def test_mandatory_fields_completeness_rate(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify mandatory fields have 100% completeness rate.

        Mandatory fields are essential for every ECI response and must be
        present in all records. Missing mandatory fields indicate scraping
        failures or data quality issues.
        """
        incomplete_fields = {}

        for field_name in self.MANDATORY_FIELDS:
            completeness = self._calculate_completeness_rate(
                complete_dataset, field_name
            )

            if completeness < 1.0:
                # Find which records are missing this field
                missing_records = []
                for record in complete_dataset:
                    value = getattr(record, field_name, None)
                    if is_empty_value(value):
                        missing_records.append(record.registration_number)

                incomplete_fields[field_name] = {
                    "completeness": completeness,
                    "missing_count": len(missing_records),
                    "missing_records": missing_records[:5],  # Show first 5
                }

        assert not incomplete_fields, (
            f"Found {len(incomplete_fields)} mandatory fields with incomplete data:\n"
            + "\n".join(
                f"  - {field}: {data['completeness']:.1%} complete "
                f"({data['missing_count']} missing)\n"
                f"    Missing in: {', '.join(data['missing_records'])}"
                + (
                    f" and {data['missing_count'] - 5} more..."
                    if data["missing_count"] > 5
                    else ""
                )
                for field, data in incomplete_fields.items()
            )
            + "\n\nMandatory fields must be present in 100% of records."
        )

    def test_optional_fields_distribution(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Analyze and validate that there are at least some values in optional fields.
        Expected: 10% < completeness < 100%

        Optional fields should have some data (not completely empty) but may not
        be present in all records. Very low completeness (<10%) suggests the
        scraper isn't extracting these fields properly. 100% completeness might
        indicate the field should be reclassified as mandatory.
        """
        field_completeness = {}
        too_sparse_fields = {}
        unexpectedly_complete_fields = {}

        for field_name in self.OPTIONAL_FIELDS:

            completeness = self._calculate_completeness_rate(
                complete_dataset, field_name
            )
            field_completeness[field_name] = completeness

            # Flag fields with less than 10% completeness (possibly broken scraping)
            if 0 < completeness < 0.10:
                too_sparse_fields[field_name] = completeness

            # Flag fields with 100% completeness (possibly should be mandatory)
            if completeness == 1.0:
                unexpectedly_complete_fields[field_name] = completeness

        # Generate informational report
        print("\n" + "=" * 70)
        print("OPTIONAL FIELDS COMPLETENESS REPORT")
        print("=" * 70)

        # Group by completeness range
        high_completeness = {k: v for k, v in field_completeness.items() if v >= 0.7}
        medium_completeness = {
            k: v for k, v in field_completeness.items() if 0.3 <= v < 0.7
        }
        low_completeness = {
            k: v for k, v in field_completeness.items() if 0.1 <= v < 0.3
        }
        very_low_completeness = {
            k: v for k, v in field_completeness.items() if 0 < v < 0.1
        }
        empty_fields = {k: v for k, v in field_completeness.items() if v == 0}

        if high_completeness:
            print("\nHigh completeness (≥70%):")
            for field, rate in sorted(
                high_completeness.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"  - {field}: {rate:.1%}")

        if medium_completeness:
            print("\nMedium completeness (30-70%):")
            for field, rate in sorted(
                medium_completeness.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"  - {field}: {rate:.1%}")

        if low_completeness:
            print("\nLow completeness (10-30%):")
            for field, rate in sorted(
                low_completeness.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"  - {field}: {rate:.1%}")

        if very_low_completeness:
            print("\n⚠ Very low completeness (<10%) - possible scraping issues:")
            for field, rate in sorted(
                very_low_completeness.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"  - {field}: {rate:.1%}")

        if empty_fields:
            print("\n❌ Empty fields (0%) - no data extracted:")
            for field in sorted(empty_fields.keys()):
                print(f"  - {field}")

        print("=" * 70 + "\n")

        # Fail if fields are completely empty (0%)
        assert not empty_fields, (
            f"Found {len(empty_fields)} optional fields with 0% completeness:\n"
            + "\n".join(f"  - {field}" for field in sorted(empty_fields.keys()))
            + "\n\nOptional fields should have at least some data. "
            + "0% completeness suggests scraper is not extracting these fields."
        )

    def test_procedural_timeline_completeness(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify procedural milestone fields have expected completeness.

        The ECI process has standard procedural steps (submission, meeting,
        hearing, plenary, communication) that most initiatives go through.
        These fields should have high completeness rates. Low completeness
        suggests scraping issues or incomplete data.
        """
        completeness_issues = {}
        actual_completeness = {}

        for field_name, expected_rate in self.PROCEDURAL_FIELDS.items():

            actual_rate = self._calculate_completeness_rate(
                complete_dataset, field_name
            )
            actual_completeness[field_name] = actual_rate

            if actual_rate < expected_rate:
                missing_count = int(
                    (expected_rate - actual_rate) * len(complete_dataset)
                )
                completeness_issues[field_name] = {
                    "expected": expected_rate,
                    "actual": actual_rate,
                    "shortfall": expected_rate - actual_rate,
                    "missing_count": missing_count,
                }

        # Generate report
        print("\n" + "=" * 70)
        print("PROCEDURAL TIMELINE COMPLETENESS REPORT")
        print("=" * 70)
        print(f"\nTotal initiatives: {len(complete_dataset)}")
        print("\nProcedural milestone completeness:")

        for field_name, expected_rate in sorted(
            self.PROCEDURAL_FIELDS.items(), key=lambda x: x[1], reverse=True
        ):
            actual_rate = actual_completeness[field_name]
            status = "✓" if actual_rate >= (expected_rate - 0.10) else "⚠"
            print(
                f"  {status} {field_name}: {actual_rate:.1%} "
                f"(expected ≥{expected_rate:.1%})"
            )
        print("=" * 70 + "\n")

        # Fail if critical procedural fields are significantly incomplete
        assert not completeness_issues, (
            f"Found {len(completeness_issues)} procedural fields below expected completeness:\n"
            + "\n".join(
                f"  - {field}: {data['actual']:.1%} (expected ≥{data['expected']:.1%})\n"
                f"    Shortfall: {data['shortfall']:.1%} (~{data['missing_count']} records)"
                for field, data in completeness_issues.items()
            )
            + "\n\nProcedural milestone fields should have high completeness rates."
        )
