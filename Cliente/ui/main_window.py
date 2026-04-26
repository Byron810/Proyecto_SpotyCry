"""
Ventana principal de SpotiCry con pestañas Catálogo / Playlists.
"""

from cliente_streaming import SpotiCryStreamingClient
import sys
import os
import tkinter as tk
from tkinter import messagebox
import threading
from tkinter import ttk
import time
import pygame

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from connection import ServerConnection

from ui.styles import (BG, BG2, BG3, ACCENT, HIGHLIGHT, HIGHLIGHT2,
                        FG, FG_DIM, FG_MUTED, DIVIDER,
                        SUCCESS, SUCCESS_H, WARNING, ERROR, ERROR_H,
                        make_button, make_separator)
from ui.song_list  import SongList
from ui.search_bar import SearchBar
from ui.dialogs    import AddSongDialog
from ui.tabs       import TabBar, PlaylistView

HOST = "127.0.0.1"
PORT = 7878


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SpotiCry")
        self.geometry("920x680")
        self.minsize(780, 550)
        self.configure(bg=BG)

        self.conn = ServerConnection(HOST, PORT)
        self.player = SpotiCryStreamingClient()

        self._build_topbar()
        make_separator(self, color=DIVIDER).pack(fill="x")
        self._build_tabs()
        make_separator(self, color=DIVIDER).pack(fill="x")
        self._build_search_bar()
        make_separator(self, color=DIVIDER).pack(fill="x")
        self._build_catalog_header()
        self._build_song_list()
        self._build_playlist_view()
        make_separator(self, color=DIVIDER).pack(fill="x")
        self._build_action_bar()
        make_separator(self, color=DIVIDER).pack(fill="x")
        self._build_statusbar()

        # Mostrar catálogo por defecto (AHORA ya existen todos los widgets)
        self._show_view("catalog")

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(120, self._auto_connect)

    # ── Topbar ────────────────────────────────────────────────────

    def _build_topbar(self):
        bar = tk.Frame(self, bg=BG2, pady=12)
        bar.pack(fill="x", side="top")
        logo_frame = tk.Frame(bar, bg=BG2)
        logo_frame.pack(side="left", padx=20)
        tk.Label(logo_frame, text="♫", bg=BG2, fg=HIGHLIGHT,
                 font=("Segoe UI", 18, "bold")).pack(side="left", padx=(0, 6))
        tk.Label(logo_frame, text="SpotiCry", bg=BG2, fg=FG,
                 font=("Segoe UI", 14, "bold")).pack(side="left")
        self._conn_dot = tk.Label(bar, text="●", bg=BG2, fg=WARNING,
                                  font=("Segoe UI", 10))
        self._conn_dot.pack(side="right", padx=(0, 4))
        self._conn_label = tk.Label(bar, text="Conectando…", bg=BG2, fg=FG_DIM,
                                    font=("Segoe UI", 9))
        self._conn_label.pack(side="right", padx=(16, 0))

    # ── Pestañas ─────────────────────────────────────────────────

    def _build_tabs(self):
        self._tab_bar = TabBar(self, on_change=self._on_tab_change)
        self._tab_bar.pack(fill="x")
        self._tab_bar.add_tab("catalog", "📀  Catálogo")
        self._tab_bar.add_tab("playlists", "📋  Playlists")

    def _on_tab_change(self, key: str):
        self._show_view(key)

    def _show_view(self, key: str):
        if key == "catalog":
            self._search_bar.pack(fill="x")
            self._catalog_header.pack(fill="x")
            self._song_list.pack(fill="both", expand=True)
            self._playlist_view.pack_forget()
            self._catalog_action_bar.pack(fill="x")
            self._playlist_action_bar.pack_forget()
        else:
            self._search_bar.pack_forget()
            self._catalog_header.pack_forget()
            self._song_list.pack_forget()
            self._catalog_action_bar.pack_forget()
            self._playlist_view.pack(fill="both", expand=True)
            self._playlist_action_bar.pack(fill="x")
            self._playlist_view.load_playlists()

    # ── Búsqueda ──────────────────────────────────────────────────

    def _build_search_bar(self):
        self._search_bar = SearchBar(self, on_search=self._do_search,
                                     on_clear=self._load_songs)

    # ── Encabezado del catálogo ───────────────────────────────────

    def _build_catalog_header(self):
        self._catalog_header = tk.Frame(self, bg=BG, pady=8, padx=16)
        tk.Label(self._catalog_header, text="CATÁLOGO DE MÚSICA", bg=BG, fg=FG_MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        self._count_var = tk.StringVar(value="")
        tk.Label(self._catalog_header, textvariable=self._count_var, bg=BG, fg=FG_MUTED,
                 font=("Segoe UI", 8)).pack(side="right")

    # ── Tabla de canciones ────────────────────────────────────────

    def _build_song_list(self):
        self._song_list = SongList(self)

    # ── Vista de playlists ────────────────────────────────────────

    def _build_playlist_view(self):
        self._playlist_view = PlaylistView(
            self, self.conn,
            on_status=self._set_status,
            on_play_playlist=self._play_playlist
        )

    # ── Barra de acciones (Catálogo) ──────────────────────────────

    def _build_action_bar(self):
        # Barra para Catálogo
        self._catalog_action_bar = tk.Frame(self, bg=BG2, pady=10, padx=16)

        bar = self._catalog_action_bar

        make_button(bar, "▶  Play", self._play_song,
                    color=SUCCESS, hover=SUCCESS_H, width=10).pack(side="left", padx=(0, 4))
        make_button(bar, "⏸  Pause", self._pause_song,
                    color=WARNING, width=10).pack(side="left", padx=(0, 4))
        make_button(bar, "⏹  Stop", self._stop_song,
                    color=ERROR, hover=ERROR_H, width=10).pack(side="left", padx=(0, 4))
        make_button(bar, "⏪ -5s", lambda: self._seek_relative(-5),
                    color=ACCENT, width=7).pack(side="left", padx=(8, 2))
        make_button(bar, "⏩ +5s", lambda: self._seek_relative(5),
                    color=ACCENT, width=7).pack(side="left", padx=(0, 16))

        make_separator(bar, color=DIVIDER).pack(side="left", fill="y", padx=8, pady=2)

        make_button(bar, "+ Agregar canción", self._add_song,
                    color=SUCCESS, hover=SUCCESS_H, width=17).pack(side="left", padx=(8, 8))
        make_button(bar, "🗑  Eliminar canción", self._delete_song,
                    color="#2a1a1a", hover=ERROR_H, width=17).pack(side="left")
        make_button(bar, "⟳  Actualizar", self._load_songs,
                    color=ACCENT, width=14).pack(side="right")

        # Barra vacía para Playlists
        self._playlist_action_bar = tk.Frame(self, bg=BG2, height=46)
        
    def _seek_relative(self, delta: int):
        """Adelanta o retrocede N segundos."""
        if self.player.is_playing:
            current = self.player._get_current_position()
            new_pos = max(0, current + delta)
            self.player.seek(new_pos)
            self._set_status(f"Posición: {int(new_pos)}s")

    # ── Statusbar ─────────────────────────────────────────────────

    def _build_statusbar(self):
        self._status_var = tk.StringVar(value="Iniciando…")
        bar = tk.Frame(self, bg=BG2, pady=5)
        bar.pack(fill="x", side="bottom")
        tk.Label(bar, textvariable=self._status_var, bg=BG2, fg=FG_MUTED,
                 font=("Segoe UI", 8), anchor="w").pack(side="left", padx=14)

    # ── Conexión ──────────────────────────────────────────────────

    def _auto_connect(self):
        self._set_status("Conectando al servidor…")
        threading.Thread(target=self._connect_worker, daemon=True).start()

    def _connect_worker(self):
        ok, err = self.conn.connect()
        if ok:
            self.after(0, self._on_connected)
        else:
            self.after(0, lambda: self._on_connect_failed(err))

    def _on_connected(self):
        self._conn_dot.config(fg=SUCCESS)
        self._conn_label.config(text=f"{HOST}:{PORT}")
        self._set_status(f"Conectado a {HOST}:{PORT}")
        self._load_songs()

    def _on_connect_failed(self, err):
        self._conn_dot.config(fg=ERROR)
        self._conn_label.config(text="Sin conexión")
        self._set_status(f"Error de conexión: {err}")
        self._show_retry_dialog(err)

    def _show_retry_dialog(self, err: str):
        dialog = tk.Toplevel(self)
        dialog.title("Sin conexión")
        dialog.configure(bg=BG2)
        dialog.resizable(False, False)
        dialog.grab_set()

        frame = tk.Frame(dialog, bg=BG2, padx=32, pady=28)
        frame.pack()
        tk.Label(frame, text="⚠", bg=BG2, fg=WARNING,
                 font=("Segoe UI", 28)).pack(pady=(0, 10))
        tk.Label(frame, text="No se pudo conectar al servidor",
                 bg=BG2, fg=FG, font=("Segoe UI", 12, "bold")).pack()
        tk.Label(frame, text=err, bg=BG2, fg=FG_DIM,
                 font=("Segoe UI", 9)).pack(pady=(6, 24))
        tk.Frame(frame, bg=DIVIDER, height=1).pack(fill="x", pady=(0, 16))

        btn_row = tk.Frame(frame, bg=BG2)
        btn_row.pack()

        def retry():
            dialog.destroy()
            self._conn_dot.config(fg=WARNING)
            self._conn_label.config(text="Reconectando…")
            self._set_status("Reconectando…")
            threading.Thread(target=self._connect_worker, daemon=True).start()

        make_button(btn_row, "⟳  Reintentar", retry,
                    color=SUCCESS, hover=SUCCESS_H, width=14).pack(side="left", padx=(0, 8))
        make_button(btn_row, "Cancelar", dialog.destroy,
                    color=ACCENT, width=10).pack(side="left")

        self.update_idletasks()
        dialog.update_idletasks()
        px = self.winfo_rootx() + self.winfo_width() // 2
        py = self.winfo_rooty() + self.winfo_height() // 2
        w, h = dialog.winfo_width(), dialog.winfo_height()
        dialog.geometry(f"+{px - w // 2}+{py - h // 2}")

    # ── Catálogo ──────────────────────────────────────────────────

    def _load_songs(self):
        if not self._require_connection():
            return
        threading.Thread(target=self._list_worker, daemon=True).start()

    def _list_worker(self):
        resp, err = self.conn.send_command("LIST_SONGS")
        if err:
            self.after(0, lambda: self._set_status(f"Error: {err}"))
            return
        songs = resp.get("data", []) if resp else []
        self.after(0, lambda: self._show_songs(songs))

    def _do_search(self, criteria: dict):
        if not self._require_connection():
            return
        if not criteria:
            self._load_songs()
            return
        self._set_status("Buscando…")
        threading.Thread(target=self._search_worker,
                         args=(criteria,), daemon=True).start()

    def _search_worker(self, criteria: dict):
        resp, err = self.conn.send_command("SEARCH", criteria)
        if err:
            self.after(0, lambda: self._set_status(f"Error: {err}"))
            return
        songs = resp.get("data", []) if resp else []
        self.after(0, lambda: self._show_songs(songs, is_search=True))

    def _show_songs(self, songs: list, is_search: bool = False):
        self._song_list.populate(songs)
        total = len(songs)
        plural = "es" if total != 1 else ""
        self._count_var.set(f"{total} canción{plural}")
        if is_search:
            self._set_status(f"{total} resultado{'s' if total != 1 else ''}.")
        else:
            self._set_status(f"Catálogo cargado — {total} canción{plural}.")

    def _add_song(self):
        if not self._require_connection():
            return
        dialog = AddSongDialog(self)
        self.wait_window(dialog)
        if dialog.result is None:
            return
        threading.Thread(target=self._add_worker,
                         args=(dialog.result,), daemon=True).start()

    def _add_worker(self, payload: dict):
        resp, err = self.conn.send_command("ADD_SONG", payload)
        if err:
            self.after(0, lambda: messagebox.showerror("Error", err))
            return
        if resp and resp.get("status") == "ok":
            song = resp.get("data", {})
            msg = f"Canción \"{song.get('name', '')}\" agregada (ID {song.get('id', '?')})."
            self.after(0, lambda: self._set_status(msg))
            self.after(0, self._load_songs)
        else:
            msg = resp.get("message", "Error") if resp else "Sin respuesta"
            self.after(0, lambda: messagebox.showerror("Error", msg))

    def _delete_song(self):
        if not self._require_connection():
            return
        values = self._song_list.selected_values()
        if not values:
            messagebox.showinfo("Sin selección", "Selecciona una canción.")
            return
        song_id, song_name = int(values[0]), values[1]
        if not messagebox.askyesno("Eliminar", f'¿Eliminar "{song_name}"?'):
            return
        threading.Thread(target=self._delete_worker,
                         args=(song_id, song_name), daemon=True).start()

    def _delete_worker(self, song_id: int, song_name: str):
        resp, err = self.conn.send_command("DELETE_SONG", {"song_id": song_id})
        if err:
            self.after(0, lambda: messagebox.showerror("Error", err))
            return
        if resp and resp.get("status") == "ok":
            self.after(0, lambda: self._set_status(f'"{song_name}" eliminada.'))
            self.after(0, self._load_songs)
        else:
            msg = resp.get("message", "Error") if resp else "Sin respuesta"
            self.after(0, lambda: messagebox.showerror("Error", msg))

    # ── Reproducción ──────────────────────────────────────────────

    def _play_song(self):
        if not self._require_connection():
            return
        values = self._song_list.selected_values()
        if not values:
            messagebox.showinfo("Sin selección", "Selecciona una canción.")
            return
        song_id = int(values[0])
        song_name = values[1]
        if not self.player.connected:
            self.player.connect()
        self._set_status(f"Reproduciendo: {song_name}")
        self.player.play_song(song_id)

    def _pause_song(self):
        if self.player.is_playing:
            self.player.pause()

    def _stop_song(self):
        self.player.stop()
        self._set_status("Reproducción detenida")

    def _play_playlist(self, songs: list):
        """Reproduce canciones en orden secuencial."""
        if not songs:
            messagebox.showinfo("Vacía", "La playlist no tiene canciones.")
            return
        if not self.player.connected:
            self.player.connect()
        
        self.player.on_status = lambda msg: self.after(0, lambda: self._set_status(msg))
        
        threading.Thread(target=self._play_sequential, args=(songs,), daemon=True).start()
    
    def _play_sequential(self, songs: list):
        """Reproduce canciones una por una."""
        for song in songs:
            song_id = song.get("id")
            song_name = song.get("name", "?")
            
            # Reproducir
            self.player.play_song(song_id)
            
            # Esperar a que termine la descarga
            while self.player.is_downloading:
                time.sleep(0.3)
            
            # Esperar a que termine la reproducción
            while self.player.is_playing:
                time.sleep(0.5)
            
            time.sleep(0.3)
        
        self.after(0, lambda: self._set_status("Playlist terminada."))

    # ── Helpers ───────────────────────────────────────────────────

    def _set_status(self, text: str):
        self._status_var.set(text)

    def _require_connection(self) -> bool:
        if not self.conn.connected:
            messagebox.showinfo("Sin conexión", "No conectado al servidor.")
            return False
        return True
    
    def _seek_relative(self, delta: int):
        """Adelanta o retrocede N segundos."""
        print(f"DEBUG _seek_relative: delta={delta}")
        print(f"DEBUG _seek_relative: is_playing={self.player.is_playing}")
        print(f"DEBUG _seek_relative: is_downloading={self.player.is_downloading}")
        
        if self.player.is_playing and not self.player.is_downloading:
            current = self.player._get_current_position()
            print(f"DEBUG _seek_relative: current={current}")
            new_pos = max(0, current + delta)
            print(f"DEBUG _seek_relative: llamando player.seek({new_pos})")
            self.player.seek(new_pos)
            self._set_status(f"Posición: {int(new_pos)}s")
        else:
            print(f"DEBUG _seek_relative: NO se ejecutó seek (playing={self.player.is_playing}, downloading={self.player.is_downloading})")

    def _on_close(self):
        self.player.stop()
        self.player.disconnect()
        self.conn.disconnect()
        self.destroy()