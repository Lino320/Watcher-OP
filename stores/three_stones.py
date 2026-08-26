import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


STORE_NAME = "Three Stones Games"

BASE_URL = "https://threestonesgames.com"

CATEGORY_URL = (
    "https://threestonesgames.com/"
    "collections/one-piece-tcg"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}


SEALED_MARKERS = [
    "booster display",
    "booster box",
    "booster pack",
    "starter deck",
    "double pack",
    "tin pack",
    "premium booster",
    "premium collection",
    "card collection",
    "deck set",
    "anniversary",
    "case",
    "display 24 sobres",
    "pack completo st-",
]


EXCLUDED_MARKERS = [
    "torneo",
    "liga ",
    "beginners deck party",
    "funko",
    "dobble",
    "adventure island",
    "desafío recuerda",
    "desafio recuerda",
]


def parse_price(text):

    if not text:
        return None

    matches = re.findall(
        r"(\d+(?:[.,]\d{2}))\s*€",
        text
    )

    if not matches:
        return None

    # Precio actual suele ser el primero.
    value = matches[0]

    value = (
        value
        .replace(".", "")
        .replace(",", ".")
    )

    try:
        return float(value)

    except ValueError:
        return None


def is_anniversary(title):

    text = title.lower()

    return (
        "anniversary" in text
        or "aniversario" in text
    )


def is_sealed(title):

    text = title.lower()

    if any(
        marker in text
        for marker in EXCLUDED_MARKERS
    ):
        return False

    return any(
        marker in text
        for marker in SEALED_MARKERS
    )


def detect_language(title):

    text = title.lower()

    # Three Stones identifica las
    # importaciones japonesas en el título.
    if any(
        marker in text
        for marker in [
            "japanese",
            "japonés",
            "japones",
            "[jp]",
            "(jp)",
        ]
    ):
        return "JP"

    # Sus productos occidentales OP/ST/etc.
    # están descritos en ficha como Inglés.
    if (
        "one piece tcg" in text
        or "one piece card game" in text
    ):
        return "EN"

    return "UNKNOWN"


def detect_stock(text):

    value = str(
        text or ""
    ).lower()

    if any(
        marker in value
        for marker in [
            "preventa",
            "pre-order",
            "preorder",
            "reserva",
        ]
    ):
        return "PREORDER"

    if any(
        marker in value
        for marker in [
            "agotado",
            "avísame",
            "avisame",
            "sin stock",
        ]
    ):
        return "OUT_OF_STOCK"

    if any(
        marker in value
        for marker in [
            "carrito",
            "agregar al carrito",
            "solo quedan",
        ]
    ):
        return "AVAILABLE"

    return "UNKNOWN"


def find_card(link):

    current = link

    for _ in range(10):

        current = current.parent

        if current is None:
            break

        text = current.get_text(
            " ",
            strip=True
        )

        if (
            "€" in text
            and len(text) < 4000
        ):
            return current

    return link.parent


def extract_title(link, card):

    # Texto propio del enlace
    title = link.get_text(
        " ",
        strip=True
    )

    if title:
        return title

    # Heading del card
    heading = card.find(
        [
            "h2",
            "h3",
            "h4",
            "h5",
        ]
    )

    if heading:
        return heading.get_text(
            " ",
            strip=True
        )

    # ALT de imagen
    image = link.find("img")

    if image:
        return image.get(
            "alt",
            ""
        ).strip()

    return None


def get_three_stones_products():

    print(
        "   Three Stones Games leyendo catálogo..."
    )

    response = requests.get(
        CATEGORY_URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    links = soup.select(
        "a[href*='/products/']"
    )

    print(
        "      Enlaces encontrados:",
        len(links)
    )

    products_by_url = {}

    for link in links:

        href = link.get(
            "href"
        )

        if not href:
            continue

        product_url = urljoin(
            BASE_URL,
            href.split("?")[0]
        )

        card = find_card(
            link
        )

        if not card:
            continue

        title = extract_title(
            link,
            card
        )

        if not title:
            continue

        title_lower = title.lower()

        # Solo One Piece
        if (
            "one piece"
            not in title_lower
        ):
            continue

        # Solo producto TCG sellado
        anniversary = is_anniversary(
            title
        )

        if (
            not is_sealed(title)
            and not anniversary
        ):
            continue

        language = detect_language(
            title
        )

        # Inglés únicamente.
        # Anniversary entra siempre.
        if (
            language != "EN"
            and not anniversary
        ):
            continue

        card_text = card.get_text(
            " ",
            strip=True
        )

        price = parse_price(
            card_text
        )

        if price is None:
            price_text = "Sin precio"
        else:
            price_text = (
                f"{price:.2f} €"
            )

        stock = detect_stock(
            card_text
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
            "published_at": None,
            "language": (
                "EN"
                if language == "EN"
                else "UNKNOWN"
            )
        }

    return list(
        products_by_url.values()
    )