"""
Legislative outcome status
definitions, hierarchies, and
keyword patterns for ECI response classification.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

# Keywords that indicate rejection reasoning
REJECTION_REASONING_KEYWORDS = [
    "will not make",
    "will not propose",
    "decided not to",
    "no legislative proposal",
    "neither scientific nor legal grounds",
    "existing legislation",
    "existing funding framework",
    "already covered",
    "no repeal",
    "differs from",
    "not to submit",
    "fall outside",
    "outside of eu competence",
    "outside the eu competence",
    "not within eu competence",
    "beyond eu competence",
    "interfere with",
]


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


class LegislativeStatus:
    """
    Defines legislative action statuses with
    keywords, patterns, and priority hierarchy for classification.
    """

    @dataclass
    class Status:
        """
        Represents a legislative status with associated metadata.

        Attributes:
            name: Status identifier (e.g., 'in_force', 'adopted')
            priority: Priority level for matching (lower number = higher priority)
            keywords: List of (keyword, weight) tuples for date extraction context
            action_patterns: List of regex patterns to match this status in text
        """

        name: str
        priority: int
        keywords: List[Tuple[str, int]]
        action_patterns: List[Dict[str, str]]

    # Define all statuses as class attributes
    IN_FORCE = Status(
        name="in_force",
        priority=1,
        keywords=[
            ("apply from", 3),
            ("applies from", 3),
            ("rules apply from", 3),
            ("entered into force", 2),
            ("came into force", 2),
            ("became applicable", 2),
        ],
        action_patterns=[
            r"(?:entered into force|became applicable|applies from|came into force|apply from)",
        ],
    )

    WITHDRAWN = Status(
        name="withdrawn",
        priority=2,
        keywords=[
            ("withdrawn", 1),
            ("withdraw", 1),
        ],
        action_patterns=[
            r"(?:withdrawn|withdraw|withdrew)",
        ],
    )

    ADOPTED = Status(
        name="adopted",
        priority=3,
        keywords=[
            ("adopted", 1),
            ("approved", 1),
        ],
        action_patterns=[
            r"(?:adopted|approved).*?(?:regulation|directive|law|amendment)",
        ],
    )

    PROPOSED = Status(
        name="proposed",
        priority=4,
        keywords=[
            ("proposal", 1),
            ("proposed", 1),
            ("tabled", 1),
        ],
        action_patterns=[
            r"(?:proposal|proposed|tabled).*?(?:regulation|directive|law|amendment)",
            r"(?:revision|revised|recast).*?(?:directive|regulation)",
        ],
    )

    PLANNED = Status(
        name="planned",
        priority=5,
        keywords=[
            ("will apply", 1),
            ("planned", 1),
            ("foresees", 1),
        ],
        action_patterns=[
            r"(?:will apply|planned|to be adopted|foresees).*?(?:from|by|in).*?\d{4}",
            r"(?:created|creation|new|adopted|establish).*?(?:tariff codes?|cn codes?|standards)",
        ],
    )

    # Lookup dictionaries for convenience
    BY_NAME: Dict[str, Status] = {
        "in_force": IN_FORCE,
        "withdrawn": WITHDRAWN,
        "adopted": ADOPTED,
        "proposed": PROPOSED,
        "planned": PLANNED,
    }

    ALL_STATUSES: List[Status] = [IN_FORCE, WITHDRAWN, ADOPTED, PROPOSED, PLANNED]

    @classmethod
    def get_status(cls, name: str) -> Optional[Status]:
        """Get Status object by name."""
        return cls.BY_NAME.get(name)


class NonLegislativeAction:
    """Defines non-legislative action types with keywords for classification and filtering."""

    @dataclass
    class ActionType:
        """
        Represents a non-legislative action type with associated metadata.

        Attributes:
            name: Human-readable action type name (e.g., 'Monitoring and Enforcement', 'Funding Programme')
            keywords: List of keywords used to classify text as this action type
        """

        name: str
        keywords: List[str]

    # Define all non-legislative action types as class attributes
    MONITORING_ENFORCEMENT = ActionType(
        name="Monitoring and Enforcement",
        keywords=[
            "monitoring",
            "monitor",
            "active monitoring",
            "will monitor",
            "better enforce",
            "strengthen enforcement",
            "enforcement",
            "ensure compliance",
            "ensuring compliance",
            "compliance",
            "support member states",
            "guarantee equal treatment",
            "withhold payments",
            "conditional funding",
            "withhold the corresponding payments",
        ],
    )

    POLICY_IMPLEMENTATION = ActionType(
        name="Policy Implementation",
        keywords=[
            "will continue",
            "continue to",
            "ensure",
            "ensuring",
            "guarantee",
            "maintain",
            "maintaining",
            "non-discriminatory access",
            "equal access",
            "implementation",
            "implementing",
            "safeguard",
            "set of benchmarks",
        ],
    )

    SCIENTIFIC_ACTIVITY = ActionType(
        name="Scientific Activity",
        keywords=[
            "scientific conference",
            "scientific opinion",
            "efsa",
            "workshop",
            "colloquium",
        ],
    )

    FUNDING_PROGRAMME = ActionType(
        name="Funding Programme",
        keywords=[
            "funding",
            "horizon europe",
            "erasmus",
            "creative europe",
            "cohesion policy",
            "cohesion funding",
            "union funding",
            "multiannual financial framework",
            "mff",
        ],
    )

    IMPACT_ASSESSMENT_CONSULTATION = ActionType(
        name="Impact Assessment and Consultation",
        keywords=[
            "impact assessment",
            "public consultation",
            "call for evidence",
            "consultation on",
        ],
    )

    STAKEHOLDER_DIALOGUE = ActionType(
        name="Stakeholder Dialogue",
        keywords=[
            "stakeholder",
            "partnership",
            "stakeholder dialogue",
        ],
    )

    INTERNATIONAL_COOPERATION = ActionType(
        name="International Cooperation",
        keywords=[
            "international cooperation",
            "reaching out",
            "international partners",
            "international level",
            "international fora",
            "international commission",
            "un general assembly",
            "ICCAT",
            "best practices between Member States",
            "Sustainable Development Goals EU",
            "EU-wide public consultation",
            "advocating universal access",
        ],
    )

    DATA_COLLECTION_TRANSPARENCY = ActionType(
        name="Data Collection and Transparency",
        keywords=[
            "data collection",
            "transparency",
            "benchmarking",
            "eurobarometer",
            "report was published",
            "publication",
        ],
    )

    POLICY_ROADMAP_STRATEGY = ActionType(
        name="Policy Roadmap and Strategy",
        keywords=[
            "roadmap",
            "strategic plan",
            "strengthened",
            "modernised",
            "enhanced",
            "policy framework",
            "mechanism",
            "mechanisms in place",
        ],
    )

    # All action types for iteration
    ALL_ACTION_TYPES: List[ActionType] = [
        MONITORING_ENFORCEMENT,
        POLICY_IMPLEMENTATION,
        SCIENTIFIC_ACTIVITY,
        FUNDING_PROGRAMME,
        IMPACT_ASSESSMENT_CONSULTATION,
        STAKEHOLDER_DIALOGUE,
        INTERNATIONAL_COOPERATION,
        DATA_COLLECTION_TRANSPARENCY,
        POLICY_ROADMAP_STRATEGY,
    ]

    # Keywords that indicate non-legislative content to skip during legislative action extraction
    SKIP_WORDS_LEGISLATIVE = [
        "roadmap",
        "tasked",
        "will communicate",
        "will report",
        "impact assessment",
        "stakeholder",
        "consultation",
        "workshop",
        "meeting",
        "better enforcement",
        "in parallel to the legislation",
        "seek specific supporting measures",
    ]

    @classmethod
    def classify_text(cls, text: str) -> Optional[ActionType]:
        """
        Classify text by matching keywords to action types.

        Args:
            text: Text to classify (should be lowercased)

        Returns:
            ActionType if match found, None otherwise
        """
        text_lower = text.lower()

        for action_type in cls.ALL_ACTION_TYPES:
            if any(keyword in text_lower for keyword in action_type.keywords):
                return action_type

        return None

    @classmethod
    def should_skip_for_legislative(cls, text: str) -> bool:
        """
        Check if text should be skipped during legislative action extraction.

        Args:
            text: Text to check (should be lowercased)

        Returns:
            True if text contains skip keywords, False otherwise
        """
        text_lower = text.lower()
        return any(word in text_lower for word in cls.SKIP_WORDS_LEGISLATIVE)

    @classmethod
    def get_all_keywords(cls) -> List[str]:
        """
        Get all keywords from all action types.

        Returns:
            Flat list of all keywords
        """
        keywords = []
        for action_type in cls.ALL_ACTION_TYPES:
            keywords.extend(action_type.keywords)
        return keywords


# Words that indicate non-legislative content to skip during extraction
SKIP_WORDS_LEGISLATIVE = [
    "roadmap",
    "tasked",
    "will communicate",
    "will report",
    "impact assessment",
    "stakeholder",
    "consultation",
    "workshop",
    "meeting",
    "better enforcement",
    "in parallel to the legislation",
    "seek specific supporting measures",
]

# Deadline extraction patterns for Commission commitments
DEADLINE_PATTERNS = [
    # Legislative proposal patterns (action BEFORE deadline)
    r"committed to come forward with a legislative proposal[,\s]+by\s+([^.,;]+)",
    r"intention to table a legislative proposal[,\s]+by\s+([^.,;]+)",
    r"communicated its intention to table a legislative proposal[,\s]+by\s+([^.,;]+)",
    r"to table a legislative proposal[,\s]+by\s+([^.,;]+)",
    r"will table a legislative proposal[,\s]+by\s+([^.,;]+)",
    r"to propose legislation[,\s]+by\s+([^.,;]+)",
    # Communication patterns (action BEFORE deadline)
    r"will (?:then )?communicate[,\s]+by\s+([^.,;]+)",
    r"committed to communicate[,\s]+by\s+([^.,;]+)",
    r"will then communicate[,\s]+by\s+([^.,;]+)",
    # Assessment and study patterns (action BEFORE deadline)
    r"launch.*?(?:impact )?assessment[,\s]+by\s+([^.,;]+)",
    r"conduct.*?study[,\s]+by\s+([^.,;]+)",
    r"carry out.*?(?:assessment|study)[,\s]+by\s+([^.,;]+)",
    r"scientific opinion[,\s]+by\s+([^.,;]+)",
    r"efsa.*?(?:to )?provide.*?(?:opinion|assessment)[,\s]+by\s+([^.,;]+)",
    r"complete.*?(?:assessment|study|evaluation)[,\s]+by\s+([^.,;]+)",
    r"external study to be carried out.*?by\s+([^.,;]+)",
    # Roadmap patterns (action BEFORE deadline)
    r"roadmap.*?(?:is planned|planned|completed?)[,\s]+by\s+([^.,;]+)",
    r"finalisation.*?roadmap.*?by\s+([^.,;]+)",
    r"work on.*?roadmap.*?by\s+([^.,;]+)",
    # Report and update patterns (action BEFORE deadline)
    r"provide.*?report[,\s]+by\s+([^.,;]+)",
    r"provide.*?(?:update|information|data|details)[,\s]+by\s+([^.,;]+)",
    r"will report[,\s]+by\s+([^.,;]+)",
    r"(?:produce|publish).*?report[,\s]+by\s+([^.,;]+)",
    r"report.*?to be produced.*?(?:by|in)\s+([^.,;]+)",
    r"to\s+be\s+produced\s+in\s+([^.,;]+)",
    # Other commitment patterns (action BEFORE deadline)
    r"preparatory work.*?(?:with a view to )?launch.*?by\s+([^.,;]+)",
    r"call for evidence.*?by\s+([^.,;]+)",
    # DEADLINE-FIRST patterns (deadline BEFORE action)
    r"by\s+([^.,;]+),\s+provide.*?(?:information|data|details)",
    r"by\s+([^.,;]+),\s+the\s+commission\s+will\s+(?:communicate|report|provide)",
    r"by\s+([^.,;]+),\s+(?:to\s+)?(?:phase\s+out|ban|prohibit|implement)",
]

# NOTE Applicable date patterns for law implementation
APPLICABLE_DATE_PATTERNS = [
    r"became applicable.*?on\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",  # became applicable 18 months later, i.e. on 27 March 2021
    r"became applicable immediately",  # became applicable immediately
    r"applicable from\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",  # applicable from 27 March 2021
    r"and applicable from\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",  # and applicable from 27 March 2021
    r"applies from\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",  # applies from 27 March 2021
    r"apply from\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",  # apply from 27 March 2021
]
