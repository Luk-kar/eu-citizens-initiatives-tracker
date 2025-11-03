"""Legislative outcome status definitions, hierarchies, and keyword patterns for ECI response classification."""

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

    class Status:
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


# Status priority for matching (higher number = higher priority)
STATUS_PRIORITY = {
    "in_force": 5,
    "withdrawn": 4,
    "adopted": 3,
    "proposed": 2,
    "planned": 1,
}

# Status-specific keywords with priority for date extraction
STATUS_KEYWORDS = {
    "in_force": [
        ("apply from", 3),  # Highest priority for in_force
        ("applies from", 3),
        ("rules apply from", 3),
        ("entered into force", 2),
        ("came into force", 2),
        ("became applicable", 2),
    ],
    "adopted": [
        ("adopted", 1),
        ("approved", 1),
    ],
    "proposed": [
        ("proposal", 1),
        ("proposed", 1),
        ("tabled", 1),
    ],
    "withdrawn": [
        ("withdrawn", 1),
        ("withdraw", 1),
    ],
    "planned": [
        ("will apply", 1),
        ("planned", 1),
        ("foresees", 1),
    ],
}

# NOTE Legislative action patterns for classification
LEGISLATIVE_ACTION_PATTERNS = [
    {
        "pattern": r"(?:proposal|proposed|tabled).*?(?:regulation|directive|law|amendment)",
        "type_hint": "proposal",
        "status": "proposed",
    },
    {
        "pattern": r"(?:adopted|approved).*?(?:regulation|directive|law|amendment)",
        "type_hint": "adoption",
        "status": "adopted",
    },
    {
        "pattern": r"(?:entered into force|became applicable|applies from|came into force|apply from)",
        "type_hint": "in_force",
        "status": "in_force",
    },
    {
        "pattern": r"(?:revision|revised|recast).*?(?:directive|regulation)",
        "type_hint": "revision",
        "status": "proposed",
    },
    {
        "pattern": r"(?:withdrawn|withdraw|withdrew)",
        "type_hint": "withdrawal",
        "status": "withdrawn",
    },
    {
        "pattern": r"(?:will apply|planned|to be adopted|foresees).*?(?:from|by|in).*?\d{4}",
        "type_hint": "planned",
        "status": "planned",
    },
    {
        "pattern": r"(?:created|creation|new|adopted|establish).*?(?:tariff codes?|cn codes?|standards)",
        "type_hint": "creation",
        "status": "planned",
    },
]


# NOTE Non-legislative action patterns with types
NON_LEGISLATIVE_ACTION_PATTERNS = [
    {
        "keywords": [
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
        "type": "Monitoring and Enforcement",
    },
    {
        "keywords": [
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
        "type": "Policy Implementation",
    },
    {
        "keywords": [
            "scientific conference",
            "scientific opinion",
            "efsa",
            "workshop",
            "colloquium",
        ],
        "type": "Scientific Activity",
    },
    {
        "keywords": [
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
        "type": "Funding Programme",
    },
    {
        "keywords": [
            "impact assessment",
            "public consultation",
            "call for evidence",
            "consultation on",
        ],
        "type": "Impact Assessment and Consultation",
    },
    {
        "keywords": [
            "stakeholder",
            "partnership",
            "stakeholder dialogue",
        ],
        "type": "Stakeholder Dialogue",
    },
    {
        "keywords": [
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
        "type": "International Cooperation",
    },
    {
        "keywords": [
            "data collection",
            "transparency",
            "benchmarking",
            "eurobarometer",
            "report was published",
            "publication",
        ],
        "type": "Data Collection and Transparency",
    },
    {
        "keywords": [
            "roadmap",
            "strategic plan",
            "strengthened",
            "modernised",
            "enhanced",
            "policy framework",
            "mechanism",
            "mechanisms in place",
        ],
        "type": "Policy Roadmap and Strategy",
    },
]

# NOTE Words that indicate non-legislative content to skip during extraction
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

# NOTE Deadline extraction patterns for Commission commitments
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
