"""
Carga variables de entorno y configura logging
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

#: Credenciales
CLIENT_ID: str = os.getenv("CLIENT_ID", "")
CLIENT_SECRET: str = os.getenv("CLIENT_SECRET", "")
REDIRECT_URI: str = os.getenv("REDIRECT_URI", "https://localhost:8888/callback")

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
