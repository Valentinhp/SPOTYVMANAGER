import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from spotipy import Spotify
import json
from ..utils.spotify_utils import (
    obtener_playlists_usuario, 
    obtener_canciones_artista, 
    agregar_canciones_a_playlist,
    crear_playlist,
    buscar_artistas
)
from ..config import logger

def ventana_asignar_artista_playlist(parent: tk.Widget, sp=None, **kwargs) -> ttk.Frame:
    """Ventana para buscar un artista, asignarlo a una playlist y sincronizar."""
    
    frame = ttk.Frame(parent)

    style = ttk.Style(frame)
    style.configure("TFrame", background="#121212")
    style.configure("TLabel", background="#121212", foreground="white", font=("Segoe UI", 10))
    style.configure("TButton", font=("Segoe UI", 10, "bold"), background="#1DB954", foreground="white")
    style.map("TButton", background=[("active", "#1ed760")])
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    main_frame = ttk.Frame(frame, padding=20, style="TFrame")
    main_frame.pack(expand=True, fill=tk.BOTH)

    ttk.Label(main_frame, text="Asignar Artista a Playlist", font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))

    # --- Búsqueda de Artista ---
    search_frame = ttk.Frame(main_frame, style="TFrame")
    search_frame.pack(fill="x", pady=5)
    ttk.Label(search_frame, text="1. Busca y selecciona un artista:").pack(anchor="w")
    
    search_inner_frame = ttk.Frame(search_frame, style="TFrame")
    search_inner_frame.pack(fill="x", pady=5)
    
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_inner_frame, textvariable=search_var, font=("Segoe UI", 10))
    search_entry.pack(side=tk.LEFT, expand=True, fill="x", padx=(0, 5))

    def buscar():
        query = search_var.get()
        if not query:
            return
        resultados = buscar_artistas(sp, query)
        for i in artist_tree.get_children():
            artist_tree.delete(i)
        if resultados:
            for artist_id, artist_name in resultados:
                artist_tree.insert("", tk.END, iid=artist_id, values=(artist_name,))
        else:
            messagebox.showinfo("Sin resultados", "No se encontraron artistas.", parent=frame)

    search_btn = ttk.Button(search_inner_frame, text="Buscar", command=buscar)
    search_btn.pack(side=tk.RIGHT)

    # Treeview para resultados de artista
    artist_tree_frame = ttk.Frame(main_frame)
    artist_tree_frame.pack(expand=True, fill=tk.BOTH, pady=10)
    
    artist_tree = ttk.Treeview(artist_tree_frame, columns=("artista",), show="headings", selectmode="browse")
    artist_tree.heading("artista", text="Resultados de la búsqueda")
    artist_tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
    
    artist_scrollbar = ttk.Scrollbar(artist_tree_frame, orient=tk.VERTICAL, command=artist_tree.yview)
    artist_tree.configure(yscroll=artist_scrollbar.set)
    artist_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # --- Playlist ---
    playlist_frame = ttk.Frame(main_frame, style="TFrame")
    playlist_frame.pack(fill="x", pady=15)
    ttk.Label(playlist_frame, text="2. Busca y selecciona o crea una playlist:").pack(anchor="w")

    playlist_search_var = tk.StringVar()
    playlist_search_entry = ttk.Entry(playlist_frame, textvariable=playlist_search_var, font=("Segoe UI", 10))
    playlist_search_entry.pack(fill="x", pady=5)

    playlist_var = tk.StringVar()
    playlist_dropdown = ttk.Combobox(playlist_frame, textvariable=playlist_var, state="readonly", font=("Segoe UI", 10))
    playlist_dropdown.pack(fill="x", pady=5)

    playlists_usuario_original = []

    def _cargar_playlists_originales(nueva_playlist_nombre: str = None):
        nonlocal playlists_usuario_original
        playlists_usuario_original = obtener_playlists_usuario(sp)
        _filtrar_playlists(None, None, None, nueva_playlist_nombre)

    def _filtrar_playlists(_, __, ___, nueva_playlist_nombre: str = None):
        query = playlist_search_var.get().lower()
        nombres_filtrados = sorted([
            nombre for _, nombre, _ in playlists_usuario_original 
            if query in nombre.lower()
        ])
        playlist_dropdown["values"] = nombres_filtrados
        if nueva_playlist_nombre:
            playlist_var.set(nueva_playlist_nombre)
        elif nombres_filtrados:
            playlist_var.set(nombres_filtrados[0])
        else:
            playlist_var.set("")

    playlist_search_var.trace_add("write", _filtrar_playlists)

    def crear_nueva_playlist():
        nombre_nueva_playlist = simpledialog.askstring("Crear Playlist", "Nombre de la nueva playlist:", parent=frame)
        if nombre_nueva_playlist:
            try:
                crear_playlist(sp, nombre_nueva_playlist)
                messagebox.showinfo("Éxito", f"Playlist '{nombre_nueva_playlist}' creada.", parent=frame)
                _cargar_playlists_originales(nombre_nueva_playlist)
            except Exception as e:
                logger.error(f"Error al crear playlist: {e}")
                messagebox.showerror("Error", "No se pudo crear la playlist.", parent=frame)

    btn_crear_playlist = ttk.Button(playlist_frame, text="Crear Nueva Playlist", command=crear_nueva_playlist)
    btn_crear_playlist.pack(pady=10)
    
    _cargar_playlists_originales()

    # --- Asignar ---
    def asignar():
        selected_artist_iid = artist_tree.focus()
        if not selected_artist_iid:
            messagebox.showerror("Error", "Debes buscar y seleccionar un artista.", parent=frame)
            return
        
        artista_nombre = artist_tree.item(selected_artist_iid)["values"][0]
        artista_id = selected_artist_iid
        playlist_nombre = playlist_var.get()

        if not playlist_nombre:
            messagebox.showerror("Error", "Debes seleccionar o crear una playlist.", parent=frame)
            return

        playlist_id = [pid for pid, pname, _ in playlists_usuario_original if pname == playlist_nombre][0]

        try:
            with open("src/data_assignments.json", "r+") as f:
                asignaciones = json.load(f)
                if any(a["artista_id"] == artista_id and a["playlist_id"] == playlist_id for a in asignaciones):
                    messagebox.showwarning("Aviso", "Esta asignación ya existe.", parent=frame)
                    return

                asignaciones.append({
                    "artista_id": artista_id, "artista_nombre": artista_nombre,
                    "playlist_id": playlist_id, "playlist_nombre": playlist_nombre
                })
                f.seek(0)
                f.truncate()
                json.dump(asignaciones, f, indent=4)

            logger.info(f"Sincronizando canciones de {artista_nombre} a {playlist_nombre}...")
            canciones_artista = obtener_canciones_artista(sp, artista_id)
            if canciones_artista:
                agregar_canciones_a_playlist(sp, playlist_id, canciones_artista)
                messagebox.showinfo("Éxito", f"Canciones de {artista_nombre} añadidas a la playlist.", parent=frame)
            else:
                messagebox.showinfo("Info", f"No se encontraron canciones para {artista_nombre}.", parent=frame)
            

        except Exception as e:
            logger.error(f"Error al asignar: {e}")
            messagebox.showerror("Error", f"Ocurrió un error al guardar la asignación: {e}", parent=frame)

    btn_asignar = ttk.Button(main_frame, text="Asignar y Sincronizar", command=asignar, style="TButton")
    btn_asignar.pack(pady=20, fill="x", ipady=5)

    return frame