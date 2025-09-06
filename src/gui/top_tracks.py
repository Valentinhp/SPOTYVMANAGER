# src/gui/top_tracks.py
"""
Ventana Top Tracks Mejorado: busca un artista, filtra y crea playlist.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from spotipy import Spotify
import time

def ventana_top_tracks(parent: tk.Widget, sp=None, **kwargs) -> ttk.Frame:
    frame = ttk.Frame(parent)

    tk.Label(frame, text="Artista:").pack(pady=(10,0))
    e_art = tk.Entry(frame, width=40); e_art.pack(pady=5)

    tk.Label(frame, text="Cuántos tracks (1–50):").pack(pady=(5,0))
    e_num = tk.Entry(frame, width=5); e_num.insert(0, "10"); e_num.pack(pady=5)

    tk.Label(frame, text="Popularidad mínima (0–100):").pack(pady=(5,0))
    e_pop = tk.Entry(frame, width=5); e_pop.insert(0, "0"); e_pop.pack(pady=5)

    tk.Label(frame, text="Colaboraciones:").pack(pady=(5,0))
    coll_var = tk.StringVar(value="Todas")
    for val, txt in [("Todas","Todas"), ("Solo","Solo artista"), ("Colab","Solo colaboraciones")]:
        tk.Radiobutton(frame, text=txt, variable=coll_var, value=val).pack(anchor="w", padx=20)

    tk.Label(frame, text="Géneros secundarios (sep. coma):").pack(pady=(5,0))
    e_gen = tk.Entry(frame, width=40); e_gen.pack(pady=5)

    tk.Label(frame, text="Ordenar por:").pack(pady=(5,0))
    order_var = tk.StringVar(value="Popularidad")
    tk.OptionMenu(frame, order_var, "Popularidad", "Nombre", "Fecha").pack(pady=5)

    text_area = tk.Text(frame, height=12, wrap="word"); text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def buscar_y_mostrar():
        text_area.delete("1.0", tk.END)
        nombre = e_art.get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "Pon el nombre del artista.")
            return

        # 1) Buscar artista
        try:
            arts = sp.search(q=nombre, type="artist", limit=1)["artists"]["items"]
            if not arts:
                messagebox.showinfo("Info", "Artista no encontrado.")
                return
            art = arts[0]
        except Exception as e:
            messagebox.showerror("Error", f"No pude buscar artista:\n{e}")
            return

        # 2) Leer TODOS sus álbumes
        album_ids = set(); offset = 0
        while True:
            resp = sp.artist_albums(art["id"], album_type="album,single,compilation,appears_on", limit=50, offset=offset, country="US")["items"]
            if not resp: break
            album_ids.update(alb["id"] for alb in resp)
            offset += len(resp)

        # 3) Sacar TODAS las pistas
        raw_tracks = []
        for alb_id in album_ids:
            off2 = 0
            while True:
                items = sp.album_tracks(alb_id, limit=50, offset=off2)["items"]
                if not items: break
                raw_tracks.extend(items)
                off2 += len(items)

        if not raw_tracks:
            messagebox.showinfo("Info","No hay pistas disponibles.")
            return

        # 4) Añadir popularidad
        seen = set(); uniq = []
        for t in raw_tracks:
            if t["id"] and t["id"] not in seen:
                seen.add(t["id"]); uniq.append(t)
        for i in range(0, len(uniq), 50):
            batch = uniq[i:i+50]; ids = [t["id"] for t in batch]
            details = sp.tracks(ids)["tracks"]
            for det, orig in zip(details, batch):
                orig["popularity"] = det.get("popularity",0)
                orig["album"] = det.get("album",{})

        # 5) Filtros
        try: n = max(1,min(int(e_num.get()),50))
        except: n = 10
        try: min_pop = max(0,min(int(e_pop.get()),100))
        except: min_pop = 0
        coll_opt = coll_var.get()
        secs = [g.strip().lower() for g in e_gen.get().split(",") if g.strip()]

        # Cache de géneros
        artist_ids = {a["id"] for t in uniq for a in t["artists"]}
        genres = {}
        for i in range(0,len(artist_ids),50):
            batch = list(artist_ids)[i:i+50]
            for aobj in sp.artists(batch)["artists"]:
                genres[aobj["id"]] = [g.lower() for g in aobj.get("genres",[])]

        filt = []
        for t in uniq:
            if t["popularity"]<min_pop: continue
            if coll_opt=="Solo" and len(t["artists"]) > 1: continue
            if coll_opt=="Colab" and len(t["artists"]) < 2: continue
            if secs and not any(any(s in g for g in genres.get(a["id"],[])) for s in secs for a in t["artists"]):
                continue
            filt.append(t)

        # 6) Ordenar y limitar
        keymap = {"Popularidad": lambda x: x["popularity"], "Nombre": lambda x: x["name"].lower(), "Fecha": lambda x: x["album"].get("release_date","")}
        rev = order_var.get() in ["Popularidad","Fecha"]
        filt.sort(key=keymap[order_var.get()], reverse=rev)
        resultados = filt[:n]
        frame.uris = [t["uri"] for t in resultados]

        text_area.insert("end", f"Mostrando {len(resultados)} de {art['name']}:\n\n")
        for i,t in enumerate(resultados,1):
            artistas = ", ".join(a["name"] for a in t["artists"])
            text_area.insert("end", f"{i}. {t['name']} — {artistas} (pop {t['popularity']})\n")

    def crear_playlist_top():
        uris = getattr(frame, "uris", [])
        if not uris:
            messagebox.showinfo("Info","Primero busca las canciones.")
            return
        pl_name = simpledialog.askstring("Playlist","Nombre para la playlist:")
        if not pl_name: return
        try:
            uid = sp.current_user()["id"]
            pl = sp.user_playlist_create(uid, pl_name, public=True)
            sp.playlist_add_items(pl["id"], uris)
            messagebox.showinfo("¡Listo!","Playlist creada.")
        except Exception as e:
            messagebox.showerror("Error",f"No pude crear la playlist:\n{e}")

    btns = tk.Frame(frame); btns.pack(pady=5)
    tk.Button(btns, text="Buscar", command=buscar_y_mostrar).pack(side="left", padx=5)
    tk.Button(btns, text="Crear Playlist", command=crear_playlist_top).pack(side="left", padx=5)
    return frame

