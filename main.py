import time
from datetime import datetime

# ==========================================
# STORES
# ==========================================

from stores.arte9 import get_arte9_products
from stores.factory_cards import get_factory_cards_products
from stores.topdeck import get_topdeck_products
from stores.padis import get_padis_products
from stores.micelion import get_micelion_products
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


# ==========================================
# CORE
# ==========================================

from monitor import process_store
from filters import filter_products


# ==========================================
# CONFIGURACIÓN
# ==========================================

CHECK_INTERVAL = 300


# ==========================================
# TIENDAS ACTIVAS
# ==========================================

STORES = [

    # ESPAÑA
    ("Arte9", get_arte9_products),
    ("Factory Cards", get_factory_cards_products),
    ("TopDeck", get_topdeck_products),
    ("Padis", get_padis_products),
    ("Micelion Games", get_micelion_products),
    ("Jupiter Juegos", get_jupiter_products),

    ("Madrid Norte TCG", get_madrid_norte_products),
    ("The Rare Box", get_rare_box_products),
    ("The Booster Box", get_booster_box_products),
    ("Nova Ohara Cards", get_nova_ohara_products),
    ("TodoHits", get_todohits_products),
    ("Geekkaos", get_geekkaos_products),
    ("Ninpo Store", get_ninpo_products),
    ("Three Stones Games", get_three_stones_products),
    ("La Tienda Scum", get_scum_products),

    # EUROPA
    ("EuroTCG", get_eurotcg_products),
    ("TCG Family", get_tcg_family_products),
]


# ==========================================
# REVISAR UNA TIENDA
# ==========================================

def check_store(store_name, scraper_function):

    try:

        print()
        print("=" * 80)
        print(f"🏪 Revisando {store_name}...")
        print("=" * 80)

        # ==========================================
        # 1. OBTENER PRODUCTOS
        # ==========================================

        all_products = scraper_function()

        print()
        print(
            f"   📦 {len(all_products)} "
            f"productos encontrados."
        )

        # ==========================================
        # 2. FILTRAR
        # English + Anniversary
        # ==========================================

        products, rejected = filter_products(
            all_products
        )

        print(
            f"   ✅ {len(products)} aceptados "
            f"(English / Anniversary)."
        )

        print(
            f"   ❌ {len(rejected)} descartados."
        )

        # ==========================================
        # 3. PROTECCIÓN CONTRA SCRAPER VACÍO
        # ==========================================
        #
        # Si una web falla temporalmente y devuelve 0,
        # NO queremos borrar su estado anterior de
        # products.json.
        # ==========================================

        if not products:

            print(
                f"   ⚠️ {store_name}: "
                f"0 productos válidos."
            )

            print(
                "   Base anterior conservada."
            )

            return

        # ==========================================
        # 4. COMPARAR CON BASE DE DATOS
        # ==========================================

        process_store(
            store_name,
            products
        )

    except Exception as error:

        print()
        print(
            f"❌ ERROR EN {store_name}:"
        )

        print(
            f"   {error}"
        )


# ==========================================
# REVISAR TODAS LAS TIENDAS
# ==========================================

def check_all_stores():

    print()
    print()
    print("#" * 80)

    print(
        "🔎 ONEPIECE WATCH EUROPE"
    )

    print(
        "🕐",
        datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    )

    print(
        f"🏪 Tiendas activas: {len(STORES)}"
    )

    print("#" * 80)

    for store_name, scraper_function in STORES:

        check_store(
            store_name,
            scraper_function
        )


# ==========================================
# MAIN
# ==========================================

def main():

    print()
    print("=" * 80)
    print("🔥 ONEPIECE WATCH INICIADO")
    print("=" * 80)

    print(
        "🌍 España + Europa"
    )

    print(
        "🎴 One Piece TCG"
    )

    print(
        "🇬🇧 Filtro: English"
    )

    print(
        "⭐ Anniversary Sets / Collections: "
        "cualquier idioma"
    )

    print(
        f"🏪 Tiendas activas: {len(STORES)}"
    )

    print(
        f"⏱️ Frecuencia: cada "
        f"{CHECK_INTERVAL} segundos"
    )

    print(
        "🔔 Discord: productos nuevos, "
        "precios y stock"
    )

    print("=" * 80)

    while True:

        try:

            check_all_stores()

        except Exception as error:

            # Un error general no mata
            # el monitor completo.
            print()
            print(
                "❌ Error general del monitor:"
            )
            print(error)

        print()
        print("=" * 80)

        print(
            f"⏳ Próxima revisión en "
            f"{CHECK_INTERVAL} segundos..."
        )

        print("=" * 80)

        time.sleep(
            CHECK_INTERVAL
        )


if __name__ == "__main__":
    main()