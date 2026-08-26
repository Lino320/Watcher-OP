import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


STORE_NAME = "The Rare Box"

BASE_URL = "https://www.therarebox.es"

CATEGORY_URL = (
    "https://www.therarebox.es/"
    "tienda/one-piece-card-game"
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

    # Si hay precio antiguo y rebajado:
    # 21,90 € 19,90 €
    # nos quedamos con el último.
    value = matches[-1]

    value = (
        value
        .replace(".", "")
        .replace(",", ".")
    )

    try:
        return float(value)

    except ValueError:
        return None


def detect_language(text):

    text = (
        " "
        + str(text or "").lower()
        + " "
    )

    # English
    if any(
        marker in text
        for marker in [
            " en ",
            " inglés",
            " ingles",
            " english",
            "english ver",
            "(eng)",
            "[eng]",
        ]
    ):
        return "EN"

    # Japanese
    if any(
        marker in text
        for marker in [
            " jp ",
            " japonés",
            " japones",
            " japanese",
            "(jp)",
            "[jp]",
        ]
    ):
        return "JP"

    # Otros
    if any(
        marker in text
        for marker in [
            " kr ",
            " korean",
            " coreano",
            " chinese",
            " chino",
            " german",
            " alemán",
            " frances",
            " francés",
        ]
    ):
        return "OTHER"

    return "UNKNOWN"


def is_anniversary(title):

    text = title.lower()

    return any(
        marker in text
        for marker in [
            "anniversary",
            "aniversario",
            "anniversary set",
            "anniversary collection",
        ]
    )


def detect_stock(text):

    text = str(
        text or ""
    ).lower()

    if any(
        marker in text
        for marker in [
            "próximo lanzamiento",
            "proximo lanzamiento",
            "próximamente",
            "proximamente",
            "preventa",
            "pre-venta",
            "preorder",
            "pre-order",
            "reserva",
        ]
    ):
        return "PREORDER"

    if any(
        marker in text
        for marker in [
            "agotado temporalmente",
            "agotado",
            "sin stock",
            "out of stock",
        ]
    ):
        return "OUT_OF_STOCK"

    return "AVAILABLE"


def find_product_card(link):

    current = link

    for _ in range(10):

        current = current.parent

        if current is None:
            break

        text = current.get_text(
            " ",
            strip=True
        )

        # Buscamos un contenedor pequeño
        # que tenga producto + precio.
        if (
            "€" in text
            and "one piece" in text.lower()
            and len(text) < 4000
        ):
            return current

    return link.parent


def extract_title(
    link,
    card
):

    # 1. Buscar heading dentro del card
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

        if (
            title
            and "one piece" in title.lower()
        ):
            return title

    # 2. Texto del propio enlace
    title = link.get_text(
        " ",
        strip=True
    )

    if (
        title
        and "one piece" in title.lower()
    ):
        return title

    # 3. ALT de la imagen
    image = link.find(
        "img"
    )

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

    # 4. Buscar cualquier texto dentro del card
    headings = card.find_all(
        [
            "h2",
            "h3",
            "h4",
            "h5",
            "p",
        ]
    )

    for element in headings:

        text = element.get_text(
            " ",
            strip=True
        )

        if (
            "one piece" in text.lower()
            and len(text) < 300
        ):
            return text

    return None


def get_page(page_number):

    if page_number == 1:

        url = CATEGORY_URL

    else:

        url = (
            f"{CATEGORY_URL}"
            f"?page={page_number}"
        )

    print(
        f"   The Rare Box página "
        f"{page_number}..."
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=25
    )

    response.raise_for_status()

    return BeautifulSoup(
        response.text,
        "html.parser"
    )


def get_rare_box_products():

    print(
        "   The Rare Box leyendo catálogo..."
    )

    products = []

    seen_urls = set()

    for page_number in range(
        1,
        10
    ):

        soup = get_page(
            page_number
        )

        # CAMBIO IMPORTANTE:
        # buscamos directamente fichas
        # /producto/...
        links = soup.select(
            "a[href*='/producto/']"
        )

        print(
            f"      Enlaces de producto encontrados: "
            f"{len(links)}"
        )

        new_products_this_page = 0

        for link in links:

            href = link.get(
                "href"
            )

            if not href:
                continue

            url = urljoin(
                BASE_URL,
                href
            )

            # Duplicados por imagen/título/botón
            if url in seen_urls:
                continue

            card = find_product_card(
                link
            )

            if card is None:
                continue

            title = extract_title(
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

            card_text = card.get_text(
                " ",
                strip=True
            )

            language = detect_language(
                title
                + " "
                + card_text
            )

            anniversary = is_anniversary(
                title
            )

            # ==========================
            # ENGLISH ONLY
            # Anniversary exception
            # ==========================

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

            products.append({
                "store": STORE_NAME,
                "title": title,
                "price": price,
                "price_text": price_text,
                "stock": stock,
                "url": url,
                "published_at": None,
                "language": (
                    "EN"
                    if language == "EN"
                    else "UNKNOWN"
                )
            })

            seen_urls.add(
                url
            )

            new_products_this_page += 1

        # Si ya no existen enlaces de producto,
        # terminamos paginación.
        if len(links) == 0:
            break

        # Página 2 actualmente es casi toda JP.
        # No usamos new_products_this_page
        # para cortar porque podría haber
        # productos EN en páginas posteriores.

    return products