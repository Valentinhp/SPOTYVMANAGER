import tkinter as tk
from tkinter import ttk, messagebox
import re
import itertools
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import logging
import time
import random
from tkinter import simpledialog


# --------------------------------------------------------------------------------
# CONFIGURACIÓN DE LOGGING
# --------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------------
# CREDENCIALES Y SCOPES (MODIFICA CON TUS DATOS)
# --------------------------------------------------------------------------------
CLIENT_ID = ""
CLIENT_SECRET = ""
REDIRECT_URI = "http://localhost:8888/callback"
SCOPES = (
    "user-library-read "
    "playlist-read-private "
    "playlist-read-collaborative "
    "playlist-modify-public "
    "playlist-modify-private "
    "user-follow-read "
    "user-read-playback-position "
    "user-top-read"
)

# --------------------------------------------------------------------------------
# data_podcasts: lista de pares {podcast_id, playlist_id}
# --------------------------------------------------------------------------------
data_podcasts = [
    {"podcast": "0u8dE1kc9CkFn8bONEq0hE", "playlist": "1MreMp1Qm4gyKZa5B2HZun"},
    {"podcast": "5JYQdA2dCaFRfCMLoUAbJp", "playlist": "5fBYes8twIslY3F41zcgwN"},
    {"podcast": "5hiPtlvSfLe4S9S5S9RCwG", "playlist": "49aOapLd6aSH0s58MBVwCF"},
    {"podcast": "6bDNRLtJsC0KCRFsSfpFA7", "playlist": "7arQDDHMeYQxQkSZM2Qc7J"},
    {"podcast": "3dYxnrAnRqAf7uPP6jXqEV", "playlist": "10qPRgsFtdJQ0NUGq5fQVs"},
    {"podcast": "1vGiDuVEehP90dv3H01WVE", "playlist": "1iIQuIEgKggq5xyaJPfvMz"},
    {"podcast": "2hIY32m7kl5mixXkwnjTBd", "playlist": "487txxFyTL6aqzYWnfJcEG"},
    {"podcast": "5XEKeuYWpH6CpEmxF0XiXl", "playlist": "4ES2LCF5xidpU32BsizcqC"},
    {"podcast": "6HOxtj2TQHFOsdPLb73C1E", "playlist": "61q9qYyNcUH77LszD3QuN3"},
    {"podcast": "2pwU20WESUl927rNFWFyw8", "playlist": "2zazPQz8WjHVFgOS2ENBGQ"},
    {"podcast": "4pAsqlBRHAYjXVY9C7HUP3", "playlist": "2zazPQz8WjHVFgOS2ENBGQ"},
    {"podcast": "0Gf2ESpFrmlPiPBxBUNecl", "playlist": "5l7PQHgCmknBVsDLc0b506"},
    {"podcast": "58wsYLsa9QPrclg3cFRoG0", "playlist": "6XG0QwcWma7EqYkLNJxTUC"}
]

# --------------------------------------------------------------------------------
# AUTENTICACIÓN SPOTIFY
# --------------------------------------------------------------------------------
def autenticar_spotify():
    """Devuelve un objeto spotipy.Spotify autenticado por OAuth."""
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
    )
    return spotipy.Spotify(auth_manager=auth_manager)

# --------------------------------------------------------------------------------
# FUNCIONES GENERALES (playlists, podcasts, artistas…) – fuera de la clase
# --------------------------------------------------------------------------------
def get_podcast_episodes(sp, podcast_id):
    """Obtiene TODOS los episodios de un podcast (maneja paginación)."""
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
            logger.error(f"Error al obtener episodios de {podcast_id}: {e}")
            break
    return episodes


def get_playlist_items(sp, playlist_id):
    """Devuelve lista de URIs (track o episode) que ya existen en la playlist."""
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
            logger.error(f"Error al leer playlist {playlist_id}: {e}")
            break
    return items


def add_episodes_to_playlist(sp, playlist_id, episode_uris):
    """Agrega URIs de episodios, evitando duplicados."""
    existentes = set(get_playlist_items(sp, playlist_id))
    nuevos = [uri for uri in episode_uris if uri not in existentes]
    for i in range(0, len(nuevos), 100):
        try:
            sp.playlist_add_items(playlist_id, nuevos[i:i + 100])
        except Exception as e:
            logger.error(f"Error agregando episodios a {playlist_id}: {e}")
            return
    if nuevos:
        logger.info(f"Agregados {len(nuevos)} episodios nuevos a {playlist_id}")
    else:
        logger.info("No hay episodios nuevos para agregar.")


def obtener_playlists_usuario(sp):
    """Devuelve [(playlist_id, nombre, total_tracks), …] del usuario."""
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


def crear_playlist(sp, nombre_playlist, public=False):
    user_id = sp.me()["id"]
    nueva = sp.user_playlist_create(user_id, name=nombre_playlist, public=public)
    return nueva["id"]


def eliminar_items_playlist(sp, playlist_id, uris):
    try:
        sp.playlist_remove_all_occurrences_of_items(playlist_id, uris)
        logger.info(f"Eliminados {len(uris)} items de {playlist_id}")
    except Exception as e:
        logger.error(f"Error al eliminar items: {e}")


def obtener_contenido_playlist(sp, playlist_id):
    """Retorna [(track_id, nombre, artista/show)] de la playlist."""
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


def obtener_artistas_seguidos(sp):
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
        logger.error(f"Error al obtener artistas seguidos: {e}")
    return artistas


def obtener_podcasts_guardados(sp):
    podcasts = []
    try:
        datos = sp.current_user_saved_shows()
        for it in datos.get("items", []):
            show = it["show"]
            podcasts.append((show["id"], show["name"], show["publisher"]))
    except Exception as e:
        logger.error(f"Error al obtener podcasts guardados: {e}")
    return podcasts


def obtener_canciones_artista(sp, artista_id):
    try:
        resp = sp.artist_top_tracks(artista_id)
        return [t["id"] for t in resp["tracks"]]
    except Exception as e:
        logger.error(f"Error al obtener top tracks de {artista_id}: {e}")
        return []


def obtener_episodios_podcast_sencillo(sp, podcast_id):
    try:
        resp = sp.show_episodes(podcast_id)
        return [ep["id"] for ep in resp.get("items", [])]
    except Exception as e:
        logger.error(f"Error al obtener episodios de {podcast_id}: {e}")
        return []


def agregar_canciones_a_playlist(sp, playlist_id, track_ids):
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
            logger.error(f"Error agregando tracks a playlist: {e}")
            break

# --------------------------------------------------------------------------------
#  VENTANAS AUXILIARES (ver, crear, contenido, agregar…)
# --------------------------------------------------------------------------------
def ventana_ver_playlists(sp, root):
    ven = tk.Toplevel(root)
    ven.title("Ver Playlists")
    ven.geometry("600x400")

    cols = ("ID", "Nombre", "Tracks")
    tree = ttk.Treeview(ven, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scroll = ttk.Scrollbar(ven, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)

    for pid, nom, tot in obtener_playlists_usuario(sp):
        tree.insert("", tk.END, values=(pid, nom, tot))


def ventana_crear_playlist(sp, root):
    ven = tk.Toplevel(root)
    ven.title("Crear Playlist")
    ven.geometry("300x150")

    tk.Label(ven, text="Nombre de la Playlist:").pack(pady=5)
    entry = tk.Entry(ven, width=30)
    entry.pack(pady=5)

    def crear():
        nombre = entry.get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "Ingresa un nombre")
            return
        pid = crear_playlist(sp, nombre)
        messagebox.showinfo("Completado", f"Playlist creada con ID: {pid}")
        ven.destroy()

    tk.Button(ven, text="Crear", command=crear).pack(pady=5)


def ventana_contenido_playlist(sp, root):
    ven = tk.Toplevel(root)
    ven.title("Contenido de Playlist")
    ven.geometry("650x450")

    tk.Label(ven, text="ID de la playlist:").pack(pady=5)
    entry_pid = tk.Entry(ven, width=40)
    entry_pid.pack()

    frame_tbl = ttk.Frame(ven)
    frame_tbl.pack(fill=tk.BOTH, expand=True)

    cols = ("TrackID", "Título", "Artista/Show")
    tree = ttk.Treeview(frame_tbl, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scroll = ttk.Scrollbar(frame_tbl, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def cargar():
        tree.delete(*tree.get_children())
        pid = entry_pid.get().strip()
        if not pid:
            messagebox.showwarning("Atención",
                                   "Debes ingresar el ID de la playlist.")
            return
        for tid, nom, art in obtener_contenido_playlist(sp, pid):
            tree.insert("", tk.END, values=(tid, nom, art))

    def eliminar_sel():
        pid = entry_pid.get().strip()
        if not pid:
            messagebox.showwarning("Atención", "Ingresa el ID primero.")
            return
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "No seleccionaste nada.")
            return
        uris = []
        for s in sel:
            tid = tree.item(s, "values")[0]
            uris += [f"spotify:track:{tid}", f"spotify:episode:{tid}"]
        eliminar_items_playlist(sp, pid, uris)
        cargar()

    frame_btns = tk.Frame(ven)
    frame_btns.pack(pady=5)
    tk.Button(frame_btns, text="Cargar Contenido", command=cargar)\
        .pack(side=tk.LEFT, padx=5)
    tk.Button(frame_btns, text="Eliminar Seleccionados", command=eliminar_sel)\
        .pack(side=tk.LEFT, padx=5)


def ventana_agregar_artista_podcast(sp, root):
    ven = tk.Toplevel(root)
    ven.title("Agregar Artista o Podcast a Playlist")
    ven.geometry("500x300")

    tk.Label(ven, text="ID de la Playlist destino:").pack(pady=5)
    entry_pl = tk.Entry(ven, width=40)
    entry_pl.pack()

    tk.Label(ven, text="ID de Artista (opcional):").pack(pady=5)
    entry_art = tk.Entry(ven, width=40)
    entry_art.pack()

    tk.Label(ven, text="ID de Podcast (opcional):").pack(pady=5)
    entry_pod = tk.Entry(ven, width=40)
    entry_pod.pack()

    def agregar():
        pid = entry_pl.get().strip()
        aid = entry_art.get().strip()
        podid = entry_pod.get().strip()
        if not pid:
            messagebox.showwarning("Atención", "Falta el ID de la Playlist.")
            return
        if aid:
            tracks = obtener_canciones_artista(sp, aid)
            if not tracks:
                messagebox.showwarning("Info",
                                       "No hay tracks para ese artista.")
                return
            agregar_canciones_a_playlist(sp, pid, tracks)
            messagebox.showinfo("Éxito", "Agregadas top tracks del artista.")
        elif podid:
            eps = obtener_episodios_podcast_sencillo(sp, podid)
            if not eps:
                messagebox.showwarning("Info", "No se encontraron episodios.")
                return
            add_episodes_to_playlist(
                sp, pid, [f"spotify:episode:{e}" for e in eps]
            )
            messagebox.showinfo("Éxito", "Agregados episodios del podcast.")
        else:
            messagebox.showinfo("Atención",
                                "No pusiste Artista ni Podcast.")

    tk.Button(ven, text="Agregar", command=agregar).pack(pady=10)


def ventana_sincronizar_podcasts_data(sp, root):
    ven = tk.Toplevel(root)
    ven.title("Sincronizar Podcasts (data_podcasts)")
    ven.geometry("520x300")

    tk.Label(ven,
             text="Sincronizando podcasts con sus playlists…",
             font=("Arial", 11)).pack(pady=8)
    prog = ttk.Progressbar(
        ven, orient="horizontal", length=460,
        mode="determinate", maximum=len(data_podcasts)
    )
    prog.pack(pady=5)
    lbl_estado = tk.Label(ven, text="Esperando…", anchor="w")
    lbl_estado.pack(fill=tk.X, padx=10)
    txt_log = tk.Text(ven, height=8, wrap=tk.WORD)
    txt_log.pack(padx=10, pady=6, fill=tk.BOTH, expand=True)

    def log(msg):
        txt_log.insert(tk.END, msg + "\n")
        txt_log.see(tk.END)
        ven.update_idletasks()

    def sincronizar():
        total = len(data_podcasts)
        prog["value"] = 0
        for idx, pair in enumerate(data_podcasts, start=1):
            pod_id = pair["podcast"]
            pl_id = pair["playlist"]
            try:
                podcast_name = sp.show(pod_id, market="US")["name"]
            except Exception:
                podcast_name = f"Podcast {pod_id[:8]}…"
            try:
                playlist_name = sp.playlist(
                    pl_id, fields="name")["name"]
            except Exception:
                playlist_name = f"Playlist {pl_id[:8]}…"
            lbl_estado.config(
                text=f"{idx}/{total}  {podcast_name} → {playlist_name}"
            )
            ven.update_idletasks()
            eps = get_podcast_episodes(sp, pod_id)
            if not eps:
                log(f"❌ {podcast_name}: sin episodios o error.")
                prog["value"] = idx
                continue
            antes = set(get_playlist_items(sp, pl_id))
            add_episodes_to_playlist(sp, pl_id, eps)
            despues = set(get_playlist_items(sp, pl_id))
            nuevos = len(despues) - len(antes)
            if nuevos:
                log(f"✅ {podcast_name}: {nuevos} nuevos → {playlist_name}")
            else:
                log(f"• {podcast_name}: 0 nuevos")
            prog["value"] = idx
            ven.update_idletasks()
        lbl_estado.config(text="¡Sincronización completa!")
        messagebox.showinfo("Terminado",
                            "Todos los podcasts han sido sincronizados.")

    tk.Button(ven, text="Iniciar sincronización",
              command=sincronizar).pack(pady=6)

# --------------------------------------------------------------------------------
# CLASE PRINCIPAL: GESTOR AUTOMÁTICO DE PLAYLISTS DE ARTISTA
# --------------------------------------------------------------------------------
class VentanaGestorAutomatico(tk.Toplevel):
    """Busca un artista, recoge todas sus canciones únicas y gestiona playlists."""

    def __init__(self, parent, sp):
        super().__init__(parent)
        self.title("Gestor de Playlists Automáticas en Spotify")
        self.geometry("600x600")
        self.sp = sp
        try:
            self.user_id = self.sp.current_user()["id"]
        except Exception:
            messagebox.showerror("Error",
                                 "No se pudo obtener info del usuario.")
            self.destroy()
            return
        self.songs = []        # lista final de canciones
        self.artist_id = None  # ID del artista seleccionado
        # frames
        self.frame_artist = tk.Frame(self)
        self.frame_playlist = tk.Frame(self)
        self.frame_clear = tk.Frame(self)
        # UI inicial
        self.create_artist_frame()
        self.frame_clear.pack(fill=tk.X)
        tk.Button(self.frame_clear, text="Vaciar Múltiples Playlists",
                  command=self.abrir_ventana_vaciar_playlists).pack(pady=5)

    # ------------------------ pantalla de artista ------------------------
    def create_artist_frame(self):
        self.frame_artist.pack(fill=tk.BOTH, expand=True)
        for w in self.frame_artist.winfo_children():
            w.destroy()
        tk.Label(self.frame_artist,
                 text="Introduce el nombre del artista:").pack(pady=10)
        self.entry_artist = tk.Entry(self.frame_artist, width=50)
        self.entry_artist.pack(pady=5)
        tk.Button(self.frame_artist, text="Buscar",
                  command=self.search_artist).pack(pady=5)
        self.listbox_artists = tk.Listbox(self.frame_artist, width=50)
        self.listbox_artists.pack(pady=10)
        self.listbox_artists.bind("<<ListboxSelect>>", self.on_artist_select)

    def search_artist(self):
        name = self.entry_artist.get().strip()
        if not name:
            messagebox.showinfo("Info", "Ingresa un nombre primero.")
            return
        try:
            res = self.sp.search(q=name, type="artist", limit=5)
            self.artists_found = res["artists"]["items"]
            self.listbox_artists.delete(0, tk.END)
            if not self.artists_found:
                messagebox.showinfo("Info", "No se encontró el artista.")
                return
            for art in self.artists_found:
                self.listbox_artists.insert(tk.END, art["name"])
        except Exception as e:
            messagebox.showerror("Error",
                                 f"Error al buscar el artista: {e}")

    def on_artist_select(self, _evt):
        if not self.listbox_artists.curselection():
            return
        idx = self.listbox_artists.curselection()[0]
        art = self.artists_found[idx]
        self.artist_id = art["id"]
        if messagebox.askyesno("Confirmar",
                               f"Seleccionaste {art['name']}. ¿Continuar?"):
            self.fetch_artist_songs()

    def fetch_artist_songs(self):
        try:
            self.songs = \
                self.obtener_canciones_artista_completas(self.artist_id)
            logger.info("DEBUG únicas = %s", len(self.songs))
            messagebox.showinfo(
                "Info", f"Se encontraron {len(self.songs)} canciones únicas."
            )
            self.frame_artist.pack_forget()
            self.create_playlist_frame()
        except Exception as e:
            messagebox.showerror("Error",
                                 f"Error al obtener las canciones: {e}")

    # -------------------- método central: CANCIONES SIN DUPES --------------------
    def obtener_canciones_artista_completas(self, artist_id):
        """Recoge todas las canciones del artista (sin duplicados)."""
        MARKETS = ("US", "MX")
        ALT_FLAGS = (
            "acoustic", "live", "en vivo", "unplugged", "instrumental",
            "remaster", "remastered", "demo", "karaoke", "edit",
            "mix", "remix", "versión", "version", "session",
        )
        elegido, total_raw = {}, 0
        import unicodedata, re
        clean = re.compile(r"[()\[\]{}\-–_:]")

        def slug(txt):
            t = unicodedata.normalize("NFKD", txt).encode(
                "ascii", "ignore").decode()
            t = clean.sub(" ", t.lower())
            for w in ALT_FLAGS:
                t = t.replace(w, "")
            return " ".join(t.split())

        def es_alt(titulo, album):
            t, a = titulo.lower(), album.lower()
            return any(w in t or w in a for w in ALT_FLAGS)

        def considera(track, album_name):
            nonlocal total_raw
            total_raw += 1
            tid = track.get("id")
            if not tid:
                return
            title = track.get("name", "").strip()
            base = slug(title)
            alt = es_alt(title, album_name)
            if base not in elegido:
                elegido[base] = {"track": track, "alt": alt}
            elif elegido[base]["alt"] and not alt:
                elegido[base] = {"track": track, "alt": alt}

        # 1) álbumes/singles/compilados
        try:
            alb_resp = self.sp.artist_albums(
                artist_id,
                album_type="album,single,compilation,appears_on",
                limit=50
            )
        except Exception as e:
            logger.error("[%s] error álbumes: %s", artist_id, e)
            return []
        albums = []
        while True:
            albums += alb_resp.get("items", [])
            if not alb_resp.get("next"):
                break
            alb_resp = self.sp.next(alb_resp)
        for alb in albums:
            alb_name = alb.get("name", "")
            for m in MARKETS:
                try:
                    tr_resp = self.sp.album_tracks(
                        alb["id"], limit=50, market=m)
                except Exception:
                    continue
                while True:
                    for t in tr_resp.get("items", []):
                        if any(a["id"] == artist_id for a in t["artists"]):
                            considera(t, alb_name)
                    if not tr_resp.get("next"):
                        break
                    tr_resp = self.sp.next(tr_resp)
        # 2) búsqueda global (colaboraciones sueltas)
        try:
            art_name = self.sp.artist(artist_id)["name"]
            offset = 0
            while True:
                sr = self.sp.search(
                    q=f'artist:"{art_name}"',
                    type="track", limit=50, offset=offset
                )
                items = sr["tracks"]["items"]
                for t in items:
                    if any(a["id"] == artist_id for a in t["artists"]):
                        considera(t, "")
                if not sr["tracks"]["next"]:
                    break
                offset += 50
        except Exception as e:
            logger.warning("[%s] búsqueda global falló: %s", artist_id, e)
        canciones = [
            {"id": d["track"]["id"], "name": d["track"]["name"]}
            for d in elegido.values()
        ]
        logger.info("[%s] vistas≈%s, únicas=%s",
                    artist_id, total_raw, len(canciones))
        return canciones

    # -------------------- informe previo --------------------
    def generar_informe_canciones(self):
        if not self.songs:
            messagebox.showinfo("Info", "No hay canciones cargadas.")
            return
        total_unicas = len(self.songs)
        total_collab = 0
        for s in self.songs:
            try:
                if len(self.sp.track(s["id"])["artists"]) > 1:
                    total_collab += 1
            except Exception:
                pass
        total_raw = total_unicas + total_collab
        total_dups = total_raw - total_unicas
        messagebox.showinfo(
            "Informe de canciones",
            f"Pistas únicas:          {total_unicas}\n"
            f"Con colaboraciones:     {total_collab}\n"
            f"Duplicadas descartadas: {total_dups}\n"
            f"Procesadas en total:    {total_raw}"
        )

    # ------------------------ pantalla de playlist ------------------------
    def create_playlist_frame(self):
        self.frame_playlist.pack(fill=tk.BOTH, expand=True)
        for w in self.frame_playlist.winfo_children():
            w.destroy()
        tk.Label(self.frame_playlist,
                 text="¿Qué deseas hacer?").pack(pady=10)
        self.playlist_option = tk.StringVar(value="nueva")
        tk.Radiobutton(
            self.frame_playlist, text="Crear nueva playlist",
            variable=self.playlist_option, value="nueva",
            command=self.update_playlist_option
        ).pack(pady=5)
        tk.Radiobutton(
            self.frame_playlist, text="Seleccionar playlist existente",
            variable=self.playlist_option, value="existente",
            command=self.update_playlist_option
        ).pack(pady=5)
        self.frame_option = tk.Frame(self.frame_playlist)
        self.frame_option.pack(pady=10, fill=tk.BOTH, expand=True)
        tk.Button(self.frame_playlist, text="Buscar otro artista",
                  command=self.reset_to_artist_search).pack(pady=5)
        self.update_playlist_option()

    def update_playlist_option(self):
        for w in self.frame_option.winfo_children():
            w.destroy()
        if self.playlist_option.get() == "nueva":
            self.new_playlist_entry = tk.Entry(self.frame_option, width=50)
            self.new_playlist_entry.pack(pady=5)
            self.new_playlist_entry.insert(
                0, "Nombre de la nueva playlist")
            tk.Button(
                self.frame_option, text="Crear Playlist",
                command=self.crear_playlist_y_agregar_songs
            ).pack(pady=5)
        else:
            self.entry_search = tk.Entry(self.frame_option, width=50)
            self.entry_search.pack(pady=5)
            self.entry_search.insert(0, "Buscar playlist")
            self.entry_search.bind("<KeyRelease>", self.filtrar_playlists)
            self.playlist_listbox = tk.Listbox(
                self.frame_option, width=50)
            self.playlists = self.obtener_todas_playlists()
            for pl in self.playlists:
                self.playlist_listbox.insert(tk.END, pl["name"])
            self.playlist_listbox.pack(
                pady=5, fill=tk.BOTH, expand=True)
            btn_frame = tk.Frame(self.frame_option)
            btn_frame.pack(pady=5)
            tk.Button(btn_frame, text="Vaciar Playlist",
                      command=self.vaciar_playlist_seleccionada).pack(
                side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="Actualizar Playlist",
                      command=self.actualizar_playlist_seleccionada).pack(
                side=tk.LEFT, padx=5)

    def crear_playlist_y_agregar_songs(self):
        name = self.new_playlist_entry.get().strip()
        if not name:
            messagebox.showinfo("Info",
                                "Ingresa un nombre para la playlist.")
            return
        try:
            playlist = self.sp.user_playlist_create(
                self.user_id,
                name,
                public=True,
                description="Playlist generada automáticamente"
            )
            pid = playlist["id"]
            ids = [s["id"] for s in self.songs]
            for i in range(0, len(ids), 100):
                self.sp.playlist_add_items(pid, ids[i:i + 100])
                time.sleep(0.5)
            messagebox.showinfo(
                "Info", "Playlist creada y canciones agregadas.")
        except Exception as e:
            messagebox.showerror("Error",
                                 f"Error al crear la playlist: {e}")

    # ---------- utilidades selección playlist existente ----------
    def filtrar_playlists(self, _evt):
        term = self.entry_search.get().strip().lower()
        self.playlist_listbox.delete(0, tk.END)
        for pl in self.playlists:
            if term in pl["name"].lower():
                self.playlist_listbox.insert(tk.END, pl["name"])

    def vaciar_playlist_seleccionada(self):
        if not self.playlist_listbox.curselection():
            messagebox.showinfo("Info",
                                "Selecciona una playlist primero.")
            return
        idx = self.playlist_listbox.curselection()[0]
        pl = self.playlists[idx]
        if not messagebox.askyesno(
            "Confirmar", f"Vaciar playlist “{pl['name']}”?"
        ):
            return
        try:
            self.sp.playlist_replace_items(pl["id"], [])
            messagebox.showinfo("Info",
                                "Playlist vaciada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo vaciar: {e}")

    def actualizar_playlist_seleccionada(self):
        if not self.playlist_listbox.curselection():
            messagebox.showinfo("Info",
                                "Selecciona una playlist primero.")
            return
        idx = self.playlist_listbox.curselection()[0]
        pl = self.playlists[idx]
        existentes = self.obtener_canciones_playlist(pl["id"])
        to_add = [
            s["id"] for s in self.songs if s["id"] not in existentes
        ]
        if not to_add:
            messagebox.showinfo("Info", "No hay canciones nuevas.")
            return
        try:
            for i in range(0, len(to_add), 100):
                self.sp.playlist_add_items(pl["id"], to_add[i:i + 100])
                time.sleep(0.5)
            messagebox.showinfo("Info", "Playlist actualizada.")
        except Exception as e:
            messagebox.showerror("Error",
                                 f"No se pudo actualizar: {e}")

    # ---------- helpers de playlists ----------
    def obtener_todas_playlists(self):
        pls, offset = [], 0
        while True:
            res = self.sp.current_user_playlists(
                limit=50, offset=offset)
            for it in res["items"]:
                pls.append({
                    "id": it["id"],
                    "name": it["name"],
                    "tracks": it["tracks"]["total"]
                })
            if not res["next"]:
                break
            offset += 50
        return pls

    def obtener_canciones_playlist(self, playlist_id):
        ids, offset = set(), 0
        while True:
            res = self.sp.playlist_items(
                playlist_id, limit=100, offset=offset)
            for it in res.get("items", []):
                track = it.get("track")
                if track and track.get("id"):
                    ids.add(track["id"])
            if not res.get("next"):
                break
            offset += 100
        return ids

    # ---------- ventana vaciar varias playlists ----------
    def abrir_ventana_vaciar_playlists(self):
        ven = tk.Toplevel(self)
        ven.title("Vaciar Múltiples Playlists")
        ven.geometry("400x400")

        tk.Label(ven, text="Selecciona las playlists a vaciar:").pack(
            pady=10)
        listbox = tk.Listbox(ven, selectmode=tk.MULTIPLE, width=50)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scroll = tk.Scrollbar(ven, command=listbox.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scroll.set)

        pls = self.obtener_todas_playlists()
        for pl in pls:
            listbox.insert(tk.END, pl["name"])

        def vaciar_sel():
            idxs = listbox.curselection()
            if not idxs:
                messagebox.showinfo("Info",
                                    "No seleccionaste ninguna playlist.")
                return
            for i in idxs:
                pid = pls[i]["id"]
                try:
                    self.sp.playlist_replace_items(pid, [])
                except Exception as e:
                    messagebox.showerror(
                        "Error",
                        f"No se pudo vaciar {pls[i]['name']}: {e}"
                    )
                    return
            messagebox.showinfo("Info",
                                "Playlists vaciadas correctamente.")
            ven.destroy()

        tk.Button(ven, text="Vaciar seleccionadas",
                  command=vaciar_sel).pack(pady=10)

    # ---------- volver a búsqueda ----------
    def reset_to_artist_search(self):
        self.frame_playlist.pack_forget()
        self.frame_artist.pack(fill=tk.BOTH, expand=True)
        self.songs.clear()
        self.artist_id = None
        self.entry_artist.delete(0, tk.END)
        self.listbox_artists.delete(0, tk.END)

# --------------------------------------------------------------------------------
# (2) #ARTISTAPY – recomendaciones por géneros
# --------------------------------------------------------------------------------
def ventana_artistapy(sp, root):
    ven = tk.Toplevel(root)
    ven.title("Recomendaciones #Artistapy")
    ven.geometry("620x540")

    tk.Label(
        ven, text="Géneros favoritos (separados por coma):",
        font=("Arial", 11)
    ).pack(pady=8)

    entry_gen = tk.Entry(ven, width=60)
    entry_gen.insert(0, "Hip Hop Latino, Indie Mexicano, Trap Mexa")
    entry_gen.pack(pady=5)

    text_area = tk.Text(ven, wrap=tk.WORD, width=75, height=20)
    text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def generar_playlist():
        text_area.delete(1.0, tk.END)
        user_genres = [g.strip() for g in entry_gen.get().split(',')
                       if g.strip()][:5]
        if not user_genres:
            messagebox.showinfo("Info", "No escribiste ningún género.")
            return
        recs = []

        for genre in user_genres:
            try:
                res = sp.search(q=genre, type="artist", limit=10)
                arts = res.get("artists", {}).get("items", [])
                for art in arts[:5]:
                    top = sp.artist_top_tracks(art["id"], country="US")
                    for track in top.get("tracks", []):
                        recs.append((
                            track["name"],
                            ", ".join(a["name"] for a in track["artists"]),
                            track["id"]
                        ))
            except Exception as e:
                text_area.insert(tk.END,
                                 f"[ERROR] Género «{genre}»: {e}\n")
        vistos = {}
        for nom, arts, tid in recs:
            key = (nom.lower(), arts.lower())
            if key not in vistos:
                vistos[key] = (nom, arts, tid)
        final_tracks = list(vistos.values())
        if not final_tracks:
            text_area.insert(tk.END,
                             "No se obtuvieron canciones.\n")
            return
        random.shuffle(final_tracks)

        text_area.insert(tk.END, "=== Recomendaciones ===\n\n")
        for i, (nom, arts, _) in enumerate(final_tracks, 1):
            text_area.insert(tk.END, f"{i}. {nom} – {arts}\n")

        try:
            user_id = sp.me()["id"]
            pl_name = f"#Artistapy {random.randint(1000,9999)}"
            desc = "Playlist generada a partir de tus géneros"
            playlist = sp.user_playlist_create(
                user_id, pl_name, public=False, description=desc)
            playlist_id = playlist["id"]
            uris = [f"spotify:track:{tid}" for (_, _, tid) in final_tracks]
            for i in range(0, len(uris), 100):
                sp.playlist_add_items(playlist_id, uris[i:i + 100])
            text_area.insert(tk.END,
                             f"\n\n✅ Playlist «{pl_name}» creada "
                             f"con {len(uris)} canciones.")
        except Exception as e:
            text_area.insert(tk.END,
                             f"\n\n[ERROR] Al crear/llenar la playlist: {e}\n")
            text_area.insert(tk.END,
                             "\nVerifica que tu token incluya el scope "
                             "«playlist-modify-private».\n")

    tk.Button(ven, text="Generar playlist",
              command=generar_playlist).pack(pady=8)

# --------------------------------------------------------------------------------
# eliminar playlists
# --------------------------------------------------------------------------------
def ventana_eliminar_playlists(sp, root):
    ven = tk.Toplevel(root)
    ven.title("Eliminar Playlists")
    ven.geometry("420x500")

    tk.Label(ven, text="Buscar playlists:",
             font=("Arial", 11)).pack(pady=(10, 0))
    entry_buscar = tk.Entry(ven, width=40)
    entry_buscar.pack(pady=(0, 8))

    pls = obtener_playlists_usuario(sp)
    filtered_pls = list(pls)

    frame = tk.Frame(ven)
    frame.pack(fill=tk.BOTH, expand=True, padx=10)
    listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scroll.set)

    def refrescar():
        listbox.delete(0, tk.END)
        for pid, nombre, _ in filtered_pls:
            listbox.insert(tk.END, f"{nombre}  ({pid[:8]}…)")

    def filtrar(_evt):
        term = entry_buscar.get().strip().lower()
        filtered_pls.clear()
        for item in pls:
            if term in item[1].lower():
                filtered_pls.append(item)
        refrescar()

    entry_buscar.bind("<KeyRelease>", filtrar)
    refrescar()

    def confirmar_elim():
        idxs = listbox.curselection()
        if not idxs:
            messagebox.showwarning("Atención",
                                   "No seleccionaste ninguna playlist.")
            return
        seleccion = [filtered_pls[i] for i in idxs]
        nombres = "\n".join(f"• {n}" for _, n, _ in seleccion)
        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"Vas a eliminar estas playlists:\n{nombres}\n\n¿Continuar?"
        ):
            return
        errores = []
        for pid, nombre, _ in seleccion:
            try:
                sp.current_user_unfollow_playlist(pid)
            except Exception as e:
                errores.append(f"{nombre}: {e}")
        if errores:
            messagebox.showerror("Errores",
                                 "Algunas no se pudieron eliminar:\n"
                                 + "\n".join(errores))
        else:
            messagebox.showinfo("¡Listo!",
                                "Las playlists seleccionadas han sido eliminadas.")
        ven.destroy()

    tk.Button(ven, text="Eliminar seleccionadas",
              command=confirmar_elim).pack(pady=10)

# --------------------------------------------------------------------------------
# vaciar playlists múltiples con búsqueda
# --------------------------------------------------------------------------------
def ventana_vaciar_playlists(sp, root):
    ven = tk.Toplevel(root)
    ven.title("Vaciar Playlists")
    ven.geometry("420x500")

    tk.Label(ven, text="Buscar playlists:",
             font=("Arial", 11)).pack(pady=(10, 0))
    entry_buscar = tk.Entry(ven, width=40)
    entry_buscar.pack(pady=(0, 8))

    todas = obtener_playlists_usuario(sp)
    mostradas = list(todas)

    frame = tk.Frame(ven)
    frame.pack(fill=tk.BOTH, expand=True, padx=10)
    listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scroll.set)

    def refrescar():
        listbox.delete(0, tk.END)
        for pid, nombre, _ in mostradas:
            listbox.insert(tk.END, f"{nombre}  ({pid[:8]}…)")

    def filtrar(_evt):
        texto = entry_buscar.get().strip().lower()
        mostradas.clear()
        for item in todas:
            if texto in item[1].lower():
                mostradas.append(item)
        refrescar()

    entry_buscar.bind("<KeyRelease>", filtrar)
    refrescar()

    def confirmar_vaciado():
        idxs = listbox.curselection()
        if not idxs:
            messagebox.showwarning("Atención",
                                   "No seleccionaste ninguna playlist.")
            return
        seleccion = [mostradas[i] for i in idxs]
        nombres = "\n".join(f"• {n}" for _, n, _ in seleccion)
        if not messagebox.askyesno(
            "Confirmar vaciado",
            f"Vas a vaciar estas playlists:\n{nombres}\n\n¿Continuar?"
        ):
            return
        errores = []
        for pid, nombre, _ in seleccion:
            try:
                sp.playlist_replace_items(pid, [])
            except Exception as e:
                errores.append(f"{nombre}: {e}")
        if errores:
            messagebox.showerror("Errores",
                                 "Errores al vaciar:\n" + "\n".join(errores))
        else:
            messagebox.showinfo("¡Hecho!",
                                "Las playlists seleccionadas han quedado vacías.")
        ven.destroy()

    tk.Button(ven, text="Vaciar seleccionadas",
              command=confirmar_vaciado).pack(pady=10)
    
    
# -------------------------------------------------------------------------
# VENTANA “BÚSQUEDA AVANZADA”  – frase libre, géneros libres, crea playlist
# -------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk, messagebox
import re, itertools, difflib, threading, queue, time

def ventana_busqueda_avanzada(sp, root):
    """
    Ventana para:
      • Buscar canciones por frase o tema/emoción.
      • Filtrar por géneros libres.
      • Ajustar número de pistas y popularidad.
      • Ver resultados con scroll.
      • Crear una playlist con un clic.
      • Atajos: ⏎ busca, Ctrl+P crea playlist.
    """
    # ——— Crear ventana ———
    ven = tk.Toplevel(root)
    ven.title("Buscar / Recomendar y Crear Playlist")
    ven.geometry("700x650")      # altura ajustada para no quedar oculta
    ven.minsize(640, 600)
    ven.resizable(True, True)

    # ——— Configurar grid ———
    ven.columnconfigure(0, weight=1)
    ven.columnconfigure(1, weight=1)
    ven.rowconfigure(4, weight=1)  # resultados crecen

    # ——— Modo de búsqueda ———
    modo = tk.StringVar(value="frase")  # "frase" o "tema"
    ttk.Radiobutton(ven, text="Por frase",     variable=modo, value="frase")\
        .grid(row=0, column=0, sticky="w", padx=10, pady=6)
    ttk.Radiobutton(ven, text="Por tema/emoción", variable=modo, value="tema")\
        .grid(row=0, column=1, sticky="w", padx=10, pady=6)

    # ——— Entrada de texto ———
    ttk.Label(ven, text="Frase/tema (puedes incluir 'genero ...'):")\
        .grid(row=1, column=0, sticky="w", padx=10)
    entry_texto = ttk.Entry(ven)
    entry_texto.grid(row=1, column=1, sticky="ew", padx=10, pady=4)
    entry_texto.focus()

    # ——— Géneros libres ———
    ttk.Label(ven, text="Géneros (opcional, sep. por coma):")\
        .grid(row=2, column=0, sticky="w", padx=10)
    entry_genres = ttk.Entry(ven)
    entry_genres.grid(row=2, column=1, sticky="ew", padx=10, pady=4)

    # ——— Parámetros numéricos ———
    frm_nums = ttk.Frame(ven)
    frm_nums.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=6)
    ttk.Label(frm_nums, text="Máx pistas (1–50):").grid(row=0, column=0, sticky="w")
    entry_limit = ttk.Entry(frm_nums, width=4); entry_limit.insert(0, "15")
    entry_limit.grid(row=0, column=1, padx=(4,20))
    ttk.Label(frm_nums, text="Pop mín (0–100):").grid(row=0, column=2, sticky="w")
    entry_pop = ttk.Entry(frm_nums, width=4); entry_pop.insert(0, "0")
    entry_pop.grid(row=0, column=3, padx=4)

    # ——— Área de resultados con scroll ———
    txt_frame = ttk.Frame(ven)
    txt_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
    txt_frame.columnconfigure(0, weight=1); txt_frame.rowconfigure(0, weight=1)
    text_area = tk.Text(txt_frame, wrap="word")
    text_area.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(txt_frame, command=text_area.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    text_area.config(yscrollcommand=scrollbar.set)

    # ——— Nombre de la nueva playlist ———
    ttk.Label(ven, text="Nombre de la nueva playlist:")\
        .grid(row=5, column=0, sticky="w", padx=10)
    entry_playlist = ttk.Entry(ven)
    entry_playlist.insert(0, "Mi playlist")
    entry_playlist.grid(row=5, column=1, sticky="ew", padx=10, pady=4)

    # ——— Barra de estado ———
    status = ttk.Label(ven, text="Listo", relief="sunken", anchor="w")
    status.grid(row=7, column=0, columnspan=2, sticky="ew", padx=0, pady=(4,0))

    # ——— Preparar seeds y cache ———
    try:
        seeds_spotify = sp.recommendation_genre_seeds()
    except:
        seeds_spotify = []
    artist_genres_cache: dict[str, list[str]] = {}

    # ——— Llamadas seguras (rate-limit) ———
    def call_safe(fn, *a, **k):
        for i in range(3):
            try:
                return fn(*a, **k)
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    time.sleep(1.5 * (i+1))
                else:
                    raise
        raise RuntimeError("Rate-limit continuo en Spotify")

    # ——— Cola y worker para no bloquear UI ———
    cola = queue.Queue()
    def _worker(params):
        texto_raw, generos_usr, seeds, lim, pop_min, texto_busq, use_pop, use_gen = params
        # 1) recomendaciones
        pistas = []
        if use_gen and seeds:
            try:
                pistas = call_safe(sp.recommendations,
                                   seed_genres=seeds, limit=lim)["tracks"]
            except:
                pistas = []
        # 2) buscar texto
        if len(pistas) < lim:
            try:
                extra = call_safe(sp.search,
                                  q=texto_busq or texto_raw,
                                  type="track", limit=lim*2)["tracks"]["items"]
                pistas.extend(extra)
            except:
                pass
        # 3) quitar duplicados
        vistos, únicos = set(), []
        for p in pistas:
            if p["id"] not in vistos:
                vistos.add(p["id"]); únicos.append(p)
        pistas = únicos
        # 4) filtrar por género
        if use_gen and generos_usr:
            ids = [a["id"] for p in pistas for a in p["artists"]]
            faltantes = [i for i in ids if i not in artist_genres_cache]
            for lote in (faltantes[i:i+50] for i in range(0, len(faltantes), 50)):
                try:
                    arts = call_safe(sp.artists, lote)["artists"]
                    for art in arts:
                        artist_genres_cache[art["id"]] = art.get("genres", [])
                except:
                    for aid in lote:
                        artist_genres_cache[aid] = []
            pistas = [
                p for p in pistas
                if any(
                    any(g in gen.lower() for gen in artist_genres_cache.get(a["id"], []))
                    for g in generos_usr for a in p["artists"]
                )
            ]
        # 5) filtrar por popularidad
        if use_pop:
            pistas = [p for p in pistas if p.get("popularity",0) >= pop_min]
        cola.put(pistas[:lim])

    # ——— Función que lanza la búsqueda escalonada ———
    def lanzar_busqueda():
        texto_raw = entry_texto.get().strip()
        if not texto_raw:
            messagebox.showinfo("Aviso", "Escribe algo para buscar.")
            return
        # géneros manuales o extraídos
        generos_usr = [g.strip().lower() for g in entry_genres.get().split(",") if g.strip()]
        if not generos_usr:
            m = re.search(r'gé?nero\s+(.+)', texto_raw, flags=re.I)
            if m:
                generos_usr = [g.strip().lower() for g in re.split(r',| y ', m.group(1))]
                texto_busq = texto_raw[:m.start()].strip()
            else:
                texto_busq = texto_raw
        else:
            texto_busq = texto_raw
        # semilla difusa
        seeds = []
        for g in generos_usr:
            match = difflib.get_close_matches(g, seeds_spotify, n=1, cutoff=0.4)
            if match:
                seeds.append(match[0])
        seeds = seeds[:5]
        # parámetros
        lim = max(1, min(int(entry_limit.get()), 50))
        pop_min = max(0, min(int(entry_pop.get()), 100))
        estrategias = [(True,True),(False,True),(True,False),(False,False)]
        status.config(text="Buscando…")
        text_area.delete("1.0","end")

        def probar(idx=0):
            if idx >= len(estrategias):
                cola.put([]); return
            use_pop, use_gen = estrategias[idx]
            params = (texto_raw, generos_usr, seeds, lim,
                      pop_min, texto_busq, use_pop, use_gen)
            threading.Thread(target=_worker, args=(params,), daemon=True).start()
            def check():
                if cola.empty():
                    ven.after(100, check)
                else:
                    pistas = cola.get()
                    if pistas or idx == len(estrategias)-1:
                        mostrar(pistas)
                    else:
                        probar(idx+1)
            check()

        probar()

    # ——— Mostrar resultados ———
    def mostrar(pistas):
        if pistas:
            status.config(text=f"Listo – {len(pistas)} pistas")
        else:
            status.config(text="Sin resultados")
        ven.uris = [p["uri"] for p in pistas]
        text_area.delete("1.0","end")
        if not pistas:
            text_area.insert("end","No se encontraron pistas.\n")
        else:
            for i,p in enumerate(pistas,1):
                artistas = ", ".join(a["name"] for a in p["artists"])
                text_area.insert("end", f"{i:2d}. {p['name']} — {artistas} (pop {p.get('popularity',0)})\n")

    # ——— Crear playlist ———
    def crear_playlist():
        uris = getattr(ven, "uris", [])
        if not uris:
            messagebox.showinfo("Aviso", "Primero haz una búsqueda.")
            return
        nombre = entry_playlist.get().strip() or "Mi playlist"
        try:
            uid = call_safe(sp.current_user)["id"]
            nueva = call_safe(sp.user_playlist_create, uid, nombre, public=True)
            call_safe(sp.playlist_add_items, nueva["id"], uris)
            messagebox.showinfo("¡Listo!", f"Playlist '{nombre}' creada.")
        except Exception as e:
            messagebox.showerror("Error", f"No pude crear la playlist:\n{e}")

    # ——— Botones y atajos ———
    frm_btn = ttk.Frame(ven)
    frm_btn.grid(row=6, column=0, columnspan=2, pady=8)
    ttk.Button(frm_btn, text="Buscar/Recomendar", command=lanzar_busqueda).pack(side="left", padx=8)
    ttk.Button(frm_btn, text="Crear Playlist",      command=crear_playlist).pack(side="left", padx=8)

    ven.bind("<Return>",     lambda e: lanzar_busqueda())
    ven.bind("<Control-p>",  lambda e: crear_playlist())

    # ayuda inicial
    status.config(text="Listo – escribe tu frase y pulsa ⏎")


from tkinter import simpledialog
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

def ventana_top_tracks(sp, root):
    """
    1) Busca un artista por nombre.
    2) Descarga TODOS sus álbumes (incluye singles, compilaciones y colaboraciones).
    3) Saca TODAS las pistas de esos álbumes.
    4) Pide a Spotify la popularidad de cada pista.
    5) Elimina duplicados.
    6) Aplica filtros de popularidad, colaboraciones y géneros.
    7) Ordena por Popularidad, Nombre o Fecha.
    8) Muestra el listado y permite crear playlist.
    """

    ven = tk.Toplevel(root)
    ven.title("Top Tracks Mejorado")
    ven.geometry("450x550")

    # — Entradas básicas
    tk.Label(ven, text="Artista:").pack(pady=(10,0))
    e_art = tk.Entry(ven, width=40); e_art.pack(pady=5)

    tk.Label(ven, text="Cuántos tracks (1–50):").pack(pady=(5,0))
    e_num = tk.Entry(ven, width=5); e_num.insert(0, "10"); e_num.pack(pady=5)

    tk.Label(ven, text="Popularidad mínima (0–100):").pack(pady=(5,0))
    e_pop = tk.Entry(ven, width=5); e_pop.insert(0, "0"); e_pop.pack(pady=5)

    tk.Label(ven, text="Colaboraciones:").pack(pady=(5,0))
    coll_var = tk.StringVar(value="Todas")
    for val, txt in [("Todas","Todas"), ("Solo","Solo artista"), ("Colab","Solo colaboraciones")]:
        tk.Radiobutton(ven, text=txt, variable=coll_var, value=val).pack(anchor="w", padx=20)

    tk.Label(ven, text="Géneros secundarios (sep. coma):").pack(pady=(5,0))
    e_gen = tk.Entry(ven, width=40); e_gen.pack(pady=5)

    tk.Label(ven, text="Ordenar por:").pack(pady=(5,0))
    order_var = tk.StringVar(value="Popularidad")
    tk.OptionMenu(ven, order_var, "Popularidad", "Nombre", "Fecha").pack(pady=5)

    text_area = tk.Text(ven, height=12, wrap="word")
    text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def buscar_y_mostrar():
        text_area.delete("1.0", tk.END)
        nombre = e_art.get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "Pon el nombre del artista.")
            return

        # — 1) Buscar artista
        try:
            arts = sp.search(q=nombre, type="artist", limit=1)["artists"]["items"]
            if not arts:
                messagebox.showinfo("Info", "Artista no encontrado.")
                return
            art = arts[0]
        except Exception as e:
            messagebox.showerror("Error", f"No pude buscar artista:\n{e}")
            return

        # — 2) Leer TODOS sus álbumes
        album_ids = set()
        offset = 0
        while True:
            resp = sp.artist_albums(
                art["id"],
                album_type="album,single,compilation,appears_on",
                limit=50,
                offset=offset,
                country="US"
            )["items"]
            if not resp:
                break
            for alb in resp:
                album_ids.add(alb["id"])
            offset += len(resp)

        # — 3) Sacar TODAS las pistas de cada álbum
        raw_tracks = []
        for alb_id in album_ids:
            off2 = 0
            while True:
                items = sp.album_tracks(alb_id, limit=50, offset=off2)["items"]
                if not items:
                    break
                raw_tracks.extend(items)
                off2 += len(items)

        if not raw_tracks:
            messagebox.showinfo("Info", "No hay pistas disponibles.")
            return

        # — 4) Pedir popularidad por lotes de 50
        # Creamos lista única de pistas por ID
        seen = set(); uniq = []
        for t in raw_tracks:
            tid = t["id"]
            if tid and tid not in seen:
                seen.add(tid)
                uniq.append(t)
        # Añadimos popularidad y álbum a cada pista
        for i in range(0, len(uniq), 50):
            batch = uniq[i:i+50]
            ids = [t["id"] for t in batch]
            details = sp.tracks(ids)["tracks"]
            for det, orig in zip(details, batch):
                orig["popularity"] = det.get("popularity", 0)
                orig["album"] = det.get("album", {})

        # — 5) Aplicar filtros
        try:
            n = max(1, min(int(e_num.get()), 50))
        except:
            n = 10
        try:
            min_pop = max(0, min(int(e_pop.get()), 100))
        except:
            min_pop = 0

        coll_opt = coll_var.get()
        secs = [g.strip().lower() for g in e_gen.get().split(",") if g.strip()]

        # Cache de géneros de artistas para filtros
        artist_ids = {a["id"] for t in uniq for a in t["artists"]}
        genres = {}
        for i in range(0, len(artist_ids), 50):
            batch = list(artist_ids)[i:i+50]
            resp2 = sp.artists(batch)["artists"]
            for aobj in resp2:
                genres[aobj["id"]] = [g.lower() for g in aobj.get("genres", [])]

        filt = []
        for t in uniq:
            if t["popularity"] < min_pop:
                continue
            if coll_opt == "Solo" and len(t["artists"])>1:
                continue
            if coll_opt == "Colab" and len(t["artists"])<2:
                continue
            if secs:
                ok = False
                for a in t["artists"]:
                    for g in genres.get(a["id"], []):
                        if any(s in g for s in secs):
                            ok = True; break
                    if ok: break
                if not ok:
                    continue
            filt.append(t)

        # — 6) Ordenar
        keymap = {
            "Popularidad": lambda x: x["popularity"],
            "Nombre":      lambda x: x["name"].lower(),
            "Fecha":       lambda x: x["album"].get("release_date","")
        }
        rev = order_var.get() in ["Popularidad","Fecha"]
        filt.sort(key=keymap[order_var.get()], reverse=rev)

        # Tomamos sólo los n primeros
        resultados = filt[:n]
        ven.uris = [t["uri"] for t in resultados]

        # — 7) Mostrar
        text_area.insert("end", f"Mostrando {len(resultados)} de {art['name']}:\n\n")
        for i, t in enumerate(resultados, 1):
            artistas = ", ".join(a["name"] for a in t["artists"])
            text_area.insert("end", f"{i}. {t['name']} — {artistas} (pop {t['popularity']})\n")

    def crear_playlist_top():
        uris = getattr(ven, "uris", [])
        if not uris:
            messagebox.showinfo("Info", "Primero busca las canciones.")
            return
        pl_name = simpledialog.askstring("Playlist", "Nombre para la playlist:")
        if not pl_name:
            return
        try:
            uid = sp.current_user()["id"]
            pl = sp.user_playlist_create(uid, pl_name, public=True)
            sp.playlist_add_items(pl["id"], uris)
            messagebox.showinfo("¡Listo!", "Playlist creada.")
            ven.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No pude crear la playlist:\n{e}")

    # — Botones
    btns = tk.Frame(ven); btns.pack(pady=5)
    tk.Button(btns, text="Buscar", command=buscar_y_mostrar).pack(side="left", padx=5)
    tk.Button(btns, text="Crear Playlist", command=crear_playlist_top).pack(side="left", padx=5)



# --------------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------------
def main():
    sp = autenticar_spotify()
    root = tk.Tk()
    root.title("Gestor Spotify (Completo)")
    root.geometry("800x600")

    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)

    # Menú Playlists
    menu_playlists = tk.Menu(menu_bar, tearoff=0)
    menu_playlists.add_command(
        label="Vaciar Playlists",
        command=lambda: ventana_vaciar_playlists(sp, root)
    )
    menu_playlists.add_command(
        label="Eliminar Playlists",
        command=lambda: ventana_eliminar_playlists(sp, root)
    )
    menu_playlists.add_command(
        label="Ver Playlists",
        command=lambda: ventana_ver_playlists(sp, root)
    )
    menu_playlists.add_command(
        label="Crear Playlist",
        command=lambda: ventana_crear_playlist(sp, root)
    )
    menu_bar.add_cascade(label="Playlists", menu=menu_playlists)

    # Menú Podcasts
    menu_podcasts = tk.Menu(menu_bar, tearoff=0)
    menu_podcasts.add_command(
        label="Sincronizar Podcasts (data)",
        command=lambda: ventana_sincronizar_podcasts_data(sp, root)
    )
    menu_bar.add_cascade(label="Podcasts", menu=menu_podcasts)

    # Gestor automático
    menu_gestor = tk.Menu(menu_bar, tearoff=0)
    menu_gestor.add_command(
        label="Gestor Automático de Artistas",
        command=lambda: VentanaGestorAutomatico(root, sp)
    )
    menu_bar.add_cascade(label="Gestor Automático", menu=menu_gestor)

    # Recomendaciones Artistapy
    menu_reco = tk.Menu(menu_bar, tearoff=0)
    menu_reco.add_command(
        label="#Artistapy",
        command=lambda: ventana_artistapy(sp, root)
    )
    menu_bar.add_cascade(label="Recomendaciones", menu=menu_reco)

     # Menú Búsqueda Libre
    menu_busqueda = tk.Menu(menu_bar, tearoff=0)
    menu_busqueda.add_command(
    label="Por Frase Libre",
    command=lambda: ventana_busqueda_avanzada(sp, root))
    menu_bar.add_cascade(label="Buscar Canciones", menu=menu_busqueda)


# ... tras menu_busqueda ...
    menu_bar.add_command(
    label="Top Tracks Artista",
    command=lambda: ventana_top_tracks(sp, root))


    menu_bar.add_command(label="Salir", command=root.destroy)

    tk.Label(root,
             text="¡Bienvenido al Gestor Completo de Spotify!",
             font=("Arial", 14)).pack(pady=20)

    status = tk.Label(root, text="Listo", bd=1,
                      relief=tk.SUNKEN, anchor=tk.W)
    status.pack(side=tk.BOTTOM, fill=tk.X)

    root.mainloop()


if __name__ == "__main__":
    main()
