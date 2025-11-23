"""
Test suite for ECI model data quality: Outcome status consistency and alignment.

These tests validate outcome status consistency and alignment in extracted
European Citizens' Initiative response data.
"""

from typing import List, Optional

import pytest

from ECI_initiatives.extractor.responses.model import ECICommissionResponseRecord
from ECI_initiatives.extractor.responses.parser.consts.eci_status import (
    ECIImplementationStatus,
)


class TestOutcomeStatusConsistency:
    """Test data quality of outcome-related fields"""

    # Get all valid human-readable statuses from ECIImplementationStatus
    VALID_OUTCOME_STATUSES = {
        status.human_readable_explanation
        for status in ECIImplementationStatus.BY_LEGAL_TERM.values()
    } | {
        None
    }  # Add None for initiatives without concluded status

    def test_final_outcome_status_has_valid_values(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify final_outcome_status uses predefined status categories"""

        invalid_statuses = set()

        for record in complete_dataset:
            if (
                record.final_outcome_status is not None
                and record.final_outcome_status not in self.VALID_OUTCOME_STATUSES
            ):
                invalid_statuses.add(
                    (record.registration_number, record.final_outcome_status)
                )

        assert not invalid_statuses, (
            "Found records with invalid final_outcome_status:\n"
            + "\n".join(
                f"  - {reg_num}: '{status}'"
                for reg_num, status in sorted(invalid_statuses)
            )
            + "\n\nValid statuses from ECIImplementationStatus:\n"
            + "\n".join(
                f"  - {status}"
                for status in sorted([s for s in self.VALID_OUTCOME_STATUSES if s])
            )
        )

    def test_law_active_status_has_implementation_date(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify records with 'Law Active' status have law_implementation_date"""

        missing_dates = []

        for record in complete_dataset:

            # Use the human-readable status from ECIImplementationStatus.APPLICABLE
            if (
                record.final_outcome_status
                == ECIImplementationStatus.APPLICABLE.human_readable_explanation
            ):
                if record.law_implementation_date is None:
                    missing_dates.append(
                        (record.registration_number, record.initiative_title)
                    )

        assert not missing_dates, (
            f"Found {len(missing_dates)} records with "
            f"'{ECIImplementationStatus.APPLICABLE.human_readable_explanation}' status "
            f"but missing law_implementation_date:\n"
            + "\n".join(
                f"  - {reg_num}: {title[:80]}..." for reg_num, title in missing_dates
            )
        )

    def test_rejected_status_has_rejection_reason(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify rejected initiatives have commission_rejection_reason"""
        missing_reasons = []

        # Get all rejection-related statuses from ECIImplementationStatus
        rejection_statuses = {
            ECIImplementationStatus.REJECTED.human_readable_explanation,
            ECIImplementationStatus.REJECTED_ALREADY_COVERED.human_readable_explanation,
            ECIImplementationStatus.REJECTED_WITH_ACTIONS.human_readable_explanation,
        }

        for record in complete_dataset:
            # If initiative has a rejection status or rejection flag
            if (
                record.final_outcome_status in rejection_statuses
                or self._normalize_boolean(record.commission_rejected_initiative)
                is True
            ):
                if not record.commission_rejection_reason:
                    missing_reasons.append(
                        (record.registration_number, record.initiative_title)
                    )

        assert not missing_reasons, (
            f"Found {len(missing_reasons)} rejected initiatives "
            f"without commission_rejection_reason:\n"
            + "\n".join(
                f"  - {reg_num}: {title[:80]}..." for reg_num, title in missing_reasons
            )
        )

    def test_promised_law_aligns_with_outcome(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify that the Commission's promise regarding new legislation aligns with
        the actual outcome status of the initiative.

        This test ensures logical consistency between what the Commission explicitly
        stated about creating new legislation (commission_promised_new_law field) and
        the final outcome that materialized (final_outcome_status field).

        The test validates two key alignment scenarios:

        1. If the Commission promised to create NEW legislation for an initiative,
        the outcome should reflect a law-related status (e.g., Law Promised,
        Law Active, Proposals Under Review). It would be inconsistent for the
        Commission to promise legislation but then have a non-legislative outcome.

        2. If the Commission did NOT promise new legislation, the outcome can still
        be "Law Active" or "Law Approved" because the initiative's goals may
        already be covered by existing or pending EU legislation. This is a valid
        Commission response where no new law is needed because adequate laws
        already exist. However, it would be contradictory if the Commission said
        "no new law needed" but then the outcome shows "Law Promised" (indicating
        a new commitment was made).

        This validation catches data quality issues where:
        - Scraped data is inconsistent between different sections of the response
        - The promise flag was incorrectly extracted
        - The outcome status was misclassified
        """
        misalignments = []

        # Define law-related statuses using ECIImplementationStatus
        law_related_statuses = {
            ECIImplementationStatus.APPLICABLE.human_readable_explanation,  # Law Active
            ECIImplementationStatus.ADOPTED.human_readable_explanation,  # Law Approved
            ECIImplementationStatus.COMMITTED.human_readable_explanation,  # Law Promised
            ECIImplementationStatus.PROPOSAL_PENDING_ADOPTION.human_readable_explanation,  # Proposals Under Review
        }

        # Define rejection statuses - outcomes where Commission declined the initiative
        # These represent different ways the Commission can say "no" to citizen requests:
        rejection_statuses = {
            # Plain rejection - no action taken
            ECIImplementationStatus.REJECTED.human_readable_explanation,
            # Rejected - existing EU law already addresses the issue
            ECIImplementationStatus.REJECTED_ALREADY_COVERED.human_readable_explanation,
            # Rejected - but Commission proposed alternative policy actions instead
            ECIImplementationStatus.REJECTED_WITH_ACTIONS.human_readable_explanation,
        }

        # Statuses that indicate the initiative's goals are met by existing/pending legislation
        # (Commission doesn't need to promise NEW law, but laws exist that address the issue)
        # already_covered_statuses = {
        #     ECIImplementationStatus.APPLICABLE.human_readable_explanation,  # Law Active (existing law)
        #     ECIImplementationStatus.ADOPTED.human_readable_explanation,  # Law Approved (pending law)
        #     ECIImplementationStatus.REJECTED_ALREADY_COVERED.human_readable_explanation,  # Explicitly already covered
        # }

        for record in complete_dataset:

            # Normalize boolean flag
            promised_law = self._normalize_boolean(record.commission_promised_new_law)

            # Skip if promise status is unknown
            if promised_law is None:
                # commission_promised_new_law must be a boolean (True/False), not None
                # This field is mandatory for data quality validation
                pytest.fail(
                    f"commission_promised_new_law is None for {record.registration_number} "
                    f"(Initiative: {record.initiative_title[:80]}...)\n"
                    f"This field must be a boolean value (True or False) to validate promise-outcome alignment.\n"
                    f"Possible causes:\n"
                    f"  - Field was not extracted during scraping\n"
                    f"  - CSV contains empty/null value\n"
                    f"  - Data type conversion issue (string 'null' instead of proper None)\n"
                    f"Expected: True (Commission promised new law) or False (no new law promised)"
                )

            # If Commission promised a new law
            if promised_law is True:

                # Outcome should reflect law-related status (not rejection)
                if (
                    record.final_outcome_status not in law_related_statuses
                    and record.final_outcome_status is not None
                    and record.final_outcome_status not in rejection_statuses
                ):

                    # Allow non-legislative actions as they may still fulfill promises
                    if (
                        record.final_outcome_status
                        != ECIImplementationStatus.NON_LEGISLATIVE_ACTION.human_readable_explanation
                    ):
                        misalignments.append(
                            (
                                record.registration_number,
                                "Promised law",
                                record.final_outcome_status or "No outcome",
                            )
                        )

            # If Commission explicitly rejected or didn't promise NEW law
            elif promised_law is False:
                # It's VALID for Commission to say "no new law needed" when:
                # 1. Issue already covered by existing law (Law Active)
                # 2. Issue already covered by pending law (Law Approved)
                # 3. Explicitly marked as "Rejected - Already Covered"
                #
                # Only flag as misalignment if Commission promised NO law,
                # but then a law was specifically PROMISED or COMMITTED for this initiative
                if (
                    record.final_outcome_status
                    == ECIImplementationStatus.COMMITTED.human_readable_explanation
                ):
                    # This is contradictory: Commission said "no new law"
                    # but status shows "Law Promised" (new commitment made)
                    misalignments.append(
                        (
                            record.registration_number,
                            "No law promised (commission_promised_new_law=False)",
                            f"but outcome is '{ECIImplementationStatus.COMMITTED.human_readable_explanation}'",
                        )
                    )

        assert not misalignments, (
            f"Found {len(misalignments)} records where commission_promised_new_law "
            f"doesn't align with final_outcome_status:\n"
            + "\n".join(
                f"  - {reg_num}: {promise} {outcome}"
                for reg_num, promise, outcome in misalignments
            )
        )

    def test_rejected_initiatives_have_rejection_flag_set(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify commission_rejected_initiative=True when rejection reason exists"""
        inconsistent_rejections = []

        for record in complete_dataset:
            # Normalize flag value (handle both bool and string "True"/"False")
            flag_value = self._normalize_boolean(record.commission_rejected_initiative)

            # If rejection reason exists, flag should be True
            if record.commission_rejection_reason:
                if flag_value is not True:
                    inconsistent_rejections.append(
                        (
                            record.registration_number,
                            record.commission_rejected_initiative,  # Show actual value
                            record.commission_rejection_reason[:100],
                        )
                    )

            # If flag is True, reason should exist
            if flag_value is True:
                if not record.commission_rejection_reason:
                    inconsistent_rejections.append(
                        (
                            record.registration_number,
                            record.commission_rejected_initiative,  # Show actual value
                            "No rejection reason provided",
                        )
                    )

        assert not inconsistent_rejections, (
            f"Found {len(inconsistent_rejections)} records with inconsistent "
            f"rejection flag and reason:\n"
            + "\n".join(
                f"  - {reg_num}: flag={flag!r}, reason='{reason}'"
                for reg_num, flag, reason in inconsistent_rejections
            )
        )

    def test_outcome_status_consistency_with_actions(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify that final_outcome_status is consistent with presence of
        laws_actions and policies_actions.
        """
        inconsistencies = []

        for record in complete_dataset:
            # If status is "Law Active", should have laws_actions
            if (
                record.final_outcome_status
                == ECIImplementationStatus.APPLICABLE.human_readable_explanation
            ):
                if not record.laws_actions or record.laws_actions == "null":
                    inconsistencies.append(
                        (
                            record.registration_number,
                            f"{ECIImplementationStatus.APPLICABLE.human_readable_explanation} but no laws_actions",
                        )
                    )

            # If status is "Policy Changes Only", should have policies_actions
            if (
                record.final_outcome_status
                == ECIImplementationStatus.NON_LEGISLATIVE_ACTION.human_readable_explanation
            ):
                if not record.policies_actions or record.policies_actions == "null":
                    inconsistencies.append(
                        (
                            record.registration_number,
                            f"{ECIImplementationStatus.NON_LEGISLATIVE_ACTION.human_readable_explanation} but no policies_actions",
                        )
                    )

            # If status is rejected, shouldn't have active laws
            rejection_statuses = {
                ECIImplementationStatus.REJECTED.human_readable_explanation,
                ECIImplementationStatus.REJECTED_ALREADY_COVERED.human_readable_explanation,
                ECIImplementationStatus.REJECTED_WITH_ACTIONS.human_readable_explanation,
            }
            if record.final_outcome_status in rejection_statuses:
                if record.law_implementation_date is not None:
                    inconsistencies.append(
                        (
                            record.registration_number,
                            "Rejected but has law_implementation_date",
                        )
                    )

        assert not inconsistencies, (
            f"Found {len(inconsistencies)} records with outcome status inconsistencies:\n"
            + "\n".join(f"  - {reg_num}: {issue}" for reg_num, issue in inconsistencies)
        )

    def _normalize_boolean(self, value: any) -> Optional[bool]:
        """
        Normalize boolean-like values to actual booleans.

        Handles cases where CSV/pandas may have converted booleans to strings.

        Args:
            value: Value to normalize (bool, str, None)

        Returns:
            True, False, or None
        """
        if value is None:
            return None

        if isinstance(value, bool):
            return value

        # Handle string representations
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ("true", "1", "yes"):
                return True
            elif value_lower in ("false", "0", "no", ""):
                return False

        # Handle numeric (pandas may convert to 1/0)
        if isinstance(value, (int, float)):
            return bool(value)

        return None
