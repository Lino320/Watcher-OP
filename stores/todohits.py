import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


STORE_NAME = "TodoHits"

BASE_URL = "https://todohits.com"
CATEGORY_URL = "https://todohits.com/collections/one-piece"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}


SEALED_MARKERS = [
    "booster box",
    "booster display",
    "sobre",
    "booster pack",
    "starter deck",
    "double pack",
    "illustration box",
    "gift box",
    "gift collection",
    "premium collection",
    "premium card collection",
    "anniversary",
    "tin pack",
    "case",
    "display",
]


EXCLUDED_MARKERS = [
    "carta metalizada",
    "carta metalica",
    "promo luffy",
    "binder",
    "álbum",
    "album",
    "caja acrílica",
    "caja acrilica",
    "playmat",
    "tapete",
    "sleeves",
    "fundas",
]


def parse_price(text):

    if not text:
        return None

    matches = re.findall(
        r"€\s*(\d+(?:[.,]\d{2}))|"
        r"(\d+(?:[.,]\d{2}))\s*€",
        text
    )

    values = []

    for first, second in matches:

        value = first or second

        if value:
            try:
                values.append(
                    float(
                        value
                        .replace(".", "")
                        .replace(",", ".")
                    )
                )
            except ValueError:
                pass

    if not values:
        return None

    # Si hay precio anterior + rebajado,
    # normalmente el último es el actual.
    return values[-1]


def is_anniversary(title):

    text = title.lower()

    return any(
        marker in text
        for marker in [
            "anniversary",
            "aniversario",
        ]
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

    if any(
        marker in text
        for marker in [
            "inglés",
            "ingles",
            "english",
            "[eng]",
            "(eng)",
        ]
    ):
        return "EN"

    if any(
        marker in text
        for marker in [
            "japonés",
            "japones",
            "japanese",
            "[jp]",
            "(jp)",
        ]
    ):
        return "JP"

    return "UNKNOWN"


def detect_stock(text):

    text = str(text or "").lower()

    if any(
        marker in text
        for marker in [
            "preventa",
            "pre-order",
            "preorder",
            "reserva",
            "próximamente",
            "proximamente",
        ]
    ):
        return "PREORDER"

    if any(
        marker in text
        for marker in [
            "agotado",
            "avísame",
            "avisame",
            "sin stock",
            "out of stock",
        ]
    ):
        return "OUT_OF_STOCK"

    if any(
        marker in text
        for marker in [
            "añadir al carrito",
            "añadir",
            "add to cart",
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
            len(text) < 3000
            and (
                "€" in text
                or "agotado" in text.lower()
                or "avísame" in text.lower()
                or "añadir" in text.lower()
            )
        ):
            return current

    return link.parent


def get_title(link, card):

    # Texto del enlace
    title = link.get_text(
        " ",
        strip=True
    )

    if (
        title
        and "one piece" in title.lower()
    ):
        return title

    # ALT de la imagen
    image = link.find("img")

    if image:

        alt = image.get(
            "alt",
            ""
        ).strip()

        if (
            alt
            and "one piece" in alt.lower()
        ):
            return alt

    # Heading del producto
    if card:

        heading = card.find(
            [
                "h2",
                "h3",
                "h4",
                "h5",
            ]
        )

        if heading:

            title = heading.get_text(
                " ",
                strip=True
            )

            if "one piece" in title.lower():
                return title

    return None


def get_todohits_products():

    print(
        "   TodoHits leyendo catálogo..."
    )

    products_by_url = {}

    for page_number in range(1, 10):

        url = (
            f"{CATEGORY_URL}"
            f"?page={page_number}"
            f"&sort_by=created-descending"
        )

        print(
            f"   TodoHits página {page_number}..."
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

        links = soup.select(
            "a[href*='/products/']"
        )

        page_urls = set()

        for link in links:

            href = link.get("href")

            if not href:
                continue

            product_url = urljoin(
                BASE_URL,
                href.split("?")[0]
            )

            page_urls.add(product_url)

            card = find_card(link)

            title = get_title(
                link,
                card
            )

            if not title:
                continue

            if (
                "one piece"
                not in title.lower()
            ):
                continue

            anniversary = is_anniversary(
                title
            )

            # Solo producto sellado
            if (
                not is_sealed(title)
                and not anniversary
            ):
                continue

            language = detect_language(
                title
            )

            # Inglés únicamente,
            # Anniversary siempre entra.
            if (
                language != "EN"
                and not anniversary
            ):
                continue

            card_text = (
                card.get_text(
                    " ",
                    strip=True
                )
                if card
                else title
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

        print(
            "      URLs encontradas:",
            len(page_urls)
        )

        # Si la página ya no contiene
        # fichas de producto, terminamos.
        if not page_urls:
            break

    return list(
        products_by_url.values()
    )