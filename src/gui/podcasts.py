import wx
from spotipy import Spotify
from ..utils.spotify_utils import (
	get_podcast_episodes,
	get_playlist_items,
	add_episodes_to_playlist,
)

data_podcasts = [
	{"podcast": "0u8dE1kc9CkFn8bONEq0hE", "playlist": "1MreMp1Qm4gyKZa5B2HZun"},
	# ... completa con tu lista original ...
]

class VentanaSincronizarPodcastsData(wx.Frame):
	"""
	Ventana accesible para sincronizar podcasts y playlists.
	Incluye controles accesibles, botón cancelar, foco y navegación por teclado.
	"""
	def __init__(self, parent: wx.Window, sp: Spotify):
		super().__init__(parent, title="Sincronizar Podcasts (data_podcasts)", size=(560, 340))
		self.sp = sp

		panel = wx.Panel(self)
		sizer = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer(sizer)

		# Etiqueta de estado general
		label = wx.StaticText(panel, label="Sincronizando podcasts con sus playlists…")
		label.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		sizer.Add(label, 0, wx.TOP | wx.LEFT | wx.RIGHT, 8)

		# Barra de progreso accesible
		self.prog = wx.Gauge(panel, range=max(1, len(data_podcasts)), style=wx.GA_HORIZONTAL)
		self.prog.SetMinSize((480, 32))
		sizer.Add(self.prog, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

		# Etiqueta de estado de elemento actual
		self.lbl_estado = wx.StaticText(panel, label="Esperando…")
		sizer.Add(self.lbl_estado, 0, wx.ALL | wx.EXPAND, 6)

		# Área de log accesible
		self.txt_log = wx.TextCtrl(
			panel,
			style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
			size=(520, 120),
			name="Log de sincronización de podcasts"
		)
		self.txt_log.SetMinSize((520, 100))
		sizer.Add(self.txt_log, 1, wx.ALL | wx.EXPAND, 10)

		# Sizer horizontal para botones
		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

		# Botón iniciar sincronización (accesible)
		self.btn_iniciar = wx.Button(panel, label="&Iniciar sincronización")
		self.btn_iniciar.Bind(wx.EVT_BUTTON, self.sincronizar)
		self.btn_iniciar.SetMinSize((200, 44))
		btn_sizer.Add(self.btn_iniciar, 0, wx.ALL, 6)

		# Botón cancelar (accesible, con atajo)
		btn_cancelar = wx.Button(panel, label="&Cancelar")
		btn_cancelar.Bind(wx.EVT_BUTTON, lambda evt: self.Close())
		btn_cancelar.SetMinSize((120, 44))
		btn_sizer.Add(btn_cancelar, 0, wx.ALL, 6)

		sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 8)

		panel.Layout()
		self.Centre()
		self.Show()

		# Accesibilidad extra: Foco inicial en botón de inicio
		self.btn_iniciar.SetFocus()

		# Escape cierra la ventana (accesibilidad)
		self.Bind(wx.EVT_CHAR_HOOK, self._on_key)

	def _on_key(self, event):
		if event.GetKeyCode() == wx.WXK_ESCAPE:
			self.Close()
		else:
			event.Skip()

	def log(self, msg: str):
		"""
		Agrega una línea al área de log y asegura el scroll automático.
		"""
		self.txt_log.AppendText(msg + "\n")
		self.txt_log.ShowPosition(self.txt_log.GetLastPosition())
		wx.YieldIfNeeded()

	def sincronizar(self, _evt):
		"""
		Sincroniza episodios de podcasts con playlists, mostrando progreso y mensajes.
		Desactiva botones durante la operación.
		"""
		self.btn_iniciar.Disable()
		total = len(data_podcasts)
		self.prog.SetValue(0)

		for idx, pair in enumerate(data_podcasts, start=1):
			pod_id, pl_id = pair["podcast"], pair["playlist"]
			try:
				podcast_name = self.sp.show(pod_id, market="US")["name"]
			except Exception:
				podcast_name = f"Podcast {pod_id[:8]}…"
			try:
				playlist_name = self.sp.playlist(pl_id, fields="name")["name"]
			except Exception:
				playlist_name = f"Playlist {pl_id[:8]}…"

			self.lbl_estado.SetLabel(f"{idx}/{total}  {podcast_name} → {playlist_name}")
			wx.YieldIfNeeded()

			eps = get_podcast_episodes(self.sp, pod_id)
			if not eps:
				self.log(f"❌ {podcast_name}: sin episodios o error.")
				self.prog.SetValue(idx)
				continue

			antes = set(get_playlist_items(self.sp, pl_id))
			try:
				add_episodes_to_playlist(self.sp, pl_id, eps)
			except Exception as e:
				self.log(f"❌ Error al agregar episodios en {podcast_name}: {e}")
				self.prog.SetValue(idx)
				continue
			despues = set(get_playlist_items(self.sp, pl_id))
			nuevos = len(despues) - len(antes)
			if nuevos:
				self.log(f"✅ {podcast_name}: {nuevos} nuevos → {playlist_name}")
			else:
				self.log(f"• {podcast_name}: 0 nuevos")
			self.prog.SetValue(idx)

		self.lbl_estado.SetLabel("¡Sincronización completa!")
		wx.MessageBox("Todos los podcasts han sido sincronizados.", "Terminado", wx.OK | wx.ICON_INFORMATION)
		self.btn_iniciar.Enable()

def ventana_sincronizar_podcasts_data(sp: Spotify, parent: wx.Window):
	"""
	Invoca la ventana de sincronización accesible.
	"""
	VentanaSincronizarPodcastsData(parent, sp)