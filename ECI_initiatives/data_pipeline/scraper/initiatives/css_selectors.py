class ECIinitiativeSelectors:
    """
    CSS selectors for European Citizens' Initiative (ECI) individual page elements
    """

    # Page structure and timeline
    INITIATIVE_PROGRESS = "ol.ecl-timeline"

    # Content section headings
    OBJECTIVES = "//h2[@class='ecl-u-type-heading-2' and text()='Objectives']"
    ANNEX = "//h2[@class='ecl-u-type-heading-2' and text()='Annex']"
    SOURCES_OF_FUNDING = (
        "//h2[@class='ecl-u-type-heading-2' and text()='Sources of funding']"
    )

    # Organizational information
    ORGANISERS = "//h2[@class='ecl-u-type-heading-2' and text()='Organisers']"
    REPRESENTATIVE = "//h3[@class='ecl-u-type-heading-3' and text()='Representative']"

    # UI elements
    SOCIAL_SHARE = "div.ecl-social-media-share"

    # Error handling
    PAGE_HEADER_TITLE = "h1.ecl-page-header-core__title"


class ECIlistingSelectors:

    # Navigation and pagination
    NEXT_BUTTON = 'li.ecl-pagination__item--next a[aria-label="Go to next page"]'
    PAGINATION_LINKS = (
        "ul.ecl-pagination__list li.ecl-pagination__item a.ecl-pagination__link"
    )

    # Content parsing
    CONTENT_BLOCKS = "div.ecl-content-block.ecl-content-item__content-block"
    INITIATIVE_CARDS = "div.ecl-content-block__title a.ecl-link"  # Same as TITLE_LINKS
    META_LABELS = "span.ecl-content-block__secondary-meta-label"
