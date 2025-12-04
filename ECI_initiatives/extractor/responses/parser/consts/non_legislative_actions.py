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
    IMPACT_ASSESSMENT_CONSULTATION = ActionType(
        name="Impact Assessment and Consultation",
        keywords=[
            "impact assessment",
            "public consultation",
            "call for evidence",
            "consultation on",
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

    POLICY_ROADMAP_STRATEGY = ActionType(
        name="Policy Roadmap and Strategy",
        keywords=[
            "roadmap",
            "strategic plan",
            "strengthened",
            "modernised",
            "enhanced",
            "policy framework",
            "long-term strategy",
            "mechanisms in place",
            "vision for",
            "strategic agenda",
            "policy priorities",
            "milestones",
            "action plan",
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

    STAKEHOLDER_DIALOGUE = ActionType(
        name="Stakeholder Dialogue",
        keywords=[
            "stakeholder",
            "stakeholder partnership",
            "stakeholder dialogue",
            "partnership with stakeholders",
        ],
    )

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

    FUNDING_PROGRAMME = ActionType(
        name="Funding Programme",
        keywords=[
            "funding",
            "financial support",
            "financial incentives",
            "subsidies",
            "horizon europe",
            "erasmus",
            "creative europe",
            "cohesion policy",
            "cohesion funding",
            "union funding",
            "multiannual financial framework",
            "mff",
            "research and innovation",
            "research projects",
            "pilot project",
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

    # All action types for iteration
    # Ordered by "Legislative Pipeline Approach" - from highest to lowest proximity to legislative proposal
    # This ordering reflects formal EU Better Regulation requirements and ECI success patterns
    ALL_ACTION_TYPES: List[ActionType] = [
        #
        # TIER 1: Pre-legislative requirements (mandatory before Commission can propose legislation)
        IMPACT_ASSESSMENT_CONSULTATION,
        # Mandatory for all significant legislative proposals
        # Requires 12-week public consultation; positive (Regulatory Scrutiny Board) opinion needed
        # before interservice consultation can proceed
        # Strongest signal Commission is seriously exploring legislation
        #
        SCIENTIFIC_ACTIVITY,
        # Provides evidence base for impact assessments and policy options
        # EFSA opinions create legal/technical justification for intervention
        # Most successful ECI outcome: End Cage Age got legislative commitment
        # after EFSA opinions
        #
        # TIER 2: Policy commitment signals (indicate legislative intent but not binding)
        POLICY_ROADMAP_STRATEGY,
        # Sets legislative timeline and political commitment
        # Often includes "will table proposal by [date]" language
        # Part of Commission Work Programme planning
        #
        DATA_COLLECTION_TRANSPARENCY,
        # Identifies problems requiring legislative solutions
        # Creates objective pressure through public evidence
        # Ban Glyphosate ECI's only legislative success was
        # Transparency Regulation
        #
        # TIER 3: Consultation mechanisms (can build consensus OR substitute for legislation)
        STAKEHOLDER_DIALOGUE,
        # Part of "Better Regulation" stakeholder input requirements
        # Can refine legislative options OR become endless consultation
        # Right2Water organizers rejected stakeholder dialogue as inadequate
        #
        # TIER 4: Implementation and support (parallel to legislation, not leading to it)
        MONITORING_ENFORCEMENT,
        # Reveals inadequacies in current law, creates reform impetus
        # Often used as substitute: "better enforce existing law"
        #
        FUNDING_PROGRAMME,
        # Supports implementation but doesn't drive legislation
        # Financial instruments like Horizon Europe, CAP eco-schemes
        # High substitution risk: "here's money instead of regulation"
        #
        POLICY_IMPLEMENTATION,
        # Applies existing rules; parallel to legislation
        # Classic substitute response: "implement what we have"
        #
        INTERNATIONAL_COOPERATION,
        # Follows Article 218 TFEU (international agreements procedure), not
        # Article 294 TFEU (ordinary legislative procedure) - requires Council
        # authorization for negotiations with foreign partners, indefinite
        # timelines, and outcomes dependent on third-party agreement
        # Structurally peripheral: international cooperation actions don't
        # produce EU legislative acts; instead create non-binding commitments
        # or long-term negotiation processes outside standard Better Regulation
        # framework (no RSB review, no impact assessment requirement for
        # advocacy activities)
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
