import requests


STORE_NAME = "The Booster Box"

BASE_URL = "https://theboosterbox.es"

PRODUCTS_URL = (
    "https://theboosterbox.es/"
    "collections/one-piece/"
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


def get_booster_box_products():

    print(
        "   The Booster Box leyendo catálogo..."
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

        available = any(
            variant.get(
                "available",
                False
            )
            for variant in variants
        )

        title_lower = title.lower()

        preorder = any(
            marker in title_lower
            for marker in [
                "preventa",
                "pre-order",
                "preorder",
                "reserva",
            ]
        )

        if preorder:
            stock = "PREORDER"

        elif available:
            stock = "AVAILABLE"

        else:
            stock = "OUT_OF_STOCK"

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
            "language": "EN"
        })

    products.sort(
        key=lambda product:
            product.get(
                "published_at"
            ) or "",
        reverse=True
    )

    return products