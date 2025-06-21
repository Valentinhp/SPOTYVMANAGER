import tkinter as tk
from tkinter import ttk
import src.config as cfg

def style_toplevel(ven: tk.Toplevel, title: str, size: str | None = None) -> ttk.Frame:
    """
    Estiliza un Toplevel con:
     - Fondo oscuro
     - Cabecera con título y línea de acento
     - Frame de contenido con padding
    Devuelve el Frame donde irá todo el contenido de la ventana.
    """
    # ventana
    if size:
        ven.geometry(size)
    ven.title(title)
    ven.configure(bg=cfg.BG_MAIN)

    # cabecera
    header = ttk.Frame(ven, style="Card.TFrame")
    header.pack(fill="x", padx=20, pady=(10,5))
    ttk.Label(header, text=title, style="Title.TLabel").pack(side="left")
    tk.Frame(header, bg=cfg.ACCENT, height=3).pack(
        fill="x", padx=(10,0), pady=(6,0), expand=True
    )

    # contenedor principal
    content = ttk.Frame(ven, style="Card.TFrame", padding=16)
    content.pack(fill="both", expand=True, padx=20, pady=10)
    return content
