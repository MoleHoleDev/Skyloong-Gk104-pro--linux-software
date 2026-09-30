#!/usr/bin/env python3
import sys
import os

# Ensure the current directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui_main import MainWindow
from theme import DARK_THEME


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("GK104 RGB Studio")
    app.setOrganizationName("Skyloong")
    app.setStyleSheet(DARK_THEME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
