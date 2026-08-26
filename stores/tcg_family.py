import requests


STORE_NAME = "TCG Family"

BASE_URL = "https://tcg-family.com"

PRODUCTS_URL = (
    "https://tcg-family.com/"
    "collections/pre-vendas-one-piece/"
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


def detect_language(title, tags):

    text = (
        title
        + " "
        + " ".join(
            str(tag)
            for tag in tags
        )
    ).lower()

    # Portugués / Español
    if (
        "inglês" in text
        or "ingles" in text
        or "inglés" in text
        or "english" in text
        or " en " in f" {text} "
    ):
        return "EN"

    if (
        "japonês" in text
        or "japones" in text
        or "japanese" in text
        or " jp " in f" {text} "
    ):
        return "JP"

    if (
        "coreano" in text
        or "korean" in text
        or " kr " in f" {text} "
    ):
        return "OTHER"

    return "UNKNOWN"


def is_anniversary(title):

    text = title.lower()

    return (
        "anniversary" in text
        or "aniversario" in text
        or "aniversário" in text
    )


def get_tcg_family_products():

    print(
        "   TCG Family leyendo catálogo..."
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

        variants = item.get(
            "variants",
            []
        )

        tags = item.get(
            "tags",
            []
        )

        if isinstance(tags, str):
            tags = [
                tags
            ]

        # ==========================
        # IDIOMA
        # ==========================

        language = detect_language(
            title,
            tags
        )

        # Excepción Anniversary
        anniversary = (
            is_anniversary(title)
        )

        # Si sabemos que NO es inglés,
        # lo descartamos.
        if (
            language not in [
                "EN",
                "UNKNOWN"
            ]
            and not anniversary
        ):
            continue

        # ==========================
        # PRECIO
        # ==========================

        prices = []

        for variant in variants:

            price = parse_price(
                variant.get("price")
            )

            if price is not None:
                prices.append(price)

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

        available = any(
            variant.get(
                "available",
                False
            )
            for variant in variants
        )

        title_lower = title.lower()

        preorder = (
            "preventa" in title_lower
            or "pré-venda" in title_lower
            or "pre-venda" in title_lower
            or "pre-order" in title_lower
            or "preorder" in title_lower
            or "sob consulta" in title_lower
        )

        if preorder and available:

            stock = "PREORDER"

        elif preorder and not available:

            # Sigue siendo preventa,
            # aunque ahora no permita compra.
            stock = "PREORDER"

        elif available:

            stock = "AVAILABLE"

        else:

            stock = "OUT_OF_STOCK"

        # ==========================
        # FECHA
        # ==========================

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
            "language": (
                "EN"
                if language == "EN"
                else "UNKNOWN"
            )
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