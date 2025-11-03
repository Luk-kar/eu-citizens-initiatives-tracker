"""Non-legislative action type definitions with classification keywords."""

from dataclasses import dataclass
from typing import List, Optional


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
