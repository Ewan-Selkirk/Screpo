import sys

from PySide6 import QtWidgets
from PySide6.QtCore import (Qt, QPoint)

import src.widgets as widgets

width, height = (550, 675)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    clipboard = app.clipboard()

    window = widgets.MainWindow(clipboard)
    settings = widgets.SettingsWindow()

    window.setFixedSize(width, height)
    window.move(app.primaryScreen().availableGeometry().bottomRight() - QPoint(width, height))

    settings.setFixedSize(width, height // 3)
    settings.move(window.pos())

    # Account for the taskbar on Windows
    if app.platformName() == "windows":
        window.move(window.pos() - QPoint(0, 32))

    window.show()

    sys.exit(app.exec())
