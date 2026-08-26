import re
import time
import requests
from bs4 import BeautifulSoup


STORE_NAME = "Jupiter Juegos"

BASE_URL = (
    "https://jupiterjuegos.com/"
    "tcg/one-piece/"
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
        r"(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})",
        price_text
    )

    if not match:
        return None

    value = match.group(1)

    value = value.replace(".", "")
    value = value.replace(",", ".")

    try:
        return float(value)

    except ValueError:
        return None


def get_page(page_number):

    # Incluimos:
    # - stock
    # - agotados
    # - preventas
    # Ordenados por más recientes
    params = (
        "?orderby=date"
        "&preventa=no,si"
        "&stock=si,no"
    )

    if page_number == 1:

        url = (
            BASE_URL
            + params
        )

    else:

        url = (
            BASE_URL
            + f"pagina/{page_number}/"
            + params
        )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=25
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    return BeautifulSoup(
        response.text,
        "html.parser"
    )


def find_product_card(anchor):

    for parent in anchor.parents:

        if parent.name not in [
            "div",
            "li",
            "article"
        ]:
            continue

        classes = " ".join(
            parent.get(
                "class",
                []
            )
        ).lower()

        if any(
            value in classes
            for value in [
                "product",
                "item",
                "card",
                "grid",
                "producto"
            ]
        ):

            # Evitamos coger contenedores enormes.
            product_links = parent.select(
                "a[href*='/producto/']"
            )

            if len(product_links) <= 4:
                return parent

    return anchor.parent


def get_price(card):

    # Primero intentamos elementos de precio
    selectors = [
        ".price",
        ".amount",
        ".woocommerce-Price-amount",
        "[itemprop='price']",
    ]

    for selector in selectors:

        elements = card.select(
            selector
        )

        for element in elements:

            text = element.get_text(
                " ",
                strip=True
            )

            price = parse_price(text)

            if price is not None:

                return (
                    price,
                    f"{price:.2f} €"
                )

    # Fallback: buscar en todo el texto
    text = card.get_text(
        " ",
        strip=True
    )

    price = parse_price(text)

    if price is not None:

        return (
            price,
            f"{price:.2f} €"
        )

    return None, "Sin precio"


def get_stock(card, title):

    text = card.get_text(
        " ",
        strip=True
    ).lower()

    title_lower = title.lower()

    # PREVENTA tiene prioridad
    if (
        "preventa" in text
        or "preventa" in title_lower
        or "pre-order" in title_lower
        or "preorder" in title_lower
        or "reserva" in title_lower
    ):

        return "PREORDER"

    if (
        "sin stock" in text
        or "agotado" in text
        or "sin existencias" in text
    ):

        return "OUT_OF_STOCK"

    if (
        "comprar" in text
        or "añadir al carrito" in text
    ):

        return "AVAILABLE"

    # "Más info" aparece en algunos productos
    # futuros sin precio/venta activa.
    return "UNKNOWN"


def get_jupiter_products():

    products = []

    seen_urls = set()

    for page_number in range(1, 10):

        print(
            f"   Jupiter página {page_number}..."
        )

        soup = get_page(page_number)

        if soup is None:

            print(
                f"   ✅ Fin de Jupiter "
                f"en página {page_number - 1}."
            )

            break

        product_links = soup.select(
            "a[href*='/producto/']"
        )

        page_count = 0

        for link in product_links:

            url = link.get("href")

            if not url:
                continue

            if url in seen_urls:
                continue

            title = link.get_text(
                " ",
                strip=True
            )

            if not title:
                continue

            if len(title) < 4:
                continue

            seen_urls.add(url)

            card = find_product_card(
                link
            )

            price, price_text = (
                get_price(card)
            )

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
                "published_at": None
            })

            page_count += 1

        if page_count == 0:

            print(
                f"   ✅ Fin de Jupiter "
                f"en página {page_number - 1}."
            )

            break

        time.sleep(0.5)

    return products