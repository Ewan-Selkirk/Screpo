import sys
import time
from functools import partial

import mss
from PIL import Image
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import (Qt, QPoint)

width, height = (550, 675)


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.screenshots = captureMonitors()
        self.currentMonitor = 0

        self.setWindowTitle("Screpo")
        self.title = QtWidgets.QLabel("Screpo", self)
        self.title.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self.tray = QtWidgets.QSystemTrayIcon()
        self.tray.setVisible(True)

        self.imageHolder = QtWidgets.QLabel(self)
        self.imageHolder.setMinimumSize(525, 525)
        self.imageHolder.setMaximumSize(525, 525)

        with mss.mss() as sct:
            self.windowOptions = {i: [f"{''.join(['Monitor ', str(i + 1) + ': ']) if len(sct.monitors[1:]) > 1 else ''}"
                                      f"Whole Monitor"] for i in range(len(sct.monitors[1:]))}
        self.windowSelector = QtWidgets.QComboBox(self)
        self.windowSelector.addItems(self.windowOptions[0])

        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.updateScreenshots()

        if len(self.screenshots) > 1:
            for mon in range(len(self.screenshots)):
                btn = QtWidgets.QPushButton(f"Monitor &{mon + 1}", self)
                btn.clicked.connect(partial(self.switch_screenshot, mon))

                self.buttonLayout.layout().addWidget(btn)

        self.getScreenshotButton = QtWidgets.QPushButton("Get &New Screenshot", self)
        self.getScreenshotButton.clicked.connect(self.updateScreenshots)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.imageHolder, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.layout.addWidget(self.windowSelector)
        if len(self.screenshots) > 1: self.layout.addLayout(self.buttonLayout)
        self.layout.addWidget(self.getScreenshotButton)

    def switch_screenshot(self, mon):
        self.currentMonitor = mon
        self.imageHolder.setPixmap(QtGui.QPixmap.fromImage(self.screenshots[mon].toqimage()).scaled(
            self.imageHolder.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

        self.windowSelector.clear()
        self.windowSelector.addItems(self.windowOptions[mon])

        self.updateButtonColours()

    def updateScreenshots(self):
        self.window().setWindowState(Qt.WindowState.WindowMinimized)
        time.sleep(.25)
        self.screenshots = captureMonitors()
        self.window().setWindowState(Qt.WindowState.WindowActive)

        self.imageHolder.setPixmap(QtGui.QPixmap.fromImage(self.screenshots[self.currentMonitor].toqimage()).scaled(
            self.imageHolder.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

        self.updateButtonColours()

    def updateButtonColours(self):
        if len(self.screenshots) > 1:
            for i, btn in enumerate([self.buttonLayout.itemAt(i) for i in range(self.buttonLayout.count())]):
                btn = btn.widget()

                if i == self.currentMonitor:
                    btn.setStyleSheet("QPushButton { background-color: rgb(85, 255, 127); }")
                else:
                    btn.setStyleSheet("")


def captureMonitors() -> list[Image]:
    shots = []

    with mss.mss() as sct:
        for mon in sct.monitors[1:]:
            shot = sct.grab(mon)
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

            shots.append(img)

    return shots


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    window = MainWindow()

    window.setMinimumSize(width, height)
    window.setMaximumSize(width, height)
    window.move(app.primaryScreen().availableGeometry().bottomRight() - QPoint(width, height) - QPoint(0, 32))
    window.show()

    sys.exit(app.exec())
