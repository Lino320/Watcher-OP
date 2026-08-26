import requests


STORE_NAME = "Factory Cards"

BASE_URL = "https://factorycardstcg.com"

PRODUCTS_URL = (
    "https://factorycardstcg.com/"
    "collections/one-piece-tcg/products.json?limit=250"
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


def get_factory_cards_products():

    print("   Factory Cards leyendo catálogo...")

    response = requests.get(
        PRODUCTS_URL,
        headers=HEADERS,
        timeout=20
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
            price = min(prices)
            price_text = f"{price:.2f} €"
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

        tags = item.get(
            "tags",
            []
        )

        if isinstance(tags, str):
            tags_text = tags.lower()
        else:
            tags_text = " ".join(
                str(tag)
                for tag in tags
            ).lower()

        preorder = (
            "preventa" in title_lower
            or "pre-order" in title_lower
            or "preorder" in title_lower
            or "reserva" in title_lower
            or "preventa" in tags_text
            or "preorder" in tags_text
            or "reserva" in tags_text
        )

        if not available:
            stock = "OUT_OF_STOCK"

        elif preorder:
            stock = "PREORDER"

        else:
            stock = "AVAILABLE"

        # ==========================
        # PRODUCTO FINAL
        # ==========================

        products.append({
    "store": STORE_NAME,
    "title": title,
    "price": price,
    "price_text": price_text,
    "stock": stock,
    "url": url,
    "published_at": item.get("published_at")
        })
        products.sort(
    key=lambda product: product.get("published_at") or "",
    reverse=True
)

    return products