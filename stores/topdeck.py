import re
import time
import requests
from bs4 import BeautifulSoup


STORE_NAME = "TopDeck"

BASE_URL = (
    "https://topdeck.es/"
    "comprar-cartas-coleccionables/"
    "one-piece-card-game/"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}


def parse_price(price_text):

    if not price_text:
        return None

    match = re.search(
        r"(\d+(?:[.,]\d{2}))",
        price_text
    )

    if not match:
        return None

    value = match.group(1)

    # TopDeck usa formato 139.99
    value = value.replace(",", ".")

    try:
        return float(value)

    except ValueError:
        return None


def get_page(page_number):

    if page_number == 1:
        url = BASE_URL
    else:
        url = BASE_URL + f"page/{page_number}/"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    return BeautifulSoup(
        response.text,
        "html.parser"
    )


def find_product_card(anchor):

    """
    Busca hacia arriba desde el título hasta
    encontrar el contenedor correspondiente
    solamente a ese producto.
    """

    for parent in anchor.parents:

        if parent.name not in [
            "div",
            "li",
            "article"
        ]:
            continue

        classes = " ".join(
            parent.get("class", [])
        ).lower()

        product_classes = [
            "product-grid-item",
            "wd-product",
            "product-wrapper",
            "product-miniature",
            "product"
        ]

        if any(
            value in classes
            for value in product_classes
        ):
            return parent

    return None


def get_topdeck_products():

    products = []

    seen_urls = set()

    for page_number in range(1, 10):

        print(
            f"   TopDeck página {page_number}..."
        )

        soup = get_page(page_number)

        if soup is None:

            print(
                f"   ✅ Fin de TopDeck "
                f"en página {page_number - 1}."
            )

            break

        page_products = 0

        # TopDeck utiliza H3 para los títulos
        # de las fichas del catálogo.
        headings = soup.find_all(
            ["h2", "h3", "h4"]
        )

        for heading in headings:

            link = heading.find(
                "a",
                href=True
            )

            if not link:
                continue

            url = link.get("href", "")

            # Las fichas reales de TopDeck utilizan
            # esta ruta.
            if (
                "/tienda-de-cartas-coleccionables/"
                not in url
            ):
                continue

            title = link.get_text(
                " ",
                strip=True
            )

            if not title:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            card = find_product_card(link)

            if card:
                card_text = card.get_text(
                    " ",
                    strip=True
                )
            else:
                # Fallback por si cambia ligeramente
                # el tema de la web.
                card_text = heading.parent.get_text(
                    " ",
                    strip=True
                )

            # ==========================
            # PRECIO
            # ==========================

            price = parse_price(
                card_text
            )

            if price is not None:

                price_text = (
                    f"{price:.2f} €"
                )

            else:

                price_text = "Sin precio"

            # ==========================
            # STOCK
            # ==========================

            lower_text = card_text.lower()

            lower_title = title.lower()

            if (
                "agotado" in lower_text
                or "sin existencias" in lower_text
                or "out of stock" in lower_text
            ):

                stock = "OUT_OF_STOCK"

            elif (
                "preventa" in lower_title
                or "pre-order" in lower_title
                or "preorder" in lower_title
                or "reserva" in lower_title
            ):

                stock = "PREORDER"

            elif "comprar" in lower_text:

                stock = "AVAILABLE"

            else:

                stock = "AVAILABLE"

            products.append({
                "store": STORE_NAME,
                "title": title,
                "price": price,
                "price_text": price_text,
                "stock": stock,
                "url": url,
                "published_at": None
            })

            page_products += 1

        if page_products == 0:

            print(
                "   ⚠️ No se encontraron "
                "más productos."
            )

            break

        time.sleep(0.5)

    return products