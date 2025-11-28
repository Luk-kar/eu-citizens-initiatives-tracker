"""Status classification and matching logic"""

from typing import Optional

from ...consts import ECIImplementationStatus


class LegislativeOutcomeClassifier:
    """Helper class for matching legislative status patterns in ECI response text"""

    # Pattern constants for status detection
    APPLICABLE_PATTERNS = [
        "became applicable",
        "became applicable immediately",
        "and applicable from",
    ]

    ADOPTION_EVIDENCE = [
        "council of the eu adopted",
        "council adopted the regulation",
        "published in the official journal",
        "following the agreement of the european parliament",
        "regulation adopted on",
        "directive adopted on",
        "was adopted by the commission",
        "implementing regulation adopted",
    ]

    COMMITMENT_PATTERNS = [
        "committed to come forward with a legislative proposal",
        "communicated its intention to table a legislative proposal",
        "intention to table a legislative proposal",
        "will table a legislative proposal",  # "will table" - UK\EU idiom phrase
        "committed to table a legislative proposal",
        "to table a legislative proposal",
        "sets out plans for a legislative proposal",
        "will present proposals",
        "commitment to phase out",
        "plans for a legislative proposal",
    ]

    REJECTION_PATTERNS = [
        "will not make a legislative proposal",
        "not propose new legislation",
        "decided not to submit a legislative proposal",
        "has decided not to submit a legislative proposal",
        "no further legal acts are proposed",
        "no new legislation will be proposed",
        "no legislative proposal",
        "neither scientific nor legal grounds",
        "already covered",
        "proposals fall outside",
        "outside of eu competence",
        "outside the eu competence",
        "not within eu competence",
        "beyond eu competence",
    ]

    # Special rejection pattern requiring two keywords
    NO_REPEAL_PATTERN = ("no repeal", "was proposed")

    EXISTING_FRAMEWORK_PATTERNS = [
        "existing funding framework",
        "existing legislation",
        "already covered",
        "already in place",
        "legislation and policies already in place",
        "recently debated and agreed",
        "is the appropriate one",
        "policies already in place",
    ]

    REJECTION_WITH_ACTIONS_INDICATORS = [
        "committed",
        "will continue",
        "monitor",
        "support",
    ]

    ASSESSMENT_INDICATORS = [
        "launch",
        "started working on",
        "external study to be carried out",
        "call for evidence",
        "preparatory work",
        "with a view to launch",
        "launched a review",
        "will communicate, by",
        "will communicate on",
    ]

    def __init__(self, content: str):
        """
        Initialize with normalized content string

        Args:
            content: Text content from ECI Commission response
        """

        self.content = content.lower()

    def check_applicable(self) -> bool:
        """
        Check if initiative reached applicable status (law is in force)

        Returns:
            True if law became applicable, False otherwise
        """

        # Direct applicable phrases
        if any(phrase in self.content for phrase in self.APPLICABLE_PATTERNS):
            return True

        # "Entered into force" with adoption evidence
        if "entered into force" in self.content:
            if any(phrase in self.content for phrase in self.ADOPTION_EVIDENCE):
                return True

        # "Applies from" with legislation context
        if "applies from" in self.content or "apply from" in self.content:
            if any(
                word in self.content for word in ["adopted", "regulation", "directive"]
            ):
                return True

        return False

    def check_adopted(self) -> bool:
        """
        Check if proposal was adopted but not yet applicable

        Returns:
            True if adopted but not yet in force, False otherwise
        """

        # First check if already applicable (higher status takes precedence)
        return any(pattern in self.content for pattern in self.ADOPTION_EVIDENCE)

        # Published in Official Journal (but not applicable yet)
        if (
            "published in the official journal" in self.content
            or "official journal of the eu" in self.content
        ):
            if (
                "became applicable" not in self.content
                and "applies from" not in self.content
            ):
                return True

        return False

    def check_committed(self) -> bool:
        """
        Check if Commission committed to legislative proposal

        Returns:
            True if commitment to legislation exists, False otherwise
        """

        # Standard commitment patterns
        if any(phrase in self.content for phrase in self.COMMITMENT_PATTERNS):
            return True

        # "To table a legislative proposal by [date]"
        if "to table a legislative proposal" in self.content and "by" in self.content:
            return True

        return False

    def check_assessment_pending(self) -> bool:
        """
        Check if initiative is in assessment phase

        Returns:
            True if assessment ongoing, False otherwise
        """

        # Avoid false positives with higher status
        if (
            "intention to table a legislative proposal" in self.content
            or "became applicable" in self.content
        ):
            return False

        # EFSA scientific opinion pending
        if (
            "tasked" in self.content
            and "efsa" in self.content
            and "scientific opinion" in self.content
        ):
            return True

        # Impact assessment ongoing
        if "impact assessment" in self.content:
            if any(phrase in self.content for phrase in self.ASSESSMENT_INDICATORS):
                return True

        # Future communication expected
        if "will communicate" in self.content and (
            "by" in self.content or "after" in self.content
        ):
            return True

        return False

    def check_roadmap_development(self) -> bool:
        """
        Check if roadmap is being developed

        Returns:
            True if roadmap in development, False otherwise
        """

        if "became applicable" in self.content:
            return False

        # Check for roadmap with various development verbs
        if "roadmap" not in self.content:
            return False

        # Roadmap action indicators
        roadmap_indicators = [
            "develop",  # "develop a roadmap"
            "work on",  # "work on a roadmap"
            "work together",  # "work together on a roadmap"
            "work with",  # "work with parties on a roadmap"
            "launched",  # "launched a roadmap"
            "started work",  # "started work on a roadmap"
            "will work",  # "will work on a roadmap"
            "working on",  # "working on a roadmap"
            "preparing",  # "preparing a roadmap"
            "towards",  # "roadmap towards" (specific pattern)
        ]

        return any(indicator in self.content for indicator in roadmap_indicators)

    def check_rejection_type(self) -> Optional[str]:
        """
        Determine rejection type if initiative was rejected

        Returns:
            'rejected', 'rejected_with_actions', 'rejected_already_covered', or None
        """

        has_primary_rejection = any(
            phrase in self.content for phrase in self.REJECTION_PATTERNS
        )
        has_no_repeal = all(
            keyword in self.content for keyword in self.NO_REPEAL_PATTERN
        )

        if not (has_primary_rejection or has_no_repeal):
            return None

        if has_no_repeal:
            if any(
                word in self.content for word in self.REJECTION_WITH_ACTIONS_INDICATORS
            ):
                return "rejected_with_actions"
            return "rejected"

        if any(phrase in self.content for phrase in self.EXISTING_FRAMEWORK_PATTERNS):
            return "rejected_already_covered"

        if any(word in self.content for word in self.REJECTION_WITH_ACTIONS_INDICATORS):
            return "rejected_with_actions"

        return "rejected"

    def check_non_legislative_action(self) -> bool:
        """
        Check if only non-legislative actions were taken

        Returns:
            True if only policy actions (no legislation), False otherwise
        """

        # Check for non-legislative focus
        has_non_legislative_focus = (
            "intends to focus on" in self.content or "implementation of" in self.content
        )

        if has_non_legislative_focus:
            # Check if there's an actual proposal (positive context)
            has_positive_proposal = any(
                phrase in self.content
                for phrase in [
                    "will propose",
                    "committed to propose",
                    "intention to table a legislative proposal",
                    "will table a legislative proposal",
                ]
            )

            # If no positive proposal context, it's non-legislative action
            if not has_positive_proposal:
                return True

        # Specific non-legislative action patterns
        action_patterns = [
            "committed, in particular, to taking the following actions",
            "launch an eu-wide public consultation",
            "improve transparency",
            "establish harmonised",
        ]

        if any(phrase in self.content for phrase in action_patterns):
            if (
                "legislative proposal" not in self.content
                and "proposal" not in self.content
            ):
                return True

        return False

    def check_proposal_pending(self) -> bool:
        """
        Check if existing proposals are pending adoption

        Returns:
            True if proposals under negotiation, False otherwise
        """

        has_tabled = "proposal" in self.content and "tabled" in self.content
        has_context = "rather than proposing new legislative acts" in self.content
        not_completed = (
            "became applicable" not in self.content
            and "entered into force" not in self.content
        )

        return has_tabled and has_context and not_completed

    def extract_technical_status(self) -> str:
        """
        Extract technical status code by checking all patterns in priority order

        Status hierarchy (highest to lowest priority):
        1. applicable (Law Active)
        2. adopted (Law Approved)
        3. committed (Law Promised)
        4. assessment_pending (Being Studied)
        5. roadmap_development (Action Plan Created)
        6. rejected_already_covered / rejected_with_actions / rejected
        7. non_legislative_action (Policy Changes Only)
        8. proposal_pending_adoption (Proposals Under Review)

        Returns:
            Technical status code (e.g., 'applicable', 'committed', etc.)

        Raises:
            ValueError: If no status pattern matches
        """

        # Define status checks in priority order (highest to lowest)
        status_checks = [
            (ECIImplementationStatus.APPLICABLE.legal_term, self.check_applicable),
            (ECIImplementationStatus.ADOPTED.legal_term, self.check_adopted),
            (ECIImplementationStatus.COMMITTED.legal_term, self.check_committed),
            (
                ECIImplementationStatus.ASSESSMENT_PENDING.legal_term,
                self.check_assessment_pending,
            ),
            (
                ECIImplementationStatus.ROADMAP_DEVELOPMENT.legal_term,
                self.check_roadmap_development,
            ),
            (None, self.check_rejection_type),  # Returns status name directly
            (
                ECIImplementationStatus.NON_LEGISLATIVE_ACTION.legal_term,
                self.check_non_legislative_action,
            ),
            (
                ECIImplementationStatus.PROPOSAL_PENDING_ADOPTION.legal_term,
                self.check_proposal_pending,
            ),
        ]

        # Check each status in priority order
        for status_name, check_func in status_checks:
            result = check_func()

            # Handle rejection check (returns status name or None)
            if status_name is None and result:
                return result

            # Handle boolean checks
            if status_name and result:
                return status_name

        # No status matched
        raise ValueError("No known status patterns matched")

    def translate_to_citizen_friendly(self, technical_status: str) -> str:
        """
        Translate technical status to citizen-friendly name

        Args:
            technical_status: Technical status code (e.g., 'applicable')

        Returns:
            Citizen-friendly status name (e.g., 'Law Active')
        """
        status = ECIImplementationStatus.get_status_by_term(technical_status)

        if status:
            return status.human_readable_explanation

        return technical_status
