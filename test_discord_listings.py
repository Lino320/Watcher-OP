print('TEST DISCORD LISTINGS FUNCIONANDO')
import time

from discord_notifier import send_discord_message
from filters import filter_products

from stores.arte9 import get_arte9_products
from stores.factory_cards import get_factory_cards_products
from stores.topdeck import get_topdeck_products
from stores.padis import get_padis_products
from stores.micelion import get_micelion_products
from stores.goblintrader import get_goblintrader_products
from stores.jupiter import get_jupiter_products

from stores.eurotcg import get_eurotcg_products
from stores.tcg_family import get_tcg_family_products

from stores.madrid_norte import get_madrid_norte_products
from stores.rare_box import get_rare_box_products
from stores.booster_box import get_booster_box_products
from stores.nova_ohara import get_nova_ohara_products
from stores.todohits import get_todohits_products
from stores.geekkaos import get_geekkaos_products
from stores.ninpo import get_ninpo_products
from stores.three_stones import get_three_stones_products
from stores.scum import get_scum_products


# Para la prueba NO mandamos cientos de productos.
# Mandamos los primeros 8 de cada tienda.
MAX_PRODUCTS_PER_STORE = 8


STORES = [
    ("Arte9", get_arte9_products),
    ("Factory Cards", get_factory_cards_products),
    ("TopDeck", get_topdeck_products),
    ("Padis", get_padis_products),
    ("Micelion Games", get_micelion_products),
    ("GoblinTrader", get_goblintrader_products),
    ("Jupiter Juegos", get_jupiter_products),

    ("EuroTCG", get_eurotcg_products),
    ("TCG Family", get_tcg_family_products),

    ("Madrid Norte TCG", get_madrid_norte_products),
    ("The Rare Box", get_rare_box_products),
    ("The Booster Box", get_booster_box_products),
    ("Nova Ohara Cards", get_nova_ohara_products),
    ("TodoHits", get_todohits_products),
    ("Geekkaos", get_geekkaos_products),
    ("Ninpo Store", get_ninpo_products),
    ("Three Stones Games", get_three_stones_products),
    ("La Tienda Scum", get_scum_products),
]


def stock_text(stock):

    names = {
        "AVAILABLE": "🟢 Disponible",
        "OUT_OF_STOCK": "🔴 Agotado",
        "PREORDER": "🟣 Preventa",
        "UNKNOWN": "⚪ Desconocido",
    }

    return names.get(
        stock,
        stock
    )


def build_store_message(
    store_name,
    products
):

    message = (
        f"🏪 **{store_name}**\n"
        f"📦 Productos válidos: **{len(products)}**\n\n"
    )

    shown_products = products[
        :MAX_PRODUCTS_PER_STORE
    ]

    for number, product in enumerate(
        shown_products,
        start=1
    ):

        message += (
            f"**{number}. {product['title']}**\n"
            f"💰 {product.get('price_text', 'Sin precio')}\n"
            f"📦 {stock_text(product.get('stock'))}\n"
            f"🔗 {product['url']}\n\n"
        )

    if len(products) > MAX_PRODUCTS_PER_STORE:

        remaining = (
            len(products)
            - MAX_PRODUCTS_PER_STORE
        )

        message += (
            f"➕ Y {remaining} productos más."
        )

    return message


def send_chunks(message):

    # Discord permite aproximadamente
    # 2000 caracteres por mensaje.
    MAX_LENGTH = 1800

    while len(message) > MAX_LENGTH:

        cut = message.rfind(
            "\n",
            0,
            MAX_LENGTH
        )

        if cut == -1:
            cut = MAX_LENGTH

        chunk = message[:cut]

        send_discord_message(
            chunk
        )

        message = message[
            cut:
        ].lstrip()

        time.sleep(0.8)

    if message:

        send_discord_message(
            message
        )


def main():

    print()
    print("=" * 80)
    print("🧪 PRUEBA DE LISTADOS → DISCORD")
    print("=" * 80)

    send_discord_message(
        "🧪 **ONEPIECE WATCH — PRUEBA DE TIENDAS**\n"
        "Comenzando comprobación de los scrapers."
    )

    summary = []

    for store_name, scraper in STORES:

        print()
        print(
            f"🏪 Probando {store_name}..."
        )

        try:

            raw_products = scraper()

            products, rejected = (
                filter_products(
                    raw_products
                )
            )

            print(
                f"   Brutos: {len(raw_products)}"
            )

            print(
                f"   Aceptados: {len(products)}"
            )

            print(
                f"   Descartados: {len(rejected)}"
            )

            summary.append(
                (
                    store_name,
                    len(products),
                    "✅"
                )
            )

            if products:

                message = build_store_message(
                    store_name,
                    products
                )

                send_chunks(
                    message
                )

            else:

                send_discord_message(
                    f"⚠️ **{store_name}**\n"
                    "0 productos después del filtro."
                )

        except Exception as error:

            print(
                f"❌ ERROR: {error}"
            )

            summary.append(
                (
                    store_name,
                    0,
                    "❌"
                )
            )

            send_discord_message(
                f"❌ **Error en {store_name}**\n"
                f"`{error}`"
            )

        # Evitamos golpear Discord demasiado rápido.
        time.sleep(1)

    final_message = (
        "📊 **RESUMEN ONEPIECE WATCH**\n\n"
    )

    total = 0

    for store_name, count, status in summary:

        final_message += (
            f"{status} {store_name}: "
            f"**{count}**\n"
        )

        total += count

    final_message += (
        f"\n🔥 Total monitorizado: "
        f"**{total} productos**"
    )

    send_chunks(
        final_message
    )

    print()
    print("=" * 80)
    print("✅ PRUEBA TERMINADA")
    print("=" * 80)


if __name__ == "__main__":
    main()