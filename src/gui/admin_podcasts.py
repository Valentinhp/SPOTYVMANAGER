# src/gui/admin_podcasts.py

"""
Vista de administración de asignaciones Podcast ↔ Playlist,
integrada en la ventana principal al estilo Spotify.
"""

import os
import importlib.util
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import src.config as cfg
from spotipy import Spotify
from .common import style_toplevel

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


class VentanaAdminPodcasts(tk.Toplevel):
    def __init__(self, parent, sp: Spotify):
        super().__init__(parent)
        self.sp = sp

        # Estiliza Toplevel (fondo, cabecera, padding)
        panel = style_toplevel(self, "Admin Podcasts ↔ Playlist", "920x650")

        # Estilos locales para entradas y tabla
        style = ttk.Style(self)
        style.configure("Entry.TEntry",
                        fieldbackground=cfg.BG_PANEL,
                        foreground=cfg.TEXT_PRIMARY)
        style.configure("Treeview",
                        background=cfg.BG_PANEL,
                        fieldbackground=cfg.BG_PANEL,
                        foreground=cfg.TEXT_PRIMARY)
        style.map("Treeview",
                  background=[("selected", cfg.ACCENT)],
                  foreground=[("selected", cfg.TEXT_PRIMARY)])

        # Datos
        self.asignaciones = cargar_asignaciones()
        self.selected = {"pod": "", "pl": ""}

        # Construir UI
        self._build_widgets(panel)

    def _build_widgets(self, cont: ttk.Frame):
        cont.columnconfigure(0, weight=1, uniform="col")
        cont.columnconfigure(1, weight=1, uniform="col")

        # — Sección 1: Podcast — #
        pod_card = ttk.Frame(cont, style="Card.TFrame", padding=12)
        pod_card.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        ttk.Label(pod_card, text="1) Buscar Podcast", style="Subtitle.TLabel")\
            .pack(anchor="w")
        f1 = ttk.Frame(pod_card, style="Card.TFrame")
        f1.pack(fill="x", pady=(6,10))
        entry_p = ttk.Entry(f1, style="Entry.TEntry")
        entry_p.pack(side="left", fill="x", expand=True)
        ttk.Button(f1, text="Buscar", style="Accent.TButton",
                   command=lambda: buscar_podcast())\
            .pack(side="left", padx=(8,0))
        lb_p = tk.Listbox(pod_card,
                          bg=cfg.BG_PANEL, fg=cfg.TEXT_PRIMARY,
                          selectbackground=cfg.ACCENT, activestyle="none",
                          highlightthickness=0, relief="flat", height=6)
        lb_p.pack(fill="both", expand=True)
        lb_p.bind("<<ListboxSelect>>", lambda e: sel_podcast())

        # — Sección 2: Playlist — #
        pl_card = ttk.Frame(cont, style="Card.TFrame", padding=12)
        pl_card.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        ttk.Label(pl_card, text="2) Buscar / Crear Playlist", style="Subtitle.TLabel")\
            .pack(anchor="w")
        f2 = ttk.Frame(pl_card, style="Card.TFrame")
        f2.pack(fill="x", pady=(6,10))
        entry_pl = ttk.Entry(f2, style="Entry.TEntry")
        entry_pl.pack(side="left", fill="x", expand=True)
        ttk.Button(f2, text="Buscar", style="Accent.TButton",
                   command=lambda: buscar_playlist())\
            .pack(side="left", padx=(8,0))
        ttk.Button(f2, text="Nueva", style="Accent.TButton",
                   command=lambda: crear_playlist())\
            .pack(side="left", padx=(8,0))
        lb_pl = tk.Listbox(pl_card,
                           bg=cfg.BG_PANEL, fg=cfg.TEXT_PRIMARY,
                           selectbackground=cfg.ACCENT, activestyle="none",
                           highlightthickness=0, relief="flat", height=6)
        lb_pl.pack(fill="both", expand=True)
        lb_pl.bind("<<ListboxSelect>>", lambda e: sel_playlist())

        # Lógica de búsqueda/selección
        def buscar_podcast():
            q = entry_p.get().strip()
            if not q: return
            shows = self.sp.search(q=q, type="show", limit=8)["shows"]["items"]
            lb_p.delete(0, "end")
            for s in shows:
                lb_p.insert("end", f'{s["name"]} — {s["id"]}')
        def sel_podcast():
            sel = lb_p.curselection()
            if not sel: return
            self.selected["pod"] = lb_p.get(sel[0]).rsplit("—",1)[-1].strip()

        def buscar_playlist():
            q = entry_pl.get().strip()
            if not q: return
            all_pl, res = [], self.sp.current_user_playlists(limit=50)
            while True:
                all_pl += res["items"]
                if res["next"]:
                    res = self.sp.next(res)
                else:
                    break
            lb_pl.delete(0, "end")
            for p in all_pl:
                if q.lower() in p["name"].lower():
                    lb_pl.insert("end", f'{p["name"]} — {p["id"]}')
        def sel_playlist():
            sel = lb_pl.curselection()
            if not sel: return
            self.selected["pl"] = lb_pl.get(sel[0]).rsplit("—",1)[-1].strip()

        def crear_playlist():
            nombre = simpledialog.askstring("Nueva Playlist", "Nombre:")
            if not nombre: return
            uid = self.sp.current_user()["id"]
            nueva = self.sp.user_playlist_create(uid, nombre)
            messagebox.showinfo("Éxito", f"Playlist creada: {nueva['name']}")
            entry_pl.delete(0, "end")
            entry_pl.insert(0, nueva["name"])
            buscar_playlist()

        # — Botón Asignar — #
        ttk.Button(cont, text="➕ Asignar Podcast → Playlist",
                   style="Accent.TButton", command=lambda: on_asignar())\
            .grid(row=1, column=0, columnspan=2, pady=(4,12))

        def on_asignar():
            pod, pl = self.selected["pod"], self.selected["pl"]
            if not pod or not pl:
                messagebox.showinfo("Faltan datos", "Selecciona podcast y playlist.")
                return
            if any(x["podcast"] == pod and x["playlist"] == pl for x in self.asignaciones):
                messagebox.showinfo("Duplicado", "Esa asignación ya existe.")
                return
            self.asignaciones.append({"podcast": pod, "playlist": pl})
            refrescar_tabla()

        # — Tabla de asignaciones — #
        tbl_card = ttk.Frame(cont, style="Card.TFrame", padding=12)
        tbl_card.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0,12))
        cont.rowconfigure(2, weight=1)
        cols = ("Podcast ID", "Playlist ID")
        tree = ttk.Treeview(tbl_card, columns=cols, show="headings", height=6)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center")
        tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(tbl_card, orient="vertical", command=tree.yview)
        sb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=sb.set)

        def refrescar_tabla():
            tree.delete(*tree.get_children())
            for a in self.asignaciones:
                tree.insert("", "end", values=(a["podcast"], a["playlist"]))

        refrescar_tabla()

        # — Botones finales — #
        foot = ttk.Frame(panel, style="Card.TFrame")
        foot.pack(fill="x", pady=(0,8))
        ttk.Button(foot, text="Eliminar seleccionado",
                   style="Accent.TButton",
                   command=lambda:
                     [self.asignaciones.pop(i) for i in reversed(tree.selection()) or [None]] or refrescar_tabla()
        ).pack(side="left", padx=8)
        ttk.Button(foot, text="Guardar cambios",
                   style="Accent.TButton", command=lambda: on_guardar()).pack(side="left")

        def on_guardar():
            if guardar_asignaciones(self.asignaciones):
                messagebox.showinfo("Guardado", "Cambios guardados correctamente.")
