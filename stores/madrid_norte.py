import requests


STORE_NAME = "Madrid Norte TCG"

BASE_URL = "https://madridnortetcg.com"

PRODUCTS_URL = (
    "https://madridnortetcg.com/"
    "collections/one-piece-tcg/"
    "products.json?limit=250"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}


def parse_price(value):

    if value is None:
        return None

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


def normalize_tags(tags):

    if isinstance(tags, list):
        return " ".join(
            str(tag)
            for tag in tags
        ).lower()

    return str(tags or "").lower()


def is_anniversary(title):

    text = title.lower()

    return (
        "anniversary" in text
        or "aniversario" in text
        or "aniversário" in text
    )


def detect_language(title, tags):

    text = (
        title
        + " "
        + normalize_tags(tags)
    ).lower()

    # ==========================
    # INGLÉS
    # ==========================

    english_markers = [
        "inglés",
        "ingles",
        "english",
        "[eng]",
        "(eng)",
        " en ",
    ]

    for marker in english_markers:

        if marker in f" {text} ":
            return "EN"

    # ==========================
    # JAPONÉS
    # ==========================

    japanese_markers = [
        "japonés",
        "japones",
        "japanese",
        "[jp]",
        "(jp)",
    ]

    for marker in japanese_markers:

        if marker in text:
            return "JP"

    # ==========================
    # OTROS IDIOMAS
    # ==========================

    other_markers = [
        "chinese",
        "chino",
        "coreano",
        "korean",
        "francés",
        "french",
        "alemán",
        "german",
        "italiano",
        "italian",
    ]

    for marker in other_markers:

        if marker in text:
            return "OTHER"

    return "UNKNOWN"


def get_stock(item):

    variants = item.get(
        "variants",
        []
    )

    available = any(
        variant.get(
            "available",
            False
        )
        for variant in variants
    )

    title = item.get(
        "title",
        ""
    ).lower()

    tags = normalize_tags(
        item.get(
            "tags",
            []
        )
    )

    body = str(
        item.get(
            "body_html",
            ""
        )
    ).lower()

    text = (
        title
        + " "
        + tags
        + " "
        + body
    )

    preorder = any(
        marker in text
        for marker in [
            "preventa",
            "pre-order",
            "preorder",
            "pre order",
            "reserva",
        ]
    )

    if preorder and available:
        return "PREORDER"

    if available:
        return "AVAILABLE"

    if preorder:
        return "PREORDER"

    return "OUT_OF_STOCK"


def get_madrid_norte_products():

    print(
        "   Madrid Norte TCG leyendo catálogo..."
    )

    response = requests.get(
        PRODUCTS_URL,
        headers=HEADERS,
        timeout=25
    )

    response.raise_for_status()

    data = response.json()

    raw_products = data.get(
        "products",
        []
    )

    products = []

    for item in raw_products:

        title = item.get(
            "title",
            "Producto sin nombre"
        )

        handle = item.get(
            "handle"
        )

        if not handle:
            continue

        url = (
            f"{BASE_URL}/products/{handle}"
        )

        tags = item.get(
            "tags",
            []
        )

        language = detect_language(
            title,
            tags
        )

        anniversary = is_anniversary(
            title
        )

        # =====================================
        # FILTRO DE IDIOMA
        #
        # Madrid Norte vende su catálogo
        # One Piece principalmente en inglés.
        #
        # Solo descartamos si detectamos
        # explícitamente otro idioma.
        # =====================================

        if (
            language in [
                "JP",
                "OTHER"
            ]
            and not anniversary
        ):
            continue

        # Si no especifica idioma,
        # lo consideramos inglés porque
        # estamos dentro de su colección
        # One Piece TCG inglesa.
        if language == "UNKNOWN":
            language = "EN"

        # =====================================
        # PRECIO
        # =====================================

        variants = item.get(
            "variants",
            []
        )

        prices = []

        for variant in variants:

            price = parse_price(
                variant.get(
                    "price"
                )
            )

            if price is not None:
                prices.append(
                    price
                )

        if prices:

            price = min(
                prices
            )

            price_text = (
                f"{price:.2f} €"
            )

        else:

            price = None
            price_text = "Sin precio"

        # =====================================
        # STOCK
        # =====================================

        stock = get_stock(
            item
        )

        # =====================================
        # FECHA
        # =====================================

        published_at = item.get(
            "published_at"
        )

        products.append({
            "store": STORE_NAME,
            "title": title,
            "price": price,
            "price_text": price_text,
            "stock": stock,
            "url": url,
            "published_at": published_at,
            "language": language
        })

    # Más nuevos primero
    products.sort(
        key=lambda product:
            product.get(
                "published_at"
            ) or "",
        reverse=True
    )

    return products