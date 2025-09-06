"""
Funciones de uso general (playlists, podcasts, artistas…)
"""
from __future__ import annotations
import time
from typing import List, Tuple, Set
from spotipy import Spotify
from ..config import logger

# --------------------------------------------------------------------------------
# PLAYLISTS Y PODCASTS
# --------------------------------------------------------------------------------
def get_podcast_episodes(sp: Spotify, podcast_id: str) -> List[str]:
    """Devuelve URIs de TODOS los episodios de un podcast (maneja paginación)."""
    episodes, offset, limit = [], 0, 50
    while True:
        try:
            resp = sp.show_episodes(podcast_id, limit=limit, offset=offset)
            items = resp.get("items", [])
            if not items:
                break
            episodes.extend(
                [f"spotify:episode:{ep['id']}" for ep in items if ep and ep.get("id")]
            )
            offset += len(items)
            if offset >= resp.get("total", 0):
                break
        except Exception as e:
            logger.error("Error al obtener episodios de %s: %s", podcast_id, e)
            break
    return episodes


def get_playlist_items(sp: Spotify, playlist_id: str) -> List[str]:
    """Devuelve URIs (track o episode) que ya existen en la playlist."""
    items, offset = [], 0
    while True:
        try:
            resp = sp.playlist_items(playlist_id, limit=100, offset=offset)
            batch = resp.get("items", [])
            if not batch:
                break
            for it in batch:
                track = it.get("track")
                if track and track.get("uri"):
                    items.append(track["uri"])
            offset += len(batch)
            if not resp.get("next"):
                break
        except Exception as e:
            logger.error("Error al leer playlist %s: %s", playlist_id, e)
            break
    return items


def add_episodes_to_playlist(sp: Spotify, playlist_id: str, episode_uris: list[str]) -> None:
    """Agrega episodios evitando duplicados."""
    existentes: Set[str] = set(get_playlist_items(sp, playlist_id))
    nuevos = [uri for uri in episode_uris if uri not in existentes]
    for i in range(0, len(nuevos), 100):
        try:
            sp.playlist_add_items(playlist_id, nuevos[i:i + 100])
        except Exception as e:
            logger.error("Error agregando episodios a %s: %s", playlist_id, e)
            return
    if nuevos:
        logger.info("Agregados %s episodios nuevos a %s", len(nuevos), playlist_id)
    else:
        logger.info("No hay episodios nuevos para agregar.")


def obtener_playlists_usuario(sp: Spotify) -> List[Tuple[str, str, int]]:
    """[(playlist_id, nombre, total_tracks)…]"""
    playlists, offset = [], 0
    while True:
        res = sp.current_user_playlists(limit=50, offset=offset)
        playlists += [
            (it["id"], it["name"], it["tracks"]["total"])
            for it in res.get("items", [])
        ]
        if not res.get("next"):
            break
        offset += 50
    return playlists


def crear_playlist(sp: Spotify, nombre_playlist: str, public: bool = False) -> str:
    user_id = sp.me()["id"]
    nueva = sp.user_playlist_create(user_id, name=nombre_playlist, public=public)
    return nueva["id"]


def eliminar_items_playlist(sp: Spotify, playlist_id: str, uris: list[str]) -> None:
    try:
        sp.playlist_remove_all_occurrences_of_items(playlist_id, uris)
        logger.info("Eliminados %s items de %s", len(uris), playlist_id)
    except Exception as e:
        logger.error("Error al eliminar items: %s", e)


def obtener_contenido_playlist(
    sp: Spotify, playlist_id: str
) -> List[Tuple[str, str, str]]:
    """[(track_id, nombre, artista/show)]"""
    contenido, offset = [], 0
    while True:
        resp = sp.playlist_items(playlist_id, limit=50, offset=offset)
        for it in resp.get("items", []):
            track = it.get("track")
            if not track:
                continue
            tid = track.get("id")
            nombre = track.get("name", "Desconocido")
            if track.get("type") == "episode":
                artista_show = track.get("show", {}).get("name", "Desconocido")
            else:
                artistas = track.get("artists", [])
                artista_show = ", ".join(a["name"] for a in artistas) if artistas else "Desconocido"
            contenido.append((tid, nombre, artista_show))
        if not resp.get("next"):
            break
        offset += 50
    return contenido


def obtener_artistas_seguidos(sp: Spotify):
    artistas = []
    try:
        datos = sp.current_user_followed_artists()
        while datos:
            for art in datos["artists"]["items"]:
                genero = art["genres"][0] if art["genres"] else ""
                artistas.append((art["id"], art["name"], genero))
            if datos["artists"]["next"]:
                datos = sp.next(datos["artists"])
            else:
                break
    except Exception as e:
        logger.error("Error al obtener artistas seguidos: %s", e)
    return artistas


def obtener_podcasts_guardados(sp: Spotify):
    podcasts = []
    try:
        datos = sp.current_user_saved_shows()
        for it in datos.get("items", []):
            show = it["show"]
            podcasts.append((show["id"], show["name"], show["publisher"]))
    except Exception as e:
        logger.error("Error al obtener podcasts guardados: %s", e)
    return podcasts


def obtener_canciones_artista(sp: Spotify, artista_id: str):
    try:
        resp = sp.artist_top_tracks(artista_id)
        return [t["id"] for t in resp["tracks"]]
    except Exception as e:
        logger.error("Error al obtener top tracks de %s: %s", artista_id, e)
        return []


def obtener_episodios_podcast_sencillo(sp: Spotify, podcast_id: str):
    try:
        resp = sp.show_episodes(podcast_id)
        return [ep["id"] for ep in resp.get("items", [])]
    except Exception as e:
        logger.error("Error al obtener episodios de %s: %s", podcast_id, e)
        return []


def agregar_canciones_a_playlist(sp: Spotify, playlist_id: str, track_ids: list[str]):
    existentes = set(get_playlist_items(sp, playlist_id))
    nuevos = [
        f"spotify:track:{tid}"
        for tid in track_ids
        if f"spotify:track:{tid}" not in existentes
    ]
    for i in range(0, len(nuevos), 100):
        try:
            sp.playlist_add_items(playlist_id, nuevos[i:i + 100])
        except Exception as e:
            logger.error("Error agregando tracks a playlist: %s", e)
            break

def buscar_artistas(sp: Spotify, query: str) -> List[Tuple[str, str]]:
    """Busca artistas por nombre."""
    if not query:
        return []
    try:
        results = sp.search(q=query, type='artist', limit=10)
        artistas = results.get('artists', {}).get('items', [])
        return [(a['id'], a['name']) for a in artistas]
    except Exception as e:
        logger.error(f"Error al buscar artistas: {e}")
        return []
