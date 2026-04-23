"""
Paleta de colores y funciones de fábrica para widgets estilizados.
"""

import tkinter as tk

# ── Colores ───────────────────────────────────────────────────────────────────
BG        = "#12121f"   # fondo principal (más oscuro)
BG2       = "#1a1a2e"   # topbar / statusbar
BG3       = "#1e2040"   # paneles interiores
ACCENT    = "#0f3460"   # filas alternas, fondos secundarios
HIGHLIGHT = "#e94560"   # acento principal (rojo-rosa)
HIGHLIGHT2= "#c73652"   # hover del acento
FG        = "#eaeaea"   # texto principal
FG_DIM    = "#7a7a9a"   # texto secundario
FG_MUTED  = "#4a4a6a"   # texto muy atenuado (empty state)
BORDER    = "#2a2a4a"   # bordes de entradas
ENTRY_BG  = "#1e2040"   # fondo de entradas
SUCCESS   = "#4caf50"
SUCCESS_H = "#3d9142"   # hover de success
WARNING   = "#ff9800"
ERROR     = "#f44336"
ERROR_H   = "#d32f2f"   # hover de error
DIVIDER   = "#252545"   # líneas separadoras


# ── Widgets ───────────────────────────────────────────────────────────────────

def make_button(parent, text, command, color=HIGHLIGHT, hover=None, width=16):
    """Botón plano con efecto hover."""
    hover_color = hover or _darken(color)
    btn = tk.Button(
        parent, text=text, command=command,
        bg=color, fg=FG,
        activebackground=hover_color, activeforeground=FG,
        relief="flat", cursor="hand2",
        font=("Segoe UI", 9, "bold"),
        width=width, pady=5, padx=4,
        borderwidth=0, highlightthickness=0,
    )
    btn.bind("<Enter>", lambda _: btn.config(bg=hover_color))
    btn.bind("<Leave>", lambda _: btn.config(bg=color))
    return btn


def make_bordered_entry(parent, textvariable=None, width=20, placeholder=""):
    """Entry envuelto en un frame que actúa como borde de color."""
    wrap = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
    entry = tk.Entry(
        wrap, textvariable=textvariable,
        bg=ENTRY_BG, fg=FG, insertbackground=FG,
        relief="flat", font=("Segoe UI", 10),
        width=width,
        borderwidth=4, highlightthickness=0,
    )
    entry.pack(fill="both")

    # Highlight al enfocar
    def _focus_in(_):
        wrap.config(bg=HIGHLIGHT)
    def _focus_out(_):
        wrap.config(bg=BORDER)
    entry.bind("<FocusIn>",  _focus_in)
    entry.bind("<FocusOut>", _focus_out)

    wrap.entry = entry   # acceso directo al widget real
    return wrap


def make_separator(parent, color=DIVIDER):
    return tk.Frame(parent, bg=color, height=1)


def make_label(parent, text="", color=FG, size=9, bold=False, **kw):
    font = ("Segoe UI", size, "bold") if bold else ("Segoe UI", size)
    return tk.Label(parent, text=text, bg=parent["bg"], fg=color, font=font, **kw)


# ── Helpers privados ──────────────────────────────────────────────────────────

_HOVER_MAP = {
    SUCCESS: SUCCESS_H,
    ERROR:   ERROR_H,
    HIGHLIGHT: HIGHLIGHT2,
}

def _darken(color: str) -> str:
    """Retorna el color de hover registrado, o el mismo color si no hay uno."""
    return _HOVER_MAP.get(color, color)
