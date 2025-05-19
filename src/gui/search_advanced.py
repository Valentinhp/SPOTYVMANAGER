import wx
import threading, queue, time, difflib, re
from spotipy import Spotify

class VentanaBusquedaAvanzada(wx.Frame):
	"""
	Ventana de búsqueda avanzada accesible: busca por frase/tema, filtra y crea una playlist personalizada.
	"""
	def __init__(self, parent: wx.Window, sp: Spotify):
		super().__init__(parent, title="Buscar / Recomendar y Crear Playlist", size=(720, 680))
		self.sp = sp
		self.uris = []

		panel = wx.Panel(self)
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer(main_sizer)

		# Modo de búsqueda
		radio_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.modo = wx.RadioBox(panel, label="Modo de búsqueda", choices=["Por frase", "Por tema/emoción"], majorDimension=2, style=wx.RA_SPECIFY_ROWS)
		self.modo.SetSelection(0)
		radio_sizer.Add(self.modo, 1, wx.ALL, 10)
		main_sizer.Add(radio_sizer, 0, wx.EXPAND)

		# Frase o tema y parámetros
		grid = wx.FlexGridSizer(4, 2, 8, 12)
		grid.AddGrowableCol(1)
		grid.Add(wx.StaticText(panel, label="Frase/tema (puedes incluir 'género ...'):"), 0, wx.ALIGN_CENTER_VERTICAL)
		self.entry_texto = wx.TextCtrl(panel, name="Frase o tema")
		self.entry_texto.SetMinSize((320, 44))
		grid.Add(self.entry_texto, 1, wx.EXPAND)

		grid.Add(wx.StaticText(panel, label="Géneros (opcional, sep. por coma):"), 0, wx.ALIGN_CENTER_VERTICAL)
		self.entry_genres = wx.TextCtrl(panel, name="Géneros")
		self.entry_genres.SetMinSize((320, 44))
		grid.Add(self.entry_genres, 1, wx.EXPAND)

		grid.Add(wx.StaticText(panel, label="Máx pistas (1–50):"), 0, wx.ALIGN_CENTER_VERTICAL)
		self.entry_limit = wx.TextCtrl(panel, value="15", size=(60, 44), name="Máximo de pistas")
		grid.Add(self.entry_limit, 0)

		grid.Add(wx.StaticText(panel, label="Pop mín (0–100):"), 0, wx.ALIGN_CENTER_VERTICAL)
		self.entry_pop = wx.TextCtrl(panel, value="0", size=(60, 44), name="Popularidad mínima")
		grid.Add(self.entry_pop, 0)

		main_sizer.Add(grid, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

		# Resultados
		txt_box = wx.BoxSizer(wx.VERTICAL)
		txt_box.Add(wx.StaticText(panel, label="Resultados:"), 0, wx.LEFT, 10)
		self.text_area = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP | wx.HSCROLL, name="Resultados")
		self.text_area.SetMinSize((640, 220))
		txt_box.Add(self.text_area, 1, wx.ALL | wx.EXPAND, 10)
		main_sizer.Add(txt_box, 1, wx.EXPAND)

		# Nombre de la nueva playlist
		grid2 = wx.FlexGridSizer(1, 2, 8, 12)
		grid2.Add(wx.StaticText(panel, label="Nombre de la nueva playlist:"), 0, wx.ALIGN_CENTER_VERTICAL)
		self.entry_playlist = wx.TextCtrl(panel, value="Mi playlist", name="Nombre de la playlist")
		self.entry_playlist.SetMinSize((240, 44))
		grid2.Add(self.entry_playlist, 1, wx.EXPAND)
		main_sizer.Add(grid2, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

		# Barra de estado accesible
		self.status = wx.StaticText(panel, label="Listo – escribe tu frase y pulsa Enter")
		self.status.SetMinSize((300, 32))
		main_sizer.Add(self.status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

		# Botones con accesibilidad
		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		btn_buscar = wx.Button(panel, label="&Buscar/Recomendar")
		btn_buscar.Bind(wx.EVT_BUTTON, self.lanzar_busqueda)
		btn_buscar.SetMinSize((180, 44))
		btn_sizer.Add(btn_buscar, 0, wx.ALL, 8)
		btn_crear = wx.Button(panel, label="&Crear Playlist")
		btn_crear.Bind(wx.EVT_BUTTON, self.crear_playlist_advanced)
		btn_crear.SetMinSize((180, 44))
		btn_sizer.Add(btn_crear, 0, wx.ALL, 8)
		btn_cancelar = wx.Button(panel, label="&Cancelar")
		btn_cancelar.Bind(wx.EVT_BUTTON, lambda evt: self.Close())
		btn_cancelar.SetMinSize((120, 44))
		btn_sizer.Add(btn_cancelar, 0, wx.ALL, 8)
		main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)

		panel.Layout()
		self.Centre()
		self.Show()

		# Foco inicial en el campo de texto
		self.entry_texto.SetFocus()

		# Bind para Enter y Escape
		panel.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)

		# Seeds y caché de géneros
		try:
			self.seeds_spotify = self.sp.recommendation_genre_seeds()
		except Exception:
			self.seeds_spotify = []
		self.artist_genres_cache = {}

		self.cola = queue.Queue()

	def on_key_down(self, evt):
		if evt.GetKeyCode() == wx.WXK_RETURN:
			self.lanzar_busqueda(None)
		elif evt.GetKeyCode() == wx.WXK_ESCAPE:
			self.Close()
		else:
			evt.Skip()

	def call_safe(self, fn, *a, **k):
		for i in range(3):
			try:
				return fn(*a, **k)
			except Exception as e:
				if "429" in str(e) or "rate" in str(e).lower():
					time.sleep(1.5 * (i+1))
				else:
					raise
		raise RuntimeError("Rate-limit continuo en Spotify")

	def _worker(self, params):
		texto_raw, generos_usr, seeds, lim, pop_min, texto_busq, use_pop, use_gen = params
		pistas = []
		if use_gen and seeds:
			try:
				pistas = self.call_safe(self.sp.recommendations, seed_genres=seeds, limit=lim)["tracks"]
			except Exception:
				pistas = []
		if len(pistas) < lim:
			try:
				extra = self.call_safe(self.sp.search, q=texto_busq or texto_raw, type="track", limit=lim*2)["tracks"]["items"]
				pistas.extend(extra)
			except Exception:
				pass
		vistos, únicos = set(), []
		for p in pistas:
			if p["id"] not in vistos:
				vistos.add(p["id"]); únicos.append(p)
		pistas = únicos
		if use_gen and generos_usr:
			faltantes = [i for p in pistas for i in [a["id"] for a in p["artists"]] if i not in self.artist_genres_cache]
			for lote in (faltantes[i:i+50] for i in range(0, len(faltantes), 50)):
				try:
					arts = self.call_safe(self.sp.artists, lote)["artists"]
					for aobj in arts:
						self.artist_genres_cache[aobj["id"]] = aobj.get("genres", [])
				except Exception:
					for aid in lote:
						self.artist_genres_cache[aid] = []
			pistas = [p for p in pistas if any(any(g in gen.lower() for gen in self.artist_genres_cache.get(a["id"], [])) for g in generos_usr for a in p["artists"])]
		if use_pop:
			pistas = [p for p in pistas if p.get("popularity",0) >= pop_min]
		self.cola.put(pistas[:lim])

	def lanzar_busqueda(self, evt):
		texto_raw = self.entry_texto.GetValue().strip()
		if not texto_raw:
			wx.MessageBox("Escribe algo para buscar.", "Aviso", wx.OK | wx.ICON_INFORMATION)
			return
		generos_usr = [g.strip().lower() for g in self.entry_genres.GetValue().split(",") if g.strip()]
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
			match = difflib.get_close_matches(g, self.seeds_spotify, n=1, cutoff=0.4)
			if match:
				seeds.append(match[0])
		seeds = seeds[:5]
		try:
			lim = max(1, min(int(self.entry_limit.GetValue()), 50))
			pop_min = max(0, min(int(self.entry_pop.GetValue()), 100))
		except Exception:
			wx.MessageBox("Introduce valores válidos para límites.", "Aviso", wx.OK | wx.ICON_WARNING)
			return

		estrategias = [(True,True),(False,True),(True,False),(False,False)]
		self.status.SetLabel("Buscando…")
		self.text_area.SetValue("")

		def probar(idx=0):
			if idx >= len(estrategias):
				self.cola.put([]); return
			use_pop, use_gen = estrategias[idx]
			threading.Thread(target=self._worker, args=((texto_raw, generos_usr, seeds, lim, pop_min, texto_busq, use_pop, use_gen),), daemon=True).start()
			def check():
				if self.cola.empty():
					wx.CallLater(100, check)
				else:
					pistas = self.cola.get()
					if pistas or idx == len(estrategias)-1:
						self.mostrar(pistas)
					else:
						probar(idx+1)
			check()

		probar()

	def mostrar(self, pistas):
		if pistas:
			self.status.SetLabel(f"Listo – {len(pistas)} pistas")
		else:
			self.status.SetLabel("Sin resultados")
		self.uris = [p["uri"] for p in pistas]
		self.text_area.SetValue("")
		if not pistas:
			self.text_area.AppendText("No se encontraron pistas.\n")
		else:
			for i, p in enumerate(pistas, 1):
				artistas = ", ".join(a["name"] for a in p["artists"])
				self.text_area.AppendText(f"{i:2d}. {p['name']} — {artistas} (pop {p.get('popularity',0)})\n")

	def crear_playlist_advanced(self, evt):
		nombre = self.entry_playlist.GetValue().strip() or "Mi playlist"
		uris = self.uris
		if not uris:
			wx.MessageBox("No hay canciones para agregar.", "Info", wx.OK | wx.ICON_INFORMATION)
			return

		try:
			uid = self.sp.current_user()["id"]
			pl = self.sp.user_playlist_create(uid, nombre, public=True)
			self.sp.playlist_add_items(pl["id"], uris)
			wx.MessageBox(f"Playlist '{nombre}' creada con {len(uris)} canciones.", "¡Listo!", wx.OK | wx.ICON_INFORMATION)
		except Exception as e:
			wx.MessageBox(f"No se pudo crear la playlist:\n{e}", "Error", wx.OK | wx.ICON_ERROR)

def ventana_busqueda_avanzada(sp: Spotify, parent: wx.Window):
	"""
	Lanza la ventana de búsqueda avanzada accesible.
	"""
	VentanaBusquedaAvanzada(parent, sp)