"""
Diálogo de búsqueda para agregar canciones a playlists.
"""

import tkinter as tk
from tkinter import messagebox
import threading

from ui.styles import (BG, BG2, BG3, ACCENT, HIGHLIGHT, FG, FG_DIM, FG_MUTED,
                       DIVIDER, SUCCESS, SUCCESS_H, make_button, make_bordered_entry)


class SearchSongDialog(tk.Toplevel):
    """Diálogo para buscar canciones por nombre/artista/género y seleccionar una."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        self.result = None
        self._songs = []
        
        self.title("Buscar canción para agregar")
        self.configure(bg=BG3)
        self.geometry("550x480")
        self.minsize(420, 380)
        self.grab_set()
        
        self._build()
        self._center(parent)
        self._do_search()

    def _build(self):
        frame = tk.Frame(self, bg=BG3, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Buscar canción", bg=BG3, fg=HIGHLIGHT,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 8))

        search_frame = tk.Frame(frame, bg=BG3)
        search_frame.pack(fill="x", pady=(0, 12))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter_local())
        
        wrap = make_bordered_entry(search_frame, textvariable=self._search_var, width=30)
        wrap.pack(side="left", padx=(0, 8))
        wrap.entry.bind("<Return>", lambda _: self._do_search())

        make_button(search_frame, "Buscar", self._do_search,
                    color=HIGHLIGHT, width=10).pack(side="left", padx=(0, 4))
        make_button(search_frame, "Limpiar", self._clear,
                    color=ACCENT, width=10).pack(side="left")

        tk.Label(frame, text="Resultados:", bg=BG3, fg=FG_DIM,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))

        list_frame = tk.Frame(frame, bg=BG3)
        list_frame.pack(fill="both", expand=True)

        self._listbox = tk.Listbox(
            list_frame, bg=BG, fg=FG, selectbackground=HIGHLIGHT,
            selectforeground=FG, relief="flat", font=("Segoe UI", 10),
            height=10, borderwidth=0, highlightthickness=0,
            exportselection=False
        )
        self._listbox.pack(side="left", fill="both", expand=True)
        self._listbox.bind("<Double-Button-1>", lambda _: self._confirm())

        scroll = tk.Scrollbar(list_frame, orient="vertical",
                              command=self._listbox.yview)
        scroll.pack(side="right", fill="y")
        self._listbox.config(yscrollcommand=scroll.set)

        self._info_var = tk.StringVar(value="Cargando canciones...")
        tk.Label(frame, textvariable=self._info_var, bg=BG3, fg=FG_MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(4, 12))

        tk.Frame(frame, bg=DIVIDER, height=1).pack(fill="x", pady=(0, 12))

        btn_frame = tk.Frame(frame, bg=BG3)
        btn_frame.pack(fill="x")

        make_button(btn_frame, "Cancelar", self.destroy,
                    color=ACCENT, width=12).pack(side="right", padx=(8, 0))
        make_button(btn_frame, "Agregar seleccionada", self._confirm,
                    color=SUCCESS, hover=SUCCESS_H, width=20).pack(side="right")

    def _do_search(self):
        query = self._search_var.get().strip()
        criteria = {}
        if query:
            criteria["name"] = query
        
        self._info_var.set("Buscando...")
        threading.Thread(target=self._search_worker,
                         args=(criteria,), daemon=True).start()

    def _search_worker(self, criteria: dict):
        cmd = "SEARCH" if criteria else "LIST_SONGS"
        resp, err = self.conn.send_command(cmd, criteria if criteria else None)
        if err:
            self.after(0, lambda: self._info_var.set(f"Error: {err}"))
            return
        songs = resp.get("data", []) if resp else []
        self._songs = songs
        self.after(0, lambda: self._show_results(songs))

    def _show_results(self, songs: list):
        self._listbox.delete(0, tk.END)
        if not songs:
            self._listbox.insert(tk.END, "  (Sin resultados)")
            self._info_var.set("No se encontraron canciones")
            return
        
        for s in songs:
            name = s.get("name", "?")
            artist = s.get("artist", "?") or "-"
            genre = s.get("genre", "?") or "-"
            sid = s.get("id", "?")
            self._listbox.insert(tk.END, f"  [ID:{sid}]  {name}  -  {artist}  ({genre})")
        
        self._info_var.set(f"{len(songs)} cancion(es) encontrada(s)")

    def _filter_local(self):
        query = self._search_var.get().strip().lower()
        if not query:
            self._do_search()
            return
        
        filtered = [
            s for s in self._songs
            if query in s.get("name", "").lower()
            or query in s.get("artist", "").lower()
            or query in s.get("genre", "").lower()
        ]
        self._show_results(filtered)

    def _clear(self):
        self._search_var.set("")
        self._do_search()

    def _confirm(self):
        sel = self._listbox.curselection()
        if not sel:
            messagebox.showinfo("Sin selección", "Selecciona una canción de la lista.", parent=self)
            return
        
        first_line = self._listbox.get(sel[0])
        if first_line.startswith("  (Sin"):
            return
        
        idx = sel[0]
        if idx < len(self._songs):
            self.result = self._songs[idx].get("id")
            self.destroy()

    def _center(self, parent):
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width() // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px - w // 2}+{py - h // 2}")