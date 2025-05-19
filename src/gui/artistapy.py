# src/gui/artistapy.py
"""
VentanaArtistapy: interfaz para obtener recomendaciones musicales y crear playlists basadas en géneros seleccionados.
"""

import wx
import random
from spotipy import Spotify

class VentanaArtistapy(wx.Frame):
	"""
	Clase que implementa una ventana para recomendar canciones por géneros y crear una playlist personalizada en Spotify.
	La ventana está optimizada para accesibilidad y navegación con lectores de pantalla.
	"""
	def __init__(self, parent: wx.Window, sp: Spotify):
		super().__init__(parent, title="Recomendaciones #Artistapy", size=(620, 540))
		self.sp = sp

		panel = wx.Panel(self)
		sizer = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer(sizer)

		# Etiqueta de instrucciones
		label = wx.StaticText(panel, label="Géneros favoritos (separados por coma):")
		label.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		label.SetName("Etiqueta de géneros")
		sizer.Add(label, 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)

		# Campo de entrada de géneros
		self.entry_gen = wx.TextCtrl(panel, size=(480, 44))
		self.entry_gen.SetValue("Hip Hop Latino, Indie Mexicano, Trap Mexa")
		self.entry_gen.SetMinSize((320, 44))
		self.entry_gen.SetName("Campo de entrada para géneros")
		sizer.Add(self.entry_gen, 0, wx.ALL, 5)

		# Área de texto para mostrar recomendaciones y mensajes
		self.text_area = wx.TextCtrl(
			panel,
			style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP | wx.HSCROLL,
			size=(560, 320)
		)
		self.text_area.SetMinSize((560, 200))
		self.text_area.SetName("Área de resultados de recomendaciones")
		sizer.Add(self.text_area, 1, wx.ALL | wx.EXPAND, 10)

		# Botón para generar la playlist
		btn = wx.Button(panel, label="Generar playlist")
		btn.SetMinSize((180, 44))
		btn.SetName("Botón para generar playlist")
		btn.Bind(wx.EVT_BUTTON, self.generar_playlist)
		sizer.Add(btn, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 8)

		panel.Layout()
		self.Centre()
		self.Show()

	def generar_playlist(self, _evt):
		"""
		Toma los géneros ingresados por el usuario, consulta artistas relacionados en Spotify, 
		obtiene las canciones principales y genera una playlist personalizada.
		Todos los mensajes y resultados se muestran en el área de texto de la ventana.
		"""
		self.text_area.SetValue("")
		user_genres = [g.strip() for g in self.entry_gen.GetValue().split(',') if g.strip()][:5]
		if not user_genres:
			self.text_area.SetValue("No escribiste ningún género.\n")
			return

		recs = []
		for genre in user_genres:
			try:
				arts = self.sp.search(q=genre, type="artist", limit=10)["artists"]["items"]
				for art in arts[:5]:
					top = self.sp.artist_top_tracks(art["id"], country="US").get("tracks", [])
					for track in top:
						recs.append((track["name"], ", ".join(a["name"] for a in track["artists"]), track["id"]))
			except Exception as e:
				self.text_area.AppendText(f"[ERROR] Género «{genre}»: {e}\n")

		vistos = {}
		for nom, arts, tid in recs:
			key = (nom.lower(), arts.lower())
			if key not in vistos:
				vistos[key] = (nom, arts, tid)
		final_tracks = list(vistos.values())

		if not final_tracks:
			self.text_area.AppendText("No se obtuvieron canciones.\n")
			return
		random.shuffle(final_tracks)

		self.text_area.AppendText("=== Recomendaciones ===\n\n")
		for i, (nom, arts, _) in enumerate(final_tracks, 1):
			self.text_area.AppendText(f"{i}. {nom} – {arts}\n")

		try:
			uid = self.sp.me()["id"]
			pl_name = f"#Artistapy {random.randint(1000,9999)}"
			playlist = self.sp.user_playlist_create(uid, pl_name, public=False, description="Playlist generada a partir de tus géneros")
			uris = [f"spotify:track:{tid}" for (_, _, tid) in final_tracks]
			for i in range(0, len(uris), 100):
				self.sp.playlist_add_items(playlist["id"], uris[i:i+100])
			self.text_area.AppendText(f"\n\nPlaylist «{pl_name}» creada con {len(uris)} canciones.\n")
		except Exception as e:
			self.text_area.AppendText(
				f"\n\n[ERROR] Al crear/llenar la playlist: {e}\nVerifica que tu token incluya el scope «playlist-modify-private».\n"
			)

# Función que se puede invocar desde el menú principal para abrir la ventana
def ventana_artistapy(sp: Spotify, parent: wx.Window):
	VentanaArtistapy(parent, sp)