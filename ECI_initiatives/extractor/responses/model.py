"""
ECI Responses Data Models
Data structures for ECI Commission responses information
"""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ECICommissionResponseRecord:
    """Data structure for ECI Commission response information"""

    # Basic Initiative Metadata
    response_url: str
    initiative_url: str
    initiative_title: str
    registration_number: str

    # Submission text
    submission_text: str

    # Submission and Verification Data
    commission_submission_date: Optional[str]
    submission_news_url: Optional[str]

    # Procedural Timeline Milestones
    commission_meeting_date: Optional[str]
    commission_officials_met: Optional[str]
    parliament_hearing_date: Optional[str]
    parliament_hearing_video_urls: Optional[str]
    plenary_debate_date: Optional[str]
    plenary_debate_video_urls: Optional[str]
    official_communication_adoption_date: Optional[str]
    official_communication_document_urls: Optional[str]

    # Commission Response Content
    commission_answer_text: Optional[str]

    # SECTION 1: Final Outcome (What citizens care about most)
    final_outcome_status: Optional[str]
    law_implementation_date: Optional[str]

    # SECTION 2: Commission's Initial Response (What they promised)
    commission_promised_new_law: Optional[bool]
    commission_deadlines: Optional[bool]
    commission_rejected_initiative: Optional[bool]
    commission_rejection_reason: Optional[str]

    # SECTION 3: Actions Taken (What actually happened)
    laws_actions: Optional[str]  # JSON string
    policies_actions: Optional[str]  # JSON string

    # Follow-up Activities Section
    has_followup_section: Optional[bool]
    followup_events: Optional[str]
    has_roadmap: Optional[bool]
    has_workshop: Optional[bool]
    has_partnership_programs: Optional[str]
    court_cases_referenced: Optional[str]
    latest_date: Optional[str]
    most_future_date: Optional[str]

    # Multimedia and Documentation Links
    commission_factsheet_url: str
    followup_dedicated_website: Optional[str]

    # Structural Analysis Flags
    referenced_legislation_by_id: Optional[str]
    referenced_legislation_by_name: Optional[str]
    followup_actions_with_dates: Optional[int]

    # Metadata
    last_updated: str

    def to_dict(self) -> dict:
        """
        Convert ECI Response object to dictionary

        Returns:
            Dictionary representation of the ECI Response object
        """
        return asdict(self)
