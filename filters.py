def normalize(text):
    return str(text or "").lower().strip()


ENGLISH_MARKERS = [
    "english",
    "inglés",
    "ingles",
    "anglais",
    "englisch",
    "inglese",
    "inglês",
    "english version",
    "eng version",
    " eng ",
    "[eng]",
    "(eng)",
]


NON_ENGLISH_MARKERS = [
    # Japanese
    "japanese",
    "japonés",
    "japones",
    "japonais",
    "japanisch",
    "giapponese",
    "japonês",
    "[jp]",
    "(jp)",
    " jp ",

    # Korean
    "korean",
    "coreano",
    "coréen",
    "koreanisch",
    "[kr]",
    "(kr)",

    # Chinese
    "chinese",
    "chino",
    "chinois",
    "chinesisch",
    "[cn]",
    "(cn)",

    # French
    "french",
    "français",
    "francais",
    "französisch",
    "[fr]",
    "(fr)",

    # German
    "german",
    "deutsch",
    "alemán",
    "aleman",
    "[de]",
    "(de)",

    # Italian
    "italian",
    "italiano",
    "[it]",
    "(it)",
]


ANNIVERSARY_MARKERS = [
    "anniversary set",
    "anniversary collection",
    "anniversary box",
    "anniversary edition",
    "1st anniversary",
    "first anniversary",
    "2nd anniversary",
    "second anniversary",
    "3rd anniversary",
    "third anniversary",
    "4th anniversary",
    "fourth anniversary",
    "5th anniversary",
    "fifth anniversary",
]


# Estas tiendas venden en su categoría One Piece
# los lanzamientos occidentales estándar.
#
# Sus scrapers antiguos no guardan "language",
# por eso UNKNOWN se interpreta como EN.
DEFAULT_ENGLISH_STORES = {
    "arte9",
    "topdeck",
}


def is_anniversary_product(product):

    title = normalize(
        product.get("title")
    )

    return any(
        marker in title
        for marker in ANNIVERSARY_MARKERS
    )


def detect_language(product):

    # ==============================
    # 1. Idioma indicado por scraper
    # ==============================

    language = normalize(
        product.get("language")
    )

    if language in [
        "en",
        "eng",
        "english",
    ]:
        return "EN"

    if language in [
        "jp",
        "jpn",
        "japanese",
    ]:
        return "JP"

    if language in [
        "other",
        "kr",
        "cn",
        "fr",
        "de",
        "it",
    ]:
        return "OTHER"

    # ==============================
    # 2. Detectar por título
    # ==============================

    title = (
        " "
        + normalize(
            product.get("title")
        )
        + " "
    )

    for marker in NON_ENGLISH_MARKERS:

        if marker in title:
            return "OTHER"

    for marker in ENGLISH_MARKERS:

        if marker in title:
            return "EN"

    return "UNKNOWN"


def should_keep_product(product):

    # Anniversary siempre entra,
    # independientemente del idioma.
    if is_anniversary_product(product):
        return True

    language = detect_language(
        product
    )

    # Idioma explícitamente inglés.
    if language == "EN":
        return True

    # Idioma explícitamente no inglés.
    if language in [
        "JP",
        "OTHER",
    ]:
        return False

    # ==============================
    # UNKNOWN
    # ==============================

    store = normalize(
        product.get("store")
    )

    # Arte9 y TopDeck no informan idioma
    # en el objeto, aunque su categoría
    # corresponde al producto occidental.
    if store in DEFAULT_ENGLISH_STORES:
        return True

    return False


def filter_products(products):

    accepted = []
    rejected = []

    for product in products:

        if should_keep_product(product):
            accepted.append(product)

        else:
            rejected.append(product)

    return accepted, rejected