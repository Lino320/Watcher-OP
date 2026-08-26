import re
import requests


STORE_NAME = "Nova Ohara Cards"

BASE_URL = "https://novaoharacards.com"

PRODUCTS_URL = (
    "https://novaoharacards.com/"
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


def clean_html(text):

    if not text:
        return ""

    text = re.sub(
        r"<[^>]+>",
        " ",
        str(text)
    )

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def normalize_tags(tags):

    if isinstance(tags, list):

        return " ".join(
            str(tag)
            for tag in tags
        )

    return str(
        tags or ""
    )


def is_one_piece(
    title,
    body,
    tags
):

    text = (
        title
        + " "
        + body
        + " "
        + tags
    ).lower()

    # Marcadores claros
    if (
        "one piece" in text
        or "onepiece" in text
    ):
        return True

    # Códigos típicos del One Piece Card Game
    if re.search(
        r"\b(OP|EB|PRB|ST|DP|IB)-?\d{2}\b",
        text,
        flags=re.IGNORECASE
    ):
        return True

    return False


def is_anniversary(text):

    value = text.lower()

    return any(
        marker in value
        for marker in [
            "anniversary",
            "aniversario",
            "anniversary set",
            "anniversary collection",
        ]
    )


def detect_language(
    title,
    body,
    tags
):

    text = (
        title
        + " "
        + body
        + " "
        + tags
    ).lower()

    # English
    if any(
        marker in text
        for marker in [
            "inglés",
            "ingles",
            "english",
            "(eng)",
            "[eng]",
            " eng ",
        ]
    ):
        return "EN"

    # Japanese
    if any(
        marker in text
        for marker in [
            "japonés",
            "japones",
            "japanese",
            "(jp)",
            "[jp]",
            " jp ",
        ]
    ):
        return "JP"

    # Otros
    if any(
        marker in text
        for marker in [
            "coreano",
            "korean",
            "chinese",
            "chino",
            "alemán",
            "german",
            "francés",
            "french",
        ]
    ):
        return "OTHER"

    return "UNKNOWN"


def detect_stock(
    item,
    text
):

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

    value = text.lower()

    preorder = any(
        marker in value
        for marker in [
            "(reserva)",
            "producto en reserva",
            "preventa",
            "pre-venta",
            "preorder",
            "pre-order",
            "precompra",
        ]
    )

    if preorder:
        return "PREORDER"

    if available:
        return "AVAILABLE"

    return "OUT_OF_STOCK"


def get_nova_ohara_products():

    print(
        "   Nova Ohara Cards leyendo catálogo..."
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

        body = clean_html(
            item.get(
                "body_html",
                ""
            )
        )

        tags = normalize_tags(
            item.get(
                "tags",
                []
            )
        )

        # ==========================
        # SOLO ONE PIECE
        # ==========================

        if not is_one_piece(
            title,
            body,
            tags
        ):
            continue

        combined_text = (
            title
            + " "
            + body
            + " "
            + tags
        )

        language = detect_language(
            title,
            body,
            tags
        )

        anniversary = is_anniversary(
            combined_text
        )

        # ==========================
        # ENGLISH ONLY
        # +
        # Anniversary exception
        # ==========================

        if (
            language in [
                "JP",
                "OTHER"
            ]
            and not anniversary
        ):
            continue

        # Nova Ohara especifica en las
        # descripciones de sus One Piece
        # principales que son ingleses.
        #
        # Si no detectamos otro idioma,
        # aceptamos UNKNOWN como EN.
        if language == "UNKNOWN":

            language = "EN"

        # ==========================
        # PRECIO
        # ==========================

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

        # ==========================
        # STOCK / PREVENTA
        # ==========================

        stock = detect_stock(
            item,
            combined_text
        )

        url = (
            f"{BASE_URL}/products/{handle}"
        )

        products.append({
            "store": STORE_NAME,
            "title": title,
            "price": price,
            "price_text": price_text,
            "stock": stock,
            "url": url,
            "published_at": item.get(
                "published_at"
            ),
            "language": language
        })

    # Más recientes primero
    products.sort(
        key=lambda product:
            product.get(
                "published_at"
            ) or "",
        reverse=True
    )

    return products