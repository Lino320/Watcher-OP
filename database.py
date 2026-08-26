import json
import os


DATA_FOLDER = "data"

DATABASE_FILE = os.path.join(
    DATA_FOLDER,
    "products.json"
)


def ensure_database():

    os.makedirs(
        DATA_FOLDER,
        exist_ok=True
    )

    if not os.path.exists(
        DATABASE_FILE
    ):

        with open(
            DATABASE_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                {
                    "stores": {}
                },
                file,
                indent=4
            )


def load_database():

    ensure_database()

    with open(
        DATABASE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def save_database(database):

    ensure_database()

    with open(
        DATABASE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            database,
            file,
            indent=4,
            ensure_ascii=False
        )