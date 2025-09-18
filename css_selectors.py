class ECIPageSelectors:
    """
    CSS selectors for European Citizens' Initiative (ECI) page elements
    """

    INITIATIVE_PROGRESS = "ol.ecl-timeline"

    OBJECTIVES = "//h2[@class='ecl-u-type-heading-2' and text()='Objectives']"

    ANNEX = "//h2[@class='ecl-u-type-heading-2' and text()='Annex']"

    ORGANISERS = "//h2[@class='ecl-u-type-heading-2' and text()='Organisers']"

    REPRESENTATIVE = "//h3[@class='ecl-u-type-heading-3' and text()='Representative']"

    SOURCES_OF_FUNDING = (
        "//h2[@class='ecl-u-type-heading-2' and text()='Sources of funding']"
    )

    SOCIAL_SHARE = "div.ecl-social-media-share"
