# src/gui/artist_manager.py
"""
VentanaGestorAutomático: busca un artista, obtiene sus canciones únicas y gestiona playlists.
Interfaz pulida: tema oscuro, estilo Spotify, grid adaptable y componentes refinados.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from spotipy import Spotify
import time
import unicodedata
import re

class VentanaGestorAutomatico(ttk.Frame):
    def __init__(self, parent: ttk.Frame, sp: Spotify, **kwargs):
        super().__init__(parent, **kwargs)
        self.sp = sp

        try:
            self.user_id = self.sp.current_user()["id"]
        except Exception as e:
            messagebox.showerror("Error de Autenticación", f"No se pudo obtener info del usuario.\n{e}")
            self.destroy()
            return

        self.artists_found: list[dict] = []
        self.songs: list[dict] = []
        self.playlists: list[dict] = []
        self.artist_id: str = ""

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#191414")
        style.configure("Header.TLabel", background="#191414", foreground="#1DB954", font=("Segoe UI", 14, "bold"))
        style.configure("TLabel", background="#191414", foreground="#FFFFFF", font=("Segoe UI", 10))
        style.configure("TButton", background="#1DB954", foreground="#FFFFFF", font=("Segoe UI", 10, "bold"), padding=6)
        style.map("TButton", background=[("active", "#1ed760")])
        style.configure("TEntry", fieldbackground="#2a2a2a", foreground="#FFFFFF", padding=4)
        style.configure("TRadiobutton", background="#191414", foreground="#FFFFFF", font=("Segoe UI", 10))

        self._crear_widgets()

    def _crear_widgets(self):
        main = ttk.Frame(self, style="TFrame", padding=15)
        main.pack(expand=True, fill=tk.BOTH)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(4, weight=1) # Fila de la lista de canciones

        # 1) Búsqueda de artista
        ttk.Label(main, text="1) Buscar artista", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 5))
        busc = ttk.Frame(main, style="TFrame")
        busc.grid(row=1, column=0, sticky="ew", pady=5)
        busc.columnconfigure(0, weight=1)
        self.entry_artist = ttk.Entry(busc, style="TEntry")
        self.entry_artist.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(busc, text="Buscar", command=self.search_artist).grid(row=0, column=1)

        self.lb_artists = tk.Listbox(main, bg="#2a2a2a", fg="white", selectbackground="#1DB954", height=6, bd=0)
        self.lb_artists.grid(row=2, column=0, sticky="nsew", pady=5)
        sb_art = ttk.Scrollbar(main, orient="vertical", command=self.lb_artists.yview)
        sb_art.grid(row=2, column=1, sticky="ns")
        self.lb_artists.config(yscrollcommand=sb_art.set)
        self.lb_artists.bind("<<ListboxSelect>>", self.on_artist_select)

        # 2) Informe de canciones (Recuperado del código original)
        rpt = ttk.LabelFrame(main, text="Resumen de canciones", padding=8)
        rpt.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        rpt.columnconfigure(0, weight=1)
        self.lbl_report = ttk.Label(rpt, text="No hay datos aún.", style="TLabel")
        self.lbl_report.grid(row=0, column=0, sticky="w")

        # 3) Lista de canciones únicas
        songs_f = ttk.LabelFrame(main, text="Canciones únicas encontradas", padding=8)
        songs_f.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=5)
        songs_f.columnconfigure(0, weight=1)
        songs_f.rowconfigure(0, weight=1)
        self.tree_songs = ttk.Treeview(songs_f, columns=("Name",), show="headings", selectmode="none", height=8)
        self.tree_songs.heading("Name", text="Título de canción")
        self.tree_songs.column("Name", anchor="w")
        self.tree_songs.grid(row=0, column=0, sticky="nsew")
        sb_songs = ttk.Scrollbar(songs_f, orient="vertical", command=self.tree_songs.yview)
        sb_songs.grid(row=0, column=1, sticky="ns")
        self.tree_songs.configure(yscrollcommand=sb_songs.set)

        # 4) Generar o actualizar playlist
        play_f = ttk.LabelFrame(main, text="Generar o actualizar playlist", padding=8)
        play_f.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        play_f.columnconfigure(1, weight=1)
        self.play_var = tk.StringVar(value="nueva")
        ttk.Radiobutton(play_f, text="Crear nueva", variable=self.play_var, value="nueva", command=self.update_play_option).grid(row=0, column=0, padx=(0, 10))
        ttk.Radiobutton(play_f, text="Usar existente", variable=self.play_var, value="existente", command=self.update_play_option).grid(row=0, column=1)

        self.dynamic = ttk.Frame(play_f, style="TFrame")
        self.dynamic.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.update_play_option()

        # Botón de Reset
        ttk.Button(main, text="Reset", command=self.reset_to_artist_search).grid(row=6, column=0, sticky="e", pady=(10, 0))

    def search_artist(self):
        q = self.entry_artist.get().strip()
        if not q: return messagebox.showinfo("Info", "Ingresa un nombre.")
        try:
            res = self.sp.search(q=q, type="artist", limit=10)["artists"]["items"]
            self.artists_found = res
            self.lb_artists.delete(0, tk.END)
            for art in res:
                self.lb_artists.insert(tk.END, art["name"])
        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar artista:\n{e}")

    def on_artist_select(self, _evt):
        sel = self.lb_artists.curselection()
        if not sel: return
        art = self.artists_found[sel[0]]
        if messagebox.askyesno("Confirmar", f"Seleccionaste {art['name']}. ¿Obtener todas sus canciones? (Puede tardar)"):
            self.artist_id = art["id"]
            self.fetch_artist_songs()

    def fetch_artist_songs(self):
        try:
            self.songs = self.obtener_canciones_artista_completas(self.artist_id)
            messagebox.showinfo("Info", f"Se encontraron {len(self.songs)} canciones únicas.")
            
            self.tree_songs.delete(*self.tree_songs.get_children())
            for s in self.songs:
                self.tree_songs.insert("", "end", values=(s["name"],))
            
            # Actualizar el label de resumen
            self.lbl_report.config(text=f"Total únicas: {len(self.songs)}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener canciones:\n{e}")

    def obtener_canciones_artista_completas(self, artist_id: str):
        """Devuelve TODAS las canciones del artista sin duplicados “alternos”."""
        MARKETS = ("US", "MX")
        ALT_FLAGS = (
            "acoustic", "live", "en vivo", "unplugged", "instrumental",
            "remaster", "remastered", "demo", "karaoke", "edit",
            "mix", "remix", "versión", "version", "session"
        )
        NOISE = (
            "feat.", "featuring", "ft.", "with", "con"
        )
        elegido: dict[str, dict] = {}
        total_raw = 0
        clean_punct = re.compile(r"[()\[\]{}\-–_:]")

        def slug(txt: str) -> str:
            txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
            txt = txt.lower()
            txt = clean_punct.sub(" ", txt)
            for w in (*ALT_FLAGS, *NOISE):
                txt = txt.replace(w, " ")
            return " ".join(txt.split())

        def es_alt(titulo: str, album: str) -> bool:
            t, a = titulo.lower(), album.lower()
            return any(w in t or w in a for w in ALT_FLAGS)

        def considera(track: dict, album_name: str):
            nonlocal total_raw
            total_raw += 1
            tid = track.get("id")
            if not tid:
                return
            title = track.get("name", "").strip()
            base = slug(title)
            alt  = es_alt(title, album_name)
            if base not in elegido or (elegido[base]["alt"] and not alt):
                elegido[base] = {"track": track, "alt": alt}

        # 1) álbumes / singles / compilados
        try:
            alb_resp = self.sp.artist_albums(
                artist_id,
                album_type="album,single,compilation,appears_on",
                limit=50
            )
        except Exception:
            return []
        albums = []
        while alb_resp:
            albums.extend(alb_resp.get("items", []))
            alb_resp = self.sp.next(alb_resp) if alb_resp.get("next") else None

        for alb in albums:
            alb_name = alb.get("name", "")
            for m in MARKETS:
                try:
                    tr_resp = self.sp.album_tracks(alb["id"], limit=50, market=m)
                except Exception:
                    continue
                while tr_resp:
                    for t in tr_resp.get("items", []):
                        if any(a["id"] == artist_id for a in t.get("artists", [])):
                            considera(t, alb_name)
                    tr_resp = self.sp.next(tr_resp) if tr_resp.get("next") else None

        # 2) búsqueda global (singles sueltos / colaboraciones)
        try:
            art_name = self.sp.artist(artist_id)["name"]
            offset = 0
            while True:
                sr = self.sp.search(q=f'artist:"{art_name}"', type="track",
                                    limit=50, offset=offset)
                if not sr or not sr.get("tracks"): break
                
                for t in sr["tracks"]["items"]:
                    if any(a["id"] == artist_id for a in t.get("artists", [])):
                        considera(t, "")
                
                if not sr["tracks"]["next"]:
                    break
                offset += 50
        except Exception:
            pass

        # resultado final
        canciones = [
            {"id": d["track"]["id"], "name": d["track"]["name"]}
            for d in elegido.values()
        ]
        return canciones

    def update_play_option(self):
        for w in self.dynamic.winfo_children(): w.destroy()
        if self.play_var.get() == "nueva":
            ttk.Label(self.dynamic, text="Nombre playlist:").grid(row=0, column=0, sticky="w")
            self.new_name = ttk.Entry(self.dynamic, style="TEntry")
            self.new_name.grid(row=0, column=1, sticky="ew", padx=(5, 0))
            ttk.Button(self.dynamic, text="Crear & Agregar", command=self.crear_playlist_y_agregar_songs).grid(row=1, column=0, columnspan=2, pady=5)
        else:
            ttk.Label(self.dynamic, text="Buscar playlist:").grid(row=0, column=0, sticky="w")
            self.search_pl = ttk.Entry(self.dynamic, style="TEntry")
            self.search_pl.grid(row=0, column=1, sticky="ew", padx=(5, 0))
            self.search_pl.bind("<KeyRelease>", self.filtrar_playlists)
            self.pl_list = tk.Listbox(self.dynamic, bg="#2a2a2a", fg="white", selectbackground="#1DB954", height=4, bd=0)
            self.pl_list.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
            self.load_all_playlists()
            ttk.Button(self.dynamic, text="Actualizar", command=self.actualizar_playlist_seleccionada).grid(row=2, column=0, columnspan=2, pady=5)

    def crear_playlist_y_agregar_songs(self):
        name = self.new_name.get().strip()
        if not name: return messagebox.showinfo("Info", "Ingresa nombre.")
        if not self.songs: return messagebox.showinfo("Info", "No hay canciones para agregar.")
        try:
            pl = self.sp.user_playlist_create(self.user_id, name, public=True, description="Playlist generada automáticamente")
            ids = [s["id"] for s in self.songs]
            for i in range(0, len(ids), 100):
                self.sp.playlist_add_items(pl["id"], ids[i:i + 100])
                time.sleep(0.2)
            messagebox.showinfo("Listo", "Playlist creada y canciones agregadas.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la playlist: {e}")

    def load_all_playlists(self):
        self.playlists.clear(); self.pl_list.delete(0, tk.END)
        res = self.sp.current_user_playlists(limit=50)
        while res:
            for p in res["items"]:
                self.playlists.append(p)
                self.pl_list.insert(tk.END, p["name"])
            res = self.sp.next(res) if res["next"] else None

    def filtrar_playlists(self, _evt):
        term = self.search_pl.get().strip().lower()
        self.pl_list.delete(0, tk.END)
        for p in self.playlists:
            if term in p["name"].lower(): self.pl_list.insert(tk.END, p["name"])

    def actualizar_playlist_seleccionada(self):
        sel = self.pl_list.curselection()
        if not sel: return messagebox.showinfo("Info", "Selecciona playlist.")
        if not self.songs: return messagebox.showinfo("Info", "No hay canciones para agregar.")

        selected_name = self.pl_list.get(sel[0])
        pl_id = None
        # Busca el ID de la playlist en la lista completa para evitar desajustes por el filtro
        for p in self.playlists:
            if p["name"] == selected_name:
                pl_id = p["id"]
                break
        if not pl_id: return messagebox.showerror("Error", "No se encontró el ID de la playlist.")

        try:
            existentes = set()
            res = self.sp.playlist_items(pl_id, fields='items(track(id)),next')
            while res:
                existentes.update({item["track"]["id"] for item in res["items"] if item and item.get("track") and item["track"].get("id")})
                res = self.sp.next(res) if res["next"] else None
            
            pendientes = [s["id"] for s in self.songs if s["id"] not in existentes]
            if not pendientes: return messagebox.showinfo("Info", "No hay canciones nuevas que agregar.")

            for i in range(0, len(pendientes), 100):
                self.sp.playlist_add_items(pl_id, pendientes[i:i + 100])
                time.sleep(0.2)
            messagebox.showinfo("Listo", f"Playlist actualizada con {len(pendientes)} canciones nuevas.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar la playlist: {e}")

    def reset_to_artist_search(self):
        self.songs.clear(); self.artists_found.clear()
        self.lb_artists.delete(0, tk.END)
        self.tree_songs.delete(*self.tree_songs.get_children())
        self.lbl_report.config(text="No hay datos aún.") # Resetear el resumen
        self.entry_artist.delete(0, tk.END)
        self.play_var.set("nueva")
        self.update_play_option()