import re
import time
import requests
from bs4 import BeautifulSoup


BASE_URL = (
    "https://arte9.com/"
    "categoria-producto/juegos_de_cartas/one-piece/"
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

    text = (
        price_text
        .replace("\xa0", "")
        .replace("€", "")
        .replace("EUR", "")
        .replace(" ", "")
    )

    if "," in text:
        text = text.replace(".", "")
        text = text.replace(",", ".")

    text = re.sub(
        r"[^0-9.]",
        "",
        text
    )

    try:
        return float(text)

    except ValueError:
        return None


def get_page(page_number):

    if page_number == 1:
        url = BASE_URL + "?orderby=date"
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

    # IMPORTANTE:
    # 404 significa que ya no existen más páginas.
    if response.status_code == 404:
        return None

    response.raise_for_status()

    return BeautifulSoup(
        response.text,
        "html.parser"
    )


def get_arte9_products():

    products = []

    for page_number in range(1, 11):

        print(
            f"   Arte9 página {page_number}..."
        )

        soup = get_page(
            page_number
        )

        # Si devuelve None hemos llegado
        # al final del catálogo.
        if soup is None:

            print(
                f"   ✅ Fin del catálogo "
                f"en página {page_number - 1}."
            )

            break

        items = soup.select(
            "li.product"
        )

        if not items:

            print(
                f"   ✅ No hay más productos."
            )

            break

        for item in items:

            title_element = item.select_one(
                ".woocommerce-loop-product__title"
            )

            if not title_element:
                continue

            title = title_element.get_text(
                " ",
                strip=True
            )

            link_element = item.select_one(
                "a.woocommerce-LoopProduct-link"
            )

            if not link_element:
                link_element = item.find(
                    "a",
                    href=True
                )

            if not link_element:
                continue

            url = link_element.get(
                "href"
            )

            price_elements = item.select(
                ".woocommerce-Price-amount.amount"
            )

            if price_elements:

                price_text = (
                    price_elements[-1]
                    .get_text(
                        " ",
                        strip=True
                    )
                )

                price = parse_price(
                    price_text
                )

            else:

                price_text = "Sin precio"
                price = None

            classes = item.get(
                "class",
                []
            )

            text = item.get_text(
                " ",
                strip=True
            ).lower()

            if (
                "outofstock" in classes
                or "agotado" in text
            ):

                stock = "OUT_OF_STOCK"

            elif (
                "preventa" in text
                or "reserva" in text
            ):

                stock = "PREORDER"

            else:

                stock = "AVAILABLE"

            products.append({
                "store": "Arte9",
                "title": title,
                "price": price,
                "price_text": price_text,
                "stock": stock,
                "url": url
            })

        time.sleep(0.5)

    # Eliminar URLs duplicadas
    unique_products = {}

    for product in products:

        unique_products[
            product["url"]
        ] = product

    return list(
        unique_products.values()
    )