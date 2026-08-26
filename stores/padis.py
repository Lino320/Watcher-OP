import re
import time
import requests
from bs4 import BeautifulSoup


STORE_NAME = "Padis"

BASE_URL = "https://www.padis-store.com/341-one-piece"

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

    # Busca cosas tipo:
    # 47,84 €
    # 1.499,95 €
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

    # Intentamos pedir primero los productos
    # más recientes.
    url = (
        BASE_URL
        + "?order=product.date_add.desc"
        + f"&page={page_number}"
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


def get_padis_products():

    products = []

    seen_urls = set()

    previous_page_urls = set()

    for page_number in range(1, 10):

        print(
            f"   Padis página {page_number}..."
        )

        soup = get_page(
            page_number
        )

        if soup is None:
            break

        # PrestaShop
        items = soup.select(
            "article.product-miniature"
        )

        if not items:
            items = soup.select(
                ".product-miniature"
            )

        if not items:

            print(
                f"   ✅ Fin de Padis "
                f"en página {page_number - 1}."
            )

            break

        current_page_urls = set()

        for item in items:

            # ==========================
            # NOMBRE + URL
            # ==========================

            title_element = item.select_one(
                ".product-title a"
            )

            if not title_element:

                title_element = item.select_one(
                    "h2 a"
                )

            if not title_element:
                continue

            title = title_element.get_text(
                " ",
                strip=True
            )

            url = title_element.get(
                "href"
            )

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)
            current_page_urls.add(url)

            # ==========================
            # PRECIO
            # ==========================

            price_element = item.select_one(
                ".product-price-and-shipping .price"
            )

            if not price_element:

                price_element = item.select_one(
                    ".price"
                )

            if price_element:

                price_text = price_element.get_text(
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
            ).lower()

            title_lower = title.lower()

            # Primero preventa
            if (
                "reserva" in title_lower
                or "preventa" in title_lower
                or "pre-order" in title_lower
                or "preorder" in title_lower
            ):

                stock = "PREORDER"

            elif (
                "agotado" in full_text
                or "fuera de stock" in full_text
                or "sin stock" in full_text
                or "no disponible" in full_text
            ):

                stock = "OUT_OF_STOCK"

            else:

                add_button = item.select_one(
                    ".add-to-cart"
                )

                if add_button:

                    disabled = (
                        add_button.has_attr(
                            "disabled"
                        )
                        or
                        add_button.get(
                            "aria-disabled"
                        ) == "true"
                    )

                    if disabled:
                        stock = "OUT_OF_STOCK"
                    else:
                        stock = "AVAILABLE"

                elif (
                    "añadir al carrito"
                    in full_text
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

                # Padis no muestra la fecha real
                # en cada tarjeta.
                "published_at": None
            })

        # Si la siguiente página nos devuelve
        # exactamente lo mismo, detenemos.
        if (
            current_page_urls
            and current_page_urls
            == previous_page_urls
        ):

            break

        previous_page_urls = (
            current_page_urls
        )

        time.sleep(0.5)

    return products