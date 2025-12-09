"""
Extractors for parsing
European Citizens' Initiative follow-up website HTML
into structured data.
"""

from .main import FollowupWebsiteExtractor
from .outcome import FollowupWebsiteLegislativeOutcomeExtractor
from .followup import FollowupWebsiteFollowUpExtractor

__all__ = [
    "FollowupWebsiteExtractor",
    "FollowupWebsiteLegislativeOutcomeExtractor",
    "FollowupWebsiteFollowUpExtractor",
]
