import math
import time
from functools import partial

import mss
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Qt, QEvent

from src.utils import Utils


class SettingsTab(QtWidgets.QTabWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QtWidgets.QVBoxLayout())


class SettingsCheckbox(QtWidgets.QCheckBox):
    def __init__(self, *args):
        super().__init__(*args)

    # Check if the checkbox is clicked and run the save function if so.
    # Not a fan of this method at all, should try and find some other way at some point
    # TODO: Try and find a better way of making every SettingsCheckbox run the same function on click
    # (Could just change it to a confirmation button...)
    def event(self, e: QEvent) -> bool:
        super().event(e)
        if isinstance(e, QtGui.QMouseEvent) and e.type() is e.Type.MouseButtonRelease:
            self.topLevelWidget().__getattribute__("utils").settings.save()
        return False


class ScreenshotCarouselButton(QtWidgets.QRadioButton):
    def __init__(self, value):
        super().__init__()

        self.value = value
        self.time = time.time()

        self.setFixedSize(18, 18)
        self.setText("")

        self.setToolTip(time.strftime("%H:%M:%S - %D"))

    def event(self, e: QEvent) -> bool:
        super().event(e)
        if isinstance(e, QtGui.QMouseEvent) and e.type() is e.Type.MouseButtonRelease:
            print("Button Pressed:", self.value)
        return False


class ScreenshotCarouselGroup(QtWidgets.QHBoxLayout):
    def __init__(self):
        super().__init__()

        self.__buttonList: list[ScreenshotCarouselButton] = []

        self.layout().addSpacerItem(QtWidgets.QSpacerItem(40, 0, QtWidgets.QSizePolicy.Policy.Expanding,
                                                          QtWidgets.QSizePolicy.Policy.Fixed))
        self.update_widget()
        self.layout().addSpacerItem(QtWidgets.QSpacerItem(40, 0, QtWidgets.QSizePolicy.Policy.Expanding,
                                                          QtWidgets.QSizePolicy.Policy.Fixed))

    def add_new_button(self):
        self.__buttonList.append(ScreenshotCarouselButton(len(self.__buttonList)))
        self.update_widget()
        self.set_checked(len(self.__buttonList) - 1)

    def update_widget(self):
        [self.layout().addWidget(b) for b in self.__buttonList]

    def set_checked(self, index):
        for i, b in enumerate(self.__buttonList):
            b.setChecked(True if i == index else False)


class HLine(QtWidgets.QFrame):
    def __init__(self):
        super(HLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)


class MainWindow(QtWidgets.QWidget):
    def __init__(self, utils: Utils = ...):
        super().__init__()

        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        self.clipboard = utils.clipboard

        self.utils = utils
        self.settingsObj = self.utils.settings

        self.settingsWidget = None

        self.screenshots = self.utils.capture_monitors()
        self.currentMonitor = 0

        self.setWindowTitle("Screpo")

        # TODO: Create an icon and set it as the tray icon here
        self.tray = QtWidgets.QSystemTrayIcon(self)
        # self.tray.setIcon(QtGui.QIcon(r""))

        self.tray_menu = QtWidgets.QMenu()
        self.tray_menu.addAction("Capture New Screenshot", self.update_screenshots)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction("Exit Screpo", self.close)

        self.tray.setContextMenu(self.tray_menu)
        self.tray.setVisible(True)

        self.imageAndButtons = QtWidgets.QVBoxLayout()

        self.imageHolder = QtWidgets.QLabel(self)
        self.imageHolder.setFixedSize(525, 525)

        self.imageSwitcher = ScreenshotCarouselGroup()

        self.imageAndButtons.addWidget(self.imageHolder)
        self.imageAndButtons.addWidget(QtWidgets.QLabel("History"))
        self.imageAndButtons.addWidget(HLine())
        self.imageAndButtons.addLayout(self.imageSwitcher)

        with mss.mss() as sct:
            self.windowOptions = {i: [f"{''.join(['Monitor ', str(i + 1) + ': ']) if len(sct.monitors[1:]) > 1 else ''}"
                                      f"Whole Monitor"] for i in range(len(sct.monitors[1:]))}
        self.windowSelector = QtWidgets.QComboBox(self)
        self.windowSelector.addItems(self.windowOptions[0])

        self.monitorButtonLayout = QtWidgets.QHBoxLayout()
        self.update_screenshots()

        self.imageButtonLayout = QtWidgets.QHBoxLayout()
        self.copyImageButton = QtWidgets.QToolButton(self)
        self.copyImageButton.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.copyImageButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum,
                                                                 QtWidgets.QSizePolicy.Policy.Maximum))
        self.copyImageButton.setMinimumSize(0, 24)
        self.copyImageButton.setText("Copy Image")
        self.copyImageButton.clicked.connect(self.copy_image)
        self.copyImageButton.setShortcut(QtGui.QKeySequence("Ctrl+C"))

        self.copyImageMenu = QtWidgets.QMenu(self)
        self.copyImageMenu.addAction(
            # TODO: Fix this icon for Windows (will likely require compiling a QRC file)
            QtGui.QIcon(r"../assets/icons/svg/discord-mark-white.svg"),
            "Copy for &Discord",
            self.copy_image_for_discord
        )
        self.copyImageButton.setMenu(self.copyImageMenu)

        self.saveImageButton = QtWidgets.QPushButton("Save Image")
        self.saveImageButton.clicked.connect(self.save_image)
        self.saveImageButton.setShortcut(QtGui.QKeySequence("Ctrl+S"))

        self.imageButtonLayout.addWidget(self.copyImageButton)
        self.imageButtonLayout.addWidget(self.saveImageButton)

        if len(self.screenshots) > 1:
            for mon in range(len(self.screenshots)):
                btn = QtWidgets.QPushButton(f"Monitor &{mon + 1}", self)
                btn.clicked.connect(partial(self.switch_screenshot, mon))

                self.monitorButtonLayout.layout().addWidget(btn)

        self.update_button_colours()

        self.bottomLayout = QtWidgets.QHBoxLayout()

        self.getScreenshotButton = QtWidgets.QPushButton("Get &New Screenshot", self)
        self.getScreenshotButton.clicked.connect(self.update_screenshots)

        self.settingsButton = QtWidgets.QPushButton("Open Settings Menu")
        self.settingsButton.clicked.connect(self.open_settings)
        self.settingsButton.setMaximumSize(24, 24)

        [self.bottomLayout.addWidget(w) for w in [self.getScreenshotButton, self.settingsButton]]

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addLayout(self.imageAndButtons)
        self.layout.addWidget(self.windowSelector)
        if len(self.screenshots) > 1: self.layout.addLayout(self.monitorButtonLayout)
        self.layout.addLayout(self.imageButtonLayout)
        self.layout.addLayout(self.bottomLayout)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self.settingsWidget:
            self.settingsWidget.close()

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
        if self.window().windowState() != Qt.WindowState.WindowMinimized:
            self.window().setWindowState(Qt.WindowState.WindowMinimized)
            time.sleep(.285)

        self.screenshots = self.utils.capture_monitors()
        self.window().setWindowState(Qt.WindowState.WindowActive)

        self.imageHolder.setPixmap(
            QtGui.QPixmap.fromImage(self.screenshots[self.currentMonitor].toqimage()).scaled(
                self.imageHolder.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))

        self.update_button_colours()
        self.imageSwitcher.add_new_button()

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
        if self.clipboard:
            self.clipboard.setImage(self.screenshots[self.currentMonitor].toqimage())
            print("Copy: Copied image to clipboard")
        else:
            print("Copy: Clipboard reference missing")

    def copy_image_for_discord(self):
        if self.clipboard:
            with self.screenshots[self.currentMonitor] as img:
                size = math.prod(img.size) / pow(10, 7)

                print(size)

                if size < 7.8:
                    self.copy_image()
                else:
                    for i in range(99, 0, -1):
                        resize = img.resize(tuple(v - (v // i) for v in img))
                        if math.prod(resize.size) / pow(10, 7) < 7.8:
                            self.clipboard.setImage(resize.toqimage())
                            print(f"Copy: Copied image to clipboard at a reduction of {100 - i}%")
                            break
        else:
            print("Copy: Clipboard reference missing")

    def save_image(self):
        filename, filter = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Screpo: Save Image As...",
            filter="PNG (*.png);;JPEG (*.jpg)",
        )

        if filename and filter:
            if filename == '' and filter == '':
                pass
            elif filename.endswith((".png", ".jpg")):
                self.screenshots[self.currentMonitor].save(filename)
                print(f"Save: Saved image to {filename}")
            elif filter in ["PNG", "JPEG"]:
                self.screenshots[self.currentMonitor].save(filename + filter.split("(")[1][1:-1])
                print(f"Save: Saved image to {filename + filter.split('(')[1][1:-1]}")

    def open_settings(self):
        if not self.settingsWidget:
            self.settingsWidget = SettingsWindow(self.utils)

        self.settingsWidget.setFixedSize(self.size().toTuple()[0] // 1.5, self.size().toTuple()[1] // 3)
        self.settingsWidget.move(self.pos())

        self.settingsWidget.show()


class SettingsWindow(QtWidgets.QWidget):
    def __init__(self, utils: Utils = ...):
        super().__init__()

        self.utils = utils
        self.settings = utils.settings

        self.setWindowTitle("Screpo Settings")

        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        self.tabs = QtWidgets.QTabWidget(self)

        self.tab_general = SettingsTab()

        self.tab_general__features_header = QtWidgets.QLabel("Features")

        self.tab_general__enable_opencv = SettingsCheckbox("Enable OpenCV features")
        self.tab_general__enable_opencv.setChecked(self.settings.values["general"]["features"]["enable_opencv"])
        self.tab_general__enable_opencv.clicked.connect(self.enable_opencv_features)

        self.tab_general.layout().addWidget(self.tab_general__features_header)
        self.tab_general.layout().addWidget(HLine())
        self.tab_general.layout().addWidget(self.tab_general__enable_opencv)
        self.tab_general.layout().addStretch(3)

        self.tab_opencv = SettingsTab()

        self.tabs.addTab(self.tab_general, "General")
        if self.tab_general__enable_opencv.isChecked():
            self.tabs.insertTab(1, self.tab_opencv, "OpenCV")

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.tabs)

    def enable_opencv_features(self, value):
        if value:
            self.tabs.insertTab(1, self.tab_opencv, "OpenCV")
            self.settings.values["general"]["features"]["enable_opencv"] = True
            print("Settings: Enabled OpenCV features")
        else:
            self.tabs.removeTab(self.tabs.indexOf(self.tab_opencv))
            self.settings.values["general"]["features"]["enable_opencv"] = False
            print("Settings: Disabled OpenCV features")
