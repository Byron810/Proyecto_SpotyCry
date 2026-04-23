"""
Widget de tabla de canciones con scrollbar y ordenamiento por columna.
"""

import tkinter as tk
from tkinter import ttk

from ui.styles import BG2, ACCENT, HIGHLIGHT, FG


_COLUMNS = ("id", "name", "artist", "album", "genre", "duration")
_HEADERS = {
    "id": "ID", "name": "Nombre", "artist": "Artista",
    "album": "Álbum", "genre": "Género", "duration": "Duración",
}
_WIDTHS = {
    "id": 40, "name": 200, "artist": 150,
    "album": 130, "genre": 90, "duration": 80,
}


class SongList(tk.Frame):
    """Treeview con scrollbar para mostrar el catálogo de canciones."""

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=parent["bg"], **kw)
        self._sort_col = None
        self._sort_rev = False
        self._build()

    def _build(self):
        self._apply_style()

        self.tree = ttk.Treeview(
            self, columns=_COLUMNS, show="headings",
            style="Songs.Treeview", selectmode="browse",
        )
        for col in _COLUMNS:
            self.tree.heading(col, text=_HEADERS[col],
                              command=lambda c=col: self._sort_by(c))
            anchor = "center" if col == "id" else "w"
            self.tree.column(col, width=_WIDTHS[col], anchor=anchor)

        self.tree.tag_configure("odd",  background=BG2)
        self.tree.tag_configure("even", background=ACCENT)

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def _apply_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Songs.Treeview",
                        background=BG2, fieldbackground=BG2, foreground=FG,
                        rowheight=26, font=("Segoe UI", 10))
        style.configure("Songs.Treeview.Heading",
                        background=ACCENT, foreground=FG,
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Songs.Treeview",
                  background=[("selected", HIGHLIGHT)],
                  foreground=[("selected", FG)])

    # ── API pública ───────────────────────────────────────────────

    def populate(self, songs: list):
        """Reemplaza el contenido de la tabla con la lista dada."""
        self.clear()
        for i, song in enumerate(songs):
            dur = song.get("duration_secs", 0)
            dur_str = f"{dur // 60}:{dur % 60:02d}" if dur else "—"
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", values=(
                song.get("id", ""),
                song.get("name", ""),
                song.get("artist", ""),
                song.get("album", ""),
                song.get("genre", ""),
                dur_str,
            ), tags=(tag,))

    def clear(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

    def selected_values(self):
        """Retorna los valores de la fila seleccionada, o None."""
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.item(sel[0], "values")

    # ── Ordenamiento local ────────────────────────────────────────

    def _sort_by(self, col: str):
        rows = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        reverse = self._sort_col == col and not self._sort_rev
        self._sort_col, self._sort_rev = col, reverse
        rows.sort(reverse=reverse,
                  key=lambda x: (x[0].isdigit() and int(x[0]), x[0].lower()))
        for i, (_, k) in enumerate(rows):
            self.tree.move(k, "", i)
            self.tree.item(k, tags=("even" if i % 2 == 0 else "odd",))
