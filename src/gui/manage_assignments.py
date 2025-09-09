import tkinter as tk
from tkinter import ttk, messagebox
from spotipy import Spotify
import json
import os
from .assign_artist import ventana_asignar_artista_playlist
from ..config import logger

DATA_FILE = "SPOTYVMANAGER/SPOTYVMANAGER/src/data_assignments.json"

class VentanaGestionarAsignaciones(ttk.Frame):
    def __init__(self, parent: ttk.Frame, sp: Spotify, **kwargs):
        super().__init__(parent, **kwargs)
        self.sp = sp
        self.parent = parent

        self.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text="Gestionar Asignaciones", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, pady=(0, 20), sticky="w")

        # Treeview
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        columns = ("artista", "playlist")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        self.tree.heading("artista", text="Artista")
        self.tree.heading("playlist", text="Playlist")
        self.tree.column("artista", width=300)
        self.tree.column("playlist", width=300)
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Botones
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=(15, 0))
        btn_frame.columnconfigure((0,1), weight=1)

        btn_crear = ttk.Button(btn_frame, text="Crear Nueva Asignación", command=self.abrir_ventana_crear)
        btn_crear.grid(row=0, column=0, sticky="ew", padx=(0, 5), ipady=4)
        
        btn_eliminar = ttk.Button(btn_frame, text="Eliminar Selección", command=self.eliminar_asignacion)
        btn_eliminar.grid(row=0, column=1, sticky="ew", padx=(5, 0), ipady=4)

        self.cargar_asignaciones()

    def cargar_asignaciones(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            if not os.path.exists(DATA_FILE):
                os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
                with open(DATA_FILE, "w") as f: json.dump([], f)

            with open(DATA_FILE, "r", encoding="utf-8") as f:
                asignaciones = json.load(f)
                for asign in sorted(asignaciones, key=lambda x: x.get("artista_nombre", "")):
                    self.tree.insert("", tk.END, 
                                     values=(asign.get("artista_nombre", "N/A"), asign.get("playlist_nombre", "N/A")),
                                     iid=asign["artista_id"])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"No se pudo cargar el archivo de asignaciones: {e}")

    def abrir_ventana_crear(self):
        messagebox.showinfo("Información", "Para crear una nueva asignación, ve a 'Artistas -> Asignar Artista a Playlist' en el menú principal.")

    def eliminar_asignacion(self):
        selected_item_iid = self.tree.focus()
        if not selected_item_iid:
            return messagebox.showerror("Error", "Selecciona una asignación para eliminar.")

        if messagebox.askyesno("Confirmar", "¿Seguro que quieres eliminar esta asignación?"):
            try:
                with open(DATA_FILE, "r+", encoding="utf-8") as f:
                    asignaciones = json.load(f)
                    asignaciones_filtradas = [a for a in asignaciones if a["artista_id"] != selected_item_iid]
                    f.seek(0)
                    f.truncate()
                    json.dump(asignaciones_filtradas, f, indent=4, ensure_ascii=False)
                self.cargar_asignaciones()
                messagebox.showinfo("Éxito", "Asignación eliminada.")
            except Exception as e:
                logger.error(f"Error al eliminar: {e}")
                messagebox.showerror("Error", "No se pudo eliminar la asignación.")
