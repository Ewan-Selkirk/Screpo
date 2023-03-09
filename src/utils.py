import json
import os
import sys
from os.path import expanduser, exists
from enum import Enum, auto

import mss
from PIL import Image
from PySide6 import QtWidgets
from PySide6.QtGui import QGuiApplication, Qt, QPixmap, QIcon
from PySide6.QtCore import QSize

# noinspection PyUnresolvedReferences
import resources


class BuildType(Enum):
    DEVELOPMENT = auto()
    RELEASE = auto()

    def __str__(self):
        return self.name.title()


VERSION = "0.3.2"
BUILD: BuildType = BuildType.DEVELOPMENT if any(c in sys.argv for c in ["-d", "--dev"]) else BuildType.RELEASE

OLD_DIR = expanduser("~") + "/"
NEW_DIR = OLD_DIR + "/Screpo/"
FILE = ".screpo"


class Utils:
    def __init__(self, app: QGuiApplication = ...):
        self.version = VERSION
        self.build = BUILD

        self.trayIcon = QIcon(":/icons/screpo-tray")
        self.desktopIcon = QIcon(":/icons/screpo-desktop")

        self.app_ref = app
        self.clipboard = app.clipboard()
        self.history = {}

        self.settings = Settings()
        self.themes: list[Theme] = get_all_themes()

        self.discordRef = None

        with mss.mss() as mons:
            self.monitors = mons.monitors[1:]

        self.check_refs()

    def capture_monitors(self) -> list[Image]:
        shots = []

        with mss.mss() as sct:
            for mon in self.monitors:
                shot = sct.grab(mon)
                img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

                shots.append(img)

        if len(self.history) > self.settings.values["general"]["performance"]["history_max_items"]:
            del self.history[list(self.history.keys())[0]]

        if len(self.history):
            self.history[list(self.history.keys())[-1] + 1] = shots.copy()
        else:
            self.history[0] = shots.copy()
        return shots

    def check_refs(self):
        if self.settings.values["general"]["features"]["enable_discord"] and not self.discordRef:
            from features.discord import Discord
            self.discordRef = Discord(self)
            print("Features: Discord reference created")

    def generate_stylesheet(self) -> str:
        theme = next((t for t in self.themes
                      if t == self.settings.values["general"]["appearance"]["current_theme"]), None)
        accent = None

        if not theme:
            return ""

        if self.settings.values["general"]["appearance"]["current_accent"] is not None:
            accent = theme.accents[self.settings.values["general"]["appearance"]["current_accent"]]

        print(f"Settings: Loading custom theme {str(theme)}")

        style = "* {\n\t"
        style += f"background-color: {theme.scheme['background'] or '#00FF00'};\n\t"
        style += f"color: {accent if not None or theme.scheme['font'] else '#00FF00'};\n"

        style += "}\n\nQPushButton, QTabBar {\n\t"
        style += f"background-color: {theme.scheme['mantle'] or '#00FF00'};\n"
        style += "}"

        return style


class Theme:
    def __init__(self, theme: dict):
        self.name: str = theme["name"]
        self.authors: str = theme["authors"]

        self.scheme: dict = theme["scheme"]
        if "accents" in theme:
            self.accents: dict = theme["accents"]

        self.filename = self.name.lower().replace(" ", "-")

    def __str__(self):
        return f"{self.name} ({', '.join(self.authors)})"

    def __eq__(self, other):
        return self.filename == other


class Settings:
    def __init__(self):
        self.values: dict = ...

        if not self.load():
            self.create()
        else:
            self.check()

    @staticmethod
    def get_default_settings() -> dict:
        return {
            "general": {
                "appearance": {
                    "current_theme": None,
                    "current_accent": None
                },
                "features": {
                    "enable_opencv": False,
                    "enable_discord": False
                },
                "performance": {
                    "history_max_items": 8
                }
            },
            "opencv": {

            },
            "discord": {
                "username": "",
                "webhooks": {}
            }
        }

    def create(self):
        self.values = self.get_default_settings()
        print("Settings: No settings file found. Creating a new one")
        self.save()

    def load(self) -> bool:
        if exists(OLD_DIR + FILE):
            from shutil import move

            if not exists(NEW_DIR):
                os.mkdir(NEW_DIR)

            print(f"Settings: Migrating old settings file to new location \n\t({OLD_DIR + FILE} -> {NEW_DIR + FILE})")
            move(OLD_DIR + FILE, NEW_DIR + FILE)

        if exists(NEW_DIR + FILE):
            try:
                with open(NEW_DIR + FILE, "r") as f:
                    self.values = json.load(f)
                    self.__convert_webhooks()

                    print("Settings: Settings file found and loaded")
                    return True
            except IOError:
                print("Settings: Settings file corrupt or unreadable. Creating a new one")
                self.create()
        else:
            return False

    def save(self):
        with open(NEW_DIR + FILE, "w") as f:
            tmp_list = self.values.copy()
            hooks = {}

            for webhook in tmp_list["discord"]["webhooks"]:
                hooks[webhook.name] = {"url": webhook.url, "username": webhook.username}

            tmp_list["discord"]["webhooks"] = hooks
            json.dump(tmp_list, f)

        # Saving for some reason turns the webhook objects into dicts (despite using an extra variable...)
        # so we need to turn them back into Webhook objects
        self.__convert_webhooks()
        print(f"Settings: Saved data to {NEW_DIR + FILE}")

    def check(self):
        # This will cause issues say if a setting is removed while another is added
        # TODO: Switch from using the length as the condition
        if nested_dict_len(self.values) < nested_dict_len(self.get_default_settings()):
            # Backup the old config just in case
            os.rename(NEW_DIR + FILE, NEW_DIR + FILE + ".bak")
            temp_config = self.get_default_settings().copy()

            migrate_config(self.values, temp_config)

            self.values = temp_config

            self.save()
            print("Settings: Successfully mitigated new settings over to old save file")

    def __convert_webhooks(self):
        from features.discord import Webhook

        tmp_list = []
        for webhook in self.values["discord"]["webhooks"]:
            tmp_list.append(Webhook(webhook, self.values["discord"]["webhooks"][webhook]["url"],
                                    self.values["discord"]["webhooks"][webhook]["username"]))

        self.values["discord"]["webhooks"] = tmp_list


# Stolen from Example 2 on GeeksForGeeks
# https://www.geeksforgeeks.org/get-length-of-dictionary-in-python/
def nested_dict_len(d):
    length = len(d)
    for key, value in d.items():
        if isinstance(value, dict):
            length += nested_dict_len(value)
    return length


def migrate_config(old: dict, new: dict) -> None:
    for k, v in old.items():
        if isinstance(v, dict):
            migrate_config(v, new[k])
        else:
            if k in new:
                new[k] = v


def image_to_pixmap(image: Image, label: QtWidgets.QLabel, offset: QSize = QSize(0, 0),
                    aspect: Qt.AspectRatioMode = Qt.AspectRatioMode.KeepAspectRatio,
                    transform: Qt.TransformationMode = Qt.TransformationMode.SmoothTransformation) -> QPixmap:
    return QPixmap.fromImage(image.toqimage()).scaled(
        label.size() - offset,
        aspect,
        transform
    )


def get_all_themes() -> list[Theme]:
    themes = []
    existing: set = set()

    if exists(NEW_DIR + "themes/"):
        for i, t in enumerate(os.listdir(NEW_DIR + "themes/")):
            with open(NEW_DIR + "themes/" + t) as f:
                themes.append(Theme(json.load(f)))
                existing.add(themes[i].filename)

    for t in os.listdir("./themes/"):
        with open(f"./themes/{t}") as f:
            if t[:-5] not in existing:
                themes.append(Theme(json.load(f)))

    return themes
