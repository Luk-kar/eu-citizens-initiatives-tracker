"""Helper functions for extracting and processing HTML links."""

from typing import Optional


def build_links_dict(links) -> Optional[dict]:
    """
    Build a dictionary mapping link text to URLs from BeautifulSoup link elements.

    Args:
        links: List of BeautifulSoup anchor elements

    Returns:
        Dictionary mapping link text to URLs, or None if no valid links found
    """
    if not links:
        return None

    links_dict = {}
    for link in links:
        link_text = link.get_text(strip=True)
        link_url = link.get("href", "")

        if link_text and link_url:
            links_dict[link_text] = link_url

    return links_dict if links_dict else None
