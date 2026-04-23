"""
Widget de tabla de canciones con scrollbar, estado vacío y ordenamiento por columna.
"""

import tkinter as tk
from tkinter import ttk

from ui.styles import BG, BG3, ACCENT, HIGHLIGHT, FG, FG_DIM, FG_MUTED, DIVIDER


_COLUMNS = ("id", "name", "artist", "album", "genre", "duration")
_HEADERS = {
    "id": "  #", "name": "Nombre", "artist": "Artista",
    "album": "Álbum", "genre": "Género", "duration": "Duración",
}
_WIDTHS = {
    "id": 44, "name": 210, "artist": 160,
    "album": 130, "genre": 100, "duration": 80,
}
_SORT_ARROWS = {"asc": " ▲", "desc": " ▼"}


class SongList(tk.Frame):
    """Treeview con scrollbar y estado vacío para el catálogo."""

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._sort_col = None
        self._sort_rev = False
        self._build()

    def _build(self):
        self._apply_style()
        self._build_table()
        self._build_empty_state()

    def _build_table(self):
        self._table_frame = tk.Frame(self, bg=BG)
        self._table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            self._table_frame, columns=_COLUMNS, show="headings",
            style="Songs.Treeview", selectmode="browse",
        )
        for col in _COLUMNS:
            self.tree.heading(col, text=_HEADERS[col],
                              command=lambda c=col: self._sort_by(c))
            anchor = "center" if col == "id" else "w"
            self.tree.column(col, width=_WIDTHS[col], anchor=anchor, minwidth=30)

        self.tree.tag_configure("odd",  background=BG3)
        self.tree.tag_configure("even", background="#161630")

        vsb = ttk.Scrollbar(self._table_frame, orient="vertical",
                             command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def _build_empty_state(self):
        self._empty_frame = tk.Frame(self, bg=BG)
        tk.Label(self._empty_frame, text="♪", bg=BG, fg=FG_MUTED,
                 font=("Segoe UI", 36)).pack(pady=(40, 8))
        tk.Label(self._empty_frame, text="No hay canciones en el catálogo",
                 bg=BG, fg=FG_MUTED,
                 font=("Segoe UI", 11)).pack()
        tk.Label(self._empty_frame,
                 text='Agrega canciones con el botón  "+ Agregar canción"',
                 bg=BG, fg=FG_MUTED,
                 font=("Segoe UI", 9)).pack(pady=(4, 0))

    def _apply_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Songs.Treeview",
                        background=BG3, fieldbackground=BG3, foreground=FG,
                        rowheight=30, font=("Segoe UI", 10),
                        borderwidth=0)
        style.configure("Songs.Treeview.Heading",
                        background="#0d2442", foreground=FG_DIM,
                        font=("Segoe UI", 8, "bold"), relief="flat",
                        padding=(6, 6))
        style.map("Songs.Treeview",
                  background=[("selected", HIGHLIGHT)],
                  foreground=[("selected", FG)])
        style.layout("Songs.Treeview", [
            ("Songs.Treeview.treearea", {"sticky": "nswe"})
        ])

    # ── API pública ───────────────────────────────────────────────

    def populate(self, songs: list):
        self.clear()
        if not songs:
            self._show_empty(True)
            return
        self._show_empty(False)
        for i, song in enumerate(songs):
            dur = song.get("duration_secs", 0)
            dur_str = f"{dur // 60}:{dur % 60:02d}" if dur else "—"
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", values=(
                song.get("id", ""),
                song.get("name", ""),
                song.get("artist", "") or "—",
                song.get("album",  "") or "—",
                song.get("genre",  "") or "—",
                dur_str,
            ), tags=(tag,))

    def clear(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

    def selected_values(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.item(sel[0], "values")

    # ── Helpers ───────────────────────────────────────────────────

    def _show_empty(self, show: bool):
        if show:
            self._table_frame.pack_forget()
            self._empty_frame.pack(fill="both", expand=True)
        else:
            self._empty_frame.pack_forget()
            self._table_frame.pack(fill="both", expand=True)

    def _sort_by(self, col: str):
        # Restaurar encabezados sin flecha
        for c in _COLUMNS:
            self.tree.heading(c, text=_HEADERS[c])

        reverse = self._sort_col == col and not self._sort_rev
        self._sort_col, self._sort_rev = col, reverse

        arrow = _SORT_ARROWS["desc" if reverse else "asc"]
        self.tree.heading(col, text=_HEADERS[col] + arrow)

        rows = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        rows.sort(reverse=reverse,
                  key=lambda x: (x[0].isdigit() and int(x[0]), x[0].lower()))
        for i, (_, k) in enumerate(rows):
            self.tree.move(k, "", i)
            self.tree.item(k, tags=("even" if i % 2 == 0 else "odd",))
