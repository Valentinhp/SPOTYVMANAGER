"""Configuración de la aplicación.

Este módulo lee las variables de entorno definidas en un archivo ``.env``
ubicado en la raíz del proyecto. Utiliza ``python-dotenv`` para cargar esos
valores y exponerlos como constantes que se usan en el resto de la aplicación.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Ruta al archivo .env situado fuera del paquete ``src``
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

#: Credenciales
CLIENT_ID: str = os.getenv("CLIENT_ID", "")
CLIENT_SECRET: str = os.getenv("CLIENT_SECRET", "")
REDIRECT_URI: str = os.getenv("REDIRECT_URI", "http://localhost:8888/callback")

#: Alcances Spotify
SCOPES: str = (
    "user-library-read "
    "playlist-read-private "
    "playlist-read-collaborative "
    "playlist-modify-public "
    "playlist-modify-private "
    "user-follow-read "
    "user-read-playback-position "
    "user-top-read"
)

# ---------------------------------------------------
# LOGGING
# ---------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)
