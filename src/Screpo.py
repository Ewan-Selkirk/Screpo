import sys

from PySide6 import QtWidgets
from PySide6.QtCore import QPoint

import widgets as widgets
from utils import Utils

width, height = (550, 710)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    clipboard = app.clipboard()

    utils = Utils(app)
    if len(utils.monitors) > 1:
        height += 45

    window = widgets.MainWindow(utils=utils)
    window.setFixedSize(width, height)
    window.move(app.primaryScreen().availableGeometry().bottomRight() - QPoint(width, height))

    app.setStyleSheet(utils.generate_stylesheet())

    # Account for the taskbar on Windows
    if app.platformName() == "windows":
        window.move(window.pos() - QPoint(0, 32))

    window.show()

    sys.exit(app.exec())
