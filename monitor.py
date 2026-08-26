from datetime import datetime

from database import (
    load_database,
    save_database
)

from discord_notifier import (
    send_discord_message
)


def format_price(price):

    if price is None:
        return "Sin precio"

    return (
        f"{price:,.2f} €"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def send_new_product(product):

    message = (
        "🚨 **NUEVO PRODUCTO ONE PIECE**\n\n"
        f"🏪 **{product['store']}**\n\n"
        f"📦 **{product['title']}**\n\n"
        f"💰 {format_price(product['price'])}\n"
        f"📊 {product['stock']}\n\n"
        f"🕐 Detectado: "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        f"🔗 {product['url']}"
    )

    send_discord_message(message)


def send_price_change(
    product,
    old_price
):

    new_price = product["price"]

    if (
        old_price is not None
        and new_price is not None
    ):

        if new_price < old_price:
            icon = "📉"
            event = "BAJADA DE PRECIO"

        else:
            icon = "📈"
            event = "SUBIDA DE PRECIO"

    else:
        icon = "💰"
        event = "CAMBIO DE PRECIO"

    message = (
        f"{icon} **{event}**\n\n"
        f"🏪 **{product['store']}**\n\n"
        f"📦 **{product['title']}**\n\n"
        f"Antes: {format_price(old_price)}\n"
        f"Ahora: **{format_price(new_price)}**\n\n"
        f"🕐 Detectado: "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        f"🔗 {product['url']}"
    )

    send_discord_message(message)


def send_stock_change(
    product,
    old_stock
):

    new_stock = product["stock"]

    if (
        old_stock == "OUT_OF_STOCK"
        and new_stock in [
            "AVAILABLE",
            "PREORDER"
        ]
    ):

        title = "🔥 RESTOCK"

    elif (
        old_stock != "OUT_OF_STOCK"
        and new_stock == "OUT_OF_STOCK"
    ):

        title = "🔴 PRODUCTO AGOTADO"

    elif new_stock == "PREORDER":

        title = "🟣 PREVENTA ABIERTA"

    else:

        title = "📦 CAMBIO DE STOCK"

    message = (
        f"{title}\n\n"
        f"🏪 **{product['store']}**\n\n"
        f"📦 **{product['title']}**\n\n"
        f"Antes: {old_stock}\n"
        f"Ahora: **{new_stock}**\n\n"
        f"💰 {format_price(product['price'])}\n\n"
        f"🕐 Detectado: "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        f"🔗 {product['url']}"
    )

    send_discord_message(message)


def process_store(
    store_name,
    products
):

    database = load_database()

    stores = database["stores"]

    # --------------------------------
    # PRIMERA VEZ QUE VEMOS LA TIENDA
    # --------------------------------

    if store_name not in stores:

        stores[store_name] = {
            "initialized": True,
            "products": {}
        }

        for product in products:

            stores[store_name][
                "products"
            ][product["url"]] = product

        save_database(database)

        print(
            f"✅ {store_name}: "
            "base inicial creada."
        )

        print(
            "   No se enviaron alertas "
            "de productos antiguos."
        )

        return

    old_products = stores[
        store_name
    ]["products"]

    # --------------------------------
    # COMPARAR PRODUCTOS
    # --------------------------------

    for product in products:

        url = product["url"]

        # PRODUCTO NUEVO
        if url not in old_products:

            print(
                "🚨 NUEVO:",
                product["title"]
            )

            send_new_product(
                product
            )

            continue

        old = old_products[url]

        # CAMBIO PRECIO

        if (
            old.get("price")
            != product.get("price")
        ):

            print(
                "💰 Precio:",
                product["title"]
            )

            send_price_change(
                product,
                old.get("price")
            )

        # CAMBIO STOCK

        if (
            old.get("stock")
            != product.get("stock")
        ):

            print(
                "📦 Stock:",
                product["title"]
            )

            send_stock_change(
                product,
                old.get("stock")
            )

    # Guardar estado nuevo

    new_state = {}

    for product in products:

        new_state[
            product["url"]
        ] = product

    stores[
        store_name
    ]["products"] = new_state

    save_database(database)