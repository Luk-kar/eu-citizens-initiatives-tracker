"""Helper functions for locating HTML sections in ECI response documents."""

from .submission import find_submission_section
from .links import build_links_dict

__all__ = ["find_submission_section", "build_links_dict"]
