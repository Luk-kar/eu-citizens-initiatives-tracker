"""Text processing utilities for cleaning and normalizing ECI response content."""

import re
import html


def normalize_whitespace(text: str) -> str:
    """
    Normalize all whitespace to single spaces.

    Replaces multiple whitespace characters (spaces, tabs, newlines, carriage returns)
    with a single space and strips leading/trailing whitespace.

    Args:
        text: Input text with potentially irregular whitespace

    Returns:
        Text with normalized whitespace

    Example:
        >>> normalize_whitespace("Hello\\n\\n   world\\t\\t")
        "Hello world"
    """
    return re.sub(r"\s+", " ", text).strip()


def clean_text_for_lowercase_comparison(text: str) -> str:
    """
    Prepare text for case-insensitive pattern matching.

    Converts to lowercase and normalizes whitespace for consistent
    pattern matching across ECI response documents.

    Args:
        text: Raw text from HTML elements

    Returns:
        Lowercase text with normalized whitespace
    """
    text = text.lower()
    return normalize_whitespace(text)


def strip_trailing_phrases(text: str, trailing_words: list = None) -> str:
    """
    Remove common trailing phrases that aren't part of core content.

    Used when extracting dates or specific information where trailing
    context needs to be removed.

    Args:
        text: Input text
        trailing_words: List of words that trigger removal of trailing text.
                       Defaults to common prepositions and conjunctions.

    Returns:
        Text with trailing phrases removed

    Example:
        >>> strip_trailing_phrases("May 2018 to implement the directive")
        "May 2018"
    """
    if trailing_words is None:
        trailing_words = ["to", "for", "in order to", "with", "amongst", "among"]

    pattern = r"\s+(?:" + "|".join(re.escape(word) for word in trailing_words) + r").*$"
    text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return text.rstrip(".,;")


def remove_leading_punctuation(text: str) -> str:
    """
    Remove leading punctuation and whitespace from text.

    Commonly used after sentence extraction to clean up fragments.

    Args:
        text: Text potentially starting with punctuation

    Returns:
        Text with leading punctuation removed
    """
    return text.lstrip(".,;:•\n\r\t ")


def remove_url_patterns(text: str, patterns: list = None) -> str:
    """
    Remove specific URL patterns from text.

    Used to filter out internal navigation links and
    standardize extracted URLs.

    Args:
        text: Text containing URLs
        patterns: List of regex patterns for URLs to remove

    Returns:
        Text with specified URLs removed
    """
    if patterns is None:
        patterns = [
            r"https?://ec\.citizens-initiative\.europa\.eu/public/initiatives/successful/details/\d{4}/\d+[a-z\-]*\??",
            r"https?://citizens-initiative\.europa\.eu/initiatives/details/\d{4}/\d+/?[a-z\-]*",
        ]

    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    return normalize_whitespace(text)


def extract_complete_text_content(element) -> str:
    """
    Extract all text from BeautifulSoup element with full cleanup.

    Combines HTML unescaping, text extraction, and whitespace normalization
    in one call for common extraction patterns.

    Args:
        element: BeautifulSoup element

    Returns:
        Fully cleaned and normalized text content
    """
    text = "".join(element.stripped_strings)
    text = html.unescape(text)
    return normalize_whitespace(text.lower())
