"""Keyword lists for classification and filtering."""

from typing import List

# Keywords that indicate rejection reasoning
REJECTION_REASONING_KEYWORDS = [
    "will not make",
    "will not propose",
    "decided not to",
    "no legislative proposal",
    "neither scientific nor legal grounds",
    "existing legislation",
    "existing funding framework",
    "already covered",
    "no repeal",
    "differs from",
    "not to submit",
    "fall outside",
    "outside of eu competence",
    "outside the eu competence",
    "not within eu competence",
    "beyond eu competence",
    "interfere with",
]

# Words that indicate non-legislative content to skip during extraction
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
