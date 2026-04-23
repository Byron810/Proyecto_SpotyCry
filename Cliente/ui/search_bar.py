"""
Barra de búsqueda con 3 criterios: nombre, artista y género.
Expone callbacks `on_search` y `on_clear` para que la ventana principal reaccione.
"""

import tkinter as tk

from ui.styles import ACCENT, HIGHLIGHT, FG, FG_DIM, make_button, make_entry


class SearchBar(tk.Frame):
    """Panel de búsqueda con campos nombre / artista / género."""

    def __init__(self, parent, on_search, on_clear, **kw):
        super().__init__(parent, bg=ACCENT, pady=8, padx=14, **kw)
        self._on_search = on_search
        self._on_clear  = on_clear
        self._build()

    def _build(self):
        tk.Label(self, text="Buscar:", bg=ACCENT, fg=FG,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))

        self.name_var   = tk.StringVar()
        self.artist_var = tk.StringVar()
        self.genre_var  = tk.StringVar()

        for label, var in [("Nombre", self.name_var),
                            ("Artista", self.artist_var),
                            ("Género",  self.genre_var)]:
            tk.Label(self, text=label, bg=ACCENT, fg=FG_DIM,
                     font=("Segoe UI", 9)).pack(side="left", padx=(4, 2))
            entry = make_entry(self, textvariable=var, width=14)
            entry.pack(side="left", padx=(0, 6))
            entry.bind("<Return>", lambda _: self._on_search(self.get_criteria()))

        make_button(self, "🔍 Buscar",
                    lambda: self._on_search(self.get_criteria()),
                    color=HIGHLIGHT, width=10).pack(side="left", padx=6)
        make_button(self, "✕ Limpiar", self._clear,
                    color=ACCENT, width=8).pack(side="left")

    def get_criteria(self) -> dict:
        """Retorna los criterios no vacíos como dict."""
        criteria = {}
        if self.name_var.get().strip():
            criteria["name"] = self.name_var.get().strip()
        if self.artist_var.get().strip():
            criteria["artist"] = self.artist_var.get().strip()
        if self.genre_var.get().strip():
            criteria["genre"] = self.genre_var.get().strip()
        return criteria

    def _clear(self):
        self.name_var.set("")
        self.artist_var.set("")
        self.genre_var.set("")
        self._on_clear()
