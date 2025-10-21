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
    
    # Submission and Verification Data
    submission_text: str
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
    legislative_proposal_status: Optional[str]
    commission_response_summary: Optional[str]
    
    # Follow-up Activities Section
    has_followup_section: Optional[bool]
    followup_meeting_date: Optional[str]
    followup_meeting_officials: Optional[str]
    roadmap_launched: Optional[bool]
    roadmap_description: Optional[str]
    roadmap_completion_target: Optional[str]
    workshop_conference_dates: Optional[str]  # JSON array
    partnership_programs: Optional[str]
    court_cases_referenced: Optional[str]
    court_judgment_dates: Optional[str]
    court_judgment_summary: Optional[str]
    latest_update_date: Optional[str]
    
    # Multimedia and Documentation Links
    commission_factsheet_url: str
    dedicated_website: bool
    
    # Structural Analysis Flags
    related_eu_legislation: Optional[str]
    petition_platforms_used: Optional[str]
    follow_up_duration_months: Optional[int]
    
    # Metadata
    created_timestamp: str
    last_updated: str

    def to_dict(self) -> dict:
        """
        Convert ECI Response object to dictionary
        
        Returns:
            Dictionary representation of the ECI Response object
        """
        return asdict(self)