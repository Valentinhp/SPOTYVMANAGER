# src/gui/podcasts.py

"""
Ventana para sincronizar podcasts con sus playlists (data_podcasts).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from spotipy import Spotify
from ..utils.spotify_utils import (
    get_podcast_episodes,
    get_playlist_items,
    add_episodes_to_playlist,
)
from ..data_podcasts import data_podcasts

def ventana_sincronizar_podcasts_data(parent: ttk.Frame, sp: Spotify) -> ttk.Frame:
    frame = ttk.Frame(parent, padding=20)
    frame.columnconfigure(0, weight=1)

    ttk.Label(frame, text="Sincronizando podcasts con sus playlists…", font=("Arial", 11)).pack(pady=8)
    prog = ttk.Progressbar(frame, orient="horizontal", length=460, mode="determinate", maximum=len(data_podcasts) if data_podcasts else 1)
    prog.pack(pady=5, fill=tk.X, expand=True)
    lbl_estado = ttk.Label(frame, text="Esperando…", anchor="w")
    lbl_estado.pack(fill=tk.X, padx=10)
    txt_log = tk.Text(frame, height=10, wrap=tk.WORD, bg="#2a2a2a", fg="white", relief="flat")
    txt_log.pack(padx=10, pady=6, fill=tk.BOTH, expand=True)

    def log(msg: str):
        txt_log.insert(tk.END, msg + "\n")
        txt_log.see(tk.END)
        frame.update_idletasks()

    def sincronizar():
        if not data_podcasts:
            log("No hay podcasts configurados en data_podcasts.py")
            return

        total = len(data_podcasts)
        prog["value"] = 0
        for idx, pair in enumerate(data_podcasts, start=1):
            pod_id, pl_id = pair["podcast"], pair["playlist"]

            try:
                podcast_name = sp.show(pod_id, market="US")["name"]
            except Exception:
                podcast_name = f"Podcast {pod_id[:8]}…"
            try:
                playlist_name = sp.playlist(pl_id, fields="name")["name"]
            except Exception:
                playlist_name = f"Playlist {pl_id[:8]}…"

            lbl_estado.config(text=f"{idx}/{total}  {podcast_name} → {playlist_name}")
            frame.update_idletasks()

            try:
                eps = get_podcast_episodes(sp, pod_id)
                if not eps:
                    log(f"❌ {podcast_name}: sin episodios o error.")
                    prog["value"] = idx
                    continue

                antes = set(get_playlist_items(sp, pl_id))
                add_episodes_to_playlist(sp, pl_id, eps)
                despues = set(get_playlist_items(sp, pl_id))
                nuevos = len(despues) - len(antes)
                if nuevos:
                    log(f"✅ {podcast_name}: {nuevos} nuevos → {playlist_name}")
                else:
                    log(f"• {podcast_name}: 0 nuevos")
            except Exception as e:
                log(f"❌ ERROR con {podcast_name}: {e}")
            
            prog["value"] = idx

        lbl_estado.config(text="¡Sincronización completa!")
        messagebox.showinfo("Terminado", "Todos los podcasts han sido sincronizados.")

    ttk.Button(frame, text="Iniciar sincronización", command=sincronizar).pack(pady=10)
    return frame