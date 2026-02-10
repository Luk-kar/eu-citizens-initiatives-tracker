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
