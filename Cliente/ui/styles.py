"""
Paleta de colores y funciones de fábrica para widgets estilizados.
"""

import tkinter as tk

# Colores
BG        = "#1a1a2e"
BG2       = "#16213e"
ACCENT    = "#0f3460"
HIGHLIGHT = "#e94560"
FG        = "#eaeaea"
FG_DIM    = "#8a8a9a"
ENTRY_BG  = "#0f3460"
SUCCESS   = "#4caf50"
WARNING   = "#ff9800"
ERROR     = "#f44336"


def make_button(parent, text, command, color=HIGHLIGHT, width=16):
    return tk.Button(
        parent, text=text, command=command,
        bg=color, fg=FG, activebackground=color, activeforeground=FG,
        relief="flat", cursor="hand2", font=("Segoe UI", 9, "bold"),
        width=width, pady=4,
    )


def make_entry(parent, textvariable=None, width=20):
    return tk.Entry(
        parent, textvariable=textvariable,
        bg=ENTRY_BG, fg=FG, insertbackground=FG,
        relief="flat", font=("Segoe UI", 10),
        width=width,
    )


def make_label(parent, text="", color=FG, size=9, bold=False, **kw):
    font = ("Segoe UI", size, "bold") if bold else ("Segoe UI", size)
    return tk.Label(parent, text=text, bg=parent["bg"], fg=color, font=font, **kw)
