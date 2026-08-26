from datetime import datetime


def format_date(date_value):

    if not date_value:
        return "Fecha desconocida"

    try:
        date = datetime.fromisoformat(
            date_value.replace("Z", "+00:00")
        )

        return date.strftime(
            "%d/%m/%Y %H:%M"
        )

    except Exception:
        return date_value


def format_stock(stock):

    stock_names = {
        "AVAILABLE": "🟢 DISPONIBLE",
        "OUT_OF_STOCK": "🔴 AGOTADO",
        "PREORDER": "🟣 PREVENTA"
    }

    return stock_names.get(
        stock,
        stock
    )


def print_products(
    store_name,
    products
):

    print()
    print("=" * 90)
    print(
        f"🏪 {store_name.upper()}"
    )
    print(
        f"📦 {len(products)} PRODUCTOS ONE PIECE"
    )
    print("=" * 90)

    for number, product in enumerate(
        products,
        start=1
    ):

        print()
        print(
            f"#{number:02d}  {product['title']}"
        )

        print(
            f"     💰 Precio: "
            f"{product['price_text']}"
        )

        print(
            f"     📦 Estado: "
            f"{format_stock(product['stock'])}"
        )

        print(
            f"     🕐 Publicado: "
            f"{format_date(product.get('published_at'))}"
        )

        print(
            f"     🔗 {product['url']}"
        )

        print("-" * 90)