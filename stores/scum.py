import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


STORE_NAME = "La Tienda Scum"

BASE_URL = "https://latiendascum.com"

CATEGORY_URL = (
    "https://latiendascum.com/"
    "1854-one-piece-tcg"
)

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
    "display",
    "case",
    "starter deck",
    "double pack",
    "double pack set",
    "collection",
    "premium card collection",
    "premium collection",
    "devil fruits collection",
    "gift collection",
    "gift box",
    "illustration box",
    "tin pack",
    "anniversary",
    "special set",
    "deck set",
    "booster pack",
]


EXCLUDED_MARKERS = [
    "fundas",
    "sleeves",
    "playmat",
    "tapete",
    "binder",
    "album",
    "álbum",
    "deck box",
    "torneo",
    "presentación",
    "presentacion",
]


def parse_price(text):

    if not text:
        return None

    matches = re.findall(
        r"(\d+(?:\.\d{3})*(?:,\d{2}))\s*€",
        text
    )

    if not matches:
        return None

    # En rebajas aparece:
    # 1.555,20 € 1.728,00 €
    #
    # El primero es el precio actual.
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

    text = (
        " "
        + title.lower()
        + " "
    )

    # ==========================
    # INGLÉS
    # ==========================

    if any(
        marker in text
        for marker in [
            " - en ",
            " en ",
            " ing ",
            " inglés",
            " ingles",
            " english",
            "[eng]",
            "(eng)",
        ]
    ):
        return "EN"

    # ==========================
    # JAPONÉS
    # ==========================

    if any(
        marker in text
        for marker in [
            " jp ",
            " japonés",
            " japones",
            " japanese",
            "[jp]",
            "(jp)",
        ]
    ):
        return "JP"

    return "UNKNOWN"


def is_western_one_piece_release(title):

    """
    La Tienda Scum publica muchos productos
    Bandai occidentales simplemente como:

    OP18 Case
    EB05 Case
    OP16 Display

    sin escribir EN en el título.

    Si no está marcado como JP y usa códigos
    occidentales estándar, lo aceptamos como EN.
    """

    text = title.lower()

    patterns = [
        r"\bop-?\d{2}\b",
        r"\beb-?\d{2}\b",
        r"\bprb-?\d{2}\b",
        r"\bst-?\d{2}\b",
        r"\bdp-?\d{2}\b",
    ]

    return any(
        re.search(pattern, text)
        for pattern in patterns
    )


def detect_preorder(title, text):

    combined = (
        title
        + " "
        + str(text or "")
    ).lower()

    # Scum usa títulos como:
    # OP19 Case R 05/03
    # EB05 Case R 30/10
    if re.search(
        r"\br\s+\d{1,2}/\d{1,2}\b",
        combined
    ):
        return True

    return any(
        marker in combined
        for marker in [
            "reserva",
            "preventa",
            "pre-order",
            "preorder",
            "próximo lanzamiento",
            "proximo lanzamiento",
        ]
    )


def detect_stock(title, text):

    value = str(
        text or ""
    ).lower()

    preorder = detect_preorder(
        title,
        value
    )

    if preorder:
        return "PREORDER"

    if any(
        marker in value
        for marker in [
            "fuera de stock",
            "agotado",
            "sin stock",
            "no disponible",
        ]
    ):
        return "OUT_OF_STOCK"

    if any(
        marker in value
        for marker in [
            "añadir al carrito",
            "en stock",
        ]
    ):
        return "AVAILABLE"

    return "UNKNOWN"


def get_scum_products():

    print(
        "   La Tienda Scum leyendo catálogo..."
    )

    products_by_url = {}

    # Actualmente hay 3 páginas.
    # Dejamos margen por si aumenta.
    for page_number in range(
        1,
        10
    ):

        url = (
            CATEGORY_URL
            if page_number == 1
            else f"{CATEGORY_URL}?page={page_number}"
        )

        print(
            f"   Scum página {page_number}..."
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
            ".product-miniature"
        )

        print(
            "      Productos HTML:",
            len(cards)
        )

        if not cards:
            break

        for card in cards:

            title_element = card.select_one(
                ".product-title a"
            )

            if not title_element:

                title_element = card.find(
                    "h2"
                )

            if not title_element:
                continue

            title = title_element.get_text(
                " ",
                strip=True
            )

            if not title:
                continue

            # ==========================
            # SOLO PRODUCTO SELLADO
            # ==========================

            anniversary = is_anniversary(
                title
            )

            if (
                not is_sealed(title)
                and not anniversary
            ):
                continue

            # ==========================
            # IDIOMA
            # ==========================

            language = detect_language(
                title
            )

            if language == "JP" and not anniversary:
                continue

            if language == "UNKNOWN":

                if is_western_one_piece_release(
                    title
                ):
                    language = "EN"

                elif anniversary:
                    language = "UNKNOWN"

                else:
                    # Si no podemos confirmar
                    # que sea inglés, no entra.
                    continue

            # ==========================
            # URL
            # ==========================

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

            product_url = urljoin(
                BASE_URL,
                link.get(
                    "href",
                    ""
                )
            )

            if not product_url:
                continue

            # ==========================
            # TEXTO DEL CARD
            # ==========================

            card_text = card.get_text(
                " ",
                strip=True
            )

            # ==========================
            # PRECIO
            # ==========================

            price_element = card.select_one(
                ".price"
            )

            if price_element:

                price_source = (
                    price_element.get_text(
                        " ",
                        strip=True
                    )
                )

            else:

                price_source = card_text

            price = parse_price(
                price_source
            )

            if price is None:

                price_text = "Sin precio"

            else:

                price_text = (
                    f"{price:.2f} €"
                )

            # ==========================
            # STOCK / PREVENTA
            # ==========================

            stock = detect_stock(
                title,
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