"""
Ventana principal de SpotiCry.
Orquesta la conexión, la tabla de canciones y la barra de búsqueda.
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from connection import ServerConnection

from ui.styles import (BG, BG2, BG3, ACCENT, HIGHLIGHT, HIGHLIGHT2,
                        FG, FG_DIM, FG_MUTED, DIVIDER,
                        SUCCESS, SUCCESS_H, WARNING, ERROR, ERROR_H,
                        make_button, make_separator)
from ui.song_list  import SongList
from ui.search_bar import SearchBar
from ui.dialogs    import AddSongDialog

HOST = "127.0.0.1"
PORT = 7878


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SpotiCry")
        self.geometry("920x600")
        self.minsize(780, 480)
        self.configure(bg=BG)

        self.conn = ServerConnection(HOST, PORT)

        self._build_topbar()
        make_separator(self, color=DIVIDER).pack(fill="x")
        self._build_search_bar()
        make_separator(self, color=DIVIDER).pack(fill="x")
        self._build_catalog_header()
        self._build_song_list()
        make_separator(self, color=DIVIDER).pack(fill="x")
        self._build_action_bar()
        make_separator(self, color=DIVIDER).pack(fill="x")
        self._build_statusbar()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(120, self._auto_connect)

    # ── Topbar ────────────────────────────────────────────────────

    def _build_topbar(self):
        bar = tk.Frame(self, bg=BG2, pady=12)
        bar.pack(fill="x", side="top")

        # Logo
        logo_frame = tk.Frame(bar, bg=BG2)
        logo_frame.pack(side="left", padx=20)
        tk.Label(logo_frame, text="♫", bg=BG2, fg=HIGHLIGHT,
                 font=("Segoe UI", 18, "bold")).pack(side="left", padx=(0, 6))
        tk.Label(logo_frame, text="SpotiCry", bg=BG2, fg=FG,
                 font=("Segoe UI", 14, "bold")).pack(side="left")

        # Indicador de conexión (derecha)
        self._conn_dot = tk.Label(bar, text="●", bg=BG2, fg=WARNING,
                                  font=("Segoe UI", 10))
        self._conn_dot.pack(side="right", padx=(0, 4))
        self._conn_label = tk.Label(bar, text="Conectando…", bg=BG2, fg=FG_DIM,
                                    font=("Segoe UI", 9))
        self._conn_label.pack(side="right", padx=(16, 0))

    # ── Búsqueda ──────────────────────────────────────────────────

    def _build_search_bar(self):
        self._search_bar = SearchBar(self, on_search=self._do_search,
                                     on_clear=self._load_songs)
        self._search_bar.pack(fill="x")

    # ── Encabezado del catálogo ───────────────────────────────────

    def _build_catalog_header(self):
        header = tk.Frame(self, bg=BG, pady=8, padx=16)
        header.pack(fill="x")
        tk.Label(header, text="CATÁLOGO DE MÚSICA", bg=BG, fg=FG_MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        self._count_var = tk.StringVar(value="")
        tk.Label(header, textvariable=self._count_var, bg=BG, fg=FG_MUTED,
                 font=("Segoe UI", 8)).pack(side="right")

    # ── Tabla de canciones ────────────────────────────────────────

    def _build_song_list(self):
        self._song_list = SongList(self)
        self._song_list.pack(fill="both", expand=True, padx=0, pady=0)

    # ── Barra de acciones ─────────────────────────────────────────

    def _build_action_bar(self):
        bar = tk.Frame(self, bg=BG2, pady=10, padx=16)
        bar.pack(fill="x")

        make_button(bar, "+ Agregar canción", self._add_song,
                    color=SUCCESS, hover=SUCCESS_H, width=17).pack(side="left", padx=(0, 8))
        make_button(bar, "🗑  Eliminar canción", self._delete_song,
                    color="#2a1a1a", hover=ERROR_H, width=17).pack(side="left")
        make_button(bar, "⟳  Actualizar", self._load_songs,
                    color=ACCENT, width=14).pack(side="right")

    # ── Statusbar ─────────────────────────────────────────────────

    def _build_statusbar(self):
        self._status_var = tk.StringVar(value="Iniciando…")
        bar = tk.Frame(self, bg=BG2, pady=5)
        bar.pack(fill="x", side="bottom")
        tk.Label(bar, textvariable=self._status_var, bg=BG2, fg=FG_MUTED,
                 font=("Segoe UI", 8), anchor="w").pack(side="left", padx=14)

    # ── Conexión automática ───────────────────────────────────────

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

        # Ícono de error
        tk.Label(frame, text="⚠", bg=BG2, fg=WARNING,
                 font=("Segoe UI", 28)).pack(pady=(0, 10))
        tk.Label(frame, text="No se pudo conectar al servidor",
                 bg=BG2, fg=FG, font=("Segoe UI", 12, "bold")).pack()
        tk.Label(frame, text=err, bg=BG2, fg=FG_DIM,
                 font=("Segoe UI", 9), wraplength=300,
                 justify="center").pack(pady=(6, 24))

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

    # ── Carga y búsqueda ──────────────────────────────────────────

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

    # ── Agregar / Eliminar ────────────────────────────────────────

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
            msg = resp.get("message", "Error desconocido") if resp else "Sin respuesta"
            self.after(0, lambda: messagebox.showerror("Error al agregar", msg))

    def _delete_song(self):
        if not self._require_connection():
            return
        values = self._song_list.selected_values()
        if not values:
            messagebox.showinfo("Sin selección", "Selecciona una canción de la lista.")
            return
        song_id, song_name = int(values[0]), values[1]
        if not messagebox.askyesno("Eliminar canción",
                                   f'¿Eliminar "{song_name}"?\nEsta acción no se puede deshacer.'):
            return
        threading.Thread(target=self._delete_worker,
                         args=(song_id, song_name), daemon=True).start()

    def _delete_worker(self, song_id: int, song_name: str):
        resp, err = self.conn.send_command("DELETE_SONG", {"song_id": song_id})
        if err:
            self.after(0, lambda: messagebox.showerror("Error", err))
            return
        if resp and resp.get("status") == "ok":
            self.after(0, lambda: self._set_status(f'"{song_name}" eliminada del catálogo.'))
            self.after(0, self._load_songs)
        else:
            msg = resp.get("message", "Error desconocido") if resp else "Sin respuesta"
            self.after(0, lambda: messagebox.showerror("No se pudo eliminar", msg))

    # ── Helpers ───────────────────────────────────────────────────

    def _show_songs(self, songs: list, is_search: bool = False):
        self._song_list.populate(songs)
        total = len(songs)
        plural = "es" if total != 1 else ""
        self._count_var.set(f"{total} canción{plural}")
        if is_search:
            self._set_status(f"{total} resultado{'s' if total != 1 else ''} para la búsqueda.")
        else:
            self._set_status(f"Catálogo cargado — {total} canción{plural}.")

    def _set_status(self, text: str):
        self._status_var.set(text)

    def _require_connection(self) -> bool:
        if not self.conn.connected:
            messagebox.showinfo("Sin conexión", "El cliente no está conectado al servidor.")
            return False
        return True

    def _on_close(self):
        self.conn.disconnect()
        self.destroy()
