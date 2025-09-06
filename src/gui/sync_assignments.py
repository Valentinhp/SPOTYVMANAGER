
import tkinter as tk
from tkinter import ttk, messagebox
from spotipy import Spotify
import json
from ..utils.spotify_utils import obtener_canciones_artista, agregar_canciones_a_playlist
from ..config import logger

def VentanaSincronizarAsignaciones(parent: tk.Widget, sp=None, **kwargs) -> ttk.Frame:
    """Ventana para ver y sincronizar asignaciones artista-playlist."""
    
    frame = ttk.Frame(parent)

    style = ttk.Style(frame)
    style.configure("TFrame", background="#121212")
    style.configure("TLabel", background="#121212", foreground="white", font=("Segoe UI", 10))
    style.configure("TButton", font=("Segoe UI", 10, "bold"), background="#1DB954", foreground="white")
    style.map("TButton", background=[("active", "#1ed760")])
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    main_frame = ttk.Frame(frame, padding=20, style="TFrame")
    main_frame.pack(expand=True, fill=tk.BOTH)

    ttk.Label(main_frame, text="Sincronizar Asignaciones", font=("Segoe UI", 16, "bold")).pack(pady=(0, 20))

    # Treeview
    tree_frame = ttk.Frame(main_frame)
    tree_frame.pack(expand=True, fill=tk.BOTH)
    columns = ("artista", "playlist")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Treeview")
    tree.heading("artista", text="Artista")
    tree.heading("playlist", text="Playlist")
    tree.column("artista", width=300)
    tree.column("playlist", width=300)
    tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def cargar_asignaciones():
        for i in tree.get_children():
            tree.delete(i)
        try:
            with open("src/data_assignments.json", "r") as f:
                asignaciones = json.load(f)
                for asign in sorted(asignaciones, key=lambda x: x["artista_nombre"]):
                    tree.insert("", tk.END, values=(asign["artista_nombre"], asign["playlist_nombre"]), iid=asign["artista_id"])
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning("No se encontró el archivo de asignaciones o está vacío.")

    def sincronizar_asignacion():
        selected_item = tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Selecciona una asignación para sincronizar.", parent=frame)
            return
        
        if not messagebox.askyesno("Confirmar", "Esto buscará nuevas canciones del artista y las agregará. ¿Continuar?", parent=frame):
            return

        try:
            with open("src/data_assignments.json", "r") as f:
                asignaciones = json.load(f)
                asign_seleccionada = next((a for a in asignaciones if a["artista_id"] == selected_item), None)

            if asign_seleccionada:
                artista_id = asign_seleccionada["artista_id"]
                playlist_id = asign_seleccionada["playlist_id"]
                artista_nombre = asign_seleccionada["artista_nombre"]
                
                logger.info(f"Sincronizando canciones de {artista_nombre}...")
                canciones = obtener_canciones_artista(sp, artista_id)
                if canciones:
                    agregar_canciones_a_playlist(sp, playlist_id, canciones)
                    messagebox.showinfo("Éxito", f"Sincronización completada para {artista_nombre}.", parent=frame)
                else:
                    messagebox.showinfo("Información", f"No se encontraron nuevas canciones para {artista_nombre}.", parent=frame)
            else:
                messagebox.showerror("Error", "No se encontró la asignación seleccionada.", parent=frame)

        except Exception as e:
            logger.error(f"Error al sincronizar: {e}")
            messagebox.showerror("Error", "Ocurrió un error durante la sincronización.", parent=frame)

    # Botones
    btn_frame = ttk.Frame(main_frame, style="TFrame")
    btn_frame.pack(fill="x", pady=(15, 0))

    btn_sincronizar = ttk.Button(btn_frame, text="Sincronizar Selección", command=sincronizar_asignacion)
    btn_sincronizar.pack(side=tk.LEFT, expand=True, padx=5, ipady=4)

    btn_recargar = ttk.Button(btn_frame, text="Recargar Lista", command=cargar_asignaciones)
    btn_recargar.pack(side=tk.RIGHT, expand=True, padx=5, ipady=4)

    cargar_asignaciones()

    return frame
