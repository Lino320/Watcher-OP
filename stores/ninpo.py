import re
import requests


STORE_NAME = "Ninpo Store"

BASE_URL = "https://ninpostore.com"

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

    if (
        "one piece" in text
        or "onepiece" in text
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
        ]
    )


def detect_language(text):

    value = (
        " "
        + text.lower()
        + " "
    )

    if any(
        marker in value
        for marker in [
            " inglés",
            " ingles",
            " english",
            "[eng]",
            "(eng)",
        ]
    ):
        return "EN"

    if any(
        marker in value
        for marker in [
            " japonés",
            " japones",
            " japanese",
            "[jp]",
            "(jp)",
        ]
    ):
        return "JP"

    if any(
        marker in value
        for marker in [
            "coreano",
            "korean",
            "chinese",
            "chino",
        ]
    ):
        return "OTHER"

    return "UNKNOWN"


def detect_stock(
    item,
    combined_text
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

    text = combined_text.lower()

    preorder = any(
        marker in text
        for marker in [
            "preventa",
            "pre-venta",
            "preorder",
            "pre-order",
            "reserva",
            "fecha de lanzamiento",
        ]
    )

    if preorder and available:
        return "PREORDER"

    if preorder:
        return "PREORDER"

    if available:
        return "AVAILABLE"

    return "OUT_OF_STOCK"


def get_ninpo_products():

    print(
        "   Ninpo Store leyendo catálogo..."
    )

    products_by_url = {}

    # Shopify permite paginar products.json.
    for page_number in range(1, 20):

        url = (
            f"{BASE_URL}/products.json"
            f"?limit=250&page={page_number}"
        )

        print(
            f"   Ninpo página API "
            f"{page_number}..."
        )

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        raw_products = data.get(
            "products",
            []
        )

        print(
            "      Productos brutos:",
            len(raw_products)
        )

        if not raw_products:
            break

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
                combined_text
            )

            anniversary = is_anniversary(
                combined_text
            )

            # ==========================
            # SOLO ENGLISH
            #
            # Anniversary siempre entra.
            # ==========================

            if (
                language != "EN"
                and not anniversary
            ):
                continue

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
            # STOCK
            # ==========================

            stock = detect_stock(
                item,
                combined_text
            )

            product_url = (
                f"{BASE_URL}/products/{handle}"
            )

            products_by_url[
                product_url
            ] = {
                "store": STORE_NAME,
                "title": title,
                "price": price,
                "price_text": price_text,
                "stock": stock,
                "url": product_url,
                "published_at": item.get(
                    "published_at"
                ),
                "language": (
                    "EN"
                    if language == "EN"
                    else "UNKNOWN"
                )
            }

        # Menos de 250 significa
        # que era la última página.
        if len(raw_products) < 250:
            break

    products = list(
        products_by_url.values()
    )

    # Más recientes primero
    products.sort(
        key=lambda product:
            product.get(
                "published_at"
            ) or "",
        reverse=True
    )

    return products