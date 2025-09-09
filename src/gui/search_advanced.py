# src/gui/search_advanced.py
"""
Ventana de Búsqueda Avanzada: busca por frase o tema, filtra, y crea playlist.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import re, threading, queue, time, difflib
from spotipy import Spotify

# Lista de géneros hardcodeada (endpoint obsoleto)
GENRE_SEEDS = [
    'acoustic', 'afrobeat', 'alt-rock', 'alternative', 'ambient', 'anime',
    'black-metal', 'bluegrass', 'blues', 'bossanova', 'brazil', 'breakbeat',
    'british', 'cantopop', 'chicago-house', 'children', 'chill', 'classical',
    'club', 'comedy', 'country', 'dance', 'dancehall', 'death-metal', 'deep-house',
    'detroit-techno', 'disco', 'disney', 'drum-and-bass', 'dub', 'dubstep', 'edm',
    'electro', 'electronic', 'emo', 'folk', 'forro', 'french', 'funk', 'garage',
    'german', 'gospel', 'goth', 'grindcore', 'groove', 'grunge', 'guitar', 'happy',
    'hard-rock', 'hardcore', 'hardstyle', 'heavy-metal', 'hip-hop', 'holidays',
    'honky-tonk', 'house', 'idm', 'indian', 'indie', 'indie-pop', 'industrial',
    'iranian', 'j-dance', 'j-idol', 'j-pop', 'j-rock', 'jazz', 'k-pop', 'kids',
    'latin', 'latino', 'malay', 'mandopop', 'metal', 'metal-misc', 'metalcore',
    'minimal-techno', 'movies', 'mpb', 'new-age', 'new-release', 'opera',
    'pagode', 'party', 'philippines-opm', 'piano', 'pop', 'pop-film',
    'post-dubstep', 'power-pop', 'progressive-house', 'psych-rock', 'punk',
    'punk-rock', 'r-n-b', 'rainy-day', 'reggae', 'reggaeton', 'road-trip',
    'rock', 'rock-n-roll', 'rockabilly', 'romance', 'sad', 'salsa', 'samba',
    'sertanejo', 'show-tunes', 'singer-songwriter', 'ska', 'sleep', 'songwriter',
    'soul', 'soundtracks', 'spanish', 'study', 'summer', 'swedish', 'synth-pop',
    'tango', 'techno', 'trance', 'trip-hop', 'turkish', 'work-out', 'world-music'
]

def ventana_busqueda_avanzada(parent: ttk.Frame, sp: Spotify) -> ttk.Frame:
    frame = ttk.Frame(parent, padding=10)
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
    text_area = tk.Text(txt_frame, wrap="word", bg="#2a2a2a", fg="white"); text_area.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(txt_frame, command=text_area.yview); scrollbar.grid(row=0, column=1, sticky="ns")
    text_area.config(yscrollcommand=scrollbar.set)

    ttk.Label(frame, text="Nombre de la nueva playlist:").grid(row=5, column=0, sticky="w", padx=10)
    entry_playlist = ttk.Entry(frame); entry_playlist.insert(0, "Mi playlist"); entry_playlist.grid(row=5, column=1, sticky="ew", padx=10, pady=4)

    status = ttk.Label(frame, text="Listo", relief="sunken", anchor="w"); status.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(4,0))

    artist_genres_cache: dict[str, list[str]] = {}
    frame.uris = []

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
            except: pistas = []
        if len(pistas) < lim:
            try:
                extra = call_safe(sp.search, q=texto_busq or texto_raw, type="track", limit=lim*2)("tracks")["items"]
                pistas.extend(extra)
            except: pass
        vistos, únicos = set(), []
        for p in pistas:
            if p and p.get("id") and p["id"] not in vistos:
                vistos.add(p["id"]); únicos.append(p)
        pistas = únicos
        if use_gen and generos_usr:
            faltantes = [i for p in pistas for i in [a["id"] for a in p["artists"]] if i and i not in artist_genres_cache]
            for lote in (faltantes[i:i+50] for i in range(0, len(faltantes), 50)):
                try:
                    arts = call_safe(sp.artists, lote)("artists")
                    for aobj in arts:
                        artist_genres_cache[aobj["id"]] = aobj.get("genres", [])
                except: 
                    for aid in lote: artist_genres_cache[aid] = []
            pistas = [p for p in pistas if any(any(g in gen.lower() for gen in artist_genres_cache.get(a["id"], [])) for g in generos_usr for a in p["artists"])]
        if use_pop:
            pistas = [p for p in pistas if p.get("popularity",0) >= pop_min]
        cola.put(pistas[:lim])

    def lanzar_busqueda():
        texto_raw = entry_texto.get().strip()
        if not texto_raw: return messagebox.showinfo("Aviso", "Escribe algo para buscar.")
        generos_usr = [g.strip().lower() for g in entry_genres.get().split(",") if g.strip()]
        m = re.search(r'gé?nero\s+(.+)', texto_raw, flags=re.I)
        if not generos_usr and m:
            generos_usr = [g.strip().lower() for g in re.split(r',| y ', m.group(1))]
            texto_busq = texto_raw[:m.start()].strip()
        else:
            texto_busq = texto_raw
        seeds = []
        for g in generos_usr:
            match = difflib.get_close_matches(g, GENRE_SEEDS, n=1, cutoff=0.4)
            if match: seeds.append(match[0])
        seeds = seeds[:5]
        lim = max(1, min(int(entry_limit.get()), 50))
        pop_min = max(0, min(int(entry_pop.get()), 100))
        status.config(text="Buscando…"); text_area.delete("1.0","end")

        threading.Thread(target=_worker, args=((texto_raw, generos_usr, seeds, lim, pop_min, texto_busq, True, True),), daemon=True).start()
        def check():
            if cola.empty():
                frame.after(100, check)
            else:
                mostrar(cola.get())
        check()

    def mostrar(pistas):
        status.config(text=f"Listo – {len(pistas)} pistas" if pistas else "Sin resultados")
        frame.uris = [p["uri"] for p in pistas if p and p.get("uri")]
        text_area.delete("1.0","end")
        if not pistas:
            text_area.insert("end","No se encontraron pistas.\n")
        else:
            for i,p in enumerate(pistas,1):
                artistas = ", ".join(a["name"] for a in p["artists"])
                text_area.insert("end", f"{i:2d}. {p['name']} — {artistas} (pop {p.get('popularity',0)})\n")

    def crear_playlist_advanced():
        nombre = entry_playlist.get().strip() or "Mi playlist"
        if not frame.uris: return messagebox.showinfo("Info", "No hay canciones para agregar.")
        try:
            uid = sp.current_user()["id"]
            pl = sp.user_playlist_create(uid, nombre, public=True)
            sp.playlist_add_items(pl["id"], frame.uris)
            messagebox.showinfo("¡Listo!", f"Playlist '{nombre}' creada con {len(frame.uris)} canciones.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la playlist:\n{e}")

    frm_btn = ttk.Frame(frame); frm_btn.grid(row=6, column=0, columnspan=2, pady=8)
    ttk.Button(frm_btn, text="Buscar/Recomendar", command=lanzar_busqueda).pack(side="left", padx=8)
    ttk.Button(frm_btn, text="Crear Playlist", command=crear_playlist_advanced).pack(side="left", padx=8)

    frame.bind("<Return>", lambda e: lanzar_busqueda())
    status.config(text="Listo – escribe tu frase y pulsa ⏎")
    return frame