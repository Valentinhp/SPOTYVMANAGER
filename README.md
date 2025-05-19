
# 🎧 SPOTYVMANAGER (Versión Modularizada)

**SPOTYVMANAGER** es una aplicación de escritorio en Python diseñada para brindar a los usuarios ciegos o con baja visión una gestión avanzada, automatizada y accesible de sus cuentas de Spotify. El objetivo es superar los límites de la aplicación oficial en cuanto a flexibilidad, automatización y accesibilidad.

---

## ✨ Características principales

* **Ver todas tus playlists** en una tabla accesible.
* **Crear nuevas playlists** de manera fácil y rápida.
* **Vaciar y/o eliminar playlists** (una o múltiples) con opciones de confirmación.
* **Visualizar y eliminar contenido de una playlist**.
* **Agregar top tracks de un artista o episodios de podcast a cualquier playlist**.
* **Sincronizar automáticamente podcasts con sus playlists dedicadas**.
* **Buscar artistas y generar playlists automáticas con todas sus canciones únicas** (evitando duplicados y versiones alternas).
* **Búsqueda avanzada** por frase, tema o emoción, con filtros de popularidad y géneros.
* **Obtener el top de canciones** de cualquier artista, filtrando por popularidad, colaboraciones y géneros secundarios.
* **Gestión completa solo con teclado**, atajos en todos los controles y mensajes claros de confirmación o error.
* **Interfaz modular** y fácil de extender.

---

## ♿ Accesibilidad

SPOTYVMANAGER ha sido desarrollado desde cero con los principios de accesibilidad universal:

* Todos los controles cumplen el tamaño mínimo recomendado (44x44 px).
* Navegación **100% por teclado** (tabulación lógica, atajos con “&”, mensajes claros).
* Compatibilidad y pruebas reales con lectores de pantalla como NVDA y Narrador de Windows.
* Diálogos con mensajes claros, sin ambigüedades.
* Todas las ventanas ofrecen botón de cancelar y soporte de ESC.
* Se priorizan los avisos por texto y el soporte de atajos de teclado en cada acción relevante.
* No se emplean elementos visuales exclusivamente gráficos para la interacción principal.

---

## 🧰 Tecnologías y dependencias

* **Python >= 3.9**
* [Spotipy](https://spotipy.readthedocs.io/en/2.22.1/) (cliente Spotify Web API)
* [wxPython](https://wxpython.org/) (Interfaz gráfica, multiplataforma, accesible)
* **Tkinter** (soporte legacy, opcional)
* [python-dotenv](https://pypi.org/project/python-dotenv/) (para cargar claves y configuración)
* Otros paquetes: `requests`, `unicodedata`, `re`, `threading`, `queue`, etc.

Instala todo con:

```bash
pip install -r requirements.txt
```

---

## ⚡ Instalación y configuración

1. **Clona el repositorio**:

   ```bash
   cd SPOTYVMANAGER
   ```

2. **Crea y activa un entorno virtual (opcional pero recomendado):**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Instala las dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configura tus credenciales de Spotify**:

   * Crea una aplicación en el [Dashboard de Spotify Developers](https://developer.spotify.com/dashboard/applications)
   * Añade `http://localhost:8888/callback` como Redirect URI (o el que elijas en `.env`)
   * Crea un archivo `.env` en la raíz del proyecto con este contenido:

     ```
     SPOTIPY_CLIENT_ID=tu_client_id
     SPOTIPY_CLIENT_SECRET=tu_client_secret
     SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
     ```
   * Puedes usar también variables de entorno estándar.

5. **Ejecuta la aplicación:**

   ```bash
   python -m src.main
   ```

   o bien (si tu entrypoint es otro):

   ```bash
   python src/main.py
   ```

---

## 📁 Estructura del proyecto

```
SPOTYVMANAGER/
│
├── src/
│   ├── main.py                # Punto de entrada principal
│   ├── auth.py                # Autenticación y obtención del cliente Spotify
│   ├── utils/
│   │   └── spotify_utils.py   # Funciones auxiliares para interactuar con la API
│   ├── gui/
│   │   ├── main_window.py         # Ventana y menú principal
│   │   ├── playlists.py           # Ventanas de gestión de playlists
│   │   ├── podcasts.py            # Ventana de sincronización de podcasts
│   │   ├── artist_manager.py      # Ventana de gestor automático de canciones únicas
│   │   ├── artistapy.py           # Ventana de recomendaciones de géneros
│   │   ├── search_advanced.py     # Búsqueda avanzada y generación de playlists
│   │   └── top_tracks.py          # Ventana para top tracks de artista
│   └── ...
├── requirements.txt
├── .env                          # Claves de acceso, no subir a repositorios públicos
└── README.md
```

---

## 🏁 Ejemplo rápido de uso

1. Abre la app y sigue el menú principal:
2. Usa el teclado (Tab/Shift+Tab y atajos con Alt) para navegar por las opciones.
3. Consulta, crea, vacía o elimina playlists; busca canciones por frase, emoción o artista; automatiza la gestión de tu biblioteca.
4. Lee los mensajes de confirmación y utiliza ESC o el botón Cancelar para salir en cualquier ventana.

---

## ❓ Preguntas frecuentes

**¿Funciona con cuentas gratuitas de Spotify?**
Sí, pero algunas funciones como agregar canciones a playlists pueden estar limitadas por la propia API.

**¿Puedo usarla con lector de pantalla?**
Sí. El diseño está orientado a la accesibilidad desde la arquitectura, widgets y mensajes.

**¿Puedo extender la app con más módulos?**
Por supuesto. La estructura modular permite añadir más ventanas, integraciones o filtros personalizados fácilmente.

**¿Soporta Windows, Linux y Mac?**
Sí. wxPython es multiplataforma. Revisa dependencias nativas en Mac/Linux.

**¿Qué hago si tengo problemas con la autenticación (client\_id, redirect URI, etc.)?**

* Verifica las variables en `.env` y que coincidan con tu app de Spotify.
* Usa una URI de redirección segura (`http://localhost:8888/callback` o con ngrok si requieres acceso remoto).
* Lee bien los mensajes de error en consola.

---

## 📝 Contribuciones y licencia

Este proyecto es **open source** y cualquier persona puede proponer mejoras, módulos, parches de accesibilidad o traducciones.
Sigue las buenas prácticas de `pull request` y comenta tu código.

**Licencia:** MIT

---

## 📫 Soporte

¿Tienes dudas, necesitas ayuda con la accesibilidad o quieres sugerir una mejora?

* Abre un Issue en GitHub
---

**¡Contribuye y haz Spotify verdaderamente accesible para todos!**
