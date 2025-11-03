"""Regex patterns for deadline and date extraction."""

from typing import List

# Deadline extraction patterns for Commission commitments
DEADLINE_PATTERNS = [
    # Legislative proposal patterns (action BEFORE deadline)
    r"committed to come forward with a legislative proposal[,\s]+by\s+([^.,;]+)",
    r"intention to table a legislative proposal[,\s]+by\s+([^.,;]+)",
    r"communicated its intention to table a legislative proposal[,\s]+by\s+([^.,;]+)",
    r"to table a legislative proposal[,\s]+by\s+([^.,;]+)",
    r"will table a legislative proposal[,\s]+by\s+([^.,;]+)",
    r"to propose legislation[,\s]+by\s+([^.,;]+)",
    # Communication patterns (action BEFORE deadline)
    r"will (?:then )?communicate[,\s]+by\s+([^.,;]+)",
    r"committed to communicate[,\s]+by\s+([^.,;]+)",
    r"will then communicate[,\s]+by\s+([^.,;]+)",
    # Assessment and study patterns (action BEFORE deadline)
    r"launch.*?(?:impact )?assessment[,\s]+by\s+([^.,;]+)",
    r"conduct.*?study[,\s]+by\s+([^.,;]+)",
    r"carry out.*?(?:assessment|study)[,\s]+by\s+([^.,;]+)",
    r"scientific opinion[,\s]+by\s+([^.,;]+)",
    r"efsa.*?(?:to )?provide.*?(?:opinion|assessment)[,\s]+by\s+([^.,;]+)",
    r"complete.*?(?:assessment|study|evaluation)[,\s]+by\s+([^.,;]+)",
    r"external study to be carried out.*?by\s+([^.,;]+)",
    # Roadmap patterns (action BEFORE deadline)
    r"roadmap.*?(?:is planned|planned|completed?)[,\s]+by\s+([^.,;]+)",
    r"finalisation.*?roadmap.*?by\s+([^.,;]+)",
    r"work on.*?roadmap.*?by\s+([^.,;]+)",
    # Report and update patterns (action BEFORE deadline)
    r"provide.*?report[,\s]+by\s+([^.,;]+)",
    r"provide.*?(?:update|information|data|details)[,\s]+by\s+([^.,;]+)",
    r"will report[,\s]+by\s+([^.,;]+)",
    r"(?:produce|publish).*?report[,\s]+by\s+([^.,;]+)",
    r"report.*?to be produced.*?(?:by|in)\s+([^.,;]+)",
    r"to\s+be\s+produced\s+in\s+([^.,;]+)",
    # Other commitment patterns (action BEFORE deadline)
    r"preparatory work.*?(?:with a view to )?launch.*?by\s+([^.,;]+)",
    r"call for evidence.*?by\s+([^.,;]+)",
    # DEADLINE-FIRST patterns (deadline BEFORE action)
    r"by\s+([^.,;]+),\s+provide.*?(?:information|data|details)",
    r"by\s+([^.,;]+),\s+the\s+commission\s+will\s+(?:communicate|report|provide)",
    r"by\s+([^.,;]+),\s+(?:to\s+)?(?:phase\s+out|ban|prohibit|implement)",
]

# Applicable date patterns for law implementation
APPLICABLE_DATE_PATTERNS = [
    r"became applicable.*?on\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",  # became applicable 18 months later, i.e. on 27 March 2021
    r"became applicable immediately",  # became applicable immediately
    r"applicable from\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",  # applicable from 27 March 2021
    r"and applicable from\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",  # and applicable from 27 March 2021
    r"applies from\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",  # applies from 27 March 2021
    r"apply from\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",  # apply from 27 March 2021
]
