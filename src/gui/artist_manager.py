# src/gui/artist_manager.py

"""
VentanaGestorAutomático: busca un artista, obtiene sus canciones únicas y gestiona playlists.
Interfaz pulida: tema oscuro, estilo Spotify, grid adaptable y scroll total.
"""

import time
import unicodedata
import re
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from spotipy import Spotify

import src.config as cfg


class VentanaGestorAutomatico(tk.Toplevel):
    def __init__(self, parent: tk.Tk, sp: Spotify):
        super().__init__(parent)
        self.sp = sp

        # Configuración de ventana
        self.title("Gestor de Playlists Automáticas")
        self.geometry("800x750")
        self.configure(bg=cfg.BG_MAIN)
        self.minsize(700, 650)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Obtener ID de usuario
        try:
            self.user_id = self.sp.current_user()["id"]
        except Exception:
            messagebox.showerror("Error", "No se pudo obtener info del usuario.")
            self.destroy()
            return

        # Datos y estado
        self.artists_found: list[dict] = []
        self.songs: list[dict] = []
        self.playlists: list[dict] = []
        self.artist_id: str = ""
        self.play_var = tk.StringVar(value="nueva")

        # Estilos
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=cfg.BG_MAIN)
        style.configure("Header.TLabel",
                        background=cfg.BG_MAIN,
                        foreground=cfg.ACCENT,
                        font=(cfg.FONT_BOLD[0], 14))
        style.configure("TLabel",
                        background=cfg.BG_MAIN,
                        foreground=cfg.TEXT_PRIMARY,
                        font=cfg.FONT_REGULAR)
        style.configure("TButton",
                        background=cfg.ACCENT,
                        foreground=cfg.TEXT_PRIMARY,
                        font=cfg.FONT_BOLD,
                        padding=6)
        style.map("TButton", background=[("active", cfg.ACCENT_HOVER)])
        style.configure("TEntry",
                        fieldbackground=cfg.BG_PANEL,
                        foreground=cfg.TEXT_PRIMARY,
                        padding=4)
        style.configure("TRadiobutton",
                        background=cfg.BG_MAIN,
                        foreground=cfg.TEXT_PRIMARY,
                        font=cfg.FONT_REGULAR)

        # — Scrollable area setup — #
        container = ttk.Frame(self, style="TFrame")
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        canvas = tk.Canvas(container,
                           bg=cfg.BG_MAIN,
                           highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(container,
                            orient="vertical",
                            command=canvas.yview)
        vsb.grid(row=0, column=1, sticky="ns")

        canvas.configure(yscrollcommand=vsb.set)

        # Frame interno
        scroll_frame = ttk.Frame(canvas, style="TFrame", padding=10)
        scroll_window = canvas.create_window((0, 0),
                                             window=scroll_frame,
                                             anchor="nw")
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        # Ajusta ancho
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(scroll_window, width=e.width)
        )

        # Scroll con rueda
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # `main` = scroll_frame
        main = scroll_frame
        main.columnconfigure(0, weight=1)
        main.rowconfigure(5, weight=1)

        # --- 1) Búsqueda de artista --- #
        ttk.Label(main, text="1) Buscar artista", style="Header.TLabel")\
            .grid(row=0, column=0, sticky="w", pady=(0,8))
        busc = ttk.Frame(main, style="TFrame")
        busc.grid(row=1, column=0, sticky="ew", pady=(0,12))
        busc.columnconfigure(0, weight=1)
        self.entry_artist = ttk.Entry(busc, style="TEntry")
        self.entry_artist.grid(row=0, column=0, sticky="ew", padx=(0,5))
        ttk.Button(busc, text="Buscar", style="TButton",
                   command=self.search_artist).grid(row=0, column=1)

        self.lb_artists = tk.Listbox(
            main,
            bg=cfg.BG_PANEL, fg=cfg.TEXT_PRIMARY,
            selectbackground=cfg.ACCENT,
            activestyle="none",
            highlightthickness=0,
            relief="flat",
            height=6
        )
        self.lb_artists.grid(row=2, column=0, sticky="nsew")
        sb_art = ttk.Scrollbar(main, orient="vertical",
                               command=self.lb_artists.yview)
        sb_art.grid(row=2, column=1, sticky="ns")
        self.lb_artists.configure(yscrollcommand=sb_art.set)
        self.lb_artists.bind("<<ListboxSelect>>", self.on_artist_select)

        # --- 2) Informe de canciones --- #
        rpt = ttk.LabelFrame(main, text="Resumen de canciones",
                             style="TFrame", padding=8)
        rpt.grid(row=3, column=0, sticky="ew", pady=10)
        rpt.columnconfigure(0, weight=1)
        self.lbl_report = ttk.Label(rpt, text="No hay datos aún.", style="TLabel")
        self.lbl_report.grid(row=0, column=0, sticky="w")

        # --- 3) Lista de canciones únicas --- #
        songs_f = ttk.LabelFrame(main, text="Canciones únicas encontradas",
                                 style="TFrame", padding=8)
        songs_f.grid(row=4, column=0, sticky="nsew", pady=5)
        songs_f.columnconfigure(0, weight=1)
        songs_f.rowconfigure(0, weight=1)
        self.tree_songs = ttk.Treeview(
            songs_f,
            columns=("Name",),
            show="headings",
            selectmode="none",
            height=4
        )
        self.tree_songs.heading("Name", text="Título de canción")
        self.tree_songs.column("Name", anchor="w")
        self.tree_songs.grid(row=0, column=0, sticky="nsew")
        sb_songs = ttk.Scrollbar(songs_f, orient="vertical",
                                 command=self.tree_songs.yview)
        sb_songs.grid(row=0, column=1, sticky="ns")
        self.tree_songs.configure(yscrollcommand=sb_songs.set)

        # --- 4) Generar o actualizar playlist --- #
        play_f = ttk.LabelFrame(main, text="Generar o actualizar playlist",
                                style="TFrame", padding=8)
        play_f.grid(row=5, column=0, sticky="ew", pady=(10,0))
        play_f.columnconfigure(1, weight=1)
        ttk.Radiobutton(play_f, text="Crear nueva",
                        variable=self.play_var, value="nueva",
                        style="TRadiobutton",
                        command=self.update_play_option)\
            .grid(row=0, column=0, padx=(0,10))
        ttk.Radiobutton(play_f, text="Usar existente",
                        variable=self.play_var, value="existente",
                        style="TRadiobutton",
                        command=self.update_play_option)\
            .grid(row=0, column=1)

        self.dynamic = ttk.Frame(play_f, style="TFrame")
        self.dynamic.grid(row=1, column=0, columnspan=2,
                          sticky="ew", pady=5)
        self.update_play_option()

        # --- Botones finales --- #
        btns = ttk.Frame(main, style="TFrame", padding=5)
        btns.grid(row=6, column=0, sticky="e", pady=(10,0))
        ttk.Button(btns, text="Reset", style="TButton",
                   command=self.reset_to_artist_search).grid(row=0, column=0, padx=5)
        ttk.Button(btns, text="Cerrar", style="TButton",
                   command=self.destroy).grid(row=0, column=1)

    # Métodos de lógica originales intactos:
    def search_artist(self):
        q = self.entry_artist.get().strip()
        if not q:
            messagebox.showinfo("Info", "Ingresa un nombre.")
            return
        try:
            res = self.sp.search(q=q, type="artist", limit=5)["artists"]["items"]
        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar artista:\n{e}")
            return
        self.artists_found = res
        self.lb_artists.delete(0, tk.END)
        for art in res:
            self.lb_artists.insert(tk.END, art["name"])

    def on_artist_select(self, _evt):
        sel = self.lb_artists.curselection()
        if not sel:
            return
        art = self.artists_found[sel[0]]
        if messagebox.askyesno("Confirmar", f"Seleccionaste {art['name']}. ¿Continuar?"):
            self.artist_id = art["id"]
            self.fetch_artist_songs()

    def fetch_artist_songs(self):
        try:
            self.songs = self.obtener_canciones_artista_completas(self.artist_id)
            messagebox.showinfo("Info", f"Se encontraron {len(self.songs)} canciones únicas.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener canciones:\n{e}")
            return
        self.tree_songs.delete(*self.tree_songs.get_children())
        for s in self.songs:
            self.tree_songs.insert("", "end", values=(s["name"],))
        self.lbl_report.config(text=f"Total únicas: {len(self.songs)}")

    def obtener_canciones_artista_completas(self, artist_id: str):
        """Devuelve TODAS las canciones del artista sin duplicados “alternos”."""
        MARKETS = ("US", "MX")
        ALT_FLAGS = (
            "acoustic", "live", "en vivo", "unplugged", "instrumental",
            "remaster", "remastered", "demo", "karaoke", "edit",
            "mix", "remix", "versión", "version", "session"
        )
        NOISE = ("feat.", "featuring", "ft.", "with", "con")
        elegido: dict[str, dict] = {}
        clean_punct = re.compile(r"[()\[\]{}\-–_:]")
        total_raw = 0

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
            alt = es_alt(title, album_name)
            if base not in elegido or (elegido[base]["alt"] and not alt):
                elegido[base] = {"track": track, "alt": alt}

        # 1) Álbumes / singles / compilados
        try:
            alb_resp = self.sp.artist_albums(
                artist_id,
                album_type="album,single,compilation,appears_on",
                limit=50
            )
        except Exception:
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
                    tr_resp = self.sp.album_tracks(alb["id"], limit=50, market=m)
                except Exception:
                    continue
                while True:
                    for t in tr_resp.get("items", []):
                        if any(a["id"] == artist_id for a in t["artists"]):
                            considera(t, alb_name)
                    if not tr_resp.get("next"):
                        break
                    tr_resp = self.sp.next(tr_resp)

        # 2) Búsqueda global
        try:
            art_name = self.sp.artist(artist_id)["name"]
            offset = 0
            while True:
                sr = self.sp.search(q=f'artist:"{art_name}"', type="track",
                                    limit=50, offset=offset)
                for t in sr["tracks"]["items"]:
                    if any(a["id"] == artist_id for a in t["artists"]):
                        considera(t, "")
                if not sr["tracks"]["next"]:
                    break
                offset += 50
        except Exception:
            pass

        return [
            {"id": d["track"]["id"], "name": d["track"]["name"]}
            for d in elegido.values()
        ]

    def update_play_option(self):
        for w in self.dynamic.winfo_children():
            w.destroy()
        if self.play_var.get() == "nueva":
            ttk.Label(self.dynamic, text="Nombre playlist:", style="TLabel")\
                .grid(row=0, column=0, sticky="w")
            self.new_name = ttk.Entry(self.dynamic, style="TEntry")
            self.new_name.grid(row=0, column=1, sticky="ew", padx=(5,0))
            ttk.Button(self.dynamic, text="Crear & Agregar", style="TButton",
                       command=self.crear_playlist_y_agregar_songs)\
                .grid(row=1, column=0, columnspan=2, pady=5)
        else:
            ttk.Label(self.dynamic, text="Buscar playlist:", style="TLabel")\
                .grid(row=0, column=0, sticky="w")
            self.search_pl = ttk.Entry(self.dynamic, style="TEntry")
            self.search_pl.grid(row=0, column=1, sticky="ew", padx=(5,0))
            self.search_pl.bind("<KeyRelease>", self.filtrar_playlists)
            self.pl_list = tk.Listbox(
                self.dynamic,
                bg=cfg.BG_PANEL, fg=cfg.TEXT_PRIMARY,
                selectbackground=cfg.ACCENT,
                activestyle="none",
                highlightthickness=0,
                relief="flat",
                height=4
            )
            self.pl_list.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
            self.load_all_playlists()
            ttk.Button(self.dynamic, text="Actualizar", style="TButton",
                       command=self.actualizar_playlist_seleccionada)\
                .grid(row=2, column=0, columnspan=2, pady=5)

    def crear_playlist_y_agregar_songs(self):
        name = self.new_name.get().strip()
        if not name:
            messagebox.showinfo("Info", "Ingresa nombre.")
            return
        pl = self.sp.user_playlist_create(
            self.user_id, name, public=True,
            description="Playlist generada automáticamente"
        )
        ids = [s["id"] for s in self.songs]
        for i in range(0, len(ids), 100):
            self.sp.playlist_add_items(pl["id"], ids[i:i+100])
            time.sleep(0.5)
        messagebox.showinfo("Listo", "Playlist creada y canciones agregadas.")

    def load_all_playlists(self):
        self.playlists.clear()
        self.pl_list.delete(0, tk.END)
        res = self.sp.current_user_playlists(limit=50)
        while True:
            for p in res["items"]:
                self.playlists.append(p)
                self.pl_list.insert(tk.END, p["name"])
            if not res.get("next"):
                break
            res = self.sp.next(res)

    def filtrar_playlists(self, _evt):
        term = self.search_pl.get().strip().lower()
        self.pl_list.delete(0, tk.END)
        for p in self.playlists:
            if term in p["name"].lower():
                self.pl_list.insert(tk.END, p["name"])

    def actualizar_playlist_seleccionada(self):
        sel = self.pl_list.curselection()
        if not sel:
            messagebox.showinfo("Info", "Selecciona playlist.")
            return
        pl = self.playlists[sel[0]]
        existentes = {
            item["track"]["id"]
            for item in self.sp.playlist_items(pl["id"])["items"]
        }
        pendientes = [s["id"] for s in self.songs if s["id"] not in existentes]
        for i in range(0, len(pendientes), 100):
            self.sp.playlist_add_items(pl["id"], pendientes[i:i+100])
            time.sleep(0.5)
        messagebox.showinfo("Listo", "Playlist actualizada.")

    def reset_to_artist_search(self):
        self.songs.clear()
        self.artists_found.clear()
        self.lb_artists.delete(0, tk.END)
        self.tree_songs.delete(*self.tree_songs.get_children())
        self.lbl_report.config(text="No hay datos aún.")
        self.entry_artist.delete(0, tk.END)
        self.play_var.set("nueva")
        self.update_play_option()
