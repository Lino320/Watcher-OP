import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


STORE_NAME = "EuroTCG"

BASE_URL = "https://eurotcg.com/gb/shop"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}


SEALED_MARKERS = [
    "booster box",
    "booster pack",
    "display",
    "case",
    "starter deck",
    "deck",
    "anniversary",
    "collection",
    "premium",
    "double pack",
    "tin",
    "box",
]


def parse_price(text):

    if not text:
        return None

    match = re.search(
        r"€\s*([\d.,]+)",
        text
    )

    if not match:
        return None

    value = match.group(1)

    # Europeo:
    # 1.499,95
    if "," in value:

        value = value.replace(".", "")
        value = value.replace(",", ".")

    try:
        return float(value)

    except ValueError:
        return None


def is_one_piece(title):

    value = title.lower()

    return (
        "one piece" in value
        or "onepiece" in value
    )


def is_sealed(title):

    value = title.lower()

    return any(
        marker in value
        for marker in SEALED_MARKERS
    )


def get_stock(card, title):

    text = card.get_text(
        " ",
        strip=True
    ).lower()

    title_lower = title.lower()

    if (
        "pre-order" in text
        or "preorder" in text
        or "pre-order" in title_lower
        or "preorder" in title_lower
    ):
        return "PREORDER"

    if (
        "out of stock" in text
        or "sold out" in text
    ):
        return "OUT_OF_STOCK"

    if (
        "add to cart" in text
        or "in stock" in text
        or "shop now" in text
    ):
        return "AVAILABLE"

    return "UNKNOWN"


def get_eurotcg_products():

    print("   EuroTCG leyendo catálogo...")

    response = requests.get(
        BASE_URL,
        headers=HEADERS,
        timeout=25
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    products = []
    seen_urls = set()

    # Buscamos enlaces que llevan a fichas
    # /product/...
    links = soup.select(
        "a[href*='/product/']"
    )

    for link in links:

        title = link.get_text(
            " ",
            strip=True
        )

        url = link.get(
            "href"
        )

        if not title or not url:
            continue

        url = urljoin(
            BASE_URL,
            url
        )

        if url in seen_urls:
            continue

        # Solo One Piece
        if not is_one_piece(title):
            continue

        # Solo sellado / collections
        if not is_sealed(title):
            continue

        seen_urls.add(url)

        # Buscar el contenedor visual
        card = link

        for parent in link.parents:

            if parent.name in [
                "article",
                "div",
                "li"
            ]:

                text = parent.get_text(
                    " ",
                    strip=True
                )

                if (
                    title.lower()
                    in text.lower()
                ):
                    card = parent

                    # No queremos subir demasiado
                    # en el DOM.
                    if len(text) < 1000:
                        break

        card_text = card.get_text(
            " ",
            strip=True
        )

        price = parse_price(
            card_text
        )

        if price is not None:
            price_text = f"{price:.2f} €"
        else:
            price_text = "Sin precio"

        stock = get_stock(
            card,
            title
        )

        products.append({
            "store": STORE_NAME,
            "title": title,
            "price": price,
            "price_text": price_text,
            "stock": stock,
            "url": url,
            "published_at": None,
            "language": "EN"
        })

    return products