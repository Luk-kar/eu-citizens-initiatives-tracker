# TODO

# """Regex patterns and keyword definitions"""

# import re


# class DatePatterns:
#     """Date format regex patterns"""
#     MONTH_NAME = re.compile(r'(\d{1,2})\s+(January|February|...)\s+(\d{4})', re.IGNORECASE)
#     SLASH_FORMAT = re.compile(r'(\d{1,2})/(\d{1,2})/(\d{4})')
#     ISO_FORMAT = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
#     # ... all date patterns


# class LegislativeActionPatterns:
#     """Legislative action detection patterns"""
#     PROPOSAL = re.compile(
#         r'(?:proposal|proposed|tabled|submitted).*?(?:regulation|directive|decision|law)',
#         re.IGNORECASE
#     )
#     ADOPTION = re.compile(
#         r'(?:adopted|approved|passed).*?(?:regulation|directive|decision|law)',
#         re.IGNORECASE
#     )
#     # ... all action patterns


# class NonLegislativeActionPatterns:
#     """Non-legislative action patterns"""
#     REPORT = re.compile(r'(?:report|study|analysis).*?(?:published|issued)', re.IGNORECASE)
#     CONSULTATION = re.compile(r'(?:consultation|dialogue|stakeholder)', re.IGNORECASE)
#     # ... all patterns


# class RejectionKeywords:
#     """Keywords for rejection reasoning"""
#     PRIMARY = [
#         'will not make', 'decided not to', 'does not intend',
#         'not propose', 'not present', 'not put forward'
#     ]
#     EXISTING_FRAMEWORK = [
#         'existing legislation', 'already covered', 'current framework',
#         'sufficient legal basis'
#     ]
#     # ... all keyword categories


# class DeadlinePatterns:
#     """Deadline extraction patterns"""
#     WITHIN_MONTHS = re.compile(r'within\s+(\d+)\s+months?', re.IGNORECASE)
#     BY_DATE = re.compile(r'by\s+(\d{1,2})\s+(\w+)\s+(\d{4})', re.IGNORECASE)
#     # ... all deadline patterns
