from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ECIFollowupWebsiteRecord:
    registration_number: str
    commission_answer_text: Optional[str]
    followup_latest_date: Optional[str]
    followup_most_future_date: Optional[str]
    commission_deadlines: Optional[str]
    official_communication_document_urls: Optional[str]
    followup_dedicated_website: Optional[str]
    laws_actions: Optional[str]
    policies_actions: Optional[str]
    followup_events_with_dates: Optional[str]
    referenced_legislation_by_name: Optional[str]
    referenced_legislation_by_id: Optional[str]
    final_outcome_status: Optional[str]
    commission_promised_new_law: Optional[bool]
    commission_rejected_initiative: Optional[bool]
    commission_rejection_reason: Optional[str]
    has_followup_section: Optional[bool]
    has_roadmap: Optional[bool]
    has_workshop: Optional[bool]
    has_partnership_programs: Optional[bool]
    court_cases_referenced: Optional[str]
    law_implementation_date: Optional[str]

    def to_dict(self) -> dict:
        return asdict(self)
