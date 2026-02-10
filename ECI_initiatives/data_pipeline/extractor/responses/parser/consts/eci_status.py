"""ECI commission response implementation status definitions."""


class ECIImplementationStatus:
    """
    Defines all possible ECI commission response
    implementation statuses with:
    - technical legal terms
    - human readable outcome
    - priority hierarchy
    """

    class Status:
        """
        Initialize a Status object.

        Args:
            legal_term: Technical status code (e.g., 'applicable', 'adopted')
            human_readable_explanation: Citizen-friendly status name (e.g., 'Law Active', 'Law Approved')
            priority: Priority level for status matching (lower number = higher priority)
        """

        def __init__(
            self, legal_term: str, human_readable_explanation: str, priority: int
        ):
            self.legal_term = legal_term
            self.human_readable_explanation = human_readable_explanation
            self.priority = priority

    # Define all statuses as class attributes (VSCode will autocomplete these)
    APPLICABLE = Status("applicable", "Law Active", priority=1)
    ADOPTED = Status("adopted", "Law Approved", priority=2)
    COMMITTED = Status("committed", "Law Promised", priority=3)
    ASSESSMENT_PENDING = Status("assessment_pending", "Being Studied", priority=4)
    ROADMAP_DEVELOPMENT = Status(
        "roadmap_development", "Action Plan Created", priority=5
    )
    REJECTED_ALREADY_COVERED = Status(
        "rejected_already_covered", "Rejected - Already Covered", priority=6
    )
    REJECTED_WITH_ACTIONS = Status(
        "rejected_with_actions", "Rejected - Alternative Actions", priority=7
    )
    REJECTED = Status("rejected", "Rejected", priority=8)
    NON_LEGISLATIVE_ACTION = Status(
        "non_legislative_action", "Policy Changes Only", priority=9
    )
    PROPOSAL_PENDING_ADOPTION = Status(
        "proposal_pending_adoption", "Proposals Under Review", priority=10
    )

    # Lookup dictionaries for convenience
    BY_LEGAL_TERM = {
        "applicable": APPLICABLE,
        "adopted": ADOPTED,
        "committed": COMMITTED,
        "assessment_pending": ASSESSMENT_PENDING,
        "roadmap_development": ROADMAP_DEVELOPMENT,
        "rejected_already_covered": REJECTED_ALREADY_COVERED,
        "rejected_with_actions": REJECTED_WITH_ACTIONS,
        "rejected": REJECTED,
        "non_legislative_action": NON_LEGISLATIVE_ACTION,
        "proposal_pending_adoption": PROPOSAL_PENDING_ADOPTION,
    }

    @classmethod
    def get_status_by_term(cls, legal_term: str) -> Status:
        """Get Status object by legal term string."""
        return cls.BY_LEGAL_TERM.get(legal_term)
