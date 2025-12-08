# Python
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ECIFollowupWebsiteRecord:
    registration_number: str
    initiative_title: str

    # Basic Initiative Metadata
    registration_number: str
    initiative_title: str
    followup_dedicated_website: str

    # Commission Response Content
    commission_answer_text: str
    official_communication_document_urls: Optional[str]  # JSON dict

    # SECTION 1: Final Outcome (What citizens care about most)
    final_outcome_status: Optional[str]
    law_implementation_date: Optional[str]

    # SECTION 2: Commission's Initial Response (What they promised)
    commission_promised_new_law: bool
    commission_deadlines: Optional[str]  # JSON dict
    commission_rejected_initiative: bool
    commission_rejection_reason: Optional[str]

    # SECTION 3: Actions Taken (What actually happened)
    laws_actions: Optional[str]  # JSON string
    policies_actions: Optional[str]  # JSON string

    # Follow-up Activities Section
    has_roadmap: bool
    has_workshop: bool
    has_partnership_programs: bool
    court_cases_referenced: Optional[str]  # JSON dict
    followup_latest_date: Optional[str]
    followup_most_future_date: Optional[str]

    # Multimedia and Documentation Links

    # Structural Analysis Flags
    referenced_legislation_by_id: Optional[str]  # JSON dict
    referenced_legislation_by_name: Optional[str]  # JSON dict
    followup_events_with_dates: str  # JSON list

    def to_dict(self) -> dict:
        return asdict(self)
