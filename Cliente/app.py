"""
SpotiCry — Punto de entrada del cliente GUI.
Ejecutar desde la carpeta Cliente/: py app.py
"""

import sys
import os

# Asegura que los módulos locales (connection, ui/) sean encontrados
sys.path.insert(0, os.path.dirname(__file__))

from ui.main_window import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()

