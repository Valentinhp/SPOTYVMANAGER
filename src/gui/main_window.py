"""
Ventana principal de SpotyVManager con estilo Spotify,
minimalista, suave y muy agradable.
"""

import tkinter as tk
from tkinter import Menu, ttk, PhotoImage
from spotipy import Spotify

# Importa tus ventanas y funciones
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
from .admin_podcasts import VentanaAdminPodcasts  # <-- NUEVO IMPORT

def build_main_window(sp: Spotify) -> tk.Tk:
    root = tk.Tk()
    root.title("SpotyVManager 🎧")
    root.geometry("1000x720")
    root.configure(bg="#0f0f0f")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TButton",
                    font=("Segoe UI", 11, "bold"),
                    background="#1DB954",
                    foreground="white",
                    padding=12,
                    borderwidth=0)
    style.map("TButton",
              background=[("active", "#1ed760")])
    style.configure("TLabel",
                    background="#0f0f0f",
                    foreground="#dddddd",
                    font=("Segoe UI", 12))
    style.configure("Title.TLabel",
                    background="#0f0f0f",
                    foreground="white",
                    font=("Segoe UI", 24, "bold"))
    style.configure("Sub.TLabel",
                    background="#0f0f0f",
                    foreground="#bbbbbb",
                    font=("Segoe UI", 14))

    menu_bar = Menu(root, tearoff=0, bg="#1a1a1a", fg="white", activebackground="#1DB954")
    root.config(menu=menu_bar)

    def new_menu():
        return Menu(menu_bar, tearoff=0, bg="#1a1a1a", fg="white", activebackground="#1DB954")

    # Playlists
    m_play = new_menu()
    m_play.add_command(label="Vaciar", command=lambda: ventana_vaciar_playlists(sp, root))
    m_play.add_command(label="Eliminar", command=lambda: ventana_eliminar_playlists(sp, root))
    m_play.add_command(label="Ver", command=lambda: ventana_ver_playlists(sp, root))
    m_play.add_command(label="Crear", command=lambda: ventana_crear_playlist(sp, root))
    menu_bar.add_cascade(label="🎵 Playlists", menu=m_play)

    # Podcasts
    m_pod = new_menu()
    m_pod.add_command(label="Sincronizar", command=lambda: ventana_sincronizar_podcasts_data(sp, root))
    m_pod.add_command(label="Administrar", command=lambda: VentanaAdminPodcasts(root, sp))  # <-- NUEVO
    menu_bar.add_cascade(label="🎙️ Podcasts", menu=m_pod)

    # Artistas
    m_art = new_menu()
    m_art.add_command(label="Gestor Automático", command=lambda: VentanaGestorAutomatico(root, sp))
    m_art.add_command(label="Artistapy", command=lambda: ventana_artistapy(sp, root))
    menu_bar.add_cascade(label="🎤 Artistas", menu=m_art)

    # Búsqueda
    m_bus = new_menu()
    m_bus.add_command(label="Avanzada", command=lambda: ventana_busqueda_avanzada(sp, root))
    menu_bar.add_cascade(label="🔍 Buscar", menu=m_bus)

    menu_bar.add_command(label="📈 Top Tracks", command=lambda: ventana_top_tracks(sp, root))
    menu_bar.add_command(label="❌ Salir", command=root.destroy)

    panel = ttk.Frame(root, padding=40)
    panel.pack(expand=True)

    ttk.Label(panel, text="SpotyVManager", style="Title.TLabel").pack(pady=(0, 10))
    ttk.Label(panel, text="Gestiona tu música como nunca antes", style="Sub.TLabel").pack(pady=(0, 30))

    features = [
        "🎵 Crear, ver, eliminar y vaciar playlists",
        "📈 Consultar tus Top Tracks",
        "🎙️ Sincronizar podcasts al instante",
        "✨ Recomendaciones con Artistapy",
        "🔍 Búsqueda por frase, título o artista",
        "🧩 Administrar Podcasts y Playlists personalizados",
    ]
    for feat in features:
        lbl = ttk.Label(panel, text=feat)
        lbl.pack(anchor="w", pady=4)

    btn1 = ttk.Button(panel, text="Ver Playlists", command=lambda: ventana_ver_playlists(sp, root))
    btn1.pack(pady=(30, 10), fill="x")
    btn2 = ttk.Button(panel, text="Ver Top Tracks", command=lambda: ventana_top_tracks(sp, root))
    btn2.pack(pady=10, fill="x")
    btn3 = ttk.Button(panel, text="Abrir Gestor Automático", command=lambda: VentanaGestorAutomatico(root, sp))
    btn3.pack(pady=10, fill="x")

    footer = tk.Label(root,
                      text="✔️ Listo para usar",
                      bg="#181818",
                      fg="#aaaaaa",
                      anchor="w",
                      padx=10)
    footer.pack(side=tk.BOTTOM, fill=tk.X)

    return root
