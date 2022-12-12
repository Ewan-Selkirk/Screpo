import sys
import time
from functools import partial

import mss
from PIL import Image
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import (Qt, QPoint)

width, height = (550, 675)
app = None
clipboard = None


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.screenshots = capture_monitors()
        self.currentMonitor = 0

        self.setWindowTitle("Screpo")

        self.tray = QtWidgets.QSystemTrayIcon()
        self.tray.setVisible(True)

        self.imageHolder = QtWidgets.QLabel(self)
        self.imageHolder.setFixedSize(525, 525)

        with mss.mss() as sct:
            self.windowOptions = {i: [f"{''.join(['Monitor ', str(i + 1) + ': ']) if len(sct.monitors[1:]) > 1 else ''}"
                                      f"Whole Monitor"] for i in range(len(sct.monitors[1:]))}
        self.windowSelector = QtWidgets.QComboBox(self)
        self.windowSelector.addItems(self.windowOptions[0])

        self.monitorButtonLayout = QtWidgets.QHBoxLayout()
        self.update_screenshots()

        self.imageButtonLayout = QtWidgets.QHBoxLayout()
        self.copyImageButton = QtWidgets.QPushButton("Copy Image")
        self.copyImageButton.clicked.connect(self.copy_image)
        self.saveImageButton = QtWidgets.QPushButton("Save Image")
        self.saveImageButton.clicked.connect(self.save_image)

        self.imageButtonLayout.addWidget(self.copyImageButton)
        self.imageButtonLayout.addWidget(self.saveImageButton)

        if len(self.screenshots) > 1:
            for mon in range(len(self.screenshots)):
                btn = QtWidgets.QPushButton(f"Monitor &{mon + 1}", self)
                btn.clicked.connect(partial(self.switch_screenshot, mon))

                self.monitorButtonLayout.layout().addWidget(btn)

        self.update_button_colours()

        self.getScreenshotButton = QtWidgets.QPushButton("Get &New Screenshot", self)
        self.getScreenshotButton.clicked.connect(self.update_screenshots)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.imageHolder, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.layout.addWidget(self.windowSelector)
        if len(self.screenshots) > 1: self.layout.addLayout(self.monitorButtonLayout)
        self.layout.addLayout(self.imageButtonLayout)
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

        self.update_button_colours()

    def update_screenshots(self):
        self.window().setWindowState(Qt.WindowState.WindowMinimized)
        time.sleep(.25)
        self.screenshots = capture_monitors()
        self.window().setWindowState(Qt.WindowState.WindowActive)

        self.imageHolder.setPixmap(QtGui.QPixmap.fromImage(self.screenshots[self.currentMonitor].toqimage()).scaled(
            self.imageHolder.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

        self.update_button_colours()

    def update_button_colours(self):
        if len(self.screenshots) > 1:
            for i, btn in enumerate([self.monitorButtonLayout.itemAt(i)
                                     for i in range(self.monitorButtonLayout.count())]):
                btn = btn.widget()

                if i == self.currentMonitor:
                    btn.setStyleSheet("QPushButton { background-color: rgb(85, 255, 127); }")
                else:
                    btn.setStyleSheet("")

    def copy_image(self):
        clipboard.setImage(self.screenshots[self.currentMonitor].toqimage())
        print("Copy: Copied image to clipboard")

    def save_image(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Screpo: Save Image As...",
            filter="PNG (*.png);;JPEG (*.jpg)",
        )

        if filename:
            if filename == ('', ''):
                pass
            elif filename[0].endswith(".png" or ".jpg"):
                self.screenshots[self.currentMonitor].save(filename[0])
            elif "PNG" in filename[1] or "JPEG" in filename[1]:
                self.screenshots[self.currentMonitor].save(filename[0]
                                                           + filename[1].split("(")[1][1:-1])


def capture_monitors() -> list[Image]:
    shots = []

    with mss.mss() as sct:
        for mon in sct.monitors[1:]:
            shot = sct.grab(mon)
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

            shots.append(img)

    return shots


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    clipboard = app.clipboard()

    window = MainWindow()

    window.setFixedSize(width, height)
    window.move(app.primaryScreen().availableGeometry().bottomRight() - QPoint(width, height))
    window.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

    # Account for the taskbar on Windows
    if app.platformName() == "windows":
        window.move(window.pos() - QPoint(0, 32))

    window.show()

    sys.exit(app.exec())
