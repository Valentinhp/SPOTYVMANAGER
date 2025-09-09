# src/gui/artistapy.py
"""
Ventana #Artistapy: genera recomendaciones y crea playlist desde géneros.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from spotipy import Spotify
import random

def ventana_artistapy(parent: ttk.Frame, sp: Spotify) -> ttk.Frame:
    frame = ttk.Frame(parent, padding=20)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(1, weight=1)

    ttk.Label(frame, text="Géneros favoritos (separados por coma):", font=("Arial", 11)).pack(pady=8)
    entry_gen = ttk.Entry(frame, width=70)
    entry_gen.insert(0, "Hip Hop Latino, Indie Mexicano, Trap Mexa")
    entry_gen.pack(pady=5, fill="x")

    text_area = tk.Text(frame, wrap=tk.WORD, height=20, bg="#2a2a2a", fg="white", relief="flat")
    text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def generar_playlist():
        text_area.delete(1.0, tk.END)
        user_genres = [g.strip() for g in entry_gen.get().split(',') if g.strip()][:5]
        if not user_genres:
            messagebox.showinfo("Info", "No escribiste ningún género.")
            return
        
        recs = []
        text_area.insert(tk.END, "Buscando recomendaciones...\n")
        frame.update_idletasks()

        for genre in user_genres:
            try:
                # Usar recomendaciones directamente es más eficiente
                results = sp.recommendations(seed_genres=[g.lower().replace(' ', '-') for g in user_genres], limit=20, country="US")
                for track in results.get("tracks", []):
                    if track:
                        recs.append((track["name"], ", ".join(a["name"] for a in track["artists"]), track["id"]))
            except Exception as e:
                text_area.insert(tk.END, f"[ERROR] Genero '{genre}': {e}\n")
        
        vistos = {}
        for nom, arts, tid in recs:
            key = (nom.lower(), arts.lower())
            if key not in vistos:
                vistos[key] = (nom, arts, tid)
        
        final_tracks = list(vistos.values())
        if not final_tracks:
            text_area.delete(1.0, tk.END)
            text_area.insert(tk.END, "No se obtuvieron canciones.\n")
            return
        
        random.shuffle(final_tracks)
        final_tracks = final_tracks[:50] # Limitar a 50 para no exceder

        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, "=== Recomendaciones ===\n\n")
        for i, (nom, arts, _) in enumerate(final_tracks, 1):
            text_area.insert(tk.END, f"{i}. {nom} – {arts}\n")

        pl_name = simpledialog.askstring("Crear Playlist", "Nombre para la playlist de #Artistapy:", initialvalue=f"#Artistapy {random.randint(1000,9999)}")
        if not pl_name:
            return

        try:
            uid = sp.me()["id"]
            playlist = sp.user_playlist_create(uid, pl_name, public=False, description="Playlist generada a partir de tus géneros")
            uris = [f"spotify:track:{tid}" for (_, _, tid) in final_tracks]
            if uris:
                for i in range(0, len(uris), 100):
                    sp.playlist_add_items(playlist["id"], uris[i:i+100])
            messagebox.showinfo("Éxito", f"Playlist ‘{pl_name}’ creada con {len(uris)} canciones.")
        except Exception as e:
            messagebox.showerror("Error", f"Al crear/llenar la playlist: {e}")

    ttk.Button(frame, text="Generar y Crear Playlist", command=generar_playlist).pack(pady=10)
    return frame