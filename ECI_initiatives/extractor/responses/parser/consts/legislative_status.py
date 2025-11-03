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
