# src/gui/artist_manager.py
"""
Clase VentanaGestorAutomatico: aquí busco un artista, obtengo todas sus canciones únicas y gestiono playlists en Spotify. 
Todo el flujo está pensado para uso accesible y navegación con lector de pantalla.
"""
import wx
import time, unicodedata, re
from spotipy import Spotify

class VentanaGestorAutomatico(wx.Frame):
	def __init__(self, parent: wx.Window, sp: Spotify):
		# Aquí uso wx.Frame porque quiero una ventana independiente y accesible.
		super().__init__(parent, title="Gestor de Playlists Automáticas en Spotify", size=(600, 600))
		self.sp = sp

		try:
			self.user_id = self.sp.current_user()["id"]
		except Exception:
			wx.MessageBox("No se pudo obtener info del usuario.", "Error", wx.OK | wx.ICON_ERROR)
			self.Destroy()
			return

		self.songs = []		# Aquí voy a guardar la lista final de canciones.
		self.artist_id = None  # Aquí el ID del artista seleccionado.
		self.artists_found = []  # Lista de resultados de búsqueda

		# Creo los paneles principales para cada sección
		self.panel = wx.Panel(self)
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.panel.SetSizer(self.sizer)

		# Creo el panel de búsqueda de artista al arrancar
		self.frame_artist = wx.Panel(self.panel)
		self.sizer.Add(self.frame_artist, 1, wx.EXPAND)
		self.create_artist_frame(self.frame_artist)

		# Panel para gestión de playlists, lo creo vacío y sólo lo muestro cuando toca
		self.frame_playlist = wx.Panel(self.panel)
		self.frame_playlist.Hide()

		# Panel para "vaciar múltiples playlists", lo pongo abajo siempre visible
		self.frame_clear = wx.Panel(self.panel)
		self.sizer.Add(self.frame_clear, 0, wx.EXPAND | wx.BOTTOM, 5)
		self.create_clear_frame(self.frame_clear)

		self.panel.Layout()
		self.Centre()
		self.Show()

	# ----------- Panel para vaciar múltiples playlists ---------
	def create_clear_frame(self, panel):
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		panel.SetSizer(sizer)
		btn = wx.Button(panel, label="Vaciar Múltiples Playlists")
		btn.SetMinSize((220, 44))
		btn.SetName("Vaciar Múltiples Playlists")
		btn.Bind(wx.EVT_BUTTON, lambda evt: self.abrir_ventana_vaciar_playlists())
		sizer.Add(btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

	# ----------- Panel de búsqueda de artista ---------------
	def create_artist_frame(self, panel):
		# Aquí destruyo widgets previos del panel para reiniciar la sección
		for w in panel.GetChildren():
			w.Destroy()
		sizer = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer(sizer)

		label = wx.StaticText(panel, label="Introduce el nombre del artista:")
		label.SetName("Etiqueta de búsqueda de artista")
		sizer.Add(label, 0, wx.TOP | wx.LEFT, 10)

		self.entry_artist = wx.TextCtrl(panel, size=(320, 44))
		self.entry_artist.SetHint("Nombre del artista")
		self.entry_artist.SetMinSize((320, 44))
		self.entry_artist.SetName("Campo de texto para nombre de artista")
		sizer.Add(self.entry_artist, 0, wx.ALL, 5)

		btn_buscar = wx.Button(panel, label="Buscar")
		btn_buscar.SetMinSize((100, 44))
		btn_buscar.Bind(wx.EVT_BUTTON, self.search_artist)
		sizer.Add(btn_buscar, 0, wx.ALL, 5)

		self.listbox_artists = wx.ListBox(panel, size=(400, 100), style=wx.LB_SINGLE)
		self.listbox_artists.SetName("Resultados de artistas")
		sizer.Add(self.listbox_artists, 1, wx.ALL | wx.EXPAND, 10)
		self.listbox_artists.Bind(wx.EVT_LISTBOX, self.on_artist_select)

	def search_artist(self, _evt):
		# Aquí tomo el texto y hago la búsqueda en Spotify
		name = self.entry_artist.GetValue().strip()
		if not name:
			wx.MessageBox("Ingresa un nombre primero.", "Info", wx.OK | wx.ICON_INFORMATION)
			return
		try:
			res = self.sp.search(q=name, type="artist", limit=5)
			self.artists_found = res["artists"]["items"]
			self.listbox_artists.Clear()
			if not self.artists_found:
				wx.MessageBox("No se encontró el artista.", "Info", wx.OK | wx.ICON_INFORMATION)
				return
			for art in self.artists_found:
				self.listbox_artists.Append(art["name"])
		except Exception as e:
			wx.MessageBox(f"Error al buscar el artista: {e}", "Error", wx.OK | wx.ICON_ERROR)

	def on_artist_select(self, evt):
		idx = evt.GetSelection()
		if idx == wx.NOT_FOUND:
			return
		art = self.artists_found[idx]
		self.artist_id = art["id"]
		if wx.MessageBox(f"Seleccionaste {art['name']}. ¿Continuar?", "Confirmar", wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
			self.fetch_artist_songs()

	def fetch_artist_songs(self):
		try:
			self.songs = self.obtener_canciones_artista_completas(self.artist_id)
			wx.MessageBox(f"Se encontraron {len(self.songs)} canciones únicas.", "Info", wx.OK | wx.ICON_INFORMATION)
			# Aquí oculto panel de artista y muestro panel de playlist
			self.frame_artist.Hide()
			self.create_playlist_frame(self.frame_playlist)
			self.sizer.Insert(0, self.frame_playlist, 1, wx.EXPAND)
			self.frame_playlist.Show()
			self.panel.Layout()
		except Exception as e:
			wx.MessageBox(f"Error al obtener las canciones: {e}", "Error", wx.OK | wx.ICON_ERROR)

	# ----------- Lógica para quitar duplicados y encontrar canciones únicas -----------
	def obtener_canciones_artista_completas(self, artist_id: str):
		MARKETS = ("US", "MX")
		ALT_FLAGS = (
			"acoustic", "live", "en vivo", "unplugged", "instrumental",
			"remaster", "remastered", "demo", "karaoke", "edit",
			"mix", "remix", "versión", "version", "session"
		)
		NOISE = (
			"feat.", "featuring", "ft.", "with", "con"
		)
		elegido = {}
		total_raw = 0
		clean_punct = re.compile(r"[()\[\]{}\-–_:]")

		def slug(txt: str) -> str:
			txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
			txt = txt.lower()
			txt = clean_punct.sub(" ", txt)
			for w in (*ALT_FLAGS, *NOISE):
				txt = txt.replace(w, " ")
			return " ".join(txt.split())

		def es_alt(titulo: str, album: str) -> bool:
			t, a = titulo.lower(), album.lower()
			return any(w in t or w in a for w in ALT_FLAGS)

		def considera(track: dict, album_name: str):
			nonlocal total_raw
			total_raw += 1
			tid = track.get("id")
			if not tid:
				return
			title = track.get("name", "").strip()
			base = slug(title)
			alt = es_alt(title, album_name)
			if base not in elegido:
				elegido[base] = {"track": track, "alt": alt}
			elif elegido[base]["alt"] and not alt:
				elegido[base] = {"track": track, "alt": alt}

		# Aquí descargo todos los álbumes
		try:
			alb_resp = self.sp.artist_albums(
				artist_id,
				album_type="album,single,compilation,appears_on",
				limit=50
			)
		except Exception as e:
			print(f"[{artist_id}] error álbumes: {e}")
			return []

		albums = []
		while True:
			albums += alb_resp.get("items", [])
			if not alb_resp.get("next"):
				break
			alb_resp = self.sp.next(alb_resp)

		for alb in albums:
			alb_name = alb.get("name", "")
			for m in MARKETS:
				try:
					tr_resp = self.sp.album_tracks(alb["id"], limit=50, market=m)
				except Exception:
					continue
				while True:
					for t in tr_resp.get("items", []):
						if any(a["id"] == artist_id for a in t["artists"]):
							considera(t, alb_name)
					if not tr_resp.get("next"):
						break
					tr_resp = self.sp.next(tr_resp)

		try:
			art_name = self.sp.artist(artist_id)["name"]
			offset = 0
			while True:
				sr = self.sp.search(q=f'artist:"{art_name}"', type="track",
									limit=50, offset=offset)
				for t in sr["tracks"]["items"]:
					if any(a["id"] == artist_id for a in t["artists"]):
						considera(t, "")
				if not sr["tracks"]["next"]:
					break
				offset += 50
		except Exception as e:
			print(f"[{artist_id}] búsqueda global falló: {e}")

		canciones = [
			{"id": d["track"]["id"], "name": d["track"]["name"]}
			for d in elegido.values()
		]
		print(f"[{artist_id}] vistas≈{total_raw}, únicas={len(canciones)}")
		return canciones

	# ----------------- Informe rápido -----------------
	def generar_informe_canciones(self):
		if not self.songs:
			wx.MessageBox("No hay canciones cargadas.", "Info", wx.OK | wx.ICON_INFORMATION)
			return
		total_unicas = len(self.songs)
		total_collab = sum(1 for s in self.songs if len(self.sp.track(s["id"])["artists"]) > 1)
		total_dups = (total_unicas + total_collab) - total_unicas
		wx.MessageBox(
			f"Pistas únicas: {total_unicas}\n"
			f"Con colaboraciones: {total_collab}\n"
			f"Duplicadas descartadas: {total_dups}",
			"Informe de canciones",
			wx.OK | wx.ICON_INFORMATION
		)

	# ----------- Panel de gestión de playlists -----------
	def create_playlist_frame(self, panel):
		# Destruyo widgets previos del panel para reiniciar la sección
		for w in panel.GetChildren():
			w.Destroy()
		sizer = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer(sizer)

		label = wx.StaticText(panel, label="¿Qué deseas hacer?")
		sizer.Add(label, 0, wx.TOP | wx.LEFT, 10)

		self.playlist_option = wx.RadioBox(
			panel, label="Tipo de acción",
			choices=["Crear nueva playlist", "Seleccionar playlist existente"],
			majorDimension=1, style=wx.RA_SPECIFY_ROWS
		)
		self.playlist_option.SetName("Opciones de playlist")
		sizer.Add(self.playlist_option, 0, wx.ALL, 5)
		self.playlist_option.Bind(wx.EVT_RADIOBOX, self.update_playlist_option)

		self.frame_option = wx.Panel(panel)
		sizer.Add(self.frame_option, 1, wx.EXPAND | wx.ALL, 5)

		btn_buscar_otro = wx.Button(panel, label="Buscar otro artista")
		btn_buscar_otro.Bind(wx.EVT_BUTTON, lambda evt: self.reset_to_artist_search())
		sizer.Add(btn_buscar_otro, 0, wx.ALL, 5)

		self.update_playlist_option(None)

	def update_playlist_option(self, _evt):
		# Aquí destruyo los controles previos del frame_option
		for w in self.frame_option.GetChildren():
			w.Destroy()
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.frame_option.SetSizer(sizer)

		if self.playlist_option.GetSelection() == 0:
			# Opción de crear nueva playlist
			self.new_playlist_entry = wx.TextCtrl(self.frame_option, size=(320, 44))
			self.new_playlist_entry.SetHint("Nombre de la nueva playlist")
			sizer.Add(self.new_playlist_entry, 0, wx.ALL, 5)
			btn = wx.Button(self.frame_option, label="Crear Playlist")
			btn.Bind(wx.EVT_BUTTON, lambda evt: self.crear_playlist_y_agregar_songs())
			sizer.Add(btn, 0, wx.ALL, 5)
		else:
			# Seleccionar playlist existente
			self.entry_search = wx.TextCtrl(self.frame_option, size=(320, 44))
			self.entry_search.SetHint("Buscar playlist")
			self.entry_search.Bind(wx.EVT_TEXT, self.filtrar_playlists)
			sizer.Add(self.entry_search, 0, wx.ALL, 5)

			self.playlists = self.obtener_todas_playlists()
			self.playlist_listbox = wx.ListBox(self.frame_option, choices=[pl["name"] for pl in self.playlists], style=wx.LB_SINGLE)
			sizer.Add(self.playlist_listbox, 1, wx.ALL | wx.EXPAND, 5)

			btn_frame = wx.BoxSizer(wx.HORIZONTAL)
			btn_vaciar = wx.Button(self.frame_option, label="Vaciar Playlist")
			btn_actualizar = wx.Button(self.frame_option, label="Actualizar Playlist")
			btn_vaciar.Bind(wx.EVT_BUTTON, lambda evt: self.vaciar_playlist_seleccionada())
			btn_actualizar.Bind(wx.EVT_BUTTON, lambda evt: self.actualizar_playlist_seleccionada())
			btn_frame.Add(btn_vaciar, 0, wx.RIGHT, 5)
			btn_frame.Add(btn_actualizar, 0, wx.LEFT, 5)
			sizer.Add(btn_frame, 0, wx.ALL, 5)

		self.frame_option.Layout()

	def crear_playlist_y_agregar_songs(self):
		name = self.new_playlist_entry.GetValue().strip()
		if not name:
			wx.MessageBox("Ingresa un nombre para la playlist.", "Info", wx.OK | wx.ICON_INFORMATION)
			return
		playlist = self.sp.user_playlist_create(self.user_id, name, public=True, description="Playlist generada automáticamente")
		pid = playlist["id"]
		ids = [s["id"] for s in self.songs]
		for i in range(0, len(ids), 100):
			self.sp.playlist_add_items(pid, ids[i:i+100])
			time.sleep(0.5)
		wx.MessageBox("Playlist creada y canciones agregadas.", "Info", wx.OK | wx.ICON_INFORMATION)

	def filtrar_playlists(self, evt):
		term = self.entry_search.GetValue().strip().lower()
		self.playlist_listbox.Clear()
		for pl in self.playlists:
			if term in pl["name"].lower():
				self.playlist_listbox.Append(pl["name"])

	def vaciar_playlist_seleccionada(self):
		idx = self.playlist_listbox.GetSelection()
		if idx == wx.NOT_FOUND:
			wx.MessageBox("Selecciona una playlist primero.", "Info", wx.OK | wx.ICON_INFORMATION)
			return
		pl = self.playlists[idx]
		if wx.MessageBox(f"Vaciar playlist “{pl['name']}”?", "Confirmar", wx.YES_NO | wx.ICON_QUESTION) != wx.YES:
			return
		self.sp.playlist_replace_items(pl["id"], [])
		wx.MessageBox("Playlist vaciada correctamente.", "Info", wx.OK | wx.ICON_INFORMATION)

	def actualizar_playlist_seleccionada(self):
		sel = self.playlist_listbox.GetSelection()
		if sel == wx.NOT_FOUND:
			wx.MessageBox("Selecciona una playlist primero.", "Info", wx.OK | wx.ICON_INFORMATION)
			return

		pl = self.playlists[sel]
		existentes = self.obtener_canciones_playlist(pl["id"])
		pendientes = [s["id"] for s in self.songs if s["id"] not in existentes]
		if not pendientes:
			wx.MessageBox("No hay canciones nuevas.", "Info", wx.OK | wx.ICON_INFORMATION)
			return

		try:
			for i in range(0, len(pendientes), 100):
				self.sp.playlist_add_items(pl["id"], pendientes[i:i+100])
				time.sleep(0.5)
			wx.MessageBox("Playlist actualizada.", "Éxito", wx.OK | wx.ICON_INFORMATION)
		except Exception as e:
			wx.MessageBox(f"No se pudo actualizar: {e}", "Error", wx.OK | wx.ICON_ERROR)

	def obtener_todas_playlists(self):
		pls, offset = [], 0
		while True:
			res = self.sp.current_user_playlists(limit=50, offset=offset)
			for it in res["items"]:
				pls.append({"id": it["id"], "name": it["name"], "tracks": it["tracks"]["total"]})
			if not res.get("next"):
				break
			offset += 50
		return pls

	def obtener_canciones_playlist(self, playlist_id: str):
		ids, offset = set(), 0
		while True:
			res = self.sp.playlist_tracks(playlist_id, limit=100, offset=offset)
			for t in res["items"]:
				if t.get("track") and t["track"].get("id"):
					ids.add(t["track"]["id"])
			if not res.get("next"):
				break
			offset += 100
		return ids

	def abrir_ventana_vaciar_playlists(self):
		# Aquí haría lo mismo que en ventana_vaciar_playlists global.
		pass

	def reset_to_artist_search(self):
		self.frame_playlist.Hide()
		self.frame_artist.Show()
		self.songs.clear()
		self.artist_id = None
		self.entry_artist.SetValue("")
		self.listbox_artists.Clear()
		self.panel.Layout()