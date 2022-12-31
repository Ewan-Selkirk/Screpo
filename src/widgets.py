import time
from functools import partial

from PySide6 import QtGui
from PySide6.QtCore import Qt, QEvent, QObject
from PySide6.QtWidgets import (QMessageBox, QSizePolicy, QSpacerItem, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
                               QTabWidget, QWidget, QFileDialog, QToolButton, QMenu, QComboBox, QSystemTrayIcon,
                               QFrame, QRadioButton, QSpinBox, QCheckBox, QLineEdit, QMainWindow, QListWidget,
                               QListWidgetItem, QDialogButtonBox)

from src.utils import *


class SettingsTab(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())


class SettingsCheckbox(QCheckBox):
    def __init__(self, *args):
        super().__init__(*args)

        self.installEventFilter(self)

    # Check if the checkbox is clicked and run the save function if so.
    # Not a fan of this method at all, should try and find some other way at some point
    # TODO: Try and find a better way of making every SettingsCheckbox run the same function on click
    # (Could just change it to a confirmation button...)
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        super().eventFilter(watched, event)

        if event.type() is event.Type.MouseButtonRelease:
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


class ListEditor(QWidget):
    def __init__(self, utils: Utils = ...):
        super().__init__()
        self.values = []

        self.utils = utils

        self.setLayout(QHBoxLayout())

        self.list = QListWidget()
        self.list.currentItemChanged.connect(self.on_selection_changed)
        self.list.itemDoubleClicked.connect(self.on_double_clicked)
        self.list.itemSelectionChanged.connect(self.on_empty_selection)

        for webhook in utils.settings.values["discord"]["webhooks"]:
            self.list.addItem(webhook.name + f" [{webhook.url}]")

        self.buttonGroup = QVBoxLayout()

        self.addButton = QPushButton("Add Webhook")
        self.addButton.clicked.connect(self.add_new_webhook)

        self.editButton = QPushButton("Edit Webhook")
        self.editButton.clicked.connect(self.edit_webhook)

        self.deleteButton = QPushButton("Delete Webhook")
        self.deleteButton.clicked.connect(self.delete_webhook)

        self.moveUpButton = QPushButton("Move Up")
        self.moveUpButton.clicked.connect(partial(self.move_webhook, True))

        self.moveDownButton = QPushButton("Move Down")
        self.moveDownButton.clicked.connect(self.move_webhook)

        self.buttons = [self.addButton, self.editButton, self.deleteButton, self.moveUpButton, self.moveDownButton]
        [b.setDisabled(True) for b in self.buttons[1:]]

        [self.buttonGroup.addWidget(w) for w in self.buttons]

        self.layout().addWidget(self.list)
        self.layout().addLayout(self.buttonGroup)

    def add_new_webhook(self):
        editor = WebhookEditor(self)
        editor.show()

    def edit_webhook(self):
        hook = self.utils.settings.values["discord"]["webhooks"][self.list.indexFromItem(
            self.list.selectedItems()[0]
        ).row()]

        editor = WebhookEditor(self, hook, self.list.selectedItems()[0])
        editor.show()

    def delete_webhook(self):
        confirmation = QMessageBox.information(self, "Delete Webhook", "Are you sure you want to delete the selected"
                                                                       " url?\nThis cannot be undone.",
                                               QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)

        if confirmation == QMessageBox.StandardButton.Ok:
            del self.utils.settings.values["discord"]["webhooks"][self.list.selectedIndexes()[0].row()]
            self.list.takeItem(self.list.indexFromItem(self.list.selectedItems()[0]).row())

    def move_webhook(self, up: bool = False):
        # index = self.list.selectedIndexes()[0].row() + (-1 if up else 1)
        # old_hook = self.utils.settings.values["discord"]["webhooks"][index]
        # old_text = self.list.itemAt(0, index).text()
        #
        # self.utils.settings.values["discord"]["webhooks"][index] = \
        #     self.utils.settings.values["discord"]["webhooks"][index + (1 if up else -1)]
        #
        # self.utils.settings.values["discord"]["webhooks"][index + (-1 if up else 1)] = old_hook
        #
        # self.list.item(index).setText(self.list.item(self.list.selectedIndexes()[0].row()).text())
        # self.list.item(self.list.selectedIndexes()[0].row()).setText(old_text)
        #
        # print(old_text, old_hook)

        print(f"Webhooks: Moved webhook {'up' if up else 'down'} the list")

    def on_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        [b.setDisabled(True if current is None else False) for b in self.buttons[1:3]]

        self.buttons[3].setDisabled(False if self.list.indexFromItem(current).row() != 0 else True)
        self.buttons[4].setDisabled(False if self.list.indexFromItem(current).row() != self.list.count() - 1 else True)

    def on_double_clicked(self, item: QListWidgetItem):
        self.edit_webhook()
        print("Double Clicked", item.text())

    def on_empty_selection(self):
        if len(self.list.selectedItems()) == 0:
            self.list.setCurrentItem(None)
            [b.setDisabled(True) for b in self.buttons[1:]]


class WebhookEditor(QMainWindow):
    def __init__(self, parent, webhook=None, listItem: QListWidgetItem = None):
        super(WebhookEditor, self).__init__(parent)

        self.setWindowTitle("Add New Webhook")
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setBaseSize(parent.size())

        self.webhook = webhook
        self.listItem = listItem

        self.widget = QWidget()
        self.layout = QVBoxLayout()

        self.widget.setLayout(self.layout)

        self.layout.addWidget(QLabel("Webhook Name*"))

        self.name = QLineEdit()
        self.name.setText(webhook.name) if webhook else ...
        self.layout.addWidget(self.name)

        self.layout.addWidget(QLabel("Webhook URL*"))

        self.url = QLineEdit()
        self.url.setText(webhook.url) if webhook else ...
        self.layout.addWidget(self.url)

        self.layout.addWidget(QLabel("Username to use"))

        self.username = QLineEdit()
        self.username.setText(webhook.username) if webhook else ...
        self.layout.addWidget(self.username)

        self.layout.addWidget(QLabel("(Leave blank to use the globally set username)"))

        self.dialogButtons = QDialogButtonBox(self.widget)
        self.dialogButtons.setStandardButtons(QDialogButtonBox.StandardButton.Ok |
                                              QDialogButtonBox.StandardButton.Cancel)

        self.dialogButtons.accepted.connect(self.on_accepted)
        self.dialogButtons.rejected.connect(self.on_rejected)
        self.layout.addWidget(self.dialogButtons)

        self.setCentralWidget(self.widget)

    def on_accepted(self):
        from src.features.discord import Webhook

        _list = self.topLevelWidget().parent().list
        _settings = self.topLevelWidget().parent().parent().topLevelWidget().utils.settings

        if not self.check():
            QMessageBox.critical(self, "Error in fields", "There is an error in one or more fields.\n"
                                                          "A label with an asterisk has to be filled",
                                 QMessageBox.StandardButton.Ok)

            return

        if not self.webhook:
            _list.addItem(self.name.text() + f" [{self.url.text()}]")
            _settings.values["discord"]["webhooks"].append(Webhook(
                self.name.text(), self.url.text(), self.username.text())
            )
            _settings.save()
        else:
            self.listItem.setText(self.name.text() + f" [{self.url.text()}]")
            _settings.values["discord"]["webhooks"][_list.indexFromItem(self.listItem).row()] = Webhook(
                self.name.text(), self.url.text(), self.username.text()
            )
            _settings.save()

        self.close()

    def on_rejected(self):
        self.close()

    def check(self) -> bool:
        if "" in [self.name.text(), self.url.text()]:
            return False

        return True


class MainWindow(QMainWindow):
    def __init__(self, parent=None, utils: Utils = ...):
        super(MainWindow, self).__init__(parent)

        self.instant: bool = False

        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        self.clipboard = utils.clipboard

        self.utils = utils
        self.settingsObj = self.utils.settings

        self.settingsWidget = None
        self.editorWidget = None

        self.screenshots = []
        self.currentMonitor = 0

        self.setWindowTitle("Screpo")
        self.setWindowIcon(self.utils.desktopIcon)

        self.tray = QSystemTrayIcon(self)
        self.tray.setToolTip("Screpo")
        self.tray.setIcon(self.utils.trayIcon)
        self.tray.activated.connect(self.showNormal)

        self.tray_menu = QMenu()
        self.tray_menu.addAction("Capture New Screenshot", self.update_screenshots)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction("Exit Screpo", self.close)

        self.tray.setContextMenu(self.tray_menu)
        self.tray.setVisible(True)

        self.imageAndButtons = QVBoxLayout()

        self.imageHolder = QLabel(self)
        self.imageHolder.setFixedSize(525, 525)
        self.imageHolder.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.imageHolder.addAction("Open in Editor", self.open_editor)

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
            "Send to Webhook"
        )
        self.saveImageMenu.addAction(
            QIcon(r"../assets/icons/svg/discord-mark-white.svg"),
            "Send to Webhook w/ Message"
        )

        for action in self.saveImageMenu.actions():
            action.setDisabled(not self.utils.settings.values["general"]["features"]["enable_discord"])

        for index, action in enumerate(self.saveImageMenu.actions()):
            if len(self.utils.settings.values["discord"]["webhooks"]) == 0:
                action.setDisabled(True)
                continue

            menu = QMenu()

            for webhook in self.utils.settings.values["discord"]["webhooks"]:
                if index == 0:
                    menu.addAction(webhook.name, partial(
                        self.utils.discordRef.send_to_webhook,
                        webhook,
                        self.get_current_screenshot
                    ))
                elif index == 1:
                    menu.addAction(webhook.name, partial(
                        self.utils.discordRef.send_to_webhook_with_message,
                        self,
                        webhook,
                        self.get_current_screenshot
                    ))

            action.setMenu(menu)

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

        self.installEventFilter(self)

        self.setTabOrder(self.imageSwitcher.widget(), self.windowSelector)
        self.setTabOrder(self.windowSelector, self.copyImageButton)
        self.setTabOrder(self.copyImageButton, self.saveImageButton)
        self.setTabOrder(self.saveImageButton, self.getScreenshotButton)
        self.setTabOrder(self.getScreenshotButton, self.miscButton)
        self.setTabOrder(self.miscButton, self.settingsButton)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        super().eventFilter(watched, event)
        
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Shift:
                self.getScreenshotButton.setText("Instantly Get New Screenshot")
                self.instant = True
        elif event.type() == QEvent.Type.KeyRelease:
            if event.key() == Qt.Key.Key_Shift:
                self.getScreenshotButton.setText("Get &New Screenshot")
                self.instant = False

        return False

    def update(self) -> None:
        super().update()

        for action in self.saveImageMenu.actions():
            action.setDisabled(not self.utils.settings.values["general"]["features"]["enable_discord"])

        for index, action in enumerate(self.saveImageMenu.actions()):
            if len(self.utils.settings.values["discord"]["webhooks"]) == 0:
                action.setDisabled(True)
                continue

            menu = QMenu()

            for webhook in self.utils.settings.values["discord"]["webhooks"]:
                if index == 0:
                    menu.addAction(webhook.name, partial(
                        self.utils.discordRef.send_to_webhook,
                        webhook,
                        self.get_current_screenshot
                    ))
                elif index == 1:
                    menu.addAction(webhook.name, partial(
                        self.utils.discordRef.send_to_webhook_with_message,
                        self,
                        webhook,
                        self.get_current_screenshot
                    ))

            action.setMenu(menu)

    def update_current_screenshot(self):
        self.imageHolder.setPixmap(
            image_to_pixmap(self.get_current_screenshot(), self.imageHolder)
        )

    def switch_screenshot(self, mon):
        self.currentMonitor = mon
        self.update_current_screenshot()

        self.windowSelector.clear()
        self.windowSelector.addItems(self.windowOptions[mon])

        self.update_button_colours()

    def update_screenshots(self):
        if not self.instant or not self.windowState() & Qt.WindowState.WindowMinimized:
            self.window().showMinimized()
            time.sleep(.285)

        self.screenshots = self.utils.capture_monitors()

        self.update_current_screenshot()

        self.update_button_colours()
        self.imageSwitcher.add_new_button(self.utils.settings.values["general"]["performance"]["history_max_items"])

        self.showNormal()

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
            self.clipboard.setImage(self.get_current_screenshot().toqimage())
            print("Copy: Copied image to clipboard")
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
                self.get_current_screenshot().save(filename)
                print(f"Save: Saved image to {filename}")
            elif filter in ["PNG", "JPEG"]:
                self.get_current_screenshot().save(filename + filter.split("(")[1][1:-1])
                print(f"Save: Saved image to {filename + filter.split('(')[1][1:-1]}")

    def open_settings(self):
        if not self.settingsWidget:
            self.settingsWidget = SettingsWindow(self)

        self.settingsWidget.setFixedSize(self.size().toTuple()[0], self.size().toTuple()[1] // 2)

        self.settingsWidget.show()

    def get_current_screenshot(self):
        return self.screenshots[self.currentMonitor]

    def open_editor(self):
        from src.features.editor import EditorWindow

        if not self.editorWidget:
            self.editorWidget = EditorWindow(self, image=self.screenshots[self.currentMonitor], utils=self.utils)

        self.editorWidget.show()


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
        self.tab_discord__username.title.setToolTip("If no username is provided when creating a url, "
                                                    "this will be used instead.")

        # self.tab_discord__webhook = SettingsLineEdit("Webhook URL", self.utils, ("discord", "webhook_url"))
        self.tab_discord__webhooks = ListEditor(self.utils)

        self.tab_discord.layout().addLayout(self.tab_discord__username)
        self.tab_discord.layout().addSpacerItem(CategorySpacer())
        [self.tab_discord.layout().addWidget(w) for w in [QLabel("Webhooks"), HLine(),
                                                          self.tab_discord__webhooks]]
        self.tab_discord.layout().addStretch(3)

        self.tabs.addTab(self.tab_general, "General")
        if self.tab_general__enable_opencv.isChecked():
            self.tabs.insertTab(1, self.tab_opencv, "OpenCV")

        if self.tab_general__enable_discord.isChecked():
            self.tabs.insertTab(2, self.tab_discord, "Discord")

        if BUILD == "Dev":
            dev_tab = SettingsTab()

            self.tabs.insertTab(999999, dev_tab, "Dev")

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
