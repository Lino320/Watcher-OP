from filters import filter_products

from stores.arte9 import get_arte9_products
from stores.topdeck import get_topdeck_products
from stores.scum import get_scum_products


STORES = [
    ("Arte9", get_arte9_products),
    ("TopDeck", get_topdeck_products),
    ("La Tienda Scum", get_scum_products),
]


for store_name, scraper in STORES:

    print()
    print("=" * 80)
    print(store_name)
    print("=" * 80)

    try:

        raw = scraper()

        accepted, rejected = filter_products(raw)

        print("BRUTOS:", len(raw))
        print("ACEPTADOS:", len(accepted))
        print("RECHAZADOS:", len(rejected))

        print()
        print("PRIMEROS PRODUCTOS BRUTOS:")

        for product in raw[:5]:

            print()
            print("TITLE:", product.get("title"))
            print("LANGUAGE:", product.get("language"))
            print("STOCK:", product.get("stock"))

    except Exception as error:

        print("ERROR:", error)