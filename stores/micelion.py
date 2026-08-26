import re
import time
import requests
from bs4 import BeautifulSoup


STORE_NAME = "Micelion Games"

BASE_URL = (
    "https://miceliongames.com/"
    "product-category/juegos-tcg/one-piece/"
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

    # Ejemplos:
    # 169,95 €
    # 1.560,00 €
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

    if page_number == 1:

        url = (
            BASE_URL
            + "?orderby=date"
        )

    else:

        url = (
            BASE_URL
            + f"page/{page_number}/"
            + "?orderby=date"
        )

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


def get_micelion_products():

    products = []

    seen_urls = set()

    for page_number in range(1, 10):

        print(
            f"   Micelion página {page_number}..."
        )

        soup = get_page(
            page_number
        )

        if soup is None:

            print(
                f"   ✅ Fin de Micelion "
                f"en página {page_number - 1}."
            )

            break

        # WooCommerce
        items = soup.select(
            "li.product"
        )

        if not items:

            items = soup.select(
                ".product"
            )

        if not items:

            print(
                "   ⚠️ No se encontraron "
                "más productos."
            )

            break

        page_count = 0

        for item in items:

            # ==========================
            # NOMBRE
            # ==========================

            title_element = item.select_one(
                ".woocommerce-loop-product__title"
            )

            if not title_element:

                title_element = item.select_one(
                    "h2"
                )

            if not title_element:

                title_element = item.select_one(
                    "h3"
                )

            if not title_element:
                continue

            title = title_element.get_text(
                " ",
                strip=True
            )

            # ==========================
            # URL
            # ==========================

            link = item.select_one(
                "a.woocommerce-LoopProduct-link"
            )

            if not link:

                link = item.find(
                    "a",
                    href=True
                )

            if not link:
                continue

            url = link.get(
                "href"
            )

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            # ==========================
            # PRECIO
            # ==========================

            price_elements = item.select(
                ".woocommerce-Price-amount.amount"
            )

            if price_elements:

                # Si hay precio anterior +
                # descuento, usamos el último.
                price_text = price_elements[-1].get_text(
                    " ",
                    strip=True
                )

                price = parse_price(
                    price_text
                )

            else:

                price_text = "Sin precio"
                price = None

            # ==========================
            # STOCK
            # ==========================

            full_text = item.get_text(
                " ",
                strip=True
            )

            lower_text = full_text.lower()
            lower_title = title.lower()

            classes = [
                str(value).lower()
                for value in item.get(
                    "class",
                    []
                )
            ]

            # Primero detectamos preventa
            if (
                "pre-compra" in lower_text
                or "precompra" in lower_text
                or "preventa" in lower_title
                or "pre-order" in lower_title
                or "preorder" in lower_title
                or "reserva" in lower_title
            ):

                stock = "PREORDER"

            elif (
                "outofstock" in classes
                or "sin existencias" in lower_text
                or "agotado" in lower_text
            ):

                stock = "OUT_OF_STOCK"

            elif (
                "hay existencias" in lower_text
                or "añadir al carrito" in lower_text
            ):

                stock = "AVAILABLE"

            else:

                stock = "UNKNOWN"

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
            break

        time.sleep(0.5)

    return products