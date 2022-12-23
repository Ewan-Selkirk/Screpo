import math
import time
from functools import partial

from PySide6 import QtGui
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QMessageBox, QSizePolicy, QSpacerItem, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
                               QTabWidget, QWidget, QFileDialog, QToolButton, QMenu, QComboBox, QSystemTrayIcon,
                               QStatusBar, QFrame, QMenuBar, QRadioButton, QSpinBox, QCheckBox, QLineEdit, QMainWindow,
                               QInputDialog)

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


class SettingsLineEdit(QHBoxLayout):
    def __init__(self, title, utils: Utils = ..., keys: tuple | list = ...):
        super().__init__()

        self.utils = utils
        self.tab, self.setting = keys

        self.title = QLabel(title)

        self.line = QLineEdit()
        self.line.setText(utils.settings.values[self.tab][self.setting] or "")
        self.line.editingFinished.connect(self.on_line_changed)

        self.layout().addWidget(self.title)
        self.layout().addSpacerItem(QSpacerItem(100, 0))
        self.layout().addWidget(self.line)

        [self.layout().setStretch(i, s) for i, s in enumerate([2, 1, 3])]

    def on_line_changed(self):
        print(f"{self.title.text()}: {self.line.text() if self.line.text() != '' else None}")
        self.utils.settings.values[self.tab][self.setting] = self.line.text()
        self.utils.settings.save()


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


class MainWindow(QMainWindow):
    def __init__(self, parent=None, utils: Utils = ...):
        super(MainWindow, self).__init__(parent)

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

        self.windowOptions = {i: [f"{''.join(['Monitor ', str(i + 1) + ': ']) if len(self.utils.monitors) > 1 else ''}"
                                  f"Whole Monitor"] for i in range(len(self.utils.monitors))}

        self.windowSelector = QComboBox(self)
        self.windowSelector.addItems(self.windowOptions[0])

        self.monitorButtonLayout = QHBoxLayout()
        self.update_screenshots()

        self.imageButtonLayout = QHBoxLayout()
        self.copyImageButton = QPushButton(self)
        self.copyImageButton.setText("Copy Image")
        self.copyImageButton.clicked.connect(self.copy_image)
        self.copyImageButton.setShortcut(QtGui.QKeySequence("Ctrl+C"))

        self.saveImageButton = QToolButton()
        self.saveImageButton.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.saveImageButton.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        self.saveImageButton.setMinimumSize(0, 24)
        self.saveImageButton.setText("Save Image")
        self.saveImageButton.clicked.connect(self.save_image)
        self.saveImageButton.setShortcut(QtGui.QKeySequence("Ctrl+S"))

        self.saveImageMenu = QMenu(self.saveImageButton)

        self.saveImageMenu.addAction(
            QIcon(r"../assets/icons/svg/discord-mark-white.svg"),
            "Send to Webhook",
            self.send_image_to_discord
        )
        self.saveImageMenu.addAction(
            QIcon(r"../assets/icons/svg/discord-mark-white.svg"),
            "Send to Webhook w/ Message",
            partial(self.send_image_to_discord, True)
        )

        for action in self.saveImageMenu.actions():
            action.setDisabled(not self.utils.settings.values["general"]["features"]["enable_discord"])

        self.saveImageButton.setMenu(self.saveImageMenu)

        self.imageButtonLayout.addWidget(self.copyImageButton)
        self.imageButtonLayout.addWidget(self.saveImageButton)

        if len(self.screenshots) > 1:
            for mon in range(len(self.screenshots)):
                btn = QPushButton(f"Monitor &{mon + 1}", self)
                btn.clicked.connect(partial(self.switch_screenshot, mon))

                self.monitorButtonLayout.layout().addWidget(btn)

        self.update_button_colours()

        self.getScreenshotButton = QPushButton("Get &New Screenshot", self)
        self.getScreenshotButton.clicked.connect(self.update_screenshots)
        self.getScreenshotButton.setMinimumSize(0, 56)
        self.getScreenshotButton.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.settingsButton = QPushButton("Open Settings Menu")
        self.settingsButton.clicked.connect(self.open_settings)
        self.settingsButton.setMaximumSize(24, 24)
        self.settingsButton.setToolTip("Settings")

        self.miscButton = QPushButton("Dunno atm")
        self.miscButton.setMaximumSize(24, 24)

        self.miscBottomButtons = QVBoxLayout()
        self.miscBottomButtons.addWidget(self.miscButton)
        self.miscBottomButtons.addWidget(self.settingsButton)

        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.addWidget(self.getScreenshotButton)
        self.bottomLayout.addLayout(self.miscBottomButtons)

        self.widget = QWidget(self)
        self.layout = QVBoxLayout(self.widget)
        self.layout.addLayout(self.imageAndButtons)
        self.layout.addWidget(self.windowSelector)
        if len(self.utils.monitors) > 1: self.layout.addLayout(self.monitorButtonLayout)
        self.layout.addLayout(self.imageButtonLayout)
        self.layout.addLayout(self.bottomLayout)

        self.setCentralWidget(self.widget)

    def update(self) -> None:
        super().update()

        for action in self.saveImageMenu.actions():
            action.setDisabled(not self.utils.settings.values["general"]["features"]["enable_discord"])

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

    def send_image_to_discord(self, message: str = None):
        if self.utils.discordRef:
            if not message:
                self.utils.discordRef.send_to_webhook(self.screenshots[self.currentMonitor])
            else:
                result, boolean = QInputDialog().getText(self, "Send Image to Webhook with Message",
                                                         "Message:", QLineEdit.EchoMode.Normal)

                if boolean:
                    self.utils.discordRef.send_to_webhook_with_message(self.screenshots[self.currentMonitor], result)

    def open_settings(self):
        if not self.settingsWidget:
            self.settingsWidget = SettingsWindow(self)

        self.settingsWidget.setFixedSize(self.size().toTuple()[0], self.size().toTuple()[1] // 2)

        self.settingsWidget.show()



class SettingsWindow(QMainWindow):
    def __init__(self, parent):
        super(SettingsWindow, self).__init__(parent)

        self.utils = self.topLevelWidget().parent().utils
        self.settings = self.utils.settings

        self.setWindowTitle("Screpo Settings")

        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        self.tabs = QTabWidget(self)

        self.tab_general = SettingsTab()

        self.tab_general__features_header = QLabel("Features")

        self.tab_general__enable_opencv = SettingsCheckbox("Enable OpenCV features")
        self.tab_general__enable_opencv.setChecked(self.settings.values["general"]["features"]["enable_opencv"])
        self.tab_general__enable_opencv.clicked.connect(self.enable_opencv_features)

        self.tab_general__enable_discord = SettingsCheckbox("Enable Discord features")
        self.tab_general__enable_discord.setChecked(self.settings.values["general"]["features"]["enable_discord"])
        self.tab_general__enable_discord.clicked.connect(self.enable_discord_features)

        self.tab_general__performance_header = QLabel("Performance")

        self.tab_general__max_history_items = SettingsSpinBox("Max History Items", self.utils,
                                                              ("general", "performance", "history_max_items"))
        self.tab_general__max_history_items.spinBox.valueChanged.connect(
            partial(self.change_spinbox_value, self.tab_general__max_history_items.keys))

        self.tab_general.layout().addWidget(self.tab_general__features_header)
        self.tab_general.layout().addWidget(HLine())
        self.tab_general.layout().addWidget(self.tab_general__enable_opencv)
        self.tab_general.layout().addWidget(self.tab_general__enable_discord)
        self.tab_general.layout().addSpacerItem(CategorySpacer())
        self.tab_general.layout().addWidget(self.tab_general__performance_header)
        self.tab_general.layout().addWidget(HLine())
        self.tab_general.layout().addLayout(self.tab_general__max_history_items)
        self.tab_general.layout().addStretch(3)

        self.tab_opencv = SettingsTab()

        self.tab_discord = SettingsTab()

        self.tab_discord__username = SettingsLineEdit("Username to use", self.utils, ("discord", "username"))
        self.tab_discord__webhook = SettingsLineEdit("Webhook URL", self.utils, ("discord", "webhook_url"))

        [self.tab_discord.layout().addLayout(l) for l in [self.tab_discord__username, self.tab_discord__webhook]]
        self.tab_discord.layout().addStretch(3)

        self.tabs.addTab(self.tab_general, "General")
        if self.tab_general__enable_opencv.isChecked():
            self.tabs.insertTab(1, self.tab_opencv, "OpenCV")

        if self.tab_general__enable_discord.isChecked():
            self.tabs.insertTab(2, self.tab_discord, "Discord")

        self.footer = QHBoxLayout()
        self.footer.addSpacerItem(QSpacerItem(100, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        self.footer.addWidget(QLabel(f"Version {self.utils.version} ({self.utils.build}) "
                                     f"[{self.utils.app_ref.platformName()}]"))

        self.widget = QWidget(self)
        self.layout = QVBoxLayout(self.widget)
        self.layout.addWidget(self.tabs)
        self.layout.addLayout(self.footer)

        self.setCentralWidget(self.widget)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.topLevelWidget().parent().update()
        super().closeEvent(event)

    def enable_opencv_features(self, value):
        if value:
            self.tabs.insertTab(1, self.tab_opencv, "OpenCV")
            self.settings.values["general"]["features"]["enable_opencv"] = True
            print("Settings: Enabled OpenCV features")
        else:
            self.tabs.removeTab(self.tabs.indexOf(self.tab_opencv))
            self.settings.values["general"]["features"]["enable_opencv"] = False
            print("Settings: Disabled OpenCV features")

    def enable_discord_features(self, value):
        self.settings.values["general"]["features"]["enable_discord"] = value

        if value:
            self.tabs.insertTab(2, self.tab_discord, "Discord")
            self.utils.check_refs()
            print("Settings: Enabled Discord features")
        else:
            self.tabs.removeTab(self.tabs.indexOf(self.tab_discord))
            print("Settings: Disabled Discord features")

    def change_spinbox_value(self, keys: tuple | list, value):
        self.settings.values[keys[0]][keys[1]][keys[2]] = value
        self.settings.save()
