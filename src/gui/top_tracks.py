import wx
from spotipy import Spotify

class VentanaTopTracks(wx.Frame):
	"""
	Ventana para buscar top tracks de un artista, aplicar filtros avanzados y crear playlist personalizada,
	cumpliendo con criterios de accesibilidad.
	"""
	def __init__(self, parent: wx.Window, sp: Spotify):
		super().__init__(parent, title="Top Tracks Mejorado", size=(480, 620))
		self.sp = sp
		self.uris = []

		panel = wx.Panel(self)
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer(main_sizer)

		# Artista
		main_sizer.Add(wx.StaticText(panel, label="Artista:"), 0, wx.TOP | wx.LEFT, 10)
		self.e_art = wx.TextCtrl(panel, size=(340, 44), name="Artista")
		main_sizer.Add(self.e_art, 0, wx.ALL, 5)

		# Cuántos tracks
		main_sizer.Add(wx.StaticText(panel, label="Cuántos tracks (1–50):"), 0, wx.TOP | wx.LEFT, 5)
		self.e_num = wx.TextCtrl(panel, value="10", size=(60, 44), name="Cantidad de tracks")
		main_sizer.Add(self.e_num, 0, wx.ALL, 5)

		# Popularidad mínima
		main_sizer.Add(wx.StaticText(panel, label="Popularidad mínima (0–100):"), 0, wx.TOP | wx.LEFT, 5)
		self.e_pop = wx.TextCtrl(panel, value="0", size=(60, 44), name="Popularidad mínima")
		main_sizer.Add(self.e_pop, 0, wx.ALL, 5)

		# Colaboraciones
		main_sizer.Add(wx.StaticText(panel, label="Colaboraciones:"), 0, wx.TOP | wx.LEFT, 5)
		self.coll_var = wx.RadioBox(panel, choices=["Todas", "Solo artista", "Solo colaboraciones"], style=wx.RA_SPECIFY_ROWS, name="Colaboraciones")
		self.coll_var.SetSelection(0)
		main_sizer.Add(self.coll_var, 0, wx.ALL, 5)

		# Géneros secundarios
		main_sizer.Add(wx.StaticText(panel, label="Géneros secundarios (sep. coma):"), 0, wx.TOP | wx.LEFT, 5)
		self.e_gen = wx.TextCtrl(panel, size=(340, 44), name="Géneros secundarios")
		main_sizer.Add(self.e_gen, 0, wx.ALL, 5)

		# Ordenar por
		main_sizer.Add(wx.StaticText(panel, label="Ordenar por:"), 0, wx.TOP | wx.LEFT, 5)
		self.order_var = wx.Choice(panel, choices=["Popularidad", "Nombre", "Fecha"], name="Ordenar por")
		self.order_var.SetSelection(0)
		main_sizer.Add(self.order_var, 0, wx.ALL, 5)

		# Área de resultados accesible
		main_sizer.Add(wx.StaticText(panel, label="Resultados:"), 0, wx.TOP | wx.LEFT, 10)
		self.text_area = wx.TextCtrl(
			panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP, name="Resultados"
		)
		self.text_area.SetMinSize((420, 180))
		main_sizer.Add(self.text_area, 1, wx.ALL | wx.EXPAND, 10)

		# Barra de estado
		self.status = wx.StaticText(panel, label="Listo")
		self.status.SetMinSize((220, 32))
		main_sizer.Add(self.status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		# Botones
		btns = wx.BoxSizer(wx.HORIZONTAL)
		btn_buscar = wx.Button(panel, label="&Buscar")
		btn_buscar.Bind(wx.EVT_BUTTON, self.buscar_y_mostrar)
		btn_buscar.SetMinSize((150, 44))
		btns.Add(btn_buscar, 0, wx.ALL, 6)

		btn_crear = wx.Button(panel, label="&Crear Playlist")
		btn_crear.Bind(wx.EVT_BUTTON, self.crear_playlist_top)
		btn_crear.SetMinSize((150, 44))
		btns.Add(btn_crear, 0, wx.ALL, 6)

		btn_cancelar = wx.Button(panel, label="&Cancelar")
		btn_cancelar.Bind(wx.EVT_BUTTON, lambda evt: self.Close())
		btn_cancelar.SetMinSize((120, 44))
		btns.Add(btn_cancelar, 0, wx.ALL, 6)

		main_sizer.Add(btns, 0, wx.ALIGN_CENTER)

		panel.Layout()
		self.Centre()
		self.Show()

		# Foco inicial y accesibilidad: campo artista
		self.e_art.SetFocus()

		# Escape para cerrar
		panel.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)

	def on_key_down(self, evt):
		if evt.GetKeyCode() == wx.WXK_ESCAPE:
			self.Close()
		else:
			evt.Skip()

	def buscar_y_mostrar(self, _evt):
		self.text_area.SetValue("")
		self.status.SetLabel("Buscando…")
		nombre = self.e_art.GetValue().strip()
		if not nombre:
			wx.MessageBox("Pon el nombre del artista.", "Atención", wx.OK | wx.ICON_WARNING)
			self.status.SetLabel("Falta el nombre del artista")
			return

		try:
			arts = self.sp.search(q=nombre, type="artist", limit=1)["artists"]["items"]
			if not arts:
				wx.MessageBox("Artista no encontrado.", "Info", wx.OK | wx.ICON_INFORMATION)
				self.status.SetLabel("Artista no encontrado")
				return
			art = arts[0]
		except Exception as e:
			wx.MessageBox(f"No pude buscar artista:\n{e}", "Error", wx.OK | wx.ICON_ERROR)
			self.status.SetLabel("Error al buscar artista")
			return

		album_ids = set(); offset = 0
		while True:
			resp = self.sp.artist_albums(
				art["id"],
				album_type="album,single,compilation,appears_on",
				limit=50, offset=offset, country="US"
			)["items"]
			if not resp: break
			album_ids.update(alb["id"] for alb in resp)
			offset += len(resp)

		raw_tracks = []
		for alb_id in album_ids:
			off2 = 0
			while True:
				items = self.sp.album_tracks(alb_id, limit=50, offset=off2)["items"]
				if not items: break
				raw_tracks.extend(items)
				off2 += len(items)

		if not raw_tracks:
			wx.MessageBox("No hay pistas disponibles.", "Info", wx.OK | wx.ICON_INFORMATION)
			self.status.SetLabel("No hay pistas")
			return

		seen = set(); uniq = []
		for t in raw_tracks:
			if t["id"] and t["id"] not in seen:
				seen.add(t["id"]); uniq.append(t)
		for i in range(0, len(uniq), 50):
			batch = uniq[i:i+50]; ids = [t["id"] for t in batch]
			details = self.sp.tracks(ids)["tracks"]
			for det, orig in zip(details, batch):
				orig["popularity"] = det.get("popularity",0)
				orig["album"] = det.get("album",{})

		try: n = max(1, min(int(self.e_num.GetValue()), 50))
		except: n = 10
		try: min_pop = max(0, min(int(self.e_pop.GetValue()), 100))
		except: min_pop = 0
		coll_opt_idx = self.coll_var.GetSelection()
		coll_opt = ["Todas", "Solo", "Colab"][coll_opt_idx]
		secs = [g.strip().lower() for g in self.e_gen.GetValue().split(",") if g.strip()]

		artist_ids = {a["id"] for t in uniq for a in t["artists"]}
		genres = {}
		for i in range(0, len(artist_ids), 50):
			batch = list(artist_ids)[i:i+50]
			for aobj in self.sp.artists(batch)["artists"]:
				genres[aobj["id"]] = [g.lower() for g in aobj.get("genres",[])]

		filt = []
		for t in uniq:
			if t["popularity"] < min_pop: continue
			if coll_opt == "Solo" and len(t["artists"]) > 1: continue
			if coll_opt == "Colab" and len(t["artists"]) < 2: continue
			if secs and not any(any(s in g for g in genres.get(a["id"],[])) for s in secs for a in t["artists"]):
				continue
			filt.append(t)

		keymap = {
			"Popularidad": lambda x: x["popularity"],
			"Nombre": lambda x: x["name"].lower(),
			"Fecha": lambda x: x["album"].get("release_date", "")
		}
		sel_order = self.order_var.GetStringSelection()
		rev = sel_order in ["Popularidad", "Fecha"]
		filt.sort(key=keymap[sel_order], reverse=rev)
		resultados = filt[:n]
		self.uris = [t["uri"] for t in resultados]

		self.text_area.SetValue(f"Mostrando {len(resultados)} de {art['name']}:\n\n")
		for i, t in enumerate(resultados, 1):
			artistas = ", ".join(a["name"] for a in t["artists"])
			self.text_area.AppendText(f"{i}. {t['name']} — {artistas} (pop {t['popularity']})\n")
		self.status.SetLabel(f"Mostrando {len(resultados)} resultados")

	def crear_playlist_top(self, _evt):
		uris = self.uris
		if not uris:
			wx.MessageBox("Primero busca las canciones.", "Info", wx.OK | wx.ICON_INFORMATION)
			return
		dlg = wx.TextEntryDialog(self, "Nombre para la playlist:", "Playlist")
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		pl_name = dlg.GetValue().strip()
		dlg.Destroy()
		if not pl_name:
			return
		try:
			uid = self.sp.current_user()["id"]
			pl = self.sp.user_playlist_create(uid, pl_name, public=True)
			self.sp.playlist_add_items(pl["id"], uris)
			wx.MessageBox("Playlist creada.", "¡Listo!", wx.OK | wx.ICON_INFORMATION)
			self.Destroy()
		except Exception as e:
			wx.MessageBox(f"No pude crear la playlist:\n{e}", "Error", wx.OK | wx.ICON_ERROR)

def ventana_top_tracks(sp: Spotify, parent: wx.Window):
	"""
	Lanza la ventana Top Tracks Mejorado accesible.
	"""
	VentanaTopTracks(parent, sp)