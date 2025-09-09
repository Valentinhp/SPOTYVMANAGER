import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from spotipy import Spotify
import json
import os
from ..utils.spotify_utils import (
    obtener_playlists_usuario, 
    obtener_canciones_artista, 
    agregar_canciones_a_playlist,
    crear_playlist as api_crear_playlist,
    buscar_artistas
)
from ..config import logger

DATA_FILE = "SPOTYVMANAGER/SPOTYVMANAGER/src/data_assignments.json"

def ventana_asignar_artista_playlist(parent: ttk.Frame, sp: Spotify) -> ttk.Frame:
    """Frame para buscar un artista, asignarlo a una playlist y sincronizar."""
    
    frame = ttk.Frame(parent, padding=20)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(2, weight=1) # Artist tree
    frame.rowconfigure(4, weight=1) # Playlist list

    ttk.Label(frame, text="Asignar Artista a Playlist", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, pady=(0, 15), sticky="w")

    # --- Búsqueda de Artista ---
    search_frame = ttk.LabelFrame(frame, text="1. Busca y selecciona un artista", padding=10)
    search_frame.grid(row=1, column=0, pady=5, sticky="ew")
    search_frame.columnconfigure(0, weight=1)
    
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var, font=("Segoe UI", 10))
    search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

    def buscar():
        query = search_var.get()
        if not query: return
        try:
            resultados = buscar_artistas(sp, query)
            for i in artist_tree.get_children(): artist_tree.delete(i)
            if resultados:
                for artist_id, artist_name in resultados:
                    artist_tree.insert("", tk.END, iid=artist_id, values=(artist_name,))
            else:
                messagebox.showinfo("Sin resultados", "No se encontraron artistas.")
        except Exception as e:
            messagebox.showerror("Error de API", f"No se pudo buscar: {e}")

    search_btn = ttk.Button(search_frame, text="Buscar", command=buscar)
    search_btn.grid(row=0, column=1)

    artist_tree = ttk.Treeview(frame, columns=("artista",), show="headings", selectmode="browse")
    artist_tree.heading("artista", text="Resultados de la búsqueda")
    artist_tree.grid(row=2, column=0, sticky="nsew", pady=5)
    
    # --- Playlist ---
    playlist_frame = ttk.LabelFrame(frame, text="2. Busca y selecciona o crea una playlist", padding=10)
    playlist_frame.grid(row=3, column=0, pady=15, sticky="ew")
    playlist_frame.columnconfigure(0, weight=1)

    playlist_search_var = tk.StringVar()
    playlist_search_entry = ttk.Entry(playlist_frame, textvariable=playlist_search_var, font=("Segoe UI", 10))
    playlist_search_entry.grid(row=0, column=0, sticky="ew", pady=5)

    playlist_var = tk.StringVar()
    playlist_dropdown = ttk.Combobox(playlist_frame, textvariable=playlist_var, state="readonly", font=("Segoe UI", 10))
    playlist_dropdown.grid(row=1, column=0, sticky="ew", pady=5)

    playlists_usuario_original = []

    def _cargar_playlists_originales(nueva_playlist_nombre: str = None):
        nonlocal playlists_usuario_original
        playlists_usuario_original = obtener_playlists_usuario(sp)
        _filtrar_playlists(None, None, None, nueva_playlist_nombre)

    def _filtrar_playlists(_, __, ___, nueva_playlist_nombre: str = None):
        query = playlist_search_var.get().lower()
        nombres_filtrados = sorted([nombre for _, nombre, _ in playlists_usuario_original if query in nombre.lower()])
        playlist_dropdown["values"] = nombres_filtrados
        if nueva_playlist_nombre:
            playlist_var.set(nueva_playlist_nombre)
        elif nombres_filtrados:
            playlist_var.set(nombres_filtrados[0])
        else:
            playlist_var.set("")

    playlist_search_var.trace_add("write", _filtrar_playlists)

    def crear_nueva_playlist():
        nombre_nueva_playlist = simpledialog.askstring("Crear Playlist", "Nombre de la nueva playlist:")
        if nombre_nueva_playlist:
            try:
                api_crear_playlist(sp, nombre_nueva_playlist)
                messagebox.showinfo("Éxito", f"Playlist '{nombre_nueva_playlist}' creada.")
                _cargar_playlists_originales(nombre_nueva_playlist)
            except Exception as e:
                logger.error(f"Error al crear playlist: {e}")
                messagebox.showerror("Error", "No se pudo crear la playlist.")

    btn_crear_playlist = ttk.Button(playlist_frame, text="Crear Nueva Playlist", command=crear_nueva_playlist)
    btn_crear_playlist.grid(row=2, column=0, pady=10)
    
    _cargar_playlists_originales()

    # --- Asignar ---
    def asignar():
        selected_artist_iid = artist_tree.focus()
        if not selected_artist_iid: return messagebox.showerror("Error", "Debes buscar y seleccionar un artista.")
        
        artista_nombre = artist_tree.item(selected_artist_iid)["values"][0]
        artista_id = selected_artist_iid
        playlist_nombre = playlist_var.get()

        if not playlist_nombre: return messagebox.showerror("Error", "Debes seleccionar o crear una playlist.")

        playlist_id = [pid for pid, pname, _ in playlists_usuario_original if pname == playlist_nombre][0]

        try:
            if not os.path.exists(DATA_FILE):
                os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
                with open(DATA_FILE, "w") as f: json.dump([], f)
            
            with open(DATA_FILE, "r+", encoding="utf-8") as f:
                asignaciones = json.load(f)
                if any(a["artista_id"] == artista_id and a["playlist_id"] == playlist_id for a in asignaciones):
                    return messagebox.showwarning("Aviso", "Esta asignación ya existe.")

                asignaciones.append({
                    "artista_id": artista_id, "artista_nombre": artista_nombre,
                    "playlist_id": playlist_id, "playlist_nombre": playlist_nombre
                })
                f.seek(0)
                f.truncate()
                json.dump(asignaciones, f, indent=4, ensure_ascii=False)

            logger.info(f"Sincronizando canciones de {artista_nombre} a {playlist_nombre}...")
            canciones_artista = obtener_canciones_artista(sp, artista_id)
            if canciones_artista:
                agregar_canciones_a_playlist(sp, playlist_id, canciones_artista)
                messagebox.showinfo("Éxito", f"Canciones de {artista_nombre} añadidas a la playlist.")
            else:
                messagebox.showinfo("Info", f"No se encontraron canciones para {artista_nombre}.")

        except Exception as e:
            logger.error(f"Error al asignar: {e}")
            messagebox.showerror("Error", f"Ocurrió un error al guardar la asignación: {e}")

    btn_asignar = ttk.Button(frame, text="Asignar y Sincronizar", command=asignar)
    btn_asignar.grid(row=5, column=0, pady=20, ipady=5, sticky="ew")

    return frame