# src/gui/playlists.py
"""
Ventanas relacionadas con Playlists en wxPython, versión accesible:
* Ver playlists
* Crear playlist
* Contenido de playlist
* Agregar artista/podcast a playlist
* Eliminar playlists (con CheckListBox)
* Vaciar playlists
"""

import wx
from spotipy import Spotify
from ..utils.spotify_utils import (
	obtener_playlists_usuario,
	crear_playlist,
	obtener_contenido_playlist,
	eliminar_items_playlist,
	obtener_canciones_artista,
	obtener_episodios_podcast_sencillo,
	agregar_canciones_a_playlist,
)

def ventana_ver_playlists(sp: Spotify, parent: wx.Window):
	ven = wx.Frame(parent, title="Ver Playlists", size=(600, 400))
	panel = wx.Panel(ven)
	sizer = wx.BoxSizer(wx.VERTICAL)
	panel.SetSizer(sizer)

	cols = ("ID", "Nombre", "Tracks")
	tree = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
	for i, c in enumerate(cols):
		tree.InsertColumn(i, c)
	tree.SetMinSize((580, 300))
	tree.SetName("Tabla de playlists")
	sizer.Add(tree, 1, wx.ALL | wx.EXPAND, 10)

	for pid, nom, tot in obtener_playlists_usuario(sp):
		idx = tree.InsertItem(tree.GetItemCount(), pid)
		tree.SetItem(idx, 1, nom)
		tree.SetItem(idx, 2, str(tot))

	btn_cancelar = wx.Button(panel, label="&Cancelar")
	btn_cancelar.Bind(wx.EVT_BUTTON, lambda evt: ven.Destroy())
	btn_cancelar.SetMinSize((110, 44))
	sizer.Add(btn_cancelar, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

	ven.Centre()
	ven.Show()

def ventana_crear_playlist(sp: Spotify, parent: wx.Window):
	ven = wx.Frame(parent, title="Crear Playlist", size=(340, 180))
	panel = wx.Panel(ven)
	sizer = wx.BoxSizer(wx.VERTICAL)
	panel.SetSizer(sizer)

	label = wx.StaticText(panel, label="Nombre de la Playlist:")
	sizer.Add(label, 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)

	entry = wx.TextCtrl(panel, size=(220, 44))
	sizer.Add(entry, 0, wx.ALL, 5)

	def crear(evt):
		nombre = entry.GetValue().strip()
		if not nombre:
			wx.MessageBox("Ingresa un nombre", "Atención", wx.OK | wx.ICON_WARNING)
			return
		pid = crear_playlist(sp, nombre)
		wx.MessageBox(f"Playlist creada con ID: {pid}", "Completado", wx.OK | wx.ICON_INFORMATION)
		ven.Destroy()

	btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
	btn_crear = wx.Button(panel, label="&Crear")
	btn_crear.Bind(wx.EVT_BUTTON, crear)
	btn_crear.SetMinSize((110, 44))
	btn_sizer.Add(btn_crear, 0, wx.ALL, 5)

	btn_cancelar = wx.Button(panel, label="&Cancelar")
	btn_cancelar.Bind(wx.EVT_BUTTON, lambda evt: ven.Destroy())
	btn_cancelar.SetMinSize((110, 44))
	btn_sizer.Add(btn_cancelar, 0, wx.ALL, 5)

	sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 8)

	ven.Centre()
	ven.Show()

def ventana_contenido_playlist(sp: Spotify, parent: wx.Window):
	ven = wx.Frame(parent, title="Contenido de Playlist", size=(680, 480))
	panel = wx.Panel(ven)
	sizer = wx.BoxSizer(wx.VERTICAL)
	panel.SetSizer(sizer)

	label = wx.StaticText(panel, label="ID de la playlist:")
	sizer.Add(label, 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)

	entry_pid = wx.TextCtrl(panel, size=(320, 44))
	sizer.Add(entry_pid, 0, wx.ALL, 5)

	cols = ("TrackID", "Título", "Artista/Show")
	tree = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
	for i, c in enumerate(cols):
		tree.InsertColumn(i, c)
	tree.SetMinSize((610, 260))
	tree.SetName("Contenido de playlist")
	sizer.Add(tree, 1, wx.ALL | wx.EXPAND, 10)

	def cargar(evt=None):
		tree.DeleteAllItems()
		pid = entry_pid.GetValue().strip()
		if not pid:
			wx.MessageBox("Debes ingresar el ID de la playlist.", "Atención", wx.OK | wx.ICON_WARNING)
			return
		for tid, nom, art in obtener_contenido_playlist(sp, pid):
			idx = tree.InsertItem(tree.GetItemCount(), tid)
			tree.SetItem(idx, 1, nom)
			tree.SetItem(idx, 2, art)

	def eliminar_sel(evt=None):
		pid = entry_pid.GetValue().strip()
		if not pid:
			wx.MessageBox("Ingresa el ID primero.", "Atención", wx.OK | wx.ICON_WARNING)
			return
		idx = tree.GetFirstSelected()
		if idx == -1:
			wx.MessageBox("No seleccionaste nada.", "Atención", wx.OK | wx.ICON_WARNING)
			return
		confirm = wx.MessageBox("¿Seguro que quieres eliminar el/los ítem(s) seleccionados?", "Confirmar eliminación", wx.YES_NO | wx.ICON_QUESTION)
		if confirm != wx.YES:
			return
		uris = []
		while idx != -1:
			tid = tree.GetItemText(idx)
			uris.append(f"spotify:track:{tid}")
			uris.append(f"spotify:episode:{tid}")
			idx = tree.GetNextSelected(idx)
		eliminar_items_playlist(sp, pid, uris)
		cargar()
		wx.MessageBox("Ítems eliminados correctamente.", "Eliminado", wx.OK | wx.ICON_INFORMATION)

	btnsizer = wx.BoxSizer(wx.HORIZONTAL)
	btn_cargar = wx.Button(panel, label="&Cargar Contenido")
	btn_cargar.Bind(wx.EVT_BUTTON, cargar)
	btn_cargar.SetMinSize((180, 44))
	btnsizer.Add(btn_cargar, 0, wx.RIGHT, 10)

	btn_eliminar = wx.Button(panel, label="&Eliminar Seleccionados")
	btn_eliminar.Bind(wx.EVT_BUTTON, eliminar_sel)
	btn_eliminar.SetMinSize((180, 44))
	btnsizer.Add(btn_eliminar, 0, wx.LEFT, 10)

	btn_cancelar = wx.Button(panel, label="&Cancelar")
	btn_cancelar.Bind(wx.EVT_BUTTON, lambda evt: ven.Destroy())
	btn_cancelar.SetMinSize((110, 44))
	btnsizer.Add(btn_cancelar, 0, wx.LEFT, 10)

	sizer.Add(btnsizer, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

	ven.Centre()
	ven.Show()

def ventana_agregar_artista_podcast(sp: Spotify, parent: wx.Window):
	ven = wx.Frame(parent, title="Agregar Artista o Podcast a Playlist", size=(500, 320))
	panel = wx.Panel(ven)
	sizer = wx.BoxSizer(wx.VERTICAL)
	panel.SetSizer(sizer)

	sizer.Add(wx.StaticText(panel, label="ID de la Playlist destino:"), 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)
	entry_pl = wx.TextCtrl(panel, size=(320, 44))
	sizer.Add(entry_pl, 0, wx.ALL, 5)

	sizer.Add(wx.StaticText(panel, label="ID de Artista (opcional):"), 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)
	entry_art = wx.TextCtrl(panel, size=(320, 44))
	sizer.Add(entry_art, 0, wx.ALL, 5)

	sizer.Add(wx.StaticText(panel, label="ID de Podcast (opcional):"), 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)
	entry_pod = wx.TextCtrl(panel, size=(320, 44))
	sizer.Add(entry_pod, 0, wx.ALL, 5)

	def agregar(evt):
		pid = entry_pl.GetValue().strip()
		if not pid:
			wx.MessageBox("Falta el ID de la Playlist.", "Atención", wx.OK | wx.ICON_WARNING)
			return
		aid = entry_art.GetValue().strip()
		podid = entry_pod.GetValue().strip()
		if aid:
			tracks = obtener_canciones_artista(sp, aid)
			if not tracks:
				wx.MessageBox("No hay tracks para ese artista.", "Info", wx.OK | wx.ICON_WARNING)
				return
			agregar_canciones_a_playlist(sp, pid, tracks)
			wx.MessageBox("Agregadas top tracks del artista.", "Éxito", wx.OK | wx.ICON_INFORMATION)
		elif podid:
			eps = obtener_episodios_podcast_sencillo(sp, podid)
			if not eps:
				wx.MessageBox("No se encontraron episodios.", "Info", wx.OK | wx.ICON_WARNING)
				return
			from ..utils.spotify_utils import add_episodes_to_playlist as _add_eps
			_add_eps(sp, pid, [f"spotify:episode:{e}" for e in eps])
			wx.MessageBox("Agregados episodios del podcast.", "Éxito", wx.OK | wx.ICON_INFORMATION)
		else:
			wx.MessageBox("No pusiste Artista ni Podcast.", "Atención", wx.OK | wx.ICON_INFORMATION)

	btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
	btn = wx.Button(panel, label="&Agregar")
	btn.Bind(wx.EVT_BUTTON, agregar)
	btn.SetMinSize((120, 44))
	btn_sizer.Add(btn, 0, wx.ALL, 5)

	btn_cancelar = wx.Button(panel, label="&Cancelar")
	btn_cancelar.Bind(wx.EVT_BUTTON, lambda evt: ven.Destroy())
	btn_cancelar.SetMinSize((120, 44))
	btn_sizer.Add(btn_cancelar, 0, wx.ALL, 5)

	sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 8)

	ven.Centre()
	ven.Show()

def ventana_eliminar_playlists(sp: Spotify, parent: wx.Window):
	ven = wx.Frame(parent, title="Eliminar Playlists", size=(440, 520))
	panel = wx.Panel(ven)
	sizer = wx.BoxSizer(wx.VERTICAL)
	panel.SetSizer(sizer)

	sizer.Add(wx.StaticText(panel, label="Buscar playlists:"), 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)
	entry_buscar = wx.TextCtrl(panel, size=(280, 44))
	sizer.Add(entry_buscar, 0, wx.ALL, 8)

	pls = list(obtener_playlists_usuario(sp))
	filtered_pls = list(pls)

	# Contenedor de checkboxes accesibles
	scroll = wx.ScrolledWindow(panel, style=wx.VSCROLL)
	scroll.SetScrollRate(0, 10)
	scroll_sizer = wx.BoxSizer(wx.VERTICAL)
	scroll.SetSizer(scroll_sizer)
	sizer.Add(scroll, 1, wx.ALL | wx.EXPAND, 10)

	checkboxes = []

	def crear_checkboxes():
		# Borra los checkboxes existentes antes de crear nuevos
		nonlocal checkboxes
		for chk in checkboxes:
			chk.Destroy()
		checkboxes.clear()
		for pid, nombre, _ in filtered_pls:
			chk = wx.CheckBox(scroll, label=f"{nombre}  ({pid[:8]}…)")
			chk.SetMinSize((390, 44))
			scroll_sizer.Add(chk, 0, wx.ALL | wx.EXPAND, 1)
			checkboxes.append(chk)
		scroll.Layout()
		scroll.FitInside()

	def refrescar():
		scroll_sizer.Clear(delete_windows=True)
		crear_checkboxes()

	def filtrar(evt):
		term = entry_buscar.GetValue().strip().lower()
		filtered_pls.clear()
		for item in pls:
			if term in item[1].lower():
				filtered_pls.append(item)
		refrescar()

	entry_buscar.Bind(wx.EVT_TEXT, filtrar)
	refrescar()

	def confirmar_elim(evt):
		seleccion = [filtered_pls[i] for i, chk in enumerate(checkboxes) if chk.IsChecked()]
		if not seleccion:
			wx.MessageBox("No seleccionaste ninguna playlist.", "Atención", wx.OK | wx.ICON_WARNING)
			return
		nombres = "\n".join(f"• {n}" for _, n, _ in seleccion)
		if wx.MessageBox(
			f"Vas a eliminar estas playlists:\n{nombres}\n\n¿Continuar?", "Confirmar eliminación",
			wx.YES_NO | wx.ICON_QUESTION
		) != wx.YES:
			return
		errores = []
		for pid, nombre, _ in seleccion:
			try:
				sp.current_user_unfollow_playlist(pid)
			except Exception as e:
				errores.append(f"{nombre}: {e}")
		if errores:
			wx.MessageBox("Algunas no se pudieron eliminar:\n" + "\n".join(errores), "Errores", wx.OK | wx.ICON_ERROR)
		else:
			wx.MessageBox("Las playlists seleccionadas han sido eliminadas.", "¡Listo!", wx.OK | wx.ICON_INFORMATION)
		ven.Destroy()

	btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
	btn = wx.Button(panel, label="&Eliminar seleccionadas")
	btn.Bind(wx.EVT_BUTTON, confirmar_elim)
	btn.SetMinSize((180, 44))
	btn_sizer.Add(btn, 0, wx.ALL, 5)

	btn_cancelar = wx.Button(panel, label="&Cancelar")
	btn_cancelar.Bind(wx.EVT_BUTTON, lambda evt: ven.Destroy())
	btn_cancelar.SetMinSize((120, 44))
	btn_sizer.Add(btn_cancelar, 0, wx.ALL, 5)

	sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 8)

	ven.Centre()
	ven.Show()

def ventana_vaciar_playlists(sp: Spotify, parent: wx.Window):
	ven = wx.Frame(parent, title="Vaciar Playlists", size=(440, 520))
	panel = wx.Panel(ven)
	sizer = wx.BoxSizer(wx.VERTICAL)
	panel.SetSizer(sizer)

	sizer.Add(wx.StaticText(panel, label="Buscar playlists:"), 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)
	entry_buscar = wx.TextCtrl(panel, size=(280, 44))
	sizer.Add(entry_buscar, 0, wx.ALL, 8)

	todas = list(obtener_playlists_usuario(sp))
	mostradas = list(todas)

	listbox = wx.CheckListBox(panel, choices=[f"{nombre}  ({pid[:8]}…)" for pid, nombre, _ in mostradas])
	listbox.SetMinSize((400, 320))
	sizer.Add(listbox, 1, wx.ALL | wx.EXPAND, 10)

	def refrescar():
		listbox.Clear()
		for pid, nombre, _ in mostradas:
			listbox.Append(f"{nombre}  ({pid[:8]}…)")

	def filtrar(evt):
		texto = entry_buscar.GetValue().strip().lower()
		mostradas.clear()
		for item in todas:
			if texto in item[1].lower():
				mostradas.append(item)
		refrescar()

	entry_buscar.Bind(wx.EVT_TEXT, filtrar)
	refrescar()

	def confirmar_vaciado(evt):
		idxs = [i for i, checked in enumerate(listbox.GetCheckedItems()) if checked]
		if not idxs:
			wx.MessageBox("No seleccionaste ninguna playlist.", "Atención", wx.OK | wx.ICON_WARNING)
			return
		seleccion = [mostradas[i] for i in idxs]
		nombres = "\n".join(f"• {n}" for _, n, _ in seleccion)
		if wx.MessageBox(
			f"Vas a vaciar estas playlists:\n{nombres}\n\n¿Continuar?", "Confirmar vaciado",
			wx.YES_NO | wx.ICON_QUESTION
		) != wx.YES:
			return
		errores = []
		for pid, nombre, _ in seleccion:
			try:
				sp.playlist_replace_items(pid, [])
			except Exception as e:
				errores.append(f"{nombre}: {e}")
		if errores:
			wx.MessageBox("Errores al vaciar:\n" + "\n".join(errores), "Errores", wx.OK | wx.ICON_ERROR)
		else:
			wx.MessageBox("Las playlists seleccionadas han quedado vacías.", "¡Hecho!", wx.OK | wx.ICON_INFORMATION)
		ven.Destroy()

	btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
	btn = wx.Button(panel, label="&Vaciar seleccionadas")
	btn.Bind(wx.EVT_BUTTON, confirmar_vaciado)
	btn.SetMinSize((180, 44))
	btn_sizer.Add(btn, 0, wx.ALL, 5)

	btn_cancelar = wx.Button(panel, label="&Cancelar")
	btn_cancelar.Bind(wx.EVT_BUTTON, lambda evt: ven.Destroy())
	btn_cancelar.SetMinSize((120, 44))
	btn_sizer.Add(btn_cancelar, 0, wx.ALL, 5)

	sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 8)

	ven.Centre()
	ven.Show()