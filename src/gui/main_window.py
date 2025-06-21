"""
Ventana principal de SpotyVManager rediseñada al estilo Spotify:
– Sidebar scrollable con secciones y subopciones
– Cabecera con título y línea de acento
– Dashboard y grid de tarjetas
– Fondo completamente negro
– Colores y tipografías desde src/config.py
"""

import logging
import tkinter as tk
from tkinter import ttk, PhotoImage
from spotipy import Spotify

import src.config as cfg
from pathlib import Path

from .playlists import (
    ventana_vaciar_playlists,
    ventana_eliminar_playlists,
    ventana_ver_playlists,
    ventana_crear_playlist,
)
from .podcasts import ventana_sincronizar_podcasts_data
from .artist_manager import VentanaGestorAutomatico
from .artistapy import ventana_artistapy
from .search_advanced import ventana_busqueda_avanzada
from .top_tracks import ventana_top_tracks
from .admin_podcasts import VentanaAdminPodcasts

logger = logging.getLogger(__name__)

def build_main_window(sp: Spotify) -> tk.Tk:
    root = tk.Tk()
    root.title("SpotyVManager 🎧")
    root.geometry("1200x750")
    root.configure(bg=cfg.BG_MAIN)

    # — Ventanas únicas — #
    root.open_windows = {}
    def open_window(key, creator_fn):
        existing = root.open_windows.get(key)
        if existing and existing.winfo_exists():
            existing.lift()
            return existing
        win = creator_fn()
        win.transient(root); win.grab_set()
        win.update_idletasks()
        x = root.winfo_x() + (root.winfo_width() - win.winfo_width()) // 2
        y = root.winfo_y() + (root.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")
        root.open_windows[key] = win
        win.protocol("WM_DELETE_WINDOW", lambda: (root.open_windows.pop(key, None), win.destroy()))
        return win

    # — Carga de iconos PNG — #
    icons = {}
    assets_dir = cfg.ICON_PATH
    missing = []
    for name in ("playlists","podcasts","artists","search","top","exit"):
        p = assets_dir / f"icon_{name}.png"
        if p.exists():
            icons[name] = PhotoImage(file=str(p))
        else:
            icons[name] = None
            missing.append(p.name)
    if missing:
        logger.warning("Faltan iconos en src/assets/: %s", ", ".join(missing))
    root._icons = icons  # evitar recolección

    # — Estilos — #
    style = ttk.Style()
    style.theme_use("clam")

    # Sidebar principal
    style.configure("Sidebar.TFrame", background=cfg.BG_PANEL)
    style.configure("Sidebar.TButton",
                    font=cfg.FONT_REGULAR,
                    background=cfg.BG_PANEL,
                    foreground=cfg.TEXT_PRIMARY,
                    padding=(12,12), anchor="w",
                    borderwidth=0, cursor="hand2")
    style.map("Sidebar.TButton", background=[("active", cfg.ACCENT_HOVER)])
    # Sidebar subbotones
    style.configure("SidebarSub.TButton",
                    font=cfg.FONT_REGULAR,
                    background=cfg.BG_PANEL,
                    foreground=cfg.TEXT_SECOND,
                    padding=(32,8), anchor="w",
                    borderwidth=0, cursor="hand2")
    style.map("SidebarSub.TButton", background=[("active", cfg.ACCENT_HOVER)])
    # Cards
    style.element_create("RoundedFrame","from","clam")
    style.layout("Card.TFrame",[("RoundedFrame",{"sticky":"nswe"})])
    style.configure("Card.TFrame",
                    background=cfg.BG_PANEL, relief="flat",
                    borderwidth=0, padding=0,
                    highlightthickness=1, highlightbackground="#111111")
    style.configure("CardHover.TFrame",
                    background="#383838", relief="flat",
                    borderwidth=0, padding=0,
                    highlightthickness=2, highlightbackground=cfg.ACCENT_HOVER)
    # Accent Buttons
    style.configure("Accent.TButton",
                    font=cfg.FONT_BOLD,
                    background=cfg.ACCENT,
                    foreground=cfg.TEXT_PRIMARY,
                    padding=(12,8),
                    borderwidth=0,
                    cursor="hand2")
    style.map("Accent.TButton", background=[("active", cfg.ACCENT_HOVER)])
    # Labels
    style.configure("Title.TLabel",
                    background=cfg.BG_MAIN,
                    foreground=cfg.ACCENT,
                    font=(cfg.FONT_BOLD[0], 28))
    style.configure("Subtitle.TLabel",
                    background=cfg.BG_PANEL,
                    foreground=cfg.TEXT_PRIMARY,
                    font=cfg.FONT_BOLD)
    style.configure("Desc.TLabel",
                    background=cfg.BG_PANEL,
                    foreground=cfg.TEXT_SECOND,
                    font=(cfg.FONT_REGULAR[0], 10))

    # — Sidebar scrollable + Content — #
    container = ttk.Frame(root)
    container.pack(fill="both", expand=True)

    sidebar_canvas = tk.Canvas(container,
                               width=240,
                               bg=cfg.BG_PANEL,
                               highlightthickness=0)
    v_scroll = ttk.Scrollbar(container,
                             orient="vertical",
                             command=sidebar_canvas.yview)
    sidebar_canvas.configure(yscrollcommand=v_scroll.set)
    v_scroll.pack(side="left", fill="y")
    sidebar_canvas.pack(side="left", fill="y")

    sidebar = ttk.Frame(sidebar_canvas, style="Sidebar.TFrame")
    sidebar_id = sidebar_canvas.create_window((0,0), window=sidebar, anchor="nw")
    sidebar.bind("<Configure>", lambda e: sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all")))

    content = ttk.Frame(container)
    content.pack(side="right", fill="both", expand=True)

    def add_side_button(text, icon_key, cmd):
        btn = ttk.Button(sidebar, text="  "+text,
                         style="Sidebar.TButton", command=cmd)
        ico = icons.get(icon_key)
        if ico:
            btn.config(image=ico, compound="left"); btn.image = ico
        btn.pack(fill="x", pady=4)
        return btn

    def add_sub_button(text, cmd):
        btn = ttk.Button(sidebar, text=text,
                         style="SidebarSub.TButton", command=cmd)
        btn.pack(fill="x", pady=2)
        return btn

    # — Playlists — #
    add_side_button("Playlists", "playlists", lambda: None)
    add_sub_button("Vaciar",    lambda: open_window("vaciar_playlists", lambda: ventana_vaciar_playlists(sp, root)))
    add_sub_button("Eliminar",  lambda: open_window("eliminar_playlists", lambda: ventana_eliminar_playlists(sp, root)))
    add_sub_button("Ver",       lambda: open_window("ver_playlists", lambda: ventana_ver_playlists(sp, root)))
    add_sub_button("Crear",     lambda: open_window("crear_playlist", lambda: ventana_crear_playlist(sp, root)))
    # — Podcasts — #
    add_side_button("Podcasts", "podcasts", lambda: None)
    add_sub_button("Sincronizar",  lambda: open_window("sync_podcasts", lambda: ventana_sincronizar_podcasts_data(sp, root)))
    add_sub_button("Administrar", lambda: open_window("admin_podcasts", lambda: VentanaAdminPodcasts(root, sp)))
    # — Artistas — #
    add_side_button("Artistas", "artists", lambda: None)
    add_sub_button("Gestor Automático", lambda: open_window("gestor_artistico", lambda: VentanaGestorAutomatico(root, sp)))
    add_sub_button("Artistapy",        lambda: open_window("artistapy", lambda: ventana_artistapy(sp, root)))
    # — Otras — #
    add_side_button("Buscar Avanzada", "search", lambda: open_window("busqueda_avanzada", lambda: ventana_busqueda_avanzada(sp, root)))
    add_side_button("Top Tracks",      "top",    lambda: open_window("top_tracks", lambda: ventana_top_tracks(sp, root)))
    ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=10)
    add_side_button("Salir", "exit", root.destroy)

    # — Cabecera — #
    header = ttk.Frame(content, style="Card.TFrame")
    header.pack(fill="x", padx=30, pady=(20,10))
    ttk.Label(header, text="SpotyVManager", style="Title.TLabel")\
        .pack(side="left", padx=10)
    tk.Frame(header, bg=cfg.ACCENT, height=4)\
        .pack(fill="x", padx=(20,0), pady=(0,4), expand=True)

    # — Dashboard — #
    dash = ttk.Frame(content, style="Card.TFrame", padding=12)
    dash.pack(fill="x", padx=30, pady=(0,20))
    ttk.Label(dash, text="Gestiona tu música como nunca antes", style="Subtitle.TLabel")\
        .pack(anchor="w", pady=(0,10))
    for feat in [
        "Crear, ver, eliminar y vaciar playlists",
        "Consultar tus Top Tracks",
        "Sincronizar podcasts al instante",
        "Recomendaciones con Artistapy",
        "Búsqueda por frase, título o artista",
        "Administrar Podcasts y Playlists personalizados",
    ]:
        ttk.Label(dash, text="• "+feat, style="Desc.TLabel")\
            .pack(anchor="w", pady=2)

    btnf = ttk.Frame(dash, style="Card.TFrame")
    btnf.pack(fill="x", pady=(12,0))
    quick = [
        ("Ver Playlists", ventana_ver_playlists, "playlists"),
        ("Ver Top Tracks", ventana_top_tracks,    "top"),
        ("Abrir Gestor",   VentanaGestorAutomatico,"artists"),
    ]
    for title, fn, icon_key in quick:
        btn = ttk.Button(btnf, text=title, style="Accent.TButton",
                         command=lambda t=title,f=fn: open_window(t, lambda: f(sp, root)))
        ico = icons.get(icon_key)
        if ico:
            btn.config(image=ico, compound="left"); btn.image = ico
        btn.pack(side="left", expand=True, fill="x", padx=4)

    # — Grid de tarjetas — #
    cards_frame = ttk.Frame(content)
    cards_frame.pack(fill="both", expand=True, padx=30, pady=20)
    cards = [
        ("Vaciar Playlists", ventana_vaciar_playlists, "playlists"),
        ("Crear Playlist",   ventana_crear_playlist,    "playlists"),
        ("Sincronizar Podcasts", ventana_sincronizar_podcasts_data, "podcasts"),
        ("Artistapy",        ventana_artistapy,         "artists"),
        ("Buscar Avanzada",  ventana_busqueda_avanzada, "search"),
        ("Admin Podcasts",   VentanaAdminPodcasts,     "podcasts"),
    ]
    for idx,(title, fn, icon_key) in enumerate(cards):
        row,col = divmod(idx,3)
        card = ttk.Frame(cards_frame, style="Card.TFrame")
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        cards_frame.grid_columnconfigure(col, weight=1)
        card.bind("<Enter>", lambda e,c=card: c.configure(style="CardHover.TFrame"))
        card.bind("<Leave>", lambda e,c=card: c.configure(style="Card.TFrame"))
        stripe = tk.Frame(card, bg=cfg.ACCENT, width=6)
        stripe.pack(side="left", fill="y")
        inner = tk.Frame(card, bg=cfg.BG_PANEL)
        inner.pack(fill="both", expand=True, padx=12, pady=12)
        lbl = ttk.Label(inner, text=title, style="Subtitle.TLabel")
        ico = icons.get(icon_key)
        if ico:
            lbl.config(image=ico, compound="left"); lbl.image = ico
        lbl.pack(anchor="w")
        ttk.Button(inner, text="Abrir", style="Accent.TButton",
                   command=lambda t=title,f=fn: open_window(t, lambda: f(sp, root)))\
            .pack(anchor="e", pady=(8,0))

    # — Footer — #
    footer = tk.Label(root, text="✔️ Listo para usar",
                      bg=cfg.BG_PANEL, fg=cfg.TEXT_SECOND,
                      anchor="w", padx=15, pady=8)
    footer.pack(side="bottom", fill="x")

    return root
