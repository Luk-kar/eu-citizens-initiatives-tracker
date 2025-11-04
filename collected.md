`./ECI_initiatives/extractor/responses/parser/extractors/html_sections/__init__.py`:
```
"""Helper functions for locating HTML sections in ECI response documents."""

from .submission import find_submission_section
from .links import build_links_dict

__all__ = ["find_submission_section", "build_links_dict"]

```

`./ECI_initiatives/extractor/responses/parser/extractors/html_sections/links.py`:
```
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

```

`./ECI_initiatives/extractor/responses/parser/extractors/html_sections/submission.py`:
```
"""Helper functions for locating HTML sections in ECI response documents."""

import re


def find_submission_section(soup, registration_number=None):
    section = soup.find("h2", id="Submission-and-examination")
    if not section:
        section = soup.find(
            "h2", string=re.compile(r"Submission and examination", re.IGNORECASE)
        )
    if not section:
        msg = "No submission section found"
        if registration_number:
            msg += f" for {registration_number}"
        raise ValueError(msg)
    return section

```

