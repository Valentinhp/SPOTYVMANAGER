# src/gui/artistapy.py
"""
Ventana #Artistapy: genera recomendaciones y crea playlist desde géneros.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from spotipy import Spotify
import random

def ventana_artistapy(parent: tk.Widget, sp=None, **kwargs) -> ttk.Frame:
    frame = ttk.Frame(parent)

    tk.Label(frame, text="Géneros favoritos (separados por coma):", font=("Arial", 11)).pack(pady=8)
    entry_gen = tk.Entry(frame, width=60)
    entry_gen.insert(0, "Hip Hop Latino, Indie Mexicano, Trap Mexa")
    entry_gen.pack(pady=5)

    text_area = tk.Text(frame, wrap=tk.WORD, width=75, height=20)
    text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def generar_playlist():
        text_area.delete(1.0, tk.END)
        user_genres = [g.strip() for g in entry_gen.get().split(',') if g.strip()][:5]
        if not user_genres:
            messagebox.showinfo("Info", "No escribiste ningún género.")
            return
        recs = []
        for genre in user_genres:
            try:
                arts = sp.search(q=genre, type="artist", limit=10)["artists"]["items"]
                for art in arts[:5]:
                    top = sp.artist_top_tracks(art["id"], country="US").get("tracks", [])
                    for track in top:
                        recs.append((track["name"], ", ".join(a["name"] for a in track["artists"]), track["id"]))
            except Exception as e:
                text_area.insert(tk.END, f"[ERROR] Género «{genre}»: {e}\n")
        vistos = {}
        for nom, arts, tid in recs:
            key = (nom.lower(), arts.lower())
            if key not in vistos:
                vistos[key] = (nom, arts, tid)
        final_tracks = list(vistos.values())
        if not final_tracks:
            text_area.insert(tk.END, "No se obtuvieron canciones.\n")
            return
        random.shuffle(final_tracks)

        text_area.insert(tk.END, "=== Recomendaciones ===\n\n")
        for i, (nom, arts, _) in enumerate(final_tracks, 1):
            text_area.insert(tk.END, f"{i}. {nom} – {arts}\n")

        try:
            uid = sp.me()["id"]
            pl_name = f"#Artistapy {random.randint(1000,9999)}"
            playlist = sp.user_playlist_create(uid, pl_name, public=False, description="Playlist generada a partir de tus géneros")
            uris = [f"spotify:track:{tid}" for (_, _, tid) in final_tracks]
            for i in range(0, len(uris), 100):
                sp.playlist_add_items(playlist["id"], uris[i:i+100])
            text_area.insert(tk.END, f"\n\n✅ Playlist «{pl_name}» creada con {len(uris)} canciones.")
        except Exception as e:
            text_area.insert(tk.END, f"\n\n[ERROR] Al crear/llenar la playlist: {e}\nVerifica que tu token incluya el scope «playlist-modify-private».")
    tk.Button(frame, text="Generar playlist", command=generar_playlist).pack(pady=8)
    return frame
