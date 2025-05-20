"""
Ventana de administración de asignaciones Podcast <-> Playlist.
Interfaz mejorada: temas oscuros, estilo Spotify, grid dinámico y detalles UX.
Ahora guarda siempre los IDs, no los nombres.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import importlib.util
from spotipy import Spotify

# ─────────────────────────────────────────────────────────────
# Funciones para cargar y guardar data_podcasts.py
# ─────────────────────────────────────────────────────────────
def cargar_asignaciones():
    base = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.abspath(os.path.join(base, "..", "data_podcasts.py"))
    if not os.path.exists(ruta):
        return []
    spec = importlib.util.spec_from_file_location("data_podcasts", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.data_podcasts

def guardar_asignaciones(asignaciones):
    """
    Reescribe el archivo data_podcasts.py con la lista actual de asignaciones.
    """
    base = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.abspath(os.path.join(base, "..", "data_podcasts.py"))
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write('"""Par de IDs podcast/playlist para sincronización"""\n')
            f.write("data_podcasts = [\n")
            for a in asignaciones:
                pod = a["podcast"].replace('"', '\\"')
                pls = a["playlist"].replace('"', '\\"')
                f.write(f'    {{"podcast": "{pod}", "playlist": "{pls}"}},\n')
            f.write("]\n")
        return True
    except Exception as e:
        messagebox.showerror("Error al guardar", f"No se pudo escribir:\n{e}")
        return False

# ─────────────────────────────────────────────────────────────
# Ventana de administración pulida
# ─────────────────────────────────────────────────────────────
class VentanaAdminPodcasts(tk.Toplevel):
    def __init__(self, parent, sp: Spotify):
        super().__init__(parent)
        self.sp = sp
        self.title("Admin Podcast ↔ Playlist")
        self.geometry("920x650")
        self.configure(bg="#191414")
        self.resizable(True, True)

        # cargar datos
        self.asignaciones = cargar_asignaciones()
        self.selected_podcast_id = ""
        self.selected_playlist_id = ""

        # estilos
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("FrameBG.TFrame", background="#191414")
        style.configure("LabelframeBG.TLabelframe",
                        background="#191414", foreground="#1DB954",
                        font=("Segoe UI", 11, "bold"))
        style.configure("LabelWhite.TLabel",
                        background="#191414", foreground="#FFFFFF")
        style.configure("Entry.TEntry",
                        foreground="#FFFFFF", fieldbackground="#2a2a2a")
        style.configure("Green.TButton",
                        background="#1DB954", foreground="#FFFFFF",
                        font=("Segoe UI", 9, "bold"))
        style.map("Green.TButton", background=[("active", "#1ed760")])

        self._crear_widgets()

    def _crear_widgets(self):
        cont = ttk.Frame(self, style="FrameBG.TFrame", padding=10)
        cont.pack(fill="both", expand=True)

        # --- sección buscar podcast ---
        pod_frame = ttk.Labelframe(cont, text="1) Buscar Podcast",
                                   style="LabelframeBG.TLabelframe", padding=8)
        pod_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        ttk.Label(pod_frame, text="Nombre:", style="LabelWhite.TLabel") \
            .grid(row=0, column=0, sticky="w")
        self.entry_pod = ttk.Entry(pod_frame, width=30, style="Entry.TEntry")
        self.entry_pod.grid(row=0, column=1, padx=5, pady=3, sticky="ew")
        ttk.Button(pod_frame, text="Buscar", style="Green.TButton",
                   command=self._buscar_podcast).grid(row=0, column=2, padx=5)
        self.lb_pod = tk.Listbox(pod_frame, bg="#2a2a2a", fg="white",
                                 selectbackground="#1DB954", height=6)
        self.lb_pod.grid(row=1, column=0, columnspan=3,
                         sticky="nsew", pady=(5, 0))
        self.lb_pod.bind("<<ListboxSelect>>", self._on_select_podcast)
        pod_frame.rowconfigure(1, weight=1)

        # --- sección buscar/crear playlist ---
        pl_frame = ttk.Labelframe(cont, text="2) Buscar / Crear Playlist",
                                  style="LabelframeBG.TLabelframe", padding=8)
        pl_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        ttk.Label(pl_frame, text="Nombre:", style="LabelWhite.TLabel") \
            .grid(row=0, column=0, sticky="w")
        self.entry_pl = ttk.Entry(pl_frame, width=30, style="Entry.TEntry")
        self.entry_pl.grid(row=0, column=1, padx=5, pady=3, sticky="ew")
        ttk.Button(pl_frame, text="Buscar", style="Green.TButton",
                   command=self._buscar_playlist).grid(row=0, column=2, padx=5)
        ttk.Button(pl_frame, text="Nueva", style="Green.TButton",
                   command=self._crear_playlist).grid(row=0, column=3, padx=5)
        self.lb_pl = tk.Listbox(pl_frame, bg="#2a2a2a", fg="white",
                                selectbackground="#1DB954", height=6)
        self.lb_pl.grid(row=1, column=0, columnspan=4,
                        sticky="nsew", pady=(5, 0))
        self.lb_pl.bind("<<ListboxSelect>>", self._on_select_playlist)
        pl_frame.rowconfigure(1, weight=1)

        # --- botón asignar ---
        ttk.Button(cont, text="➕ Asignar Podcast → Playlist",
                   style="Green.TButton", command=self._asignar) \
            .grid(row=1, column=0, columnspan=2, pady=10)

        # --- tabla de asignaciones ---
        table_frame = ttk.Frame(cont, style="FrameBG.TFrame")
        table_frame.grid(row=2, column=0, columnspan=2,
                         sticky="nsew", pady=(10, 0))
        cont.rowconfigure(2, weight=1)
        cols = ("Podcast ID", "Playlist ID")
        self.tree = ttk.Treeview(table_frame, columns=cols,
                                 show="headings", selectmode="extended")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center", width=400)
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(table_frame, orient="vertical",
                           command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)
        self._refrescar_tabla()

        # --- botones finales ---
        btn_frame = ttk.Frame(cont, style="FrameBG.TFrame")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Eliminar seleccionado",
                   style="Green.TButton", command=self._eliminar) \
            .grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Guardar cambios",
                   style="Green.TButton", command=self._guardar) \
            .grid(row=0, column=1, padx=10)
        ttk.Button(btn_frame, text="Cerrar",
                   style="Green.TButton", command=self.destroy) \
            .grid(row=0, column=2, padx=10)

    # ──────────────────────────────────────────────────
    def _buscar_podcast(self):
        q = self.entry_pod.get().strip()
        if not q: return
        shows = self.sp.search(q=q, type="show", limit=8)["shows"]["items"]
        self.lb_pod.delete(0, "end")
        for i, s in enumerate(shows):
            self.lb_pod.insert("end", f'{s["name"]} — {s["id"]}')

    def _buscar_playlist(self):
        q = self.entry_pl.get().strip()
        if not q: return
        all_pl, res = [], self.sp.current_user_playlists(limit=50)
        while True:
            all_pl += res["items"]
            if res["next"]: res = self.sp.next(res)
            else: break
        self.lb_pl.delete(0, "end")
        for p in all_pl:
            if q.lower() in p["name"].lower():
                self.lb_pl.insert("end", f'{p["name"]} — {p["id"]}')

    def _on_select_podcast(self, event):
        sel = self.lb_pod.curselection()
        if sel:
            _, id_ = self.lb_pod.get(sel[0]).rsplit("—", 1)
            self.selected_podcast_id = id_.strip()
            self.entry_pod.delete(0, "end")
            self.entry_pod.insert(0, self.selected_podcast_id)

    def _on_select_playlist(self, event):
        sel = self.lb_pl.curselection()
        if sel:
            _, id_ = self.lb_pl.get(sel[0]).rsplit("—", 1)
            self.selected_playlist_id = id_.strip()
            self.entry_pl.delete(0, "end")
            self.entry_pl.insert(0, self.selected_playlist_id)

    def _crear_playlist(self):
        nombre = simpledialog.askstring(
            "Nueva playlist", "Nombre para la nueva playlist:")
        if not nombre: return
        try:
            uid = self.sp.current_user()["id"]
            nueva = self.sp.user_playlist_create(user=uid, name=nombre)
            messagebox.showinfo("Éxito", f"Playlist creada: {nueva['name']}")
            # recargar resultados
            self.entry_pl.delete(0, "end")
            self.entry_pl.insert(0, nueva["name"])
            self._buscar_playlist()
        except Exception as e:
            messagebox.showerror("Error al crear", str(e))

    def _asignar(self):
        pod = self.selected_podcast_id
        pl  = self.selected_playlist_id
        if not pod or not pl:
            messagebox.showinfo("Faltan datos",
                                "Selecciona ambos antes de asignar.")
            return
        if any(x["podcast"] == pod and x["playlist"] == pl
               for x in self.asignaciones):
            messagebox.showinfo("Duplicado",
                                "Esa asignación ya existe.")
            return
        self.asignaciones.append({"podcast": pod, "playlist": pl})
        self._refrescar_tabla()

    def _refrescar_tabla(self):
        self.tree.delete(*self.tree.get_children())
        for i, a in enumerate(self.asignaciones):
            self.tree.insert("", "end", values=(
                a["podcast"], a["playlist"]))

    def _eliminar(self):
        for sel in self.tree.selection():
            pod, pl = self.tree.item(sel)["values"]
            self.asignaciones = [
                x for x in self.asignaciones
                if not (x["podcast"] == pod and x["playlist"] == pl)
            ]
        self._refrescar_tabla()

    def _guardar(self):
        if guardar_asignaciones(self.asignaciones):
            messagebox.showinfo("Guardado", "Cambios guardados correctamente.")
