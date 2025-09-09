import tkinter as tk
from tkinter import ttk, messagebox
from spotipy import Spotify
import json
import os
from ..utils.spotify_utils import obtener_canciones_artista, agregar_canciones_a_playlist, get_playlist_items
from ..config import logger

DATA_FILE = "SPOTYVMANAGER/SPOTYVMANAGER/src/data_assignments.json"

class VentanaSincronizarAsignaciones(ttk.Frame):
    def __init__(self, parent: ttk.Frame, sp: Spotify, **kwargs):
        super().__init__(parent, **kwargs)
        self.sp = sp

        self.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text="Sincronizar Asignaciones", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, pady=(0, 20), sticky="w")

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
        btn_frame.columnconfigure(0, weight=1)

        btn_sincronizar = ttk.Button(btn_frame, text="Sincronizar Selección", command=self.sincronizar_asignacion)
        btn_sincronizar.grid(row=0, column=0, sticky="ew", padx=(0,5), ipady=4)
        
        btn_sinc_todos = ttk.Button(btn_frame, text="Sincronizar Todo", command=self.sincronizar_todo)
        btn_sinc_todos.grid(row=0, column=1, sticky="ew", padx=(5,0), ipady=4)

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

    def sincronizar_asignacion(self, artista_id=None, playlist_id=None, artista_nombre=None):
        if not artista_id:
            selected_item = self.tree.focus()
            if not selected_item:
                return messagebox.showerror("Error", "Selecciona una asignación para sincronizar.")
            
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                asignaciones = json.load(f)
                asign_sel = next((a for a in asignaciones if a["artista_id"] == selected_item), None)
                if not asign_sel: return messagebox.showerror("Error", "Asignación no encontrada.")
                artista_id = asign_sel["artista_id"]
                playlist_id = asign_sel["playlist_id"]
                artista_nombre = asign_sel["artista_nombre"]

        try:
            logger.info(f"Sincronizando canciones de {artista_nombre}...")
            canciones_nuevas = obtener_canciones_artista(self.sp, artista_id)
            if not canciones_nuevas:
                logger.info(f"No se encontraron canciones para {artista_nombre}.")
                return 0

            uris_nuevas = {c["uri"] for c in canciones_nuevas}
            uris_actuales = {t["track"]["uri"] for t in get_playlist_items(self.sp, playlist_id, fields="items(track(uri))") if t.get("track") and t["track"]}
            
            uris_para_agregar = list(uris_nuevas - uris_actuales)

            if uris_para_agregar:
                agregar_canciones_a_playlist(self.sp, playlist_id, uris_para_agregar)
                logger.info(f"{len(uris_para_agregar)} canciones nuevas de {artista_nombre} añadidas.")
                return len(uris_para_agregar)
            else:
                logger.info(f"No hay canciones nuevas de {artista_nombre} para añadir.")
                return 0

        except Exception as e:
            logger.error(f"Error al sincronizar {artista_nombre}: {e}")
            messagebox.showerror("Error de Sincronización", f"Ocurrió un error con {artista_nombre}:\n{e}")
            return -1 # Indicar error

    def sincronizar_todo(self):
        if not messagebox.askyesno("Confirmar Sincronización Total", "Esto puede tardar un rato y realizar muchas peticiones a la API. ¿Continuar?"):
            return

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                asignaciones = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return messagebox.showinfo("Info", "No hay asignaciones para sincronizar.")

        total_agregadas = 0
        errores = []
        for asign in asignaciones:
            res = self.sincronizar_asignacion(asign["artista_id"], asign["playlist_id"], asign["artista_nombre"])
            if res > 0:
                total_agregadas += res
            elif res < 0:
                errores.append(asign["artista_nombre"])

        msg_final = f"Sincronización completada. Se agregaron {total_agregadas} canciones en total."
        if errores:
            msg_final += "\n\nOcurrieron errores con los siguientes artistas:\n" + "\n".join(errores)
        
        messagebox.showinfo("Proceso Terminado", msg_final)
