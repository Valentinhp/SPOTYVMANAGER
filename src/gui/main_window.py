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
from .admin_podcasts import VentanaAdminPodcasts
from .assign_artist import ventana_asignar_artista_playlist
from .manage_assignments import VentanaGestionarAsignaciones
from .sync_assignments import VentanaSincronizarAsignaciones

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
    m_play.add_command(label="Vaciar", command=lambda: show_frame(ventana_vaciar_playlists, content_frame, sp_arg=sp))
    m_play.add_command(label="Eliminar", command=lambda: show_frame(ventana_eliminar_playlists, content_frame, sp_arg=sp))
    m_play.add_command(label="Ver", command=lambda: show_frame(ventana_ver_playlists, content_frame, sp_arg=sp))
    m_play.add_command(label="Crear", command=lambda: show_frame(ventana_crear_playlist, content_frame, sp_arg=sp))
    menu_bar.add_cascade(label="🎵 Playlists", menu=m_play)

    # Podcasts
    m_pod = new_menu()
    m_pod.add_command(label="Sincronizar", command=lambda: show_frame(ventana_sincronizar_podcasts_data, content_frame, sp_arg=sp))
    m_pod.add_command(label="Administrar", command=lambda: show_frame(VentanaAdminPodcasts, content_frame, sp_arg=sp))
    menu_bar.add_cascade(label="🎙️ Podcasts", menu=m_pod)

    # Artistas
    m_art = new_menu()
    m_art.add_command(label="Asignar Artista a Playlist", command=lambda: show_frame(ventana_asignar_artista_playlist, content_frame, sp_arg=sp))
    m_art.add_command(label="Gestionar Asignaciones", command=lambda: show_frame(VentanaGestionarAsignaciones, content_frame, sp_arg=sp))
    m_art.add_command(label="Sincronizar Asignaciones", command=lambda: show_frame(VentanaSincronizarAsignaciones, content_frame, sp_arg=sp))
    m_art.add_separator()
    m_art.add_command(label="Gestor Automático", command=lambda: show_frame(VentanaGestorAutomatico, content_frame, sp_arg=sp))
    m_art.add_command(label="Artistapy", command=lambda: show_frame(ventana_artistapy, content_frame, sp_arg=sp))
    menu_bar.add_cascade(label="🎤 Artistas", menu=m_art)

    # Búsqueda
    m_bus = new_menu()
    m_bus.add_command(label="Avanzada", command=lambda: show_frame(ventana_busqueda_avanzada, content_frame, sp_arg=sp))
    menu_bar.add_cascade(label="🔍 Buscar", menu=m_bus)

    menu_bar.add_command(label="📈 Top Tracks", command=lambda: show_frame(ventana_top_tracks, content_frame, sp_arg=sp))
    menu_bar.add_command(label="❌ Salir", command=root.destroy)

    content_frame = ttk.Frame(root, padding=40)
    content_frame.pack(expand=True, fill=tk.BOTH)

    current_frame = None

    def show_frame(frame_factory, parent, sp_arg=None):
        nonlocal current_frame
        if current_frame:
            current_frame.destroy()
        current_frame = frame_factory(parent, sp=sp_arg)
        current_frame.pack(expand=True, fill=tk.BOTH)

    # Show the home frame by default
    def create_home_frame(parent, sp):
        home_frame = ttk.Frame(parent)

        ttk.Label(home_frame, text="SpotyVManager", style="Title.TLabel").pack(pady=(0, 10))
        ttk.Label(home_frame, text="Gestiona tu música como nunca antes", style="Sub.TLabel").pack(pady=(0, 30))

        features = [
            "🎵 Crear, ver, eliminar y vaciar playlists",
            "📈 Consultar tus Top Tracks",
            "🎙️ Sincronizar podcasts al instante",
            "✨ Recomendaciones con Artistapy",
            "🔍 Búsqueda por frase, título o artista",
            "🧩 Administrar Podcasts y Playlists personalizados",
        ]
        for feat in features:
            lbl = ttk.Label(home_frame, text=feat)
            lbl.pack(anchor="w", pady=4)

        btn1 = ttk.Button(home_frame, text="Ver Playlists", command=lambda: show_frame(ventana_ver_playlists, content_frame, sp_arg=sp))
        btn1.pack(pady=(30, 10), fill="x")
        btn2 = ttk.Button(home_frame, text="Ver Top Tracks", command=lambda: show_frame(ventana_top_tracks, content_frame, sp_arg=sp))
        btn2.pack(pady=10, fill="x")
        btn3 = ttk.Button(home_frame, text="Abrir Gestor Automático", command=lambda: show_frame(VentanaGestorAutomatico, content_frame, sp_arg=sp))
        btn3.pack(pady=10, fill="x")
        return home_frame

    show_frame(create_home_frame, content_frame, sp_arg=sp)

    footer = tk.Label(root,
                      text="✔️ Listo para usar",
                      bg="#181818",
                      fg="#aaaaaa",
                      anchor="w",
                      padx=10)
    footer.pack(side=tk.BOTTOM, fill=tk.X)

    return root
