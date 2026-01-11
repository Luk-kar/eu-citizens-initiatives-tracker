"""Legislative action status definitions with patterns and keywords."""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional


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
            name: Status identifier (e.g., '"in_vacatio_legis"', 'adopted')
            priority: Priority level for matching (lower number = higher priority)
            keywords: List of (keyword, weight) tuples for date extraction context
            action_patterns: List of regex patterns to match this status in text
        """

        name: str
        priority: int
        keywords: List[Tuple[str, int]]
        action_patterns: List[Dict[str, str]]

    # Define all statuses as class attributes

    # Status for laws that are actually binding and enforceable
    LAW_ACTIVE = Status(
        name="law_active",
        priority=1,  # HIGHEST priority - most advanced stage
        keywords=[
            ("applies from", 3),
            ("apply from", 3),
            ("rules apply from", 3),
            ("became applicable", 3),
        ],
        action_patterns=[
            # Match actual applicability phrases
            r"(?<!will\s)(?:became applicable|applies from|apply from|rules apply from)",
        ],
    )

    # Vacatio legis: Law is active but binding obligations delayed (implementation window)
    IN_VACATIO_LEGIS = Status(
        name="in_vacatio_legis",
        priority=2,  # Lower priority than LAW_ACTIVE
        keywords=[
            ("entered into force", 2),
            ("came into force", 2),
        ],
        action_patterns=[
            # Match "entered/came into force" WITHOUT "became applicable/applies from" nearby
            r"(?<!will\s)(?:entered into force|came into force)(?!.*(?:became applicable|applies from|apply from))",
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
            # Verb before instrument: "withdrawn proposal for a regulation"
            r"(?:withdrawn|withdraw|withdrew)(?:(?!\bnot\b).)*?(?:proposal|regulation|directive|law|amendment|legislation)",
            # Instrument before verb: "proposal was withdrawn"
            r"(?:proposal|regulation|directive|law|amendment|legislation)(?:(?!\bnot\b).)*?(?:was |were )?(?:withdrawn|withdraw|withdrew)",
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
            # Instrument before verb: "directive was adopted"
            r"(?:regulation|directive|law|amendment|legislation)(?:(?!\bnot\b).)*?(?:was |were )?(?:adopted|approved)",
            # Verb before instrument with policy document exclusion AND "not" exclusion
            r"(?<!vision\s)(?<!strategy\s)(?<!communication\s)(?<!roadmap\s)(?<!plan\s)(?<!framework\s)(?<!programme\s)(?<!program\s)(?<!initiative\s)(?<!agenda\s)(?<!approach\s)(?<!guideline\s)(?<!guidelines\s)(?<!report\s)(?<!study\s)(?<!assessment\s)(?<!review\s)(?<!consultation\s)(?<!opinion\s)(?<!document\s)(?:adopted|approved)(?:(?!\bnot\b).)*?(?:regulation|directive|law|amendment|legislation)",
        ],
    )

    PROPOSED = Status(
        name="proposed",
        priority=4,
        keywords=[
            ("proposal", 1),
            ("proposed", 1),
            ("tabled", 1),
            ("plans for", 1),
            ("committed to", 1),
        ],
        action_patterns=[
            # Standard proposal patterns
            r"(?:revision|revised|recast|decided|proposal|proposed|tabled)(?:(?!\bnot\b).)*?(?:regulation|directive|law|amendment|legislation|legislative)",
            # Commitment/plan patterns
            r"(?:plans? for|committed? to|intends? to|will)(?:(?!\bnot\b).)*?(?:legislative proposal)",
            r"(?:plans? for|committed? to)(?:(?!\bnot\b).)*?(?:revision|review)(?:(?!\bnot\b).)*?(?:legislation|directive|regulation)",
            # Proposals on revision
            r"proposals? on(?:(?!\bnot\b).)*?(?:revision|review)(?:(?!\bnot\b).)*?(?:legislation|directive|regulation)",
        ],
    )

    PLANNED = Status(
        name="planned",
        priority=5,
        keywords=[
            ("will apply", 1),
            ("planned", 1),
            ("foresees", 1),
            ("intends", 1),
        ],
        action_patterns=[
            r"(?:will apply|planned|to be adopted|foresees).*?(?:from|by|in).*?\d{4}",
            r"(?:created|creation|new|adopted|establish).*?(?:tariff codes?|cn codes?|standards)",
        ],
    )

    # Lookup dictionaries for convenience
    BY_NAME: Dict[str, Status] = {
        "in_vacatio_legis": IN_VACATIO_LEGIS,
        "withdrawn": WITHDRAWN,
        "adopted": ADOPTED,
        "proposed": PROPOSED,
        "planned": PLANNED,
    }

    ALL_STATUSES: List[Status] = [
        LAW_ACTIVE,
        IN_VACATIO_LEGIS,
        WITHDRAWN,
        ADOPTED,
        PROPOSED,
        PLANNED,
    ]

    @classmethod
    def get_status(cls, name: str) -> Optional[Status]:
        """Get Status object by name."""
        return cls.BY_NAME.get(name)
