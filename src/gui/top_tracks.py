# src/gui/top_tracks.py
"""
Ventana Top Tracks Mejorado: busca un artista, filtra y crea playlist.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from spotipy import Spotify

def ventana_top_tracks(parent: ttk.Frame, sp: Spotify) -> ttk.Frame:
    frame = ttk.Frame(parent, padding=15)
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(8, weight=1)

    # --- Controles ---
    controls_frame = ttk.Frame(frame)
    controls_frame.grid(row=0, column=0, sticky="ew", pady=5)
    controls_frame.grid_columnconfigure(1, weight=1)

    ttk.Label(controls_frame, text="Artista:").grid(row=0, column=0, padx=(0,5), pady=5, sticky="w")
    e_art = ttk.Entry(controls_frame, width=40)
    e_art.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

    ttk.Label(controls_frame, text="Cuántos tracks (1–50):").grid(row=1, column=0, padx=(0,5), pady=5, sticky="w")
    e_num = ttk.Entry(controls_frame, width=10); e_num.insert(0, "10")
    e_num.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    ttk.Label(controls_frame, text="Popularidad mínima (0–100):").grid(row=2, column=0, padx=(0,5), pady=5, sticky="w")
    e_pop = ttk.Entry(controls_frame, width=10); e_pop.insert(0, "0")
    e_pop.grid(row=2, column=1, padx=5, pady=5, sticky="w")

    ttk.Label(controls_frame, text="Colaboraciones:").grid(row=3, column=0, padx=(0,5), pady=5, sticky="w")
    coll_var = tk.StringVar(value="Todas")
    collab_frame = ttk.Frame(controls_frame)
    for val, txt in [("Todas","Todas"), ("Solo","Solo artista"), ("Colab","Solo colaboraciones")]:
        ttk.Radiobutton(collab_frame, text=txt, variable=coll_var, value=val).pack(side="left", padx=5, anchor="w")
    collab_frame.grid(row=3, column=1, columnspan=2, sticky="w")

    ttk.Label(controls_frame, text="Géneros secundarios (sep. coma):").grid(row=4, column=0, padx=(0,5), pady=5, sticky="w")
    e_gen = ttk.Entry(controls_frame, width=40)
    e_gen.grid(row=4, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

    ttk.Label(controls_frame, text="Ordenar por:").grid(row=5, column=0, padx=(0,5), pady=5, sticky="w")
    order_var = tk.StringVar(value="Popularidad")
    ttk.OptionMenu(controls_frame, order_var, "Popularidad", "Popularidad", "Nombre", "Fecha").grid(row=5, column=1, padx=5, pady=5, sticky="w")

    # --- Área de texto para resultados ---
    text_area = tk.Text(frame, height=15, wrap="word", bg="#2a2a2a", fg="white", relief="flat")
    text_area.grid(row=8, column=0, sticky="nsew", pady=(10,0))

    # --- Botones ---
    btn_frame = ttk.Frame(frame)
    btn_frame.grid(row=9, column=0, pady=10)

    frame.uris = [] # para guardar las uris de los tracks

    def buscar_y_mostrar():
        text_area.delete("1.0", tk.END)
        nombre = e_art.get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "Pon el nombre del artista.")
            return

        try:
            arts = sp.search(q=nombre, type="artist", limit=1)["artists"]["items"]
            if not arts:
                messagebox.showinfo("Info", "Artista no encontrado.")
                return
            art = arts[0]
        except Exception as e:
            messagebox.showerror("Error", f"No pude buscar artista:\n{e}")
            return

        album_ids = set(); offset = 0
        while True:
            try:
                resp = sp.artist_albums(art["id"], album_type="album,single,compilation,appears_on", limit=50, offset=offset, country="US")["items"]
                if not resp: break
                album_ids.update(alb["id"] for alb in resp)
                offset += len(resp)
            except Exception: break

        raw_tracks = []
        for alb_id in album_ids:
            off2 = 0
            while True:
                try:
                    items = sp.album_tracks(alb_id, limit=50, offset=off2)["items"]
                    if not items: break
                    raw_tracks.extend(items)
                    off2 += len(items)
                except Exception: break
        
        if not raw_tracks: return messagebox.showinfo("Info","No hay pistas disponibles.")

        seen = set(); uniq = []
        for t in raw_tracks:
            if t["id"] and t["id"] not in seen:
                seen.add(t["id"]); uniq.append(t)
        
        for i in range(0, len(uniq), 50):
            batch = uniq[i:i+50]; ids = [t["id"] for t in batch]
            try:
                details = sp.tracks(ids)["tracks"]
                for det, orig in zip(details, batch):
                    orig["popularity"] = det.get("popularity",0)
                    orig["album"] = det.get("album",{})
            except Exception: continue

        try: n = max(1,min(int(e_num.get()),50))
        except: n = 10
        try: min_pop = max(0,min(int(e_pop.get()),100))
        except: min_pop = 0
        coll_opt = coll_var.get()
        secs = [g.strip().lower() for g in e_gen.get().split(",") if g.strip()]

        artist_ids = {a["id"] for t in uniq for a in t["artists"] if a and a.get("id")}
        genres = {}
        if secs:
            for i in range(0,len(list(artist_ids)),50):
                batch = list(artist_ids)[i:i+50]
                try:
                    for aobj in sp.artists(batch)["artists"]:
                        genres[aobj["id"]] = [g.lower() for g in aobj.get("genres",[])]
                except Exception: continue

        filt = []
        for t in uniq:
            if t.get("popularity", 0) < min_pop: continue
            # FIX: La siguiente línea tenía un error de sintaxis
            if coll_opt == "Solo" and len(t["artists"]) > 1: continue
            if coll_opt == "Colab" and len(t["artists"]) < 2: continue
            if secs and not any(any(s in g for g in genres.get(a["id"],[])) for s in secs for a in t["artists"]):
                continue
            filt.append(t)

        keymap = {"Popularidad": lambda x: x.get("popularity", 0), "Nombre": lambda x: x["name"].lower(), "Fecha": lambda x: x.get("album", {}).get("release_date","")}
        rev = order_var.get() in ["Popularidad","Fecha"]
        filt.sort(key=keymap[order_var.get()], reverse=rev)
        resultados = filt[:n]
        frame.uris = [t["uri"] for t in resultados if t.get("uri")]

        text_area.insert("end", f"Mostrando {len(resultados)} de {art['name']}:\n\n")
        for i,t in enumerate(resultados,1):
            artistas = ", ".join(a["name"] for a in t["artists"])
            text_area.insert("end", f"{i}. {t['name']} — {artistas} (pop {t.get('popularity', 'N/A')})\n")

    def crear_playlist_top():
        if not frame.uris:
            messagebox.showinfo("Info","Primero busca las canciones.")
            return
        pl_name = simpledialog.askstring("Playlist","Nombre para la playlist:")
        if not pl_name: return
        try:
            uid = sp.current_user()["id"]
            pl = sp.user_playlist_create(uid, pl_name, public=True)
            sp.playlist_add_items(pl["id"], frame.uris)
            messagebox.showinfo("¡Listo!","Playlist creada.")
        except Exception as e:
            messagebox.showerror("Error",f"No pude crear la playlist:\n{e}")

    ttk.Button(btn_frame, text="Buscar", command=buscar_y_mostrar).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Crear Playlist", command=crear_playlist_top).pack(side="left", padx=5)
    
    return frame