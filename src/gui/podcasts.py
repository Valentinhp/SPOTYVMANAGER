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
from ..data_podcasts import data_podcasts  # <-- ahora toma la lista externa

def ventana_sincronizar_podcasts_data(sp: Spotify, root: tk.Tk):
    ven = tk.Toplevel(root)
    ven.title("Sincronizar Podcasts (data_podcasts)")
    ven.geometry("520x300")

    tk.Label(ven, text="Sincronizando podcasts con sus playlists…",
             font=("Arial", 11)).pack(pady=8)
    prog = ttk.Progressbar(ven, orient="horizontal",
                           length=460, mode="determinate",
                           maximum=len(data_podcasts))
    prog.pack(pady=5)
    lbl_estado = tk.Label(ven, text="Esperando…", anchor="w")
    lbl_estado.pack(fill=tk.X, padx=10)
    txt_log = tk.Text(ven, height=8, wrap=tk.WORD)
    txt_log.pack(padx=10, pady=6, fill=tk.BOTH, expand=True)

    def log(msg: str):
        txt_log.insert(tk.END, msg + "\n")
        txt_log.see(tk.END)
        ven.update_idletasks()

    def sincronizar():
        total = len(data_podcasts)
        prog["value"] = 0
        for idx, pair in enumerate(data_podcasts, start=1):
            pod_id, pl_id = pair["podcast"], pair["playlist"]

            # Intentamos obtener nombres para mostrar estado
            try:
                podcast_name = sp.show(pod_id, market="US")["name"]
            except:
                podcast_name = f"Podcast {pod_id[:8]}…"
            try:
                playlist_name = sp.playlist(pl_id, fields="name")["name"]
            except:
                playlist_name = f"Playlist {pl_id[:8]}…"

            lbl_estado.config(
                text=f"{idx}/{total}  {podcast_name} → {playlist_name}"
            )
            ven.update_idletasks()

            # Obtener episodios y agregarlos
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
            prog["value"] = idx

        lbl_estado.config(text="¡Sincronización completa!")
        messagebox.showinfo("Terminado", "Todos los podcasts han sido sincronizados.")

    tk.Button(ven, text="Iniciar sincronización", command=sincronizar) \
        .pack(pady=6)
