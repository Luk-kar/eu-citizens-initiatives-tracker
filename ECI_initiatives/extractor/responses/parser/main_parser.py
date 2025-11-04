"""
ECI Response HTML Parser - Main Orchestrator
Coordinates all extractor classes to parse response pages
"""

from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, Optional
from bs4 import BeautifulSoup

from ..model import ECICommissionResponseRecord

# Import all extractors
from .extractors.metadata import BasicMetadataExtractor
from .extractors.submission import SubmissionDataExtractor
from .extractors.timeline import ProceduralTimelineExtractor
from .extractors.parliament import ParliamentActivityExtractor
from .extractors.response import CommissionResponseExtractor
from .extractors.outcome import LegislativeOutcomeExtractor
from .extractors.followup import FollowUpActivityExtractor
from .extractors.multimedia import MultimediaDocumentationExtractor
from .extractors.structural import StructuralAnalysisExtractor


class ECIResponseHTMLParser:
    """Main parser that orchestrates all extractor classes"""

    def __init__(self, logger: logging.Logger):
        """Initialize parser with shared logger"""
        self.logger = logger
        self._registration_number = (
            None  # Sets private field directly, no setter called
        )

        # Initialize all extractor instances
        self.basic_metadata = BasicMetadataExtractor(logger)
        self.submission_data = SubmissionDataExtractor(logger)
        self.procedural_timeline = ProceduralTimelineExtractor(logger)
        self.parliament_activity = ParliamentActivityExtractor(logger)
        self.commission_response = CommissionResponseExtractor(logger)
        self.legislative_outcome = LegislativeOutcomeExtractor(
            registration_number=self.registration_number
        )
        self.followup_activity = FollowUpActivityExtractor(logger)
        self.multimedia_docs = MultimediaDocumentationExtractor(logger)
        self.structural_analysis = StructuralAnalysisExtractor(logger)

    @property
    def registration_number(self):
        """Get registration number"""

        return self._registration_number

    @registration_number.setter
    def registration_number(self, value):
        """Set registration number and propagate to all extractors"""

        self._registration_number = value

        # Automatically update ALL extractors
        for extractor in [
            self.basic_metadata,
            self.submission_data,
            self.procedural_timeline,
            self.parliament_activity,
            self.commission_response,
            self.followup_activity,
            self.multimedia_docs,
            self.structural_analysis,
        ]:
            extractor.set_registration_number(value)

    def parse_file(
        self, html_path: Path, responses_list_data: Dict
    ) -> Optional[ECICommissionResponseRecord]:
        """Parse a single ECI response HTML file and extract data"""
        try:
            self.logger.info(f"Parsing response file: {html_path.name}")

            self.registration_number = responses_list_data["registration_number"]

            # Update registration number in all extractors
            for extractor in [
                self.basic_metadata,
                self.submission_data,
                self.procedural_timeline,
                self.parliament_activity,
                self.commission_response,
                self.legislative_outcome,
                self.followup_activity,
                self.multimedia_docs,
                self.structural_analysis,
            ]:
                extractor.set_registration_number(self.registration_number)

            # Read and parse HTML file
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, "html.parser")

            current_timestamp = datetime.now().isoformat()

            # Extract commission communication date for follow-up calculation
            official_communication_adoption_date = (
                self.commission_response.extract_official_communication_adoption_date(
                    soup
                )
            )
            latest_date = self.followup_activity.extract_latest_date(soup)

            # Create and return ECI Response object using extractors
            response = ECICommissionResponseRecord(
                # Basic Initiative Metadata
                response_url=self.basic_metadata.extract_response_url(soup),
                initiative_url=self.basic_metadata.extract_initiative_url(soup),
                initiative_title=responses_list_data.get("title"),
                registration_number=self.registration_number,
                # Submission text
                submission_text=self.submission_data.extract_submission_text(soup),
                # Submission and Verification Data
                commission_submission_date=self.submission_data.extract_commission_submission_date(
                    soup
                ),
                submission_news_url=self.submission_data.extract_submission_news_url(
                    soup
                ),
                # Procedural Timeline Milestones
                commission_meeting_date=self.procedural_timeline.extract_commission_meeting_date(
                    soup
                ),
                commission_officials_met=self.procedural_timeline.extract_commission_officials_met(
                    soup
                ),
                parliament_hearing_date=self.parliament_activity.extract_parliament_hearing_date(
                    soup
                ),
                parliament_hearing_video_urls=self.parliament_activity.extract_parliament_hearing_video_urls(
                    soup
                ),
                plenary_debate_date=self.parliament_activity.extract_plenary_debate_date(
                    soup
                ),
                plenary_debate_video_urls=self.parliament_activity.extract_plenary_debate_video_urls(
                    soup
                ),
                official_communication_adoption_date=official_communication_adoption_date,
                official_communication_document_urls=self.commission_response.extract_official_communication_document_urls(
                    soup
                ),
                # Commission Response Content
                commission_answer_text=self.commission_response.extract_commission_answer_text(
                    soup
                ),
                # Legislative Outcome Assessment
                # Final Outcome (What citizens care about most)
                final_outcome_status=self.legislative_outcome.extract_highest_status_reached(
                    soup
                ),
                law_implementation_date=self.legislative_outcome.extract_applicable_date(
                    soup
                ),
                # Commission's Initial Response (What they promised)
                commission_promised_new_law=self.legislative_outcome.extract_proposal_commitment_stated(
                    soup
                ),
                commission_deadlines=self.legislative_outcome.extract_commissions_deadlines(
                    soup
                ),
                commission_rejected_initiative=self.legislative_outcome.extract_proposal_rejected(
                    soup
                ),
                commission_rejection_reason=self.legislative_outcome.extract_rejection_reasoning(
                    soup
                ),
                # Actions Taken (What actually happened)
                laws_actions=self.legislative_outcome.extract_legislative_action(soup),
                policies_actions=self.legislative_outcome.extract_non_legislative_action(
                    soup
                ),
                # Follow-up Activities Section
                has_followup_section=self.followup_activity.extract_has_followup_section(
                    soup
                ),
                followup_events=self.followup_activity.extract_followup_events(soup),
                has_roadmap=self.followup_activity.extract_has_roadmap(soup),
                has_workshop=self.followup_activity.extract_has_workshop(soup),
                has_partnership_programs=self.followup_activity.extract_has_partnership_programs(
                    soup
                ),
                court_cases_referenced=self.followup_activity.extract_court_cases_referenced(
                    soup
                ),
                latest_date=latest_date,
                # Multimedia and Documentation Links
                commission_factsheet_url=self.multimedia_docs.extract_commission_factsheet_url(
                    soup
                ),
                dedicated_website=self.multimedia_docs.extract_has_dedicated_website(
                    soup
                ),
                # Structural Analysis Flags
                related_eu_legislation=self.structural_analysis.extract_related_eu_legislation(
                    soup
                ),
                petition_platforms_used=self.structural_analysis.extract_petition_platforms_used(
                    soup
                ),
                follow_up_duration_months=self.structural_analysis.calculate_follow_up_duration_months(
                    official_communication_adoption_date, latest_date
                ),
                # Metadata
                created_timestamp=current_timestamp,
                last_updated=current_timestamp,
            )

            self.logger.info(
                f"Successfully parsed response: {response.registration_number}"
            )
            return response

        except FileNotFoundError:
            self.logger.error(f"File not found: {html_path}")
            return None
        except Exception as e:
            self.logger.error(
                f"Error parsing {html_path.name}: {str(e)}", exc_info=True
            )
            return None
        finally:
            self.registration_number = None
