import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


STORE_NAME = "Geekkaos"

BASE_URL = "https://geekkaos.com"

CATEGORY_URL = (
    "https://geekkaos.com/"
    "26-one-piece-tcg"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}


def parse_price(text):

    if not text:
        return None

    matches = re.findall(
        r"(\d+(?:[.,]\d{2}))\s*€",
        text
    )

    if not matches:
        return None

    # Normalmente:
    # precio actual + precio anterior.
    # Nos quedamos con el primero.
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


def is_anniversary(text):

    value = str(
        text or ""
    ).lower()

    return any(
        marker in value
        for marker in [
            "anniversary",
            "aniversario",
        ]
    )


def detect_language(text):

    value = str(
        text or ""
    ).lower()

    if any(
        marker in value
        for marker in [
            "idioma: ingles",
            "idioma: inglés",
            "english",
            "[eng]",
            "(eng)",
        ]
    ):
        return "EN"

    if any(
        marker in value
        for marker in [
            "idioma: japones",
            "idioma: japonés",
            "japanese",
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


def detect_stock(text):

    value = str(
        text or ""
    ).lower()

    if any(
        marker in value
        for marker in [
            "artículo en reserva",
            "articulo en reserva",
            "producto en reserva",
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
            "no hay stock",
            "agotado",
            "sin stock",
            "no disponible",
        ]
    ):
        return "OUT_OF_STOCK"

    if any(
        marker in value
        for marker in [
            "añadir a la cesta",
            "añadir al carrito",
            "en stock",
        ]
    ):
        return "AVAILABLE"

    return "UNKNOWN"


def get_product_card(link):

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
            and len(text) < 5000
        ):
            return current

    return link.parent


def extract_title(link, card):

    # Título típico PrestaShop
    title_element = card.select_one(
        ".product-title"
    )

    if title_element:

        title = title_element.get_text(
            " ",
            strip=True
        )

        if title:
            return title

    # Heading
    heading = card.find(
        [
            "h2",
            "h3",
            "h4",
        ]
    )

    if heading:

        title = heading.get_text(
            " ",
            strip=True
        )

        if title:
            return title

    # Texto del enlace
    title = link.get_text(
        " ",
        strip=True
    )

    if title:
        return title

    # ALT imagen
    image = link.find("img")

    if image:

        return image.get(
            "alt",
            ""
        ).strip()

    return None


def get_geekkaos_products():

    print(
        "   Geekkaos leyendo catálogo..."
    )

    products_by_url = {}

    for page_number in range(
        1,
        10
    ):

        if page_number == 1:

            url = CATEGORY_URL

        else:

            url = (
                f"{CATEGORY_URL}"
                f"?page={page_number}"
            )

        print(
            f"   Geekkaos página "
            f"{page_number}..."
        )

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # PrestaShop
        cards = soup.select(
            "article.product-miniature, "
            ".js-product-miniature"
        )

        print(
            "      Cards encontradas:",
            len(cards)
        )

        if not cards:
            break

        new_urls = 0

        for card in cards:

            link = card.select_one(
                ".product-title a[href]"
            )

            if not link:

                link = card.find(
                    "a",
                    href=True
                )

            if not link:
                continue

            href = link.get(
                "href"
            )

            if not href:
                continue

            product_url = urljoin(
                BASE_URL,
                href
            )

            title = extract_title(
                link,
                card
            )

            if not title:
                continue

            card_text = card.get_text(
                " ",
                strip=True
            )

            combined_text = (
                title
                + " "
                + card_text
            )

            # Solo One Piece TCG
            if (
                "one piece"
                not in combined_text.lower()
            ):
                continue

            language = detect_language(
                combined_text
            )

            anniversary = is_anniversary(
                combined_text
            )

            # Inglés únicamente.
            # Anniversary entra siempre.
            if (
                language != "EN"
                and not anniversary
            ):
                continue

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

            if (
                product_url
                not in products_by_url
            ):
                new_urls += 1

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

        # Si una página no aporta nada nuevo,
        # terminamos.
        if new_urls == 0:
            break

    return list(
        products_by_url.values()
    )