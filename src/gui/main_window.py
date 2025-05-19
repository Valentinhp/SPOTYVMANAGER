import wx


from spotipy import Spotify
from .playlists import (
	ventana_vaciar_playlists,
	ventana_eliminar_playlists,
	ventana_ver_playlists,
	ventana_crear_playlist,
)
from .podcasts import ventana_sincronizar_podcasts_data
from .artist_manager import VentanaGestorAutomatico
from .artistapy import ventana_artistapy
from .search_advanced import ventana_busqueda_avanzada
from .top_tracks import ventana_top_tracks

class MainFrame(wx.Frame):
	def __init__(self, sp: Spotify):
		super().__init__(None, title="Gestor Spotify (Modular)", size=(840, 620))
		self.sp = sp
		self._build_menu_bar()
		self._build_ui()
		self.Centre()
		self.Show()

	def _build_menu_bar(self):
		menu_bar = wx.MenuBar()

		# --- PLAYLISTS ---
		menu_playlists = wx.Menu()
		menu_playlists.Append(wx.ID_ANY, "Vaciar Playlists\tCtrl+V", "Vacía todas las playlists")
		menu_playlists.Append(wx.ID_ANY, "Eliminar Playlists\tCtrl+E", "Elimina playlists seleccionadas")
		menu_playlists.Append(wx.ID_ANY, "Ver Playlists\tCtrl+R", "Muestra tus playlists")
		menu_playlists.Append(wx.ID_ANY, "Crear Playlist\tCtrl+C", "Crea una nueva playlist")
		menu_bar.Append(menu_playlists, "Playlists")

		# --- PODCASTS ---
		menu_podcasts = wx.Menu()
		menu_podcasts.Append(wx.ID_ANY, "Sincronizar Podcasts (data)\tCtrl+S", "Sincroniza tus podcasts")
		menu_bar.Append(menu_podcasts, "Podcasts")

		# --- ARTISTA AUTO ---
		menu_gestor = wx.Menu()
		menu_gestor.Append(wx.ID_ANY, "Gestor Automático de Artistas\tCtrl+G", "Gestor automático para artistas")
		menu_bar.Append(menu_gestor, "Gestor Automático")

		# --- RECOMENDACIONES ---
		menu_reco = wx.Menu()
		menu_reco.Append(wx.ID_ANY, "#Artistapy\tCtrl+A", "Obtén recomendaciones personalizadas")
		menu_bar.Append(menu_reco, "Recomendaciones")

		# --- BÚSQUEDA LIBRE ---
		menu_busqueda = wx.Menu()
		menu_busqueda.Append(wx.ID_ANY, "Por Frase Libre\tCtrl+B", "Buscar canciones por frase")
		menu_bar.Append(menu_busqueda, "Buscar Canciones")

		# --- TOP TRACKS ---
		menu_bar.Append(wx.Menu(), "Top Tracks Artista")
		# --- Salir ---
		menu_bar.Append(wx.Menu(), "Salir")

		# Asignación de IDs para los menús, guardando handlers
		self.menu_handlers = {
			# Playlists
			menu_playlists.FindItemByPosition(0).GetId(): lambda e: ventana_vaciar_playlists(self.sp, self),
			menu_playlists.FindItemByPosition(1).GetId(): lambda e: ventana_eliminar_playlists(self.sp, self),
			menu_playlists.FindItemByPosition(2).GetId(): lambda e: ventana_ver_playlists(self.sp, self),
			menu_playlists.FindItemByPosition(3).GetId(): lambda e: ventana_crear_playlist(self.sp, self),
			# Podcasts
			menu_podcasts.FindItemByPosition(0).GetId(): lambda e: ventana_sincronizar_podcasts_data(self.sp, self),
			# Gestor
			menu_gestor.FindItemByPosition(0).GetId(): lambda e: VentanaGestorAutomatico(self, self.sp),
			# Recomendaciones
			menu_reco.FindItemByPosition(0).GetId(): lambda e: ventana_artistapy(self.sp, self),
			# Búsqueda
			menu_busqueda.FindItemByPosition(0).GetId(): lambda e: ventana_busqueda_avanzada(self.sp, self),
			# Top Tracks
			menu_bar.FindMenu("Top Tracks Artista"): lambda e: ventana_top_tracks(self.sp, self),
			# Salir
			menu_bar.FindMenu("Salir"): lambda e: self.Close(),
		}

		self.SetMenuBar(menu_bar)
		self.Bind(wx.EVT_MENU, self.on_menu)

	def on_menu(self, event):
		handler = self.menu_handlers.get(event.GetId())
		# Top Tracks y Salir se disparan por menú, no por comando individual
		if handler:
			handler(event)
		else:
			menu_idx = self.GetMenuBar().FindMenu(self.GetMenuBar().GetLabelTop(event.GetId()))
			if menu_idx != wx.NOT_FOUND:
				handler = self.menu_handlers.get(menu_idx)
				if handler:
					handler(event)

	def _build_ui(self):
		panel = wx.Panel(self)
		main_sizer = wx.BoxSizer(wx.VERTICAL)

		welcome_label = wx.StaticText(panel, label="¡Bienvenido al Gestor Modular de Spotify!")
		font = wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		welcome_label.SetFont(font)
		welcome_label.SetName("Mensaje de bienvenida")
		welcome_label.SetMinSize((400, 44))
		main_sizer.Add(welcome_label, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 20)

		# Barra de estado accesible
		self.status_bar = self.CreateStatusBar()
		self.status_bar.SetStatusText("Listo")
		self.status_bar.SetName("Barra de estado")
		# Tamaño mínimo para accesibilidad
		self.status_bar.SetMinHeight(44)

		panel.SetSizer(main_sizer)

def build_main_window(sp: Spotify):
	app = wx.App(False)
	frame = MainFrame(sp)
	app.MainLoop()
	return frame