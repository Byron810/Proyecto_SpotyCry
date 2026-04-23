"""
Diálogos modales de la aplicación.
"""

import tkinter as tk
from tkinter import messagebox, filedialog

from ui.styles import BG, ACCENT, HIGHLIGHT, FG, FG_DIM, make_button, make_entry


class AddSongDialog(tk.Toplevel):
    """Diálogo para ingresar los datos de una nueva canción."""

    # (label_visible, clave_payload, necesita_browse)
    _FIELDS = [
        ("Nombre *",          "name",          False),
        ("Artista",           "artist",         False),
        ("Álbum",             "album",          False),
        ("Género",            "genre",          False),
        ("Duración (seg)",    "duration_secs",  False),
        ("Ruta del archivo *","file_path",      True),
    ]

    def __init__(self, parent):
        super().__init__(parent)
        self.result = None
        self.title("Agregar canción")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        self._vars = {}
        self._build()
        self._center(parent)

    def _build(self):
        frame = tk.Frame(self, bg=BG, padx=24, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Nueva canción", bg=BG, fg=HIGHLIGHT,
                 font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 14))

        for i, (label, key, has_browse) in enumerate(self._FIELDS, start=1):
            tk.Label(frame, text=label, bg=BG, fg=FG_DIM,
                     font=("Segoe UI", 9)).grid(row=i, column=0, sticky="w", pady=4)

            var = tk.StringVar()
            self._vars[key] = var
            make_entry(frame, textvariable=var, width=28).grid(
                row=i, column=1, padx=(8, 4), pady=4)

            if has_browse:
                make_button(frame, "Examinar",
                            lambda k=key: self._browse(k),
                            color=ACCENT, width=9).grid(row=i, column=2)

        btn_frame = tk.Frame(frame, bg=BG)
        btn_frame.grid(row=len(self._FIELDS) + 2, column=0,
                       columnspan=3, pady=(16, 0), sticky="e")
        make_button(btn_frame, "Cancelar", self.destroy,
                    color=ACCENT, width=10).pack(side="right", padx=(6, 0))
        make_button(btn_frame, "Agregar", self._submit,
                    color=HIGHLIGHT, width=10).pack(side="right")

    def _browse(self, key):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo de audio",
            filetypes=[("Audio", "*.mp3 *.wav *.flac *.ogg"), ("Todos", "*.*")],
        )
        if path:
            self._vars[key].set(path)

    def _submit(self):
        name      = self._vars["name"].get().strip()
        file_path = self._vars["file_path"].get().strip()

        if not name:
            messagebox.showwarning("Campo requerido", "El nombre es obligatorio.", parent=self)
            return
        if not file_path:
            messagebox.showwarning("Campo requerido", "La ruta del archivo es obligatoria.", parent=self)
            return

        payload = {"name": name, "file_path": file_path}
        for key in ("artist", "album", "genre"):
            val = self._vars[key].get().strip()
            if val:
                payload[key] = val
        dur = self._vars["duration_secs"].get().strip()
        if dur:
            try:
                payload["duration_secs"] = int(dur)
            except ValueError:
                messagebox.showwarning("Valor inválido",
                                       "La duración debe ser un número entero.", parent=self)
                return

        self.result = payload
        self.destroy()

    def _center(self, parent):
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width() // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px - w // 2}+{py - h // 2}")
