"""Non-legislative action type definitions with classification keywords."""

import re
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
            keywords: List of regex patterns used to classify text as this action type
        """

        name: str
        keywords: List[str]

    # Define all non-legislative action types as class attributes
    IMPACT_ASSESSMENT_CONSULTATION = ActionType(
        name="Impact Assessment and Consultation",
        keywords=[
            r"\bimpact assessments?\b",
            r"\bpublic consultations?\b",
            r"\bcalls? for evidence\b",
            r"\bconsultations? on\b",
        ],
    )

    SCIENTIFIC_ACTIVITY = ActionType(
        name="Scientific Activity",
        keywords=[
            r"\bscientific conferences?\b",
            r"\bscientific opinions?\b",
            r"\befsa\b",
            r"\bworkshops?\b",
            r"\bcolloquia\b",
            r"\bcolloquiums?\b",
        ],
    )

    POLICY_ROADMAP_STRATEGY = ActionType(
        name="Policy Roadmap and Strategy",
        keywords=[
            r"\broadmaps?\b",
            r"\bstrategic plans?\b",
            r"\bstrengthened\b",
            r"\bmodernised\b",
            r"\benhanced\b",
            r"\bpolicy frameworks?\b",
            r"\blong-term strateg(?:y|ies)\b",
            r"\bmechanisms? in place\b",
            r"\bvisions? for\b",
            r"\bstrategic agendas?\b",
            r"\bpolicy priorities\b",
            r"\bmilestones?\b",
            r"\baction plans?\b",
        ],
    )

    DATA_COLLECTION_TRANSPARENCY = ActionType(
        name="Data Collection and Transparency",
        keywords=[
            r"\bdata collection\b",
            r"\btransparency\b",
            r"\bbenchmarking\b",
            r"\beurobarometers?\b",
            r"\bcollected factual information\b",
            r"\bdata on\b",
            r"\breports? (?:was|were) published\b",
            r"\bpublications?\b",
        ],
    )

    STAKEHOLDER_DIALOGUE = ActionType(
        name="Stakeholder Dialogue",
        keywords=[
            r"\bstakeholders?\b",
            r"\bstakeholder partnerships?\b",
            r"\bstakeholder dialogues?\b",
            r"\bpartnerships? with stakeholders\b",
            r"\bpublic consultations?\b",
        ],
    )

    MONITORING_ENFORCEMENT = ActionType(
        name="Monitoring and Enforcement",
        keywords=[
            r"\bmonitoring\b",
            r"\bmonitor\b",
            r"\bactive monitoring\b",
            r"\bwill monitor\b",
            r"\bbetter enforce\b",
            r"\bstrengthen enforcement\b",
            r"\benforcement\b",
            r"\bensure compliance\b",
            r"\bensuring compliance\b",
            r"\bcompliance\b",
            r"\bsupport member states\b",
            r"\bguarantee equal treatment\b",
            r"\bwithhold payments?\b",
            r"\bconditional funding\b",
            r"\bwithhold the corresponding payments?\b",
        ],
    )

    FUNDING_PROGRAMME = ActionType(
        name="Funding Programme",
        keywords=[
            r"\bfunding\b",
            r"\bfinancial support\b",
            r"\bfinancial incentives?\b",
            r"\bsubsidies\b",
            r"\bhorizon europe\b",
            r"\berasmus\b",
            r"\bcreative europe\b",
            r"\bcohesion policy\b",
            r"\bcohesion policies\b",
            r"\bcohesion funding\b",
            r"\bunion funding\b",
            r"\bmultiannual financial frameworks?\b",
            r"\bmff\b",
            r"\bresearch and innovation\b",
            r"\bresearch projects?\b",
            r"\bpilot projects?\b",
        ],
    )

    POLICY_IMPLEMENTATION = ActionType(
        name="Policy Implementation",
        keywords=[
            r"\bwill continue\b",
            r"\bcontinue to\b",
            r"\bensure\b",
            r"\bensuring\b",
            r"\bguarantee\b",
            r"\bmaintain\b",
            r"\bmaintaining\b",
            r"\bnon-discriminatory access\b",
            r"\bequal access\b",
            r"\bimplementation\b",
            r"\bimplementing\b",
            r"\bsafeguard\b",
            r"\bsets? of benchmarks?\b",
            r"\bcollect evidence on the current regulations?\b",
        ],
    )

    INTERNATIONAL_COOPERATION = ActionType(
        name="International Cooperation",
        keywords=[
            r"\binternational cooperation\b",
            r"\breaching out\b",
            r"\binternational partners?\b",
            r"\binternational levels?\b",
            r"\binternational fora\b",
            r"\binternational forums?\b",
            r"\binternational commissions?\b",
            r"\bun general assembly\b",
            r"\bICCAT\b",
            r"\bbest practices? between Member States\b",
            r"\bSustainable Development Goals EU\b",
            r"\bEU-wide public consultations?\b",
            r"\badvocating universal access\b",
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
        r"\broadmaps?\b",
        r"\btasked\b",
        r"\bwill communicate\b",
        r"\bwill report\b",
        r"\bimpact assessments?\b",
        r"\bstakeholders?\b",
        r"\bconsultations?\b",
        r"\bworkshops?\b",
        r"\bmeetings?\b",
        r"\bbetter enforcement\b",
        r"\bin parallel to the legislation\b",
        r"\bseek specific supporting measures?\b",
    ]

    @classmethod
    def classify_text(cls, text: str) -> Optional[ActionType]:
        """
        Classify text by matching regex patterns to action types.

        Args:
            text: Text to classify (should be lowercased)

        Returns:
            ActionType if match found, None otherwise
        """
        text_lower = text.lower()

        for action_type in cls.ALL_ACTION_TYPES:
            if any(re.search(keyword, text_lower) for keyword in action_type.keywords):
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
        return any(re.search(word, text_lower) for word in cls.SKIP_WORDS_LEGISLATIVE)

    @classmethod
    def get_all_keywords(cls) -> List[str]:
        """
        Get all regex patterns from all action types.

        Returns:
            Flat list of all regex patterns
        """
        keywords = []
        for action_type in cls.ALL_ACTION_TYPES:
            keywords.extend(action_type.keywords)
        return keywords
