"""
Ventana principal de SpotyVManager con estilo Spotify,
minimalista, suave y muy agradable.
"""

import tkinter as tk
from tkinter import Menu, ttk
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

# Variable global para mantener la referencia al frame actual
current_frame = None

def build_main_window(sp: Spotify) -> tk.Tk:
    root = tk.Tk()
    root.title("SpotyVManager 🎧")
    root.geometry("1000x720")
    root.configure(bg="#0f0f0f")

    style = ttk.Style()
    style.theme_use("clam")
    # Estilos generales
    style.configure("TButton", font=("Segoe UI", 11, "bold"), background="#1DB954", foreground="white", padding=12, borderwidth=0)
    style.map("TButton", background=[("active", "#1ed760")])
    style.configure("TLabel", background="#121212", foreground="#dddddd", font=("Segoe UI", 12))
    style.configure("Title.TLabel", background="#121212", foreground="white", font=("Segoe UI", 24, "bold"))
    style.configure("Sub.TLabel", background="#121212", foreground="#bbbbbb", font=("Segoe UI", 14))
    style.configure("Content.TFrame", background="#121212")


    # --- Frame principal de contenido ---
    content_frame = ttk.Frame(root, style="Content.TFrame")
    content_frame.pack(expand=True, fill=tk.BOTH)

    def show_frame(frame_factory, *args):
        global current_frame
        if current_frame:
            current_frame.destroy()
        
        current_frame = frame_factory(content_frame, sp, *args)
        current_frame.pack(expand=True, fill=tk.BOTH)

    menu_bar = Menu(root, tearoff=0, bg="#1a1a1a", fg="white", activebackground="#1DB954")
    root.config(menu=menu_bar)

    def new_menu():
        return Menu(menu_bar, tearoff=0, bg="#1a1a1a", fg="white", activebackground="#1DB954")

    # --- Menú ---
    m_play = new_menu()
    m_play.add_command(label="Ver", command=lambda: show_frame(ventana_ver_playlists))
    m_play.add_command(label="Crear", command=lambda: show_frame(ventana_crear_playlist))
    m_play.add_command(label="Vaciar", command=lambda: show_frame(ventana_vaciar_playlists))
    m_play.add_command(label="Eliminar", command=lambda: show_frame(ventana_eliminar_playlists))
    menu_bar.add_cascade(label="🎵 Playlists", menu=m_play)

    m_pod = new_menu()
    m_pod.add_command(label="Sincronizar", command=lambda: show_frame(ventana_sincronizar_podcasts_data))
    m_pod.add_command(label="Administrar", command=lambda: show_frame(VentanaAdminPodcasts))
    menu_bar.add_cascade(label="🎙️ Podcasts", menu=m_pod)

    m_art = new_menu()
    m_art.add_command(label="Asignar Artista a Playlist", command=lambda: show_frame(ventana_asignar_artista_playlist))
    m_art.add_command(label="Gestionar Asignaciones", command=lambda: show_frame(VentanaGestionarAsignaciones))
    m_art.add_command(label="Sincronizar Asignaciones", command=lambda: show_frame(VentanaSincronizarAsignaciones))
    m_art.add_separator()
    m_art.add_command(label="Gestor Automático", command=lambda: show_frame(VentanaGestorAutomatico))
    m_art.add_command(label="Artistapy", command=lambda: show_frame(ventana_artistapy))
    menu_bar.add_cascade(label="🎤 Artistas", menu=m_art)

    m_bus = new_menu()
    m_bus.add_command(label="Avanzada", command=lambda: show_frame(ventana_busqueda_avanzada))
    menu_bar.add_cascade(label="🔍 Buscar", menu=m_bus)

    menu_bar.add_command(label="📈 Top Tracks", command=lambda: show_frame(ventana_top_tracks))
    menu_bar.add_command(label="❌ Salir", command=root.destroy)

    # --- Pantalla de inicio ---
    def create_home_frame(parent, sp_instance):
        home_frame = ttk.Frame(parent, style="Content.TFrame", padding=40)
        
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

        btn1 = ttk.Button(home_frame, text="Ver Playlists", command=lambda: show_frame(ventana_ver_playlists))
        btn1.pack(pady=(30, 10), fill="x")
        btn2 = ttk.Button(home_frame, text="Ver Top Tracks", command=lambda: show_frame(ventana_top_tracks))
        btn2.pack(pady=10, fill="x")
        btn3 = ttk.Button(home_frame, text="Abrir Gestor Automático", command=lambda: show_frame(VentanaGestorAutomatico))
        btn3.pack(pady=10, fill="x")
        
        return home_frame

    # Mostrar la pantalla de inicio al arrancar
    show_frame(create_home_frame)

    footer = tk.Label(root, text="✔️ Listo para usar", bg="#181818", fg="#aaaaaa", anchor="w", padx=10)
    footer.pack(side=tk.BOTTOM, fill=tk.X)

    return root
