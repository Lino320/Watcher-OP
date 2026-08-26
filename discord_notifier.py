import requests
from discord_config import DISCORD_WEBHOOK_URL


def send_discord_message(message):
    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json={
            "content": message
        },
        timeout=20
    )

    response.raise_for_status()

    print("Notificación enviada a Discord")


def send_discord_file(file_path, message="📂 Estado actual de productos One Piece"):
    with open(file_path, "rb") as file:

        response = requests.post(
            DISCORD_WEBHOOK_URL,
            data={
                "content": message
            },
            files={
                "file": (
                    "products.json",
                    file,
                    "application/json"
                )
            },
            timeout=30
        )

    response.raise_for_status()

    print("JSON enviado a Discord")