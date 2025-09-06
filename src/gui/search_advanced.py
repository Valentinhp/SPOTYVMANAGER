# src/gui/search_advanced.py
"""
Ventana de Búsqueda Avanzada: busca por frase o tema, filtra, y crea playlist.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import re, threading, queue, time, difflib
from spotipy import Spotify

def ventana_busqueda_avanzada(parent: tk.Widget, sp=None, **kwargs) -> ttk.Frame:
    frame = ttk.Frame(parent)
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(4, weight=1)

    modo = tk.StringVar(value="frase")
    ttk.Radiobutton(frame, text="Por frase", variable=modo, value="frase").grid(row=0, column=0, sticky="w", padx=10, pady=6)
    ttk.Radiobutton(frame, text="Por tema/emoción", variable=modo, value="tema").grid(row=0, column=1, sticky="w", padx=10, pady=6)

    ttk.Label(frame, text="Frase/tema (puedes incluir 'genero ...'):").grid(row=1, column=0, sticky="w", padx=10)
    entry_texto = ttk.Entry(frame)
    entry_texto.grid(row=1, column=1, sticky="ew", padx=10, pady=4)
    entry_texto.focus()

    ttk.Label(frame, text="Géneros (opcional, sep. por coma):").grid(row=2, column=0, sticky="w", padx=10)
    entry_genres = ttk.Entry(frame)
    entry_genres.grid(row=2, column=1, sticky="ew", padx=10, pady=4)

    frm_nums = ttk.Frame(frame)
    frm_nums.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=6)
    ttk.Label(frm_nums, text="Máx pistas (1–50):").grid(row=0, column=0, sticky="w")
    entry_limit = ttk.Entry(frm_nums, width=4); entry_limit.insert(0, "15"); entry_limit.grid(row=0, column=1, padx=(4,20))
    ttk.Label(frm_nums, text="Pop mín (0–100):").grid(row=0, column=2, sticky="w")
    entry_pop = ttk.Entry(frm_nums, width=4); entry_pop.insert(0, "0"); entry_pop.grid(row=0, column=3, padx=4)

    txt_frame = ttk.Frame(frame)
    txt_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
    txt_frame.columnconfigure(0, weight=1); txt_frame.rowconfigure(0, weight=1)
    text_area = tk.Text(txt_frame, wrap="word"); text_area.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(txt_frame, command=text_area.yview); scrollbar.grid(row=0, column=1, sticky="ns")
    text_area.config(yscrollcommand=scrollbar.set)

    ttk.Label(frame, text="Nombre de la nueva playlist:").grid(row=5, column=0, sticky="w", padx=10)
    entry_playlist = ttk.Entry(frame); entry_playlist.insert(0, "Mi playlist"); entry_playlist.grid(row=5, column=1, sticky="ew", padx=10, pady=4)

    status = ttk.Label(frame, text="Listo", relief="sunken", anchor="w"); status.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(4,0))

    seeds_spotify = []
    artist_genres_cache: dict[str, list[str]] = {}

    def call_safe(fn, *a, **k):
        for i in range(3):
            try:
                return fn(*a, **k)
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    time.sleep(1.5 * (i+1))
                else:
                    raise
        raise RuntimeError("Rate-limit continuo en Spotify")

    cola = queue.Queue()
    def _worker(params):
        texto_raw, generos_usr, seeds, lim, pop_min, texto_busq, use_pop, use_gen = params
        pistas = []
        if use_gen and seeds:
            try:
                pistas = call_safe(sp.recommendations, seed_genres=seeds, limit=lim)("tracks")
            except:
                pistas = []
        if len(pistas) < lim:
            try:
                extra = call_safe(sp.search, q=texto_busq or texto_raw, type="track", limit=lim*2)("tracks")["items"]
                pistas.extend(extra)
            except:
                pass
        vistos, únicos = set(), []
        for p in pistas:
            if p["id"] not in vistos:
                vistos.add(p["id"]); únicos.append(p)
        pistas = únicos
        if use_gen and generos_usr:
            faltantes = [i for p in pistas for i in [a["id"] for a in p["artists"]] if i not in artist_genres_cache]
            for lote in (faltantes[i:i+50] for i in range(0, len(faltantes), 50)):
                try:
                    arts = call_safe(sp.artists, lote)("artists")
                    for aobj in arts:
                        artist_genres_cache[aobj["id"]] = aobj.get("genres", [])
                except:
                    for aid in lote:
                        artist_genres_cache[aid] = []
            pistas = [p for p in pistas if any(any(g in gen.lower() for gen in artist_genres_cache.get(a["id"], [])) for g in generos_usr for a in p["artists"])]
        if use_pop:
            pistas = [p for p in pistas if p.get("popularity",0) >= pop_min]
        cola.put(pistas[:lim])

    def lanzar_busqueda():
        texto_raw = entry_texto.get().strip()
        if not texto_raw:
            messagebox.showinfo("Aviso", "Escribe algo para buscar.")
            return
        generos_usr = [g.strip().lower() for g in entry_genres.get().split(",") if g.strip()]
        if not generos_usr:
            m = re.search(r'gé?nero\s+(.+)', texto_raw, flags=re.I)
            if m:
                generos_usr = [g.strip().lower() for g in re.split(r',| y ', m.group(1))]
                texto_busq = texto_raw[:m.start()].strip()
            else:
                texto_busq = texto_raw
        else:
            texto_busq = texto_raw
        seeds = []
        for g in generos_usr:
            match = difflib.get_close_matches(g, seeds_spotify, n=1, cutoff=0.4)
            if match:
                seeds.append(match[0])
        seeds = seeds[:5]
        lim = max(1, min(int(entry_limit.get()), 50))
        pop_min = max(0, min(int(entry_pop.get()), 100))
        estrategias = [(True,True),(False,True),(True,False),(False,False)]
        status.config(text="Buscando…"); text_area.delete("1.0","end")

        def probar(idx=0):
            if idx >= len(estrategias):
                cola.put([]); return
            use_pop, use_gen = estrategias[idx]
            threading.Thread(target=_worker, args=((texto_raw, generos_usr, seeds, lim, pop_min, texto_busq, use_pop, use_gen),), daemon=True).start()
            def check():
                if cola.empty():
                    frame.after(100, check)
                else:
                    pistas = cola.get()
                    if pistas or idx == len(estrategias)-1:
                        mostrar(pistas)
                    else:
                        probar(idx+1)
            check()

        probar()

    def mostrar(pistas):
        if pistas:
            status.config(text=f"Listo – {len(pistas)} pistas")
        else:
            status.config(text="Sin resultados")
        frame.uris = [p["uri"] for p in pistas]
        text_area.delete("1.0","end")
        if not pistas:
            text_area.insert("end","No se encontraron pistas.\n")
        else:
            for i,p in enumerate(pistas,1):
                artistas = ", ".join(a["name"] for a in p["artists"])
                text_area.insert("end", f"{i:2d}. {p['name']} — {artistas} (pop {p.get('popularity',0)})\n")

    def crear_playlist_advanced(sp: Spotify, nombre: str, uris: list[str]):
        """
        Crea una lista nueva con las URIs que le pases.
        """
        if not uris:
            messagebox.showinfo("Info", "No hay canciones para agregar.")
            return

        try:
            uid = sp.current_user()["id"]
            pl = sp.user_playlist_create(uid, nombre, public=True)
            sp.playlist_add_items(pl["id"], uris)
            messagebox.showinfo("¡Listo!", f"Playlist '{nombre}' creada con {len(uris)} canciones.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la playlist:\n{e}")

    frm_btn = ttk.Frame(frame); frm_btn.grid(row=6, column=0, columnspan=2, pady=8)
    ttk.Button(frm_btn, text="Buscar/Recomendar", command=lanzar_busqueda).pack(side="left", padx=8)
    ttk.Button(frm_btn, text="Crear Playlist", command=lambda: crear_playlist_advanced(sp, entry_playlist.get().strip() or "Mi playlist", getattr(frame, "uris", []))).pack(side="left", padx=8)

    frame.bind("<Return>", lambda e: lanzar_busqueda())
    status.config(text="Listo – escribe tu frase y pulsa ⏎")
    return frame

