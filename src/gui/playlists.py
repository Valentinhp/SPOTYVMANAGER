# src/gui/playlists.py
"""
Ventanas relacionadas con Playlists:
* Ver playlists
* Crear playlist
* Contenido de playlist
* Agregar artista/podcast a playlist
* Eliminar playlists
* Vaciar playlists
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from spotipy import Spotify
from ..utils.spotify_utils import (
    obtener_playlists_usuario,
    crear_playlist,
    obtener_contenido_playlist,
    eliminar_items_playlist,
    obtener_canciones_artista,
    obtener_episodios_podcast_sencillo,
    agregar_canciones_a_playlist,
)

def ventana_ver_playlists(parent: tk.Widget, sp=None, **kwargs) -> ttk.Frame:
    frame = ttk.Frame(parent)

    cols = ("ID", "Nombre", "Tracks")
    tree = ttk.Treeview(frame, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)

    for pid, nom, tot in obtener_playlists_usuario(sp):
        tree.insert("", tk.END, values=(pid, nom, tot))
    
    return frame

def ventana_crear_playlist(parent: tk.Widget, sp=None, **kwargs) -> ttk.Frame:
    frame = ttk.Frame(parent)

    tk.Label(frame, text="Nombre de la Playlist:").pack(pady=5)
    entry = tk.Entry(frame, width=30)
    entry.pack(pady=5)

    def crear():
        nombre = entry.get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "Ingresa un nombre")
            return
        pid = crear_playlist(sp, nombre)
        messagebox.showinfo("Completado", f"Playlist creada con ID: {pid}")

    tk.Button(frame, text="Crear", command=crear).pack(pady=5)
    return frame

def ventana_contenido_playlist(sp: Spotify, root: tk.Tk):
    ven = tk.Toplevel(root)
    ven.title("Contenido de Playlist")
    ven.geometry("650x450")

    tk.Label(ven, text="ID de la playlist:").pack(pady=5)
    entry_pid = tk.Entry(ven, width=40)
    entry_pid.pack()

    frame_tbl = ttk.Frame(ven)
    frame_tbl.pack(fill=tk.BOTH, expand=True)

    cols = ("TrackID", "Título", "Artista/Show")
    tree = ttk.Treeview(frame_tbl, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scroll = ttk.Scrollbar(frame_tbl, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def cargar():
        tree.delete(*tree.get_children())
        pid = entry_pid.get().strip()
        if not pid:
            messagebox.showwarning("Atención", "Debes ingresar el ID de la playlist.")
            return
        for tid, nom, art in obtener_contenido_playlist(sp, pid):
            tree.insert("", tk.END, values=(tid, nom, art))

    def eliminar_sel():
        pid = entry_pid.get().strip()
        if not pid:
            messagebox.showwarning("Atención", "Ingresa el ID primero.")
            return
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "No seleccionaste nada.")
            return
        uris = []
        for s in sel:
            tid = tree.item(s, "values")[0]
            uris += [f"spotify:track:{tid}", f"spotify:episode:{tid}"]
        eliminar_items_playlist(sp, pid, uris)
        cargar()

    frame_btns = tk.Frame(ven)
    frame_btns.pack(pady=5)
    tk.Button(frame_btns, text="Cargar Contenido", command=cargar).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_btns, text="Eliminar Seleccionados", command=eliminar_sel).pack(side=tk.LEFT, padx=5)

def ventana_agregar_artista_podcast(sp: Spotify, root: tk.Tk):
    ven = tk.Toplevel(root)
    ven.title("Agregar Artista o Podcast a Playlist")
    ven.geometry("500x300")

    tk.Label(ven, text="ID de la Playlist destino:").pack(pady=5)
    entry_pl = tk.Entry(ven, width=40)
    entry_pl.pack()

    tk.Label(ven, text="ID de Artista (opcional):").pack(pady=5)
    entry_art = tk.Entry(ven, width=40)
    entry_art.pack()

    tk.Label(ven, text="ID de Podcast (opcional):").pack(pady=5)
    entry_pod = tk.Entry(ven, width=40)
    entry_pod.pack()

    def agregar():
        pid = entry_pl.get().strip()
        if not pid:
            messagebox.showwarning("Atención", "Falta el ID de la Playlist.")
            return
        aid = entry_art.get().strip()
        podid = entry_pod.get().strip()
        if aid:
            tracks = obtener_canciones_artista(sp, aid)
            if not tracks:
                messagebox.showwarning("Info", "No hay tracks para ese artista.")
                return
            agregar_canciones_a_playlist(sp, pid, tracks)
            messagebox.showinfo("Éxito", "Agregadas top tracks del artista.")
        elif podid:
            eps = obtener_episodios_podcast_sencillo(sp, podid)
            if not eps:
                messagebox.showwarning("Info", "No se encontraron episodios.")
                return
            from ..utils.spotify_utils import add_episodes_to_playlist as _add_eps
            _add_eps(sp, pid, [f"spotify:episode:{e}" for e in eps])
            messagebox.showinfo("Éxito", "Agregados episodios del podcast.")
        else:
            messagebox.showinfo("Atención", "No pusiste Artista ni Podcast.")

    tk.Button(ven, text="Agregar", command=agregar).pack(pady=10)

def ventana_eliminar_playlists(parent: tk.Widget, sp=None, **kwargs) -> ttk.Frame:
    frame = ttk.Frame(parent)

    tk.Label(frame, text="Buscar playlists:", font=("Arial", 11)).pack(pady=(10, 0))
    entry_buscar = tk.Entry(frame, width=40)
    entry_buscar.pack(pady=(0, 8))

    pls = obtener_playlists_usuario(sp)
    filtered_pls = list(pls)

    list_frame = tk.Frame(frame)
    list_frame.pack(fill=tk.BOTH, expand=True, padx=10)
    listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scroll.set)

    def refrescar():
        listbox.delete(0, tk.END)
        for pid, nombre, _ in filtered_pls:
            listbox.insert(tk.END, f"{nombre}  ({pid[:8]}…)")

    def filtrar(_evt):
        term = entry_buscar.get().strip().lower()
        filtered_pls.clear()
        for item in pls:
            if term in item[1].lower():
                filtered_pls.append(item)
        refrescar()

    entry_buscar.bind("<KeyRelease>", filtrar)
    refrescar()

    def confirmar_elim():
        idxs = listbox.curselection()
        if not idxs:
            messagebox.showwarning("Atención", "No seleccionaste ninguna playlist.")
            return
        seleccion = [filtered_pls[i] for i in idxs]
        nombres = "\n".join(f"• {n}" for _, n, _ in seleccion)
        if not messagebox.askyesno("Confirmar eliminación", f"Vas a eliminar estas playlists:\n{nombres}\n\n¿Continuar?"):
            return
        errores = []
        for pid, nombre, _ in seleccion:
            try:
                sp.current_user_unfollow_playlist(pid)
            except Exception as e:
                errores.append(f"{nombre}: {e}")
        if errores:
            messagebox.showerror("Errores", "Algunas no se pudieron eliminar:\n" + "\n".join(errores))
        else:
            messagebox.showinfo("¡Listo!", "Las playlists seleccionadas han sido eliminadas.")

    tk.Button(frame, text="Eliminar seleccionadas", command=confirmar_elim).pack(pady=10)
    return frame

def ventana_vaciar_playlists(parent: tk.Widget, sp=None, **kwargs) -> ttk.Frame:
    frame = ttk.Frame(parent)

    tk.Label(frame, text="Buscar playlists:", font=("Arial", 11)).pack(pady=(10, 0))
    entry_buscar = tk.Entry(frame, width=40)
    entry_buscar.pack(pady=(0, 8))

    todas = obtener_playlists_usuario(sp)
    mostradas = list(todas)

    list_frame = tk.Frame(frame)
    list_frame.pack(fill=tk.BOTH, expand=True, padx=10)
    listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scroll.set)

    def refrescar():
        listbox.delete(0, tk.END)
        for pid, nombre, _ in mostradas:
            listbox.insert(tk.END, f"{nombre}  ({pid[:8]}…)")

    def filtrar(_evt):
        texto = entry_buscar.get().strip().lower()
        mostradas.clear()
        for item in todas:
            if texto in item[1].lower():
                mostradas.append(item)
        refrescar()

    entry_buscar.bind("<KeyRelease>", filtrar)
    refrescar()

    def confirmar_vaciado():
        idxs = listbox.curselection()
        if not idxs:
            messagebox.showwarning("Atención", "No seleccionaste ninguna playlist.")
            return
        seleccion = [mostradas[i] for i in idxs]
        nombres = "\n".join(f"• {n}" for _, n, _ in seleccion)
        if not messagebox.askyesno("Confirmar vaciado", f"Vas a vaciar estas playlists:\n{nombres}\n\n¿Continuar?"):
            return
        errores = []
        for pid, nombre, _ in seleccion:
            try:
                sp.playlist_replace_items(pid, [])
            except Exception as e:
                errores.append(f"{nombre}: {e}")
        if errores:
            messagebox.showerror("Errores", "Errores al vaciar:\n" + "\n".join(errores))
        else:
            messagebox.showinfo("¡Hecho!", "Las playlists seleccionadas han quedado vacías.")

    tk.Button(frame, text="Vaciar seleccionadas", command=confirmar_vaciado).pack(pady=10)
    return frame