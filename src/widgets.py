import math
import time
from functools import partial

import mss
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import (QMessageBox, QSizePolicy, QSpacerItem, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
                               QTabWidget, QWidget, QFileDialog, QToolButton, QMenu, QComboBox, QSystemTrayIcon,
                               QStatusBar, QFrame, QMenuBar, QRadioButton, QSpinBox, QCheckBox)

from src.utils import *


class SettingsTab(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())


class SettingsCheckbox(QCheckBox):
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


class SettingsSpinBox(QHBoxLayout):
    def __init__(self, title: str = ..., utils: Utils = ..., keys: tuple | list = ...):
        super().__init__()

        self.keys = keys
        tab, category, option = keys

        self.title = QLabel(title)
        self.spinBox = QSpinBox()

        self.spinBox.setMinimum(1)
        self.spinBox.setValue(utils.settings.values[tab][category][option])
        self.spinBox.setMinimumWidth(80)

        self.layout().addWidget(self.title)
        self.layout().addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        self.layout().addWidget(self.spinBox)


class ScreenshotCarouselButton(QRadioButton):
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
            print(f"Button Pressed: {self.value}")
            self.parentWidget().topLevelWidget().goto_in_history(self.value)
        return False


class ScreenshotCarouselGroup(QHBoxLayout):
    def __init__(self):
        super().__init__()

        self.__buttonList: list[ScreenshotCarouselButton] = []
        self.__buttonIndex = 0

        self.layout().addSpacerItem(QSpacerItem(40, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        self.update_widget()
        self.layout().addSpacerItem(QSpacerItem(40, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))

    def add_new_button(self, max_btns):
        self.__buttonList.append(ScreenshotCarouselButton(self.__buttonIndex))
        self.__buttonIndex += 1

        if len(self.__buttonList) > max_btns:
            self.layout().removeWidget(self.__buttonList[0])
            del self.__buttonList[0]
        self.update_widget()
        self.set_checked(len(self.__buttonList) - 1)

    def update_widget(self):
        [self.layout().addWidget(b) for b in self.__buttonList]

    def set_checked(self, index):
        for i, b in enumerate(self.__buttonList):
            b.setChecked(True if i == index else False)


class HLine(QFrame):
    def __init__(self):
        super(HLine, self).__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)


class CategorySpacer(QtWidgets.QSpacerItem):
    def __init__(self):
        super().__init__(0, 24, QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)


class MainWindow(QWidget):
    def __init__(self, utils: Utils = ...):
        super().__init__()

        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        self.clipboard = utils.clipboard

        self.utils = utils
        self.settingsObj = self.utils.settings

        self.settingsWidget = None

        self.screenshots = []
        self.currentMonitor = 0

        self.setWindowTitle("Screpo")

        # TODO: Create an icon and set it as the tray icon here
        self.tray = QSystemTrayIcon(self)
        # self.tray.setIcon(QtGui.QIcon(r""))

        self.tray_menu = QMenu()
        self.tray_menu.addAction("Capture New Screenshot", self.update_screenshots)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction("Exit Screpo", self.close)

        self.tray.setContextMenu(self.tray_menu)
        self.tray.setVisible(True)

        self.imageAndButtons = QVBoxLayout()

        self.imageHolder = QLabel(self)
        self.imageHolder.setFixedSize(525, 525)

        self.imageSwitcher = ScreenshotCarouselGroup()

        self.imageAndButtons.addWidget(self.imageHolder)
        self.imageAndButtons.addWidget(QLabel("History"))
        self.imageAndButtons.addWidget(HLine())
        self.imageAndButtons.addLayout(self.imageSwitcher)

        with mss.mss() as sct:
            self.windowOptions = {i: [f"{''.join(['Monitor ', str(i + 1) + ': ']) if len(sct.monitors[1:]) > 1 else ''}"
                                      f"Whole Monitor"] for i in range(len(sct.monitors[1:]))}
        self.windowSelector = QComboBox(self)
        self.windowSelector.addItems(self.windowOptions[0])

        self.monitorButtonLayout = QHBoxLayout()
        self.update_screenshots()

        self.imageButtonLayout = QHBoxLayout()
        self.copyImageButton = QToolButton(self)
        self.copyImageButton.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.copyImageButton.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))
        self.copyImageButton.setMinimumSize(0, 24)
        self.copyImageButton.setText("Copy Image")
        self.copyImageButton.clicked.connect(self.copy_image)
        self.copyImageButton.setShortcut(QtGui.QKeySequence("Ctrl+C"))

        self.copyImageMenu = QMenu(self)
        self.copyImageMenu.addAction(
            # TODO: Fix this icon for Windows (will likely require compiling a QRC file)
            QtGui.QIcon(r"../assets/icons/svg/discord-mark-white.svg"),
            "Copy for &Discord",
            self.copy_image_for_discord
        )
        self.copyImageButton.setMenu(self.copyImageMenu)

        self.saveImageButton = QPushButton("Save Image")
        self.saveImageButton.clicked.connect(self.save_image)
        self.saveImageButton.setShortcut(QtGui.QKeySequence("Ctrl+S"))

        self.imageButtonLayout.addWidget(self.copyImageButton)
        self.imageButtonLayout.addWidget(self.saveImageButton)

        if len(self.screenshots) > 1:
            for mon in range(len(self.screenshots)):
                btn = QPushButton(f"Monitor &{mon + 1}", self)
                btn.clicked.connect(partial(self.switch_screenshot, mon))

                self.monitorButtonLayout.layout().addWidget(btn)

        self.update_button_colours()

        self.bottomLayout = QHBoxLayout()

        self.getScreenshotButton = QPushButton("Get &New Screenshot", self)
        self.getScreenshotButton.clicked.connect(self.update_screenshots)

        self.settingsButton = QPushButton("Open Settings Menu")
        self.settingsButton.clicked.connect(self.open_settings)
        self.settingsButton.setMaximumSize(24, 24)

        [self.bottomLayout.addWidget(w) for w in [self.getScreenshotButton, self.settingsButton]]

        self.layout = QVBoxLayout(self)
        self.layout.addLayout(self.imageAndButtons)
        self.layout.addWidget(self.windowSelector)
        if len(self.utils.monitors) > 1: self.layout.addLayout(self.monitorButtonLayout)
        self.layout.addLayout(self.imageButtonLayout)
        self.layout.addLayout(self.bottomLayout)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self.settingsWidget:
            self.settingsWidget.close()

    def update_current_screenshot(self):
        self.imageHolder.setPixmap(
            image_to_pixmap(self.screenshots[self.currentMonitor], self.imageHolder)
        )

    def switch_screenshot(self, mon):
        self.currentMonitor = mon
        self.update_current_screenshot()

        self.windowSelector.clear()
        self.windowSelector.addItems(self.windowOptions[mon])

        self.update_button_colours()

    def update_screenshots(self):
        if self.window().windowState() != Qt.WindowState.WindowMinimized:
            self.window().setWindowState(Qt.WindowState.WindowMinimized)
            time.sleep(.285)

        self.screenshots = self.utils.capture_monitors()
        self.window().setWindowState(Qt.WindowState.WindowActive)

        self.update_current_screenshot()

        self.update_button_colours()
        self.imageSwitcher.add_new_button(self.utils.settings.values["general"]["performance"]["history_max_items"])

    def goto_in_history(self, pos):
        self.screenshots = self.utils.history[pos].copy()
        self.update_current_screenshot()

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
        filename, filter = QFileDialog.getSaveFileName(
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

        self.settingsWidget.setFixedSize(self.size().toTuple()[0], self.size().toTuple()[1] // 2)
        self.settingsWidget.move(self.pos())

        self.settingsWidget.show()



class SettingsWindow(QWidget):
    def __init__(self, utils: Utils = ...):
        super().__init__()

        self.utils = utils
        self.settings = utils.settings

        self.setWindowTitle("Screpo Settings")

        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        self.tabs = QTabWidget(self)

        self.tab_general = SettingsTab()

        self.tab_general__features_header = QLabel("Features")

        self.tab_general__enable_opencv = SettingsCheckbox("Enable OpenCV features")
        self.tab_general__enable_opencv.setChecked(self.settings.values["general"]["features"]["enable_opencv"])
        self.tab_general__enable_opencv.clicked.connect(self.enable_opencv_features)

        self.tab_general__performance_header = QLabel("Performance")

        self.tab_general__max_history_items = SettingsSpinBox("Max History Items", self.utils,
                                                              ("general", "performance", "history_max_items"))
        self.tab_general__max_history_items.spinBox.valueChanged.connect(
            partial(self.change_spinbox_value, self.tab_general__max_history_items.keys))

        self.tab_general.layout().addWidget(self.tab_general__features_header)
        self.tab_general.layout().addWidget(HLine())
        self.tab_general.layout().addWidget(self.tab_general__enable_opencv)
        self.tab_general.layout().addSpacerItem(CategorySpacer())
        self.tab_general.layout().addWidget(self.tab_general__performance_header)
        self.tab_general.layout().addWidget(HLine())
        self.tab_general.layout().addLayout(self.tab_general__max_history_items)
        self.tab_general.layout().addStretch(3)

        self.tab_opencv = SettingsTab()

        self.tabs.addTab(self.tab_general, "General")
        if self.tab_general__enable_opencv.isChecked():
            self.tabs.insertTab(1, self.tab_opencv, "OpenCV")

        self.footer = QHBoxLayout()
        self.footer.addSpacerItem(QSpacerItem(100, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        self.footer.addWidget(QLabel(f"Version {utils.version} ({utils.build}) [{utils.app_ref.platformName()}]"))

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tabs)
        self.layout.addLayout(self.footer)

    def enable_opencv_features(self, value):
        if value:
            self.tabs.insertTab(1, self.tab_opencv, "OpenCV")
            self.settings.values["general"]["features"]["enable_opencv"] = True
            print("Settings: Enabled OpenCV features")
        else:
            self.tabs.removeTab(self.tabs.indexOf(self.tab_opencv))
            self.settings.values["general"]["features"]["enable_opencv"] = False
            print("Settings: Disabled OpenCV features")

    def change_spinbox_value(self, keys: tuple | list, value):
        self.settings.values[keys[0]][keys[1]][keys[2]] = value
        self.settings.save()
