"""
Barra de búsqueda con 3 criterios: nombre, artista y género.
"""

import tkinter as tk

from ui.styles import (BG3, BORDER, ACCENT, HIGHLIGHT, HIGHLIGHT2,
                        FG, FG_DIM, make_button, make_bordered_entry,
                        make_separator)


class SearchBar(tk.Frame):
    """Panel de búsqueda con campos nombre / artista / género."""

    def __init__(self, parent, on_search, on_clear, **kw):
        super().__init__(parent, bg=BG3, **kw)
        self._on_search = on_search
        self._on_clear  = on_clear
        self._build()

    def _build(self):
        inner = tk.Frame(self, bg=BG3, pady=12, padx=16)
        inner.pack(fill="x")

        tk.Label(inner, text="Buscar en el catálogo", bg=BG3, fg=FG_DIM,
                 font=("Segoe UI", 8, "bold")).grid(
            row=0, column=0, columnspan=8, sticky="w", pady=(0, 8))

        self.name_var   = tk.StringVar()
        self.artist_var = tk.StringVar()
        self.genre_var  = tk.StringVar()

        col = 0
        for label, var in [("Nombre", self.name_var),
                            ("Artista", self.artist_var),
                            ("Género",  self.genre_var)]:
            tk.Label(inner, text=label, bg=BG3, fg=FG_DIM,
                     font=("Segoe UI", 9)).grid(row=1, column=col, sticky="w")
            col += 1
            wrap = make_bordered_entry(inner, textvariable=var, width=16)
            wrap.grid(row=1, column=col, padx=(2, 16), sticky="ew")
            wrap.entry.bind("<Return>", lambda _: self._on_search(self.get_criteria()))
            col += 1

        make_button(inner, "🔍  Buscar",
                    lambda: self._on_search(self.get_criteria()),
                    color=HIGHLIGHT, hover=HIGHLIGHT2, width=11).grid(
            row=1, column=col, padx=(0, 6))
        col += 1
        make_button(inner, "✕  Limpiar", self._clear,
                    color=ACCENT, width=9).grid(row=1, column=col)

    def get_criteria(self) -> dict:
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
