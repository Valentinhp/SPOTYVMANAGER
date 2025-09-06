
import tkinter as tk
from tkinter import ttk, messagebox
from spotipy import Spotify
import json
from .assign_artist import ventana_asignar_artista_playlist
from ..config import logger

def VentanaGestionarAsignaciones(parent: tk.Widget, sp=None, **kwargs) -> ttk.Frame:
    """Ventana para crear y eliminar asignaciones artista-playlist."""
    
    frame = ttk.Frame(parent)

    style = ttk.Style(frame)
    style.configure("TFrame", background="#121212")
    style.configure("TLabel", background="#121212", foreground="white", font=("Segoe UI", 10))
    style.configure("TButton", font=("Segoe UI", 10, "bold"), background="#1DB954", foreground="white")
    style.map("TButton", background=[("active", "#1ed760")])
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    main_frame = ttk.Frame(frame, padding=20, style="TFrame")
    main_frame.pack(expand=True, fill=tk.BOTH)

    ttk.Label(main_frame, text="Gestionar Asignaciones", font=("Segoe UI", 16, "bold")).pack(pady=(0, 20))

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

    def abrir_ventana_crear():
        ventana_asignar_artista_playlist(sp, frame)
        cargar_asignaciones() # Recargar

    def eliminar_asignacion():
        selected_item = tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Selecciona una asignación para eliminar.", parent=frame)
            return

        if messagebox.askyesno("Confirmar", "¿Seguro que quieres eliminar esta asignación?", parent=frame):
            try:
                with open("src/data_assignments.json", "r+") as f:
                    asignaciones = json.load(f)
                    asignaciones_filtradas = [a for a in asignaciones if a["artista_id"] != selected_item]
                    f.seek(0)
                    f.truncate()
                    json.dump(asignaciones_filtradas, f, indent=4)
                cargar_asignaciones()
                messagebox.showinfo("Éxito", "Asignación eliminada.", parent=frame)
            except Exception as e:
                logger.error(f"Error al eliminar: {e}")
                messagebox.showerror("Error", "No se pudo eliminar la asignación.", parent=frame)

    # Botones
    btn_frame = ttk.Frame(main_frame, style="TFrame")
    btn_frame.pack(fill="x", pady=(15, 0))

    btn_crear = ttk.Button(btn_frame, text="Crear Nueva Asignación", command=abrir_ventana_crear)
    btn_crear.pack(side=tk.LEFT, expand=True, padx=(0, 5), ipady=4)
    
    btn_eliminar = ttk.Button(btn_frame, text="Eliminar Selección", command=eliminar_asignacion)
    btn_eliminar.pack(side=tk.LEFT, expand=True, padx=(5, 0), ipady=4)

    btn_recargar = ttk.Button(btn_frame, text="Recargar Lista", command=cargar_asignaciones)
    btn_recargar.pack(side=tk.RIGHT, padx=(10,0))

    cargar_asignaciones()

    return frame
