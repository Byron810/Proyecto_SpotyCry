"""
Pestañas de la aplicación: Catálogo y Playlists.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import threading

from ui.styles import (BG, BG2, BG3, ACCENT, HIGHLIGHT, FG, FG_DIM, FG_MUTED,
                       DIVIDER, SUCCESS, SUCCESS_H, WARNING, ERROR, ERROR_H,
                       make_button, make_separator)


class TabBar(tk.Frame):
    """Barra de pestañas personalizada."""

    def __init__(self, parent, on_change, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._on_change = on_change
        self._buttons = {}
        self._active = None
        self._build()

    def _build(self):
        self._btn_frame = tk.Frame(self, bg=BG, pady=4, padx=12)
        self._btn_frame.pack(fill="x")

    def add_tab(self, key: str, text: str):
        btn = tk.Button(
            self._btn_frame, text=text,
            bg=BG3, fg=FG_DIM,
            font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2",
            padx=16, pady=6,
            borderwidth=0, highlightthickness=0,
            command=lambda: self._select(key)
        )
        btn.pack(side="left", padx=(0, 2))
        self._buttons[key] = {"btn": btn, "text": text}

        # Activar visualmente la primera sin disparar callback
        if self._active is None:
            self._active = key
            btn.config(bg=HIGHLIGHT, fg=FG)

    def _select(self, key: str):
        if self._active and self._active in self._buttons:
            self._buttons[self._active]["btn"].config(bg=BG3, fg=FG_DIM)
        self._active = key
        self._buttons[key]["btn"].config(bg=HIGHLIGHT, fg=FG)
        self._on_change(key)


class PlaylistView(tk.Frame):
    """Vista de playlists con tabla de canciones y botones."""

    def __init__(self, parent, conn, on_status, on_play_playlist, **kw):
        super().__init__(parent, bg=BG, **kw)
        self.conn = conn
        self._on_status = on_status
        self._on_play_playlist = on_play_playlist
        self._playlists = []
        self._current_playlist_id = None
        self._current_songs = []
        self._build()

    def _build(self):
        # ── Encabezado ──
        header = tk.Frame(self, bg=BG, pady=8, padx=16)
        header.pack(fill="x")
        tk.Label(header, text="MIS PLAYLISTS", bg=BG, fg=FG_MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        self._count_var = tk.StringVar(value="")
        tk.Label(header, textvariable=self._count_var, bg=BG, fg=FG_MUTED,
                 font=("Segoe UI", 8)).pack(side="right")

        make_separator(self, color=DIVIDER).pack(fill="x")

        # ── Panel superior: lista de playlists ──
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=8, pady=4)

        list_frame = tk.Frame(top, bg=BG2)
        list_frame.pack(side="left", fill="x", expand=True)

        tk.Label(list_frame, text="Playlists", bg=BG2, fg=FG_DIM,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=4)

        self._pl_listbox = tk.Listbox(
            list_frame, bg=BG3, fg=FG, selectbackground=HIGHLIGHT,
            selectforeground=FG, relief="flat", font=("Segoe UI", 10),
            height=4, borderwidth=0, highlightthickness=0,
            exportselection=False  # ← IMPORTANTE: evita perder selección
        )
        self._pl_listbox.pack(fill="x", padx=2, pady=2)
        self._pl_listbox.bind("<<ListboxSelect>>", self._on_pl_select)

        self._pl_info_var = tk.StringVar(value="Selecciona una playlist")
        tk.Label(list_frame, textvariable=self._pl_info_var, bg=BG2, fg=FG_DIM,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=4, pady=(2, 0))

        make_separator(self, color=DIVIDER).pack(fill="x")

        # ── Canciones de la playlist ──
        songs_header = tk.Frame(self, bg=BG, pady=4, padx=16)
        songs_header.pack(fill="x")
        tk.Label(songs_header, text="CANCIONES EN LA PLAYLIST", bg=BG, fg=FG_MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        self._songs_count_var = tk.StringVar(value="")
        tk.Label(songs_header, textvariable=self._songs_count_var, bg=BG, fg=FG_MUTED,
                 font=("Segoe UI", 8)).pack(side="right")

        songs_frame = tk.Frame(self, bg=BG3)
        songs_frame.pack(fill="both", expand=True, padx=8, pady=2)

        self._songs_listbox = tk.Listbox(
            songs_frame, bg=BG3, fg=FG, selectbackground=HIGHLIGHT,
            selectforeground=FG, relief="flat", font=("Segoe UI", 10),
            height=6, borderwidth=0, highlightthickness=0,
            exportselection=False
        )
        self._songs_listbox.pack(side="left", fill="both", expand=True, padx=2, pady=2)

        scroll = tk.Scrollbar(songs_frame, orient="vertical",
                              command=self._songs_listbox.yview)
        scroll.pack(side="right", fill="y")
        self._songs_listbox.config(yscrollcommand=scroll.set)

        # ── Barra de acciones ──
        make_separator(self, color=DIVIDER).pack(fill="x")
        bar = tk.Frame(self, bg=BG2, pady=10, padx=16)
        bar.pack(fill="x")

        make_button(bar, "+ Crear", self._create_playlist,
                    color=SUCCESS, hover=SUCCESS_H, width=10).pack(side="left", padx=(0, 4))
        make_button(bar, "🗑 Eliminar", self._delete_playlist,
                    color=ERROR, hover=ERROR_H, width=10).pack(side="left", padx=(0, 16))

        make_separator(bar, color=DIVIDER).pack(side="left", fill="y", padx=8, pady=2)

        make_button(bar, "+ Agregar canción", self._add_song_to_pl,
                    color=ACCENT, width=14).pack(side="left", padx=(8, 4))
        make_button(bar, "🗑 Quitar", self._remove_song,
                    color=ERROR, hover=ERROR_H, width=10).pack(side="left", padx=(0, 4))
        make_button(bar, "▶ Reproducir", self._play_playlist,
                    color=SUCCESS, hover=SUCCESS_H, width=12).pack(side="right")

    # ── API pública ───────────────────────────────────────────────

    def load_playlists(self):
        threading.Thread(target=self._load_worker, daemon=True).start()

    # ── Workers ──────────────────────────────────────────────────

    def _load_worker(self):
        resp, err = self.conn.send_command("LIST_PLAYLISTS")
        if err:
            print(f"ERROR cargando playlists: {err}")
            return
        playlists = resp.get("data", []) if resp else []
        print(f"DEBUG: playlists cargadas = {playlists}")
        self.after(0, lambda: self._show_playlists(playlists))

    def _show_playlists(self, playlists: list):
        self._playlists = playlists
        self._pl_listbox.delete(0, tk.END)
        for pl in playlists:
            name = pl.get("name", "Sin nombre")
            count = len(pl.get("song_ids", []))
            self._pl_listbox.insert(tk.END, f"  {name}  ({count})")
        total = len(playlists)
        self._count_var.set(f"{total} playlist{'s' if total != 1 else ''}")

    def _on_pl_select(self, event):
        sel = self._pl_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self._playlists):
            pl = self._playlists[idx]
            self._current_playlist_id = pl.get("id")
            name = pl.get("name", "")
            count = len(pl.get("song_ids", []))
            self._pl_info_var.set(f"Seleccionada: {name} | {count} canciones")
            self._load_playlist_songs()

    def _load_playlist_songs(self):
        if not self._current_playlist_id:
            return
        # Guardar el ID actual para verificar que no cambió durante la carga
        pl_id = self._current_playlist_id
        threading.Thread(target=self._load_songs_worker, args=(pl_id,), daemon=True).start()

    def _load_songs_worker(self, pl_id: int = None):
        if pl_id is None:
            pl_id = self._current_playlist_id
        resp, err = self.conn.send_command("GET_PLAYLIST", {
            "playlist_id": pl_id
        })
        if err:
            return
        data = resp.get("data", {}) if resp else {}
        songs = data.get("songs", [])
        duration = data.get("total_duration_secs", 0)
        # Solo actualizar si sigue siendo la misma playlist
        self.after(0, lambda: self._show_songs(songs, duration) if self._current_playlist_id == pl_id else None)

    def _show_songs(self, songs: list, duration: int):
        self._current_songs = songs
        self._songs_listbox.delete(0, tk.END)
        mins = duration // 60
        secs = duration % 60
        for s in songs:
            name = s.get("name", "?")
            artist = s.get("artist", "?")
            self._songs_listbox.insert(tk.END, f"  [ID:{s.get('id', '?')}] {name} - {artist}")
        total = len(songs)
        self._songs_count_var.set(f"{total} cancione{'s' if total != 1 else ''} | {mins}:{secs:02d}")

    # ── Acciones ─────────────────────────────────────────────────

    def _create_playlist(self):
        name = simpledialog.askstring("Nueva playlist", "Nombre:", parent=self)
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

    def _delete_playlist(self):
        if not self._current_playlist_id:
            messagebox.showinfo("Sin playlist", "Selecciona una playlist.")
            return
        if not messagebox.askyesno("Eliminar", "¿Eliminar esta playlist?"):
            return
        threading.Thread(target=self._delete_worker,
                         args=(self._current_playlist_id,), daemon=True).start()

    def _delete_worker(self, pl_id: int):
        resp, err = self.conn.send_command("DELETE_PLAYLIST", {"playlist_id": pl_id})
        if err:
            self.after(0, lambda: messagebox.showerror("Error", err))
            return
        if resp and resp.get("status") == "ok":
            self._current_playlist_id = None
            self._current_songs = []
            self.after(0, lambda: self._on_status("Playlist eliminada."))
            self.after(0, self.load_playlists)
            self.after(0, lambda: self._songs_listbox.delete(0, tk.END))
            self.after(0, lambda: self._songs_count_var.set(""))
            self.after(0, lambda: self._pl_info_var.set("Selecciona una playlist"))
        else:
            msg = resp.get("message", "Error") if resp else ""
            self.after(0, lambda: messagebox.showerror("Error", msg))

    def _add_song_to_pl(self):
        if not self._current_playlist_id:
            messagebox.showinfo("Sin playlist", "Selecciona una playlist primero.")
            return
        
        from ui.playlist_dialogs import SearchSongDialog
        
        dialog = SearchSongDialog(self.winfo_toplevel(), self.conn)
        self.wait_window(dialog)
        
        if dialog.result is None:
            return
        
        song_id = dialog.result
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
            # Primero recargar canciones, luego playlists
            self.after(50, self._load_playlist_songs)
            self.after(100, self.load_playlists)
        else:
            msg = resp.get("message", "Error") if resp else ""
            self.after(0, lambda: messagebox.showerror("Error", msg))

    def _remove_song(self):
        if not self._current_playlist_id:
            messagebox.showinfo("Sin playlist", "Selecciona una playlist.")
            return
        sel = self._songs_listbox.curselection()
        if not sel:
            messagebox.showinfo("Sin canción", "Selecciona una canción de la playlist.")
            return
        idx = sel[0]
        if idx < len(self._current_songs):
            song = self._current_songs[idx]
            song_id = song.get("id")
            song_name = song.get("name", "")
            if not messagebox.askyesno("Quitar", f'¿Quitar "{song_name}"?'):
                return
            threading.Thread(target=self._remove_worker,
                             args=(song_id,), daemon=True).start()

    def _remove_worker(self, song_id: int):
        resp, err = self.conn.send_command("REMOVE_FROM_PLAYLIST", {
            "playlist_id": self._current_playlist_id, "song_id": song_id
        })
        if err:
            self.after(0, lambda: messagebox.showerror("Error", err))
            return
        if resp and resp.get("status") == "ok":
            self.after(0, lambda: self._on_status("Canción eliminada."))
            self.after(50, self._load_playlist_songs)
            self.after(100, self.load_playlists)
        else:
            msg = resp.get("message", "Error") if resp else ""
            self.after(0, lambda: messagebox.showerror("Error", msg))

    def _play_playlist(self):
        if not self._current_songs:
            messagebox.showinfo("Vacía", "La playlist no tiene canciones.")
            return
        self._on_play_playlist(self._current_songs)