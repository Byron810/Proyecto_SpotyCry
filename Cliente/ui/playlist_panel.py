"""
Panel de playlists para la GUI de SpotiCry.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import threading

from ui.styles import (BG, BG2, BG3, ACCENT, HIGHLIGHT, FG, FG_DIM, FG_MUTED,
                       DIVIDER, SUCCESS, SUCCESS_H, WARNING, ERROR, ERROR_H,
                       make_button, make_separator)


class PlaylistPanel(tk.Frame):
    """Panel lateral/ inferior para gestionar playlists."""

    def __init__(self, parent, conn, on_status, **kw):
        super().__init__(parent, bg=BG2, **kw)
        self.conn = conn
        self._on_status = on_status
        self._playlists = []
        self._current_playlist_id = None
        self._build()

    def _build(self):
        # Encabezado
        header = tk.Frame(self, bg=BG2, pady=8, padx=16)
        header.pack(fill="x")
        tk.Label(header, text="PLAYLISTS", bg=BG2, fg=FG_MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        self._pl_count_var = tk.StringVar(value="")
        tk.Label(header, textvariable=self._pl_count_var, bg=BG2, fg=FG_MUTED,
                 font=("Segoe UI", 8)).pack(side="right")

        make_separator(self, color=DIVIDER).pack(fill="x")

        # Lista de playlists
        list_frame = tk.Frame(self, bg=BG2)
        list_frame.pack(fill="x", padx=8, pady=4)

        self._playlist_listbox = tk.Listbox(
            list_frame, bg=BG3, fg=FG, selectbackground=HIGHLIGHT,
            selectforeground=FG, relief="flat", font=("Segoe UI", 10),
            height=6, borderwidth=0, highlightthickness=0
        )
        self._playlist_listbox.pack(side="left", fill="x", expand=True)
        self._playlist_listbox.bind("<<ListboxSelect>>", self._on_select)

        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame, orient="vertical",
                                 command=self._playlist_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self._playlist_listbox.config(yscrollcommand=scrollbar.set)

        # Info de playlist seleccionada
        self._info_var = tk.StringVar(value="Selecciona una playlist")
        tk.Label(self, textvariable=self._info_var, bg=BG2, fg=FG_DIM,
                 font=("Segoe UI", 8), padx=16).pack(fill="x", anchor="w")

        make_separator(self, color=DIVIDER).pack(fill="x")

        # Botones
        btn_frame = tk.Frame(self, bg=BG2, pady=8, padx=8)
        btn_frame.pack(fill="x")

        make_button(btn_frame, "+ Crear", self._create_playlist,
                    color=SUCCESS, hover=SUCCESS_H, width=10).pack(side="left", padx=(0, 4))
        make_button(btn_frame, "+ Agregar", self._add_to_playlist,
                    color=ACCENT, width=10).pack(side="left", padx=(0, 4))
        make_button(btn_frame, "Ver", self._view_playlist,
                    color=ACCENT, width=8).pack(side="left", padx=(0, 4))
        make_button(btn_frame, "🗑", self._delete_playlist,
                    color=ERROR, hover=ERROR_H, width=4).pack(side="right")

    # ── API pública ───────────────────────────────────────────────

    def load_playlists(self):
        """Carga las playlists desde el servidor."""
        threading.Thread(target=self._load_worker, daemon=True).start()

    def get_selected_playlist_id(self):
        """Retorna el ID de la playlist seleccionada."""
        return self._current_playlist_id

    # ── Workers ──────────────────────────────────────────────────

    def _load_worker(self):
        resp, err = self.conn.send_command("LIST_PLAYLISTS")
        if err:
            self.after(0, lambda: self._on_status(f"Error: {err}"))
            return
        playlists = resp.get("data", []) if resp else []
        self.after(0, lambda: self._show_playlists(playlists))

    def _show_playlists(self, playlists: list):
        self._playlists = playlists
        self._playlist_listbox.delete(0, tk.END)
        for pl in playlists:
            name = pl.get("name", "Sin nombre")
            count = len(pl.get("song_ids", []))
            self._playlist_listbox.insert(tk.END, f"{name}  ({count})")
        total = len(playlists)
        self._pl_count_var.set(f"{total} playlist{'s' if total != 1 else ''}")

    def _on_select(self, event):
        sel = self._playlist_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self._playlists):
            pl = self._playlists[idx]
            self._current_playlist_id = pl.get("id")
            name = pl.get("name", "")
            count = len(pl.get("song_ids", []))
            self._info_var.set(f"Playlist: {name} | {count} cancione{'s' if count != 1 else ''}")

    # ── Acciones ─────────────────────────────────────────────────

    def _create_playlist(self):
        name = simpledialog.askstring("Nueva playlist", "Nombre de la playlist:",
                                      parent=self)
        if not name or not name.strip():
            return

        threading.Thread(target=self._create_worker,
                         args=(name.strip(),), daemon=True).start()

    def _create_worker(self, name: str):
        resp, err = self.conn.send_command("CREATE_PLAYLIST", {"name": name})
        if err:
            self.after(0, lambda: messagebox.showerror("Error", err))
            return
        if resp and resp.get("status") == "ok":
            self.after(0, lambda: self._on_status(f"Playlist '{name}' creada."))
            self.after(0, self.load_playlists)
        else:
            msg = resp.get("message", "Error") if resp else "Sin respuesta"
            self.after(0, lambda: messagebox.showerror("Error", msg))

    def _add_to_playlist(self):
        if not self._current_playlist_id:
            messagebox.showinfo("Sin playlist", "Selecciona una playlist primero.")
            return
        song_id = simpledialog.askinteger("Agregar canción",
                                           "ID de la canción a agregar:",
                                           parent=self)
        if not song_id:
            return

        threading.Thread(target=self._add_worker,
                         args=(self._current_playlist_id, song_id), daemon=True).start()

    def _add_worker(self, pl_id: int, song_id: int):
        resp, err = self.conn.send_command("ADD_TO_PLAYLIST", {
            "playlist_id": pl_id, "song_id": song_id
        })
        if err:
            self.after(0, lambda: messagebox.showerror("Error", err))
            return
        if resp and resp.get("status") == "ok":
            self.after(0, lambda: self._on_status(f"Canción {song_id} agregada."))
            self.after(0, self.load_playlists)
        else:
            msg = resp.get("message", "Error") if resp else "Sin respuesta"
            self.after(0, lambda: messagebox.showerror("Error", msg))

    def _view_playlist(self):
        if not self._current_playlist_id:
            messagebox.showinfo("Sin playlist", "Selecciona una playlist primero.")
            return

        threading.Thread(target=self._view_worker,
                         args=(self._current_playlist_id,), daemon=True).start()

    def _view_worker(self, pl_id: int):
        resp, err = self.conn.send_command("GET_PLAYLIST", {"playlist_id": pl_id})
        if err:
            self.after(0, lambda: messagebox.showerror("Error", err))
            return
        data = resp.get("data", {}) if resp else {}
        playlist = data.get("playlist", {})
        songs = data.get("songs", [])
        duration = data.get("total_duration_secs", 0)

        def _show():
            name = playlist.get("name", "")
            mins = duration // 60
            secs = duration % 60
            msg = f"Playlist: {name}\n\nCanciones:\n"
            for s in songs:
                msg += f"  • {s.get('name', '?')} - {s.get('artist', '?')}\n"
            msg += f"\nDuración total: {mins}:{secs:02d}"
            messagebox.showinfo("Ver Playlist", msg)

        self.after(0, _show)

    def _delete_playlist(self):
        if not self._current_playlist_id:
            messagebox.showinfo("Sin playlist", "Selecciona una playlist primero.")
            return
        pl = next((p for p in self._playlists
                   if p.get("id") == self._current_playlist_id), None)
        name = pl.get("name", "") if pl else ""
        if not messagebox.askyesno("Eliminar playlist",
                                   f'¿Eliminar playlist "{name}"?'):
            return

        threading.Thread(target=self._delete_worker,
                         args=(self._current_playlist_id,), daemon=True).start()

    def _delete_worker(self, pl_id: int):
        resp, err = self.conn.send_command("DELETE_PLAYLIST", {"playlist_id": pl_id})
        if err:
            self.after(0, lambda: messagebox.showerror("Error", err))
            return
        if resp and resp.get("status") == "ok":
            self.after(0, lambda: self._on_status("Playlist eliminada."))
            self.after(0, self.load_playlists)
        else:
            msg = resp.get("message", "Error") if resp else "Sin respuesta"
            self.after(0, lambda: messagebox.showerror("Error", msg))