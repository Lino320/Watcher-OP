import os


# ==========================================
# 1. GITHUB ACTIONS / VARIABLE DE ENTORNO
# ==========================================

DISCORD_WEBHOOK_URL = os.getenv(
    "DISCORD_WEBHOOK_URL"
)


# ==========================================
# 2. DESARROLLO LOCAL
# ==========================================

if not DISCORD_WEBHOOK_URL:

    try:

        from discord_config_local import (
            DISCORD_WEBHOOK_URL
        )

    except ImportError:

        DISCORD_WEBHOOK_URL = None


# ==========================================
# 3. VALIDACIÓN
# ==========================================

if not DISCORD_WEBHOOK_URL:

    raise RuntimeError(
        "No se ha configurado DISCORD_WEBHOOK_URL"
    )